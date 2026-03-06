export type AchievementIconMeta = {
  key: string;
  fileName: string;
  url: string;
};

// Auto-detect all SVGs under `src/assets/achievements`.
// Adding/removing SVGs here updates the admin icon dropdown at build time (and via HMR in dev).
const iconModules = import.meta.glob('../assets/achievements/*.svg', {
  eager: true,
}) as Record<string, { default: string }>;

const ICONS: AchievementIconMeta[] = Object.entries(iconModules)
  .map(([path, module]) => {
    const fileName = path.split('/').pop() || path;
    const key = fileName.replace(/\.svg$/i, '');
    return { key, fileName, url: module.default };
  })
  .sort((a, b) => a.key.localeCompare(b.key, 'en'));

const ICONS_BY_KEY = new Map(ICONS.map((i) => [i.key, i.url] as const));

export const ACHIEVEMENT_ICONS = ICONS;
export const ACHIEVEMENT_ICON_KEYS = ICONS.map((i) => i.key);

export function getAchievementIconUrl(key?: string | null): string | null {
  if (!key) return null;
  return ICONS_BY_KEY.get(key) || null;
}

export function hasAchievementIcon(key?: string | null): boolean {
  return !!getAchievementIconUrl(key);
}
