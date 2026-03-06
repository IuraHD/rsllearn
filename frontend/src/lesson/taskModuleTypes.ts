import { Task } from '@/types';

export type TaskFeedback = 'correct' | 'incorrect' | null;

export interface TaskRenderContext {
  task: Task;
  selectedOption: string | null;
  feedback: TaskFeedback;
  onSelectOption: (optionId: string) => void;
}
