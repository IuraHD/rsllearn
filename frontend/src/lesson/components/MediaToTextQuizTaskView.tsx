import React from 'react';
import { TaskRenderContext } from '../taskModuleTypes';
import { PromptVideo } from './PromptVideo';
import { TaskScreenSection } from './TaskScreenSection';
import { TextOptionButtons } from './TextOptionButtons';

interface MediaToTextQuizTaskViewProps {
  context: TaskRenderContext;
}

export const MediaToTextQuizTaskView: React.FC<MediaToTextQuizTaskViewProps> = ({ context }) => (
  <TaskScreenSection title={context.task.prompt}>
    <PromptVideo videoUrl={context.task.videoUrl} />
    <TextOptionButtons
      options={context.task.options}
      selectedOption={context.selectedOption}
      feedback={context.feedback}
      onSelectOption={context.onSelectOption}
    />
  </TaskScreenSection>
);
