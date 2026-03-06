import React from 'react';
import { PromptVideo } from './PromptVideo';

interface CameraPracticeCardProps {
  heading: string;
  prompt: string;
  videoUrl?: string;
  showExampleVideo?: boolean;
}

export const CameraPracticeCard: React.FC<CameraPracticeCardProps> = ({
  heading,
  prompt,
  videoUrl,
  showExampleVideo = true,
}) => (
  <div className="text-center flex flex-col items-center justify-center flex-grow animate-pop-in">
    <div className="bg-white p-6 sm:p-8 rounded-3xl shadow-lifted border border-light-300/50 max-w-md sm:max-w-lg w-full">
      <h2 className="text-xl sm:text-2xl font-bold text-dark-100 mb-4">{heading}</h2>
      <p className="text-4xl sm:text-5xl font-black text-primary mb-6 sm:mb-8 leading-tight break-words">{prompt}</p>

      {showExampleVideo && (
        <div className="mb-6 sm:mb-8">
          <PromptVideo videoUrl={videoUrl} />
        </div>
      )}

      <div className="flex items-center justify-center gap-3 text-dark-300 font-medium bg-light-200 p-3 rounded-xl">
        <div className="w-2 h-2 bg-accent-red rounded-full animate-pulse"></div>
        Vei folosi camera pentru acest exercițiu
      </div>
    </div>
  </div>
);
