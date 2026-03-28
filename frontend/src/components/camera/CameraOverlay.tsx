import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mascot } from '@/components/ui/Mascot';
import { signAPI, type SignPrediction } from '@/services/api';
import { extractKeypoints429, getLandmarkers, TOTAL_FEATURES } from './mediapipeTasks';

export interface CameraEvaluationResult {
  success: boolean;
  score: number;
  confidence: number;
  targetConfidence?: number;
  idleConfidence?: number;
  predictedLabel: string;
  expectedLabel: string;
  noSignDetected?: boolean;
  message?: string;
  error?: string;
  topPredictions: SignPrediction[];
}

interface CameraOverlayProps {
  prompt: string;
  expectedLabel?: string;
  minConfidence?: number;
  onComplete: (result: CameraEvaluationResult) => void;
  onClose: () => void;
}

const DEFAULT_SEQUENCE_LENGTH = 60; // default to the current 2-second model window

const zeros = (count: number): number[] => Array.from({ length: count }, () => 0);

const resampleSequence = (sequence: number[][], targetLength: number): number[][] => {
  if (!sequence.length) {
    return Array.from({ length: targetLength }, () => zeros(TOTAL_FEATURES));
  }

  if (sequence.length === targetLength) {
    return sequence.map((frame) => frame.slice());
  }

  if (sequence.length === 1) {
    return Array.from({ length: targetLength }, () => sequence[0].slice());
  }

  return Array.from({ length: targetLength }, (_, outIndex) => {
    const position = (outIndex * (sequence.length - 1)) / (targetLength - 1);
    const lower = Math.floor(position);
    const upper = Math.ceil(position);
    const alpha = position - lower;
    const lowFrame = sequence[lower];
    const highFrame = sequence[upper];
    return lowFrame.map((value, featureIndex) => (
      value * (1 - alpha) + highFrame[featureIndex] * alpha
    ));
  });
};

export const CameraOverlay: React.FC<CameraOverlayProps> = ({ prompt, expectedLabel, minConfidence, onComplete, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  const [status, setStatus] = useState<'loading' | 'countdown' | 'recording' | 'processing' | 'result'>('loading');
  const [countdown, setCountdown] = useState(3);
  const [result, setResult] = useState<CameraEvaluationResult | null>(null);
  const [framesCount, setFramesCount] = useState(0);
  const [initError, setInitError] = useState<string | null>(null);
  const [sequenceLength, setSequenceLength] = useState(DEFAULT_SEQUENCE_LENGTH);
  const [recordingHint, setRecordingHint] = useState('Aștept semnul...');

  const statusRef = useRef(status);
  const isFinishingRef = useRef(false);
  const framesRef = useRef<number[][]>([]);
  const warnedNoModelRef = useRef(false);
  const sequenceLengthRef = useRef(DEFAULT_SEQUENCE_LENGTH);
  const captureFramesRef = useRef(0);

  const streamRef = useRef<MediaStream | null>(null);
  const rafIdRef = useRef<number | null>(null);
  const vfcHandleRef = useRef<number | null>(null);
  const stopRequestedRef = useRef(false);
  const lastProcessMsRef = useRef(0);
  const lastMpTimestampMsRef = useRef(0);

  const landmarkersRef = useRef<Awaited<ReturnType<typeof getLandmarkers>> | null>(null);

  const resetRecordingState = useCallback(() => {
    framesRef.current = [];
    captureFramesRef.current = 0;
    setFramesCount(0);
    setRecordingHint('Înregistrare...');
  }, []);

  const finalizeWithResult = useCallback((nextResult: CameraEvaluationResult) => {
    setResult(nextResult);
    statusRef.current = 'result';
    setStatus('result');
    isFinishingRef.current = false;
  }, []);

  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  const stopLoopAndCamera = useCallback(() => {
    stopRequestedRef.current = true;

    if (rafIdRef.current !== null) {
      cancelAnimationFrame(rafIdRef.current);
      rafIdRef.current = null;
    }

    const videoAny = videoRef.current as any;
    if (vfcHandleRef.current !== null && videoAny?.cancelVideoFrameCallback) {
      try {
        videoAny.cancelVideoFrameCallback(vfcHandleRef.current);
      } catch {
        // ignore
      }
      vfcHandleRef.current = null;
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
  }, []);

  // Initialize camera + MediaPipe Tasks (local models, no CDN).
  useEffect(() => {
    let cancelled = false;

    const init = async () => {
      try {
        // Kick off model init early (runs in parallel with webcam permission prompt).
        const landmarkersPromise = getLandmarkers();

        // Informative log for prototype: if model isn't deployed, be explicit.
        signAPI.getStatus()
          .then((st) => {
            if (typeof st?.required_sequence_length === 'number' && st.required_sequence_length > 0) {
              sequenceLengthRef.current = st.required_sequence_length;
              setSequenceLength(st.required_sequence_length);
            }
            if (!st?.model_loaded && !warnedNoModelRef.current) {
              warnedNoModelRef.current = true;
              console.warn('[ai] No server model loaded yet. Recognition calls will return stub results until a model is deployed.');
            }
          })
          .catch(() => {
            // backend not reachable; ignore here
          });

        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480, facingMode: 'user' },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;

        if (!videoRef.current) throw new Error('Video element not ready');
        videoRef.current.srcObject = stream;
        videoRef.current.muted = true;
        await videoRef.current.play();
        if (cancelled) {
          stopLoopAndCamera();
          return;
        }

        landmarkersRef.current = await landmarkersPromise;
        if (cancelled) {
          stopLoopAndCamera();
          return;
        }

        stopRequestedRef.current = false;
        // Reset local throttling/timestamp guards for this session.
        lastProcessMsRef.current = 0;
        lastMpTimestampMsRef.current = 0;
        setStatus('countdown');

        const runFrame = (now: number, _meta?: any) => {
          if (stopRequestedRef.current) return;

          const video = videoRef.current;
          if (!video) return;

          const currentStatus = statusRef.current;
          const shouldDetect = currentStatus !== 'processing' && currentStatus !== 'result';

          const videoAny = video as any;
          const hasVfc = typeof videoAny?.requestVideoFrameCallback === 'function';
          const rawNow = typeof now === 'number' ? now : performance.now();

          // Throttle to ~30fps so the web recorder follows the model-required clip length.
          // This also reduces compute and makes timing more stable.
          const shouldSample = rawNow - lastProcessMsRef.current >= 33;

          if (shouldDetect && shouldSample && video.readyState >= 2 && landmarkersRef.current) {
            try {
              lastProcessMsRef.current = rawNow;

              // MediaPipe VIDEO mode requires *strictly* increasing timestamps.
              // Use an integer and enforce monotonicity to avoid occasional float rounding issues.
              let mpTimestampMs = Math.floor(rawNow);
              if (mpTimestampMs <= lastMpTimestampMsRef.current) {
                mpTimestampMs = lastMpTimestampMsRef.current + 1;
              }
              lastMpTimestampMsRef.current = mpTimestampMs;
              const { pose, hands, face } = landmarkersRef.current;

              const poseRes = pose.detectForVideo(video, mpTimestampMs);
              const handRes = hands.detectForVideo(video, mpTimestampMs);
              const faceRes = face.detectForVideo(video, mpTimestampMs);

              if (currentStatus === 'recording' && !isFinishingRef.current) {
                const keypoints = extractKeypoints429(poseRes, handRes, faceRes);
                if (keypoints.length !== TOTAL_FEATURES) {
                  console.warn(`[mediapipe] Expected ${TOTAL_FEATURES} features, got ${keypoints.length}.`);
                }

                framesRef.current.push(keypoints);
                captureFramesRef.current += 1;
                setFramesCount(Math.min(captureFramesRef.current, sequenceLengthRef.current));
                setRecordingHint('Înregistrare...');

                if (captureFramesRef.current >= sequenceLengthRef.current) {
                  isFinishingRef.current = true;
                  statusRef.current = 'processing';
                  setStatus('processing');
                  const payload = resampleSequence(
                    framesRef.current.slice(-sequenceLengthRef.current),
                    sequenceLengthRef.current,
                  );
                  setTimeout(() => finishRecording(payload), 0);
                }
              }
            } catch (err) {
              // Detection can fail transiently; don't kill the stream/loop.
              console.warn('[mediapipe] detectForVideo failed:', err);
            }
          }

          if (typeof videoAny?.requestVideoFrameCallback === 'function') {
            vfcHandleRef.current = videoAny.requestVideoFrameCallback(runFrame);
          } else {
            rafIdRef.current = requestAnimationFrame((t) => runFrame(t));
          }
        };

        const videoAny = videoRef.current as any;
        if (typeof videoAny?.requestVideoFrameCallback === 'function') {
          vfcHandleRef.current = videoAny.requestVideoFrameCallback(runFrame);
        } else {
          rafIdRef.current = requestAnimationFrame((t) => runFrame(t));
        }
      } catch (e: any) {
        console.error(e);
        setInitError(e?.message || 'Camera init failed');
      }
    };

    init();

    return () => {
      cancelled = true;
      stopLoopAndCamera();
    };
  }, [stopLoopAndCamera]);

  // Countdown Logic
  useEffect(() => {
    if (status === 'countdown') {
      if (countdown > 0) {
        const timer = setTimeout(() => setCountdown(c => c - 1), 1000);
        return () => clearTimeout(timer);
      } else {
        isFinishingRef.current = false;
        resetRecordingState();
        statusRef.current = 'recording';
        lastProcessMsRef.current = 0;
        lastMpTimestampMsRef.current = 0;
        setStatus('recording');
      }
    }
  }, [status, countdown, resetRecordingState]);

  const normalizeLabel = (value: string): string =>
    (value || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/["'`“”„]/g, '')
      .replace(/[_-]+/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();

  const extractTargetFromPrompt = (rawPrompt: string): string => {
    const afterColon = rawPrompt.includes(':') ? rawPrompt.split(':').pop() || rawPrompt : rawPrompt;
    return normalizeLabel(afterColon);
  };

  const displayPrompt = (expectedLabel || (prompt.includes(':') ? (prompt.split(':').pop() || prompt) : prompt)).trim();

  const finishRecording = async (finalFrames: number[][]) => {
    statusRef.current = 'processing';
    setStatus('processing');
    try {
      const targetRaw = (expectedLabel || extractTargetFromPrompt(prompt)).trim();
      const target = normalizeLabel(targetRaw);
      const threshold = typeof minConfidence === 'number' ? minConfidence : 0.6;
      const payload = resampleSequence(finalFrames, sequenceLengthRef.current).slice(0, sequenceLengthRef.current);
      const res = await signAPI.recognise(payload, {
        targetLabel: targetRaw,
        topK: 5,
      });

      if (!res) {
        throw new Error('Recunoasterea semnului a esuat.');
      }
      if (!res.success) {
        throw new Error(res.error || 'Recunoasterea semnului a esuat.');
      }

      if ((res as any)?.model_stub && !warnedNoModelRef.current) {
        warnedNoModelRef.current = true;
        console.warn('[ai] Model not deployed yet; server returned a stub recognition result.');
      }

      const predictedRaw = (res.prediction || '').trim();
      const predicted = normalizeLabel(predictedRaw);
      const targetConfidence = typeof res.target_confidence === 'number' ? res.target_confidence : 0;
      const idleConfidence = typeof res.idle_confidence === 'number' ? res.idle_confidence : 0;
      const verificationConfidence = target ? targetConfidence : (res.confidence || 0);
      const score = Math.round(verificationConfidence * 100);
      const conf = res.confidence || 0;
      const isIdlePrediction = predicted === 'idle';
      const isMatch = !!target && (
        predicted === target ||
        predicted.includes(target) ||
        target.includes(predicted) ||
        targetConfidence >= threshold
      );
      const success = !!target
        ? (targetConfidence >= threshold && targetConfidence >= idleConfidence)
        : (isMatch && conf >= threshold);

      finalizeWithResult({
        success,
        score,
        confidence: conf,
        targetConfidence,
        idleConfidence,
        predictedLabel: predictedRaw,
        expectedLabel: targetRaw,
        noSignDetected: isIdlePrediction,
        topPredictions: res.all_predictions || [],
        message: success
          ? 'Perfect!'
          : isIdlePrediction
            ? 'Modelul a detectat fundal sau lipsa unui semn clar. Incearca sa faci semnul mai aproape de camera si cu mainile complet in cadru.'
            : predictedRaw
              ? `Modelul a detectat "${predictedRaw}".`
              : 'Modelul nu a putut identifica semnul.',
        error: isIdlePrediction
          ? 'Semnul nu a fost capturat suficient de clar. Incearca sa incepi cu mainile deja vizibile in cadru.'
          : undefined,
      });
    } catch (e) {
      console.error(e);
      finalizeWithResult({
        success: false,
        score: 0,
        confidence: 0,
        predictedLabel: '',
        expectedLabel: expectedLabel || displayPrompt,
        noSignDetected: true,
        message: 'Evaluarea nu s-a putut finaliza.',
        error: e instanceof Error ? e.message : 'A aparut o eroare la evaluarea semnului.',
        topPredictions: [],
      });
    }
  };

  const handleRetry = () => {
    isFinishingRef.current = false;
    statusRef.current = 'countdown';
    resetRecordingState();
    setCountdown(3);
    setResult(null);
    setStatus('countdown');
  };

  return (
    <div className="fixed inset-0 bg-black/90 flex flex-col items-center justify-center z-50 p-4">
      <div className="relative w-[calc(100vw-2rem)] max-w-[640px] aspect-[4/3] bg-black rounded-xl overflow-hidden shadow-2xl border-4 border-gray-800">
        {/* Clean webcam preview; MediaPipe reads from this element without drawing overlays */}
        <video
          ref={videoRef}
          className="w-full h-full object-cover transform -scale-x-100"
          playsInline
          muted
        />

        {/* Overlays */}
        <div className="absolute top-4 left-0 right-0 text-center">
          <h2 className="text-white text-lg sm:text-2xl font-bold bg-black/50 inline-block px-3 sm:px-4 py-1 rounded-full max-w-[95%] leading-snug break-words">
            Semnul: "{displayPrompt}"
          </h2>
        </div>

        {status === 'loading' && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/80 text-white">
            {initError ? `Eroare: ${initError}` : 'Se încarcă camera...'}
          </div>
        )}

        {status === 'countdown' && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/40">
            <span className="text-7xl sm:text-9xl font-bold text-white animate-bounce">{countdown}</span>
          </div>
        )}

        {status === 'recording' && (
          <div className="absolute bottom-4 left-0 right-0 px-6 sm:px-8">
            <div className="h-2 bg-gray-600 rounded-full overflow-hidden">
                <div
                className="h-full bg-red-500 transition-all duration-75"
                style={{ width: `${(framesCount / sequenceLength) * 100}%` }}
              />
            </div>
            <p className="text-center text-white mt-1">{recordingHint}</p>
          </div>
        )}

        {status === 'processing' && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/60 text-white text-lg sm:text-xl">
            Analizez...
          </div>
        )}

        {status === 'result' && result && (
          <div className="absolute inset-0 bg-black/80 flex flex-col items-center justify-center text-white p-4 sm:p-6 text-center">
            <Mascot pose={result.success ? 'celebrate' : 'wink'} className="w-24 h-24 sm:w-32 sm:h-32 mb-4" />
            <h3 className="text-2xl sm:text-3xl font-bold mb-2">{result.success ? 'Perfect!' : 'Mai încearcă!'}</h3>
            <p className="text-lg sm:text-xl">
              {result.expectedLabel ? 'Încredere pentru semnul cerut' : 'Încrederea modelului'}: {result.score}%
            </p>
            {!result.success && result.predictedLabel && (
              <p className="text-sm sm:text-base text-white/80 mt-2">
                Detectat: <span className="font-bold">{result.predictedLabel}</span>
              </p>
            )}
            {!result.success && typeof result.idleConfidence === 'number' && result.idleConfidence > 0 && (
              <p className="text-sm sm:text-base text-white/70 mt-1">
                Fundal/idle: <span className="font-bold">{Math.round(result.idleConfidence * 100)}%</span>
              </p>
            )}
            {!result.success && !!result.expectedLabel && (
              <p className="text-sm sm:text-base text-white/80 mt-1">
                Așteptat: <span className="font-bold">{result.expectedLabel}</span>
              </p>
            )}
            {result.error && (
              <p className="text-sm sm:text-base text-red-200 mt-3 max-w-md">{result.error}</p>
            )}
            {!result.error && result.message && !result.success && (
              <p className="text-sm sm:text-base text-white/80 mt-3 max-w-md">{result.message}</p>
            )}

            <div className="flex gap-4">
              <button onClick={handleRetry} className="px-4 sm:px-6 py-2 bg-gray-600 rounded-lg hover:bg-gray-500 font-bold">
                Reîncearcă
              </button>
              <button
                onClick={() => onComplete(result)}
                className={`px-4 sm:px-6 py-2 rounded-lg font-bold ${result.success ? 'bg-green-500 hover:bg-green-400' : 'bg-gray-600'}`}
              >
                Continuă
              </button>
            </div>
          </div>
        )}
      </div>

      <button onClick={onClose} className="mt-4 sm:mt-6 text-white text-sm hover:underline">
        Anulează și închide
      </button>

    </div>
  );
};
