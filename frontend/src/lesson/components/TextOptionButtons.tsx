import React from 'react';
import { TaskOption } from '@/types';
import { TaskFeedback } from '../taskModuleTypes';

interface TextOptionButtonsProps {
  options?: TaskOption[];
  selectedOption: string | null;
  feedback: TaskFeedback;
  onSelectOption: (optionId: string) => void;
}

const optionCardClasses = (
  optionId: string,
  isCorrect: boolean,
  selectedOption: string | null,
  feedback: TaskFeedback
) => {
  const base = 'p-4 sm:p-6 border-2 rounded-2xl text-lg sm:text-xl font-bold text-left transition-all duration-200 shadow-sm relative overflow-hidden break-words';
  const selected = selectedOption === optionId
    ? 'border-primary bg-primary/5 ring-2 ring-primary/30 text-primary'
    : 'border-light-300 bg-white text-dark-200 hover:bg-light-200 hover:border-light-400';
  const feedbackSuccess = feedback && isCorrect ? '!bg-accent-green/10 !border-accent-green !text-accent-green' : '';
  const feedbackFail = feedback && !isCorrect && selectedOption === optionId ? '!bg-accent-red/10 !border-accent-red !text-accent-red' : '';
  return `${base} ${selected} ${feedbackSuccess} ${feedbackFail}`;
};

export const TextOptionButtons: React.FC<TextOptionButtonsProps> = ({
  options,
  selectedOption,
  feedback,
  onSelectOption,
}) => (
  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
    {options?.map((option, idx) => (
      <button
        key={option.id}
        onClick={() => !feedback && onSelectOption(option.id)}
        className={optionCardClasses(option.id, !!option.isCorrect, selectedOption, feedback)}
        disabled={!!feedback}
      >
        <span className="relative z-10">{option.text || `Option ${idx + 1}`}</span>
        {selectedOption === option.id && !feedback && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2 w-3 h-3 bg-primary rounded-full"></div>
        )}
      </button>
    ))}
  </div>
);
