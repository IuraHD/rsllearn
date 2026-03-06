import React from 'react';
import { Task, TaskOption, TaskType } from '@/types';
import { TaskFeedback, TaskRenderContext } from './taskModuleTypes';
import { SignToTextTask } from './tasks/SignToTextTask';
import { TextToSignTask } from './tasks/TextToSignTask';
import { RepeatSignTask } from './tasks/RepeatSignTask';
import { VideoMultipleChoiceTask } from './tasks/VideoMultipleChoiceTask';

type TaskInteraction = 'camera' | 'choice_text' | 'choice_video';

interface TaskTypeModule {
  label: string;
  interaction: TaskInteraction;
  render: (ctx: TaskRenderContext) => React.JSX.Element;
}

const modules: Record<TaskType, TaskTypeModule> = {
  [TaskType.SignToText]: {
    label: 'Sign to Text',
    interaction: 'choice_text',
    render: (ctx) => <SignToTextTask {...ctx} />,
  },
  [TaskType.TextToSign]: {
    label: 'Text to Sign',
    interaction: 'camera',
    render: (ctx) => <TextToSignTask {...ctx} />,
  },
  [TaskType.RepeatSign]: {
    label: 'Repeat Sign',
    interaction: 'camera',
    render: (ctx) => <RepeatSignTask {...ctx} />,
  },
  [TaskType.VideoMultipleChoice]: {
    label: 'Video Multiple Choice',
    interaction: 'choice_video',
    render: (ctx) => <VideoMultipleChoiceTask {...ctx} />,
  },
};

const fallbackModule: TaskTypeModule = modules[TaskType.SignToText];

export const getTaskTypeModule = (taskType: TaskType): TaskTypeModule => {
  return modules[taskType] || fallbackModule;
};

export const isCameraTaskType = (taskType: TaskType): boolean => {
  return getTaskTypeModule(taskType).interaction === 'camera';
};

export const isSelectionRequired = (taskType: TaskType): boolean => {
  return getTaskTypeModule(taskType).interaction !== 'camera';
};

export const evaluateSelectionTask = (task: Task, selectedOption: string | null): { isCorrect: boolean; correctOption?: TaskOption } => {
  const correctOption = task.options?.find((o) => o.isCorrect);
  return {
    isCorrect: selectedOption === correctOption?.id,
    correctOption,
  };
};

export const isCheckDisabledForTask = (task: Task, selectedOption: string | null, feedback: TaskFeedback): boolean => {
  if (feedback) return false;
  return isSelectionRequired(task.type) && !selectedOption;
};
