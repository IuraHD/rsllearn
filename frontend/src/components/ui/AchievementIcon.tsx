import React from 'react';
import { getAchievementIconUrl } from '@/achievements/iconRegistry';
import { Icon } from '@/components/ui/Icon';

type AchievementIconProps = Omit<React.HTMLAttributes<HTMLSpanElement>, 'children'> & {
  name: string;
};

// Renders achievement icons from `src/assets/achievements/*.svg`.
// Uses CSS mask so the icon inherits `currentColor` (Tailwind `text-*` classes work).
export const AchievementIcon: React.FC<AchievementIconProps> = ({ name, className, style, ...rest }) => {
  if (!name) {
    return <Icon name="trophy" className={className as any} style={style as any} {...(rest as any)} />;
  }

  // Back-compat: existing DB values might still be URLs from uploads.
  if (name.startsWith('/') || name.startsWith('http')) {
    return <img src={name} alt="icon" className={className} style={style} {...(rest as any)} />;
  }

  const url = getAchievementIconUrl(name);
  if (!url) {
    // Back-compat: still allow the old built-in icon names.
    return <Icon name={name as any} className={className as any} style={style as any} {...(rest as any)} />;
  }

  return (
    <span
      aria-hidden="true"
      className={className}
      style={{
        display: 'inline-block',
        backgroundColor: 'currentColor',
        WebkitMaskImage: `url("${url}")`,
        maskImage: `url("${url}")`,
        WebkitMaskRepeat: 'no-repeat',
        maskRepeat: 'no-repeat',
        WebkitMaskPosition: 'center',
        maskPosition: 'center',
        WebkitMaskSize: 'contain',
        maskSize: 'contain',
        ...style,
      }}
      {...rest}
    />
  );
};
