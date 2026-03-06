import React from 'react';
import { TaskRenderContext } from '../taskModuleTypes';
import { Icon } from '@/components/ui/Icon';
import { TaskScreenSection } from '../components/TaskScreenSection';
import { resolveLessonMediaUrl } from '@/media/lessonMediaRegistry';

export const VideoMultipleChoiceTask: React.FC<TaskRenderContext> = ({
  task,
  selectedOption,
  feedback,
  onSelectOption,
}) => (
  <TaskScreenSection title={task.prompt} maxWidthClass="max-w-4xl">
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
      {task.options?.map((option, idx) => {
        const src = resolveLessonMediaUrl(option.videoUrl);
        return (
          <div
            key={option.id}
            onClick={() => !feedback && onSelectOption(option.id)}
            className={`p-3 sm:p-4 border-2 rounded-2xl transition-all duration-200 shadow-sm relative overflow-hidden group cursor-pointer
              ${selectedOption === option.id ? 'border-primary bg-primary/5 ring-2 ring-primary/30' : 'border-light-300 bg-white hover:bg-light-200 hover:border-light-400'}
              ${feedback && option.isCorrect ? '!bg-accent-green/10 !border-accent-green' : ''}
              ${feedback && !option.isCorrect && selectedOption === option.id ? '!bg-accent-red/10 !border-accent-red' : ''}
            `}
          >
            <div className="aspect-video rounded-xl overflow-hidden bg-black/5 mb-2 sm:mb-3 relative z-10" onClick={(e) => e.stopPropagation()}>
              {src ? (
                <video src={src} className="w-full h-full object-cover" controls playsInline preload="metadata" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-dark-300/50">
                  <Icon name="play" className="w-8 h-8" />
                </div>
              )}
            </div>

            <div className="flex items-center justify-between px-2">
              <span className="font-bold text-dark-200 text-xs sm:text-sm">Varianta {idx + 1}</span>
              <div className={`w-5 h-5 sm:w-6 sm:h-6 rounded-full border-2 flex items-center justify-center transition-colors
                ${selectedOption === option.id ? 'bg-primary border-primary text-white' : 'border-light-300 bg-white'}
                ${feedback && option.isCorrect ? '!bg-accent-green !border-accent-green !text-white' : ''}
                ${feedback && !option.isCorrect && selectedOption === option.id ? '!bg-accent-red !border-accent-red !text-white' : ''}
              `}>
                {selectedOption === option.id && <Icon name="check" className="w-3 h-3" />}
                {feedback && option.isCorrect && selectedOption !== option.id && <Icon name="check" className="w-3 h-3 text-accent-green" />}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  </TaskScreenSection>
);
