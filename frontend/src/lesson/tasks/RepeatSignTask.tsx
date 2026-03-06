import React from 'react';
import { TaskRenderContext } from '../taskModuleTypes';
import { CameraPracticeCard } from '../components/CameraPracticeCard';

export const RepeatSignTask: React.FC<TaskRenderContext> = ({ task }) => (
  <CameraPracticeCard
    heading="Repetă semnul:"
    prompt={task.expectedLabel || task.prompt}
    videoUrl={task.videoUrl}
  />
);
