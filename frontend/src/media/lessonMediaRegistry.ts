export type LessonMediaMeta = {
  // Stable value to store in the DB/editor. We use the file name (including extension).
  key: string;
  fileName: string;
  url: string;
};

// Auto-detect all videos under `src/assets/lesson-media`.
// Adding/removing files here updates the admin video suggestions at build time (and via HMR in dev).
const mediaModules = import.meta.glob('../assets/lesson-media/*.{mp4,webm,ogg}', {
  eager: true,
}) as Record<string, { default: string }>;

const MEDIA: LessonMediaMeta[] = Object.entries(mediaModules)
  .map(([path, module]) => {
    const fileName = path.split('/').pop() || path;
    const key = fileName;
    return { key, fileName, url: module.default };
  })
  .sort((a, b) => a.fileName.localeCompare(b.fileName, 'en'));

const MEDIA_BY_KEY = new Map(MEDIA.map((m) => [m.key, m.url] as const));

export const LESSON_MEDIA = MEDIA;
export const LESSON_MEDIA_KEYS = MEDIA.map((m) => m.key);

export function getLessonMediaUrl(key?: string | null): string | null {
  if (!key) return null;
  return MEDIA_BY_KEY.get(key) || null;
}

// For persisted values coming from the DB:
// - accept absolute/relative URLs (`/..`, `http..`, `https..`, `data:`, `blob:`)
// - accept an asset key (`hello.mp4`) or an explicitly prefixed one (`asset:hello.mp4`)
export function resolveLessonMediaUrl(value?: string | null): string | null {
  if (!value) return null;
  const raw = String(value).trim();
  if (!raw) return null;

  if (
    raw.startsWith('/') ||
    raw.startsWith('http://') ||
    raw.startsWith('https://') ||
    raw.startsWith('data:') ||
    raw.startsWith('blob:')
  ) {
    return raw;
  }

  const key = raw.startsWith('asset:') ? raw.slice('asset:'.length) : raw;
  return getLessonMediaUrl(key) || raw;
}

