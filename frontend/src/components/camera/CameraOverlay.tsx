import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Mascot } from '@/components/ui/Mascot';
import { signAPI } from '@/services/api';
import { DrawingUtils, HandLandmarker, PoseLandmarker } from '@mediapipe/tasks-vision';
import { extractKeypoints429, getLandmarkers, TOTAL_FEATURES } from './mediapipeTasks';

interface CameraOverlayProps {
  prompt: string;
  expectedLabel?: string;
  minConfidence?: number;
  onComplete: (success: boolean, score: number) => void;
  onClose: () => void;
}

const SEQUENCE_LENGTH = 90; // 3 seconds

export const CameraOverlay: React.FC<CameraOverlayProps> = ({ prompt, expectedLabel, minConfidence, onComplete, onClose }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [status, setStatus] = useState<'loading' | 'countdown' | 'recording' | 'processing' | 'result'>('loading');
  const [countdown, setCountdown] = useState(3);
  const [result, setResult] = useState<{ success: boolean, score: number } | null>(null);
  const [framesCount, setFramesCount] = useState(0);
  const [initError, setInitError] = useState<string | null>(null);

  const statusRef = useRef(status);
  const isFinishingRef = useRef(false);
  const framesRef = useRef<number[][]>([]);
  const warnedNoModelRef = useRef(false);

  const streamRef = useRef<MediaStream | null>(null);
  const rafIdRef = useRef<number | null>(null);
  const vfcHandleRef = useRef<number | null>(null);
  const stopRequestedRef = useRef(false);
  const lastProcessMsRef = useRef(0);
  const lastMpTimestampMsRef = useRef(0);

  const landmarkersRef = useRef<Awaited<ReturnType<typeof getLandmarkers>> | null>(null);
  const drawingRef = useRef<DrawingUtils | null>(null);

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
          const canvas = canvasRef.current;
          if (!video || !canvas) return;

          const ctx = canvas.getContext('2d');
          if (!ctx) return;

          if (!drawingRef.current) {
            drawingRef.current = new DrawingUtils(ctx);
          }

          // Always draw the video frame as the base layer.
          ctx.save();
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          if (video.readyState >= 2) {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          }

          const currentStatus = statusRef.current;
          const shouldDetect = currentStatus !== 'processing' && currentStatus !== 'result';

          const videoAny = video as any;
          const hasVfc = typeof videoAny?.requestVideoFrameCallback === 'function';
          const rawNow = typeof now === 'number' ? now : performance.now();

          // Throttle to ~30fps so 90 frames ~= 3 seconds and matches the dataset pipeline.
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

              // Draw pose + hands (simple, low-overhead).
              const drawing = drawingRef.current;
              const poseLm = poseRes.landmarks?.[0];
              if (poseLm?.length) {
                drawing.drawConnectors(poseLm, PoseLandmarker.POSE_CONNECTIONS, { color: '#00FF00', lineWidth: 1 });
              }

              const handsLm = handRes.landmarks ?? [];
              const handedness = handRes.handedness ?? [];
              for (let i = 0; i < handsLm.length; i++) {
                const lms = handsLm[i];
                if (!lms?.length) continue;
                const side = (handedness[i]?.[0]?.categoryName || '').toLowerCase();
                const color = side === 'left' ? '#FF0000' : '#0000FF';
                drawing.drawConnectors(lms, HandLandmarker.HAND_CONNECTIONS, { color, lineWidth: 2 });
              }

              // Record (exactly 90 frames), using the same 429-feature layout as `RSLdataset/utils.py`.
              if (currentStatus === 'recording' && !isFinishingRef.current) {
                const keypoints = extractKeypoints429(poseRes, handRes, faceRes);
                if (keypoints.length !== TOTAL_FEATURES) {
                  console.warn(`[mediapipe] Expected ${TOTAL_FEATURES} features, got ${keypoints.length}.`);
                }

                if (framesRef.current.length < SEQUENCE_LENGTH) {
                  framesRef.current.push(keypoints);
                  setFramesCount(framesRef.current.length);
                }

                if (framesRef.current.length >= SEQUENCE_LENGTH) {
                  isFinishingRef.current = true;
                  statusRef.current = 'processing';
                  setStatus('processing');
                  const payload = framesRef.current.slice(0, SEQUENCE_LENGTH);
                  setTimeout(() => finishRecording(payload), 0);
                }
              }
            } catch (err) {
              // Detection can fail transiently; don't kill the stream/loop.
              console.warn('[mediapipe] detectForVideo failed:', err);
            }
          }

          ctx.restore();

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
        setStatus('recording');
        framesRef.current = [];
        setFramesCount(0);
      }
    }
  }, [status, countdown]);

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
      // Send only first SEQUENCE_LENGTH frames if we have more
      const payload = finalFrames.slice(0, SEQUENCE_LENGTH);
      const res = await signAPI.recognise(payload);

      if ((res as any)?.model_stub && !warnedNoModelRef.current) {
        warnedNoModelRef.current = true;
        console.warn('[ai] Model not deployed yet; server returned a stub recognition result.');
      }

      const predicted = normalizeLabel(res.prediction || '');
      const target = expectedLabel ? normalizeLabel(expectedLabel) : extractTargetFromPrompt(prompt);
      const threshold = typeof minConfidence === 'number' ? minConfidence : 0.6;
      const score = Math.round((res.confidence || 0) * 100);

      const conf = res.confidence || 0;
      const isMatch = !!target && (
        predicted === target ||
        predicted.includes(target) ||
        target.includes(predicted)
      );
      const success = isMatch && conf >= threshold;

      setResult({ success, score });
      statusRef.current = 'result';
      setStatus('result');
    } catch (e) {
      console.error(e);
      setResult({ success: false, score: 0 });
      statusRef.current = 'result';
      setStatus('result');
    } finally {
      isFinishingRef.current = false;
    }
  };

  const handleRetry = () => {
    isFinishingRef.current = false;
    statusRef.current = 'countdown';
    framesRef.current = [];
    setFramesCount(0);
    setCountdown(3);
    setResult(null);
    setStatus('countdown');
  };

  return (
    <div className="fixed inset-0 bg-black/90 flex flex-col items-center justify-center z-50 p-4">

      {/* MediaPipe Hidden Video */}
      <video ref={videoRef} className="hidden" playsInline />

      <div className="relative w-[calc(100vw-2rem)] max-w-[640px] aspect-[4/3] bg-black rounded-xl overflow-hidden shadow-2xl border-4 border-gray-800">
        <canvas ref={canvasRef} width={640} height={480} className="w-full h-full object-cover transform -scale-x-100" />

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
                style={{ width: `${(framesCount / SEQUENCE_LENGTH) * 100}%` }}
              />
            </div>
            <p className="text-center text-white mt-1">Înregistrare...</p>
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
            <p className="text-lg sm:text-xl mb-6">Acuratețe: {result.score}%</p>

            <div className="flex gap-4">
              <button onClick={handleRetry} className="px-4 sm:px-6 py-2 bg-gray-600 rounded-lg hover:bg-gray-500 font-bold">
                Reîncearcă
              </button>
              <button
                onClick={() => onComplete(result.success, result.score)}
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
