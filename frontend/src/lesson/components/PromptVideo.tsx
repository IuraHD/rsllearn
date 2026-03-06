import React from 'react';
import { Icon } from '@/components/ui/Icon';
import { resolveLessonMediaUrl } from '@/media/lessonMediaRegistry';

interface PromptVideoProps {
  videoUrl?: string;
}

export const PromptVideo: React.FC<PromptVideoProps> = ({ videoUrl }) => {
  const src = resolveLessonMediaUrl(videoUrl);

  return src ? (
    <div className="relative group mb-6 sm:mb-10 mx-auto max-w-md md:max-w-lg lg:max-w-xl w-full">
      <div className="absolute -inset-1 bg-gradient-to-r from-primary to-accent-blue rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
      <div className="relative bg-white w-full aspect-video rounded-xl flex items-center justify-center shadow-lifted overflow-hidden border border-light-300">
        <video src={src} controls playsInline preload="metadata" className="w-full h-full object-cover" />
      </div>
    </div>
  ) : (
    <div className="relative group mb-6 sm:mb-10 mx-auto max-w-md md:max-w-lg lg:max-w-xl w-full">
      <div className="relative bg-light-200 w-full aspect-video rounded-xl flex items-center justify-center shadow-inner border border-light-300">
        <div className="flex flex-col items-center text-dark-300 opacity-50">
          <Icon name="play" className="w-12 h-12 mb-2" />
          <span className="text-sm font-medium">Video indisponibil</span>
        </div>
      </div>
    </div>
  );
};
