import React from 'react';

interface UserAvatarProps {
  name: string;
  className?: string;
  textClassName?: string;
}

const avatarBgClasses = [
  'bg-primary/20 text-primary-dark',
  'bg-accent-blue/20 text-accent-blue',
  'bg-accent-green/20 text-accent-green',
  'bg-accent-orange/20 text-accent-orange',
  'bg-accent-red/20 text-accent-red',
];

function getAvatarStyle(name: string): string {
  const safe = (name || '').trim().toLowerCase();
  let hash = 0;
  for (let i = 0; i < safe.length; i += 1) {
    hash = (hash + safe.charCodeAt(i)) % avatarBgClasses.length;
  }
  return avatarBgClasses[hash];
}

function getInitial(name: string): string {
  const trimmed = (name || '').trim();
  return trimmed ? trimmed[0].toUpperCase() : '?';
}

export const UserAvatar: React.FC<UserAvatarProps> = ({
  name,
  className = '',
  textClassName = '',
}) => {
  const styleClass = getAvatarStyle(name);
  const initial = getInitial(name);

  return (
    <div className={`rounded-full flex items-center justify-center font-black select-none ${styleClass} ${className}`}>
      <span className={textClassName}>{initial}</span>
    </div>
  );
};

