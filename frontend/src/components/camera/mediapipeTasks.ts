import {
  FaceLandmarker,
  HandLandmarker,
  PoseLandmarker,
  FilesetResolver,
  type FaceLandmarkerResult,
  type HandLandmarkerResult,
  type PoseLandmarkerResult,
} from '@mediapipe/tasks-vision';

// Keep in sync with `RSLdataset/utils.py` FACE_KEY_INDICES.
const FACE_KEY_INDICES_RAW: number[] = [
  // Face outline (17)
  10, 21, 54, 103, 127, 132, 150, 152, 172, 176, 284, 297, 361, 379, 389, 397, 400,
  // Eyes (12)
  33, 133, 144, 153, 158, 160, 263, 362, 373, 380, 385, 387,
  // Eyebrows (10)
  46, 52, 53, 55, 65, 276, 282, 283, 285, 295,
  // Nose (9)
  1, 2, 4, 5, 6, 98, 168, 195, 327,
  // Lips (20)
  13, 17, 61, 78, 82, 84, 87, 91, 146, 178, 181, 291, 308, 310, 311, 312, 314, 321, 375, 405,
];

// The trainer uses `sorted(set([...]))`, so ordering must be ascending.
export const FACE_KEY_INDICES: number[] = Array.from(new Set(FACE_KEY_INDICES_RAW)).sort((a, b) => a - b);

export const TOTAL_FEATURES = 99 + (FACE_KEY_INDICES.length * 3) + 63 + 63; // 429

type Landmarkers = {
  pose: PoseLandmarker;
  hands: HandLandmarker;
  face: FaceLandmarker;
};

let landmarkersPromise: Promise<Landmarkers> | null = null;

async function createLandmarkers(delegate: 'GPU' | 'CPU'): Promise<Landmarkers> {
  const wasm = await FilesetResolver.forVisionTasks('/wasm');

  // For GPU delegate we must provide a canvas to bind textures.
  // Keep it separate from any UI canvas to avoid WebGL/2D context conflicts.
  const gpuCanvas = delegate === 'GPU' ? document.createElement('canvas') : undefined;

  const pose = await PoseLandmarker.createFromOptions(wasm, {
    baseOptions: { modelAssetPath: '/mp_models/pose_landmarker.task', delegate },
    runningMode: 'VIDEO',
    numPoses: 1,
    minPoseDetectionConfidence: 0.5,
    minPosePresenceConfidence: 0.5,
    minTrackingConfidence: 0.5,
    canvas: gpuCanvas,
  });

  const hands = await HandLandmarker.createFromOptions(wasm, {
    baseOptions: { modelAssetPath: '/mp_models/hand_landmarker.task', delegate },
    runningMode: 'VIDEO',
    numHands: 2,
    minHandDetectionConfidence: 0.5,
    minHandPresenceConfidence: 0.5,
    minTrackingConfidence: 0.5,
    canvas: gpuCanvas,
  });

  const face = await FaceLandmarker.createFromOptions(wasm, {
    baseOptions: { modelAssetPath: '/mp_models/face_landmarker.task', delegate },
    runningMode: 'VIDEO',
    numFaces: 1,
    minFaceDetectionConfidence: 0.5,
    minFacePresenceConfidence: 0.5,
    minTrackingConfidence: 0.5,
    outputFaceBlendshapes: false,
    outputFacialTransformationMatrixes: false,
    canvas: gpuCanvas,
  });

  return { pose, hands, face };
}

export async function getLandmarkers(): Promise<Landmarkers> {
  if (landmarkersPromise) return landmarkersPromise;

  landmarkersPromise = (async () => {
    try {
      return await createLandmarkers('GPU');
    } catch (err) {
      console.warn('[mediapipe] GPU init failed, falling back to CPU.', err);
      return await createLandmarkers('CPU');
    }
  })();

  return landmarkersPromise;
}

function zeros(n: number): number[] {
  return Array.from({ length: n }, () => 0);
}

function fixedLen(arr: number[], n: number): number[] {
  if (arr.length === n) return arr;
  if (arr.length > n) return arr.slice(0, n);
  return arr.concat(zeros(n - arr.length));
}

// Extract and flatten keypoints into a vector compatible with `RSLdataset/utils.py`.
// Shape: Pose(33x3)=99 + Face(key_indices x3) + LH(21x3)=63 + RH(21x3)=63 => 429
export function extractKeypoints429(
  poseRes: PoseLandmarkerResult | null,
  handRes: HandLandmarkerResult | null,
  faceRes: FaceLandmarkerResult | null,
): number[] {
  // Pose: 33 x 3 (take first detected pose)
  const poseLandmarks = poseRes?.landmarks?.[0] ?? [];
  const pose = poseLandmarks.length
    ? fixedLen(poseLandmarks.flatMap((l) => [l.x, l.y, l.z]), 99)
    : zeros(99);

  // Face: key indices x 3 (take first detected face)
  const faceLandmarks = faceRes?.faceLandmarks?.[0] ?? [];
  let face: number[];
  if (faceLandmarks.length) {
    const out: number[] = [];
    for (const idx of FACE_KEY_INDICES) {
      const lm = faceLandmarks[idx];
      out.push(lm?.x ?? 0, lm?.y ?? 0, lm?.z ?? 0);
    }
    face = out;
  } else {
    face = zeros(FACE_KEY_INDICES.length * 3);
  }

  // Hands: left and right, assigned via handedness
  let lh = zeros(63);
  let rh = zeros(63);
  const handLandmarks = handRes?.landmarks ?? [];
  const handedness = handRes?.handedness ?? [];
  for (let i = 0; i < handLandmarks.length; i++) {
    const lms = handLandmarks[i] ?? [];
    const data = fixedLen(lms.flatMap((l) => [l.x, l.y, l.z]), 63);
    const side = (handedness[i]?.[0]?.categoryName || '').toLowerCase();
    if (side === 'left') lh = data;
    else rh = data;
  }

  const full = [...pose, ...face, ...lh, ...rh];
  // Defensive: guarantee stable size for the model input contract.
  return fixedLen(full, TOTAL_FEATURES);
}
