import React from 'react';
import { TaskRenderContext } from '../taskModuleTypes';
import { CameraPracticeCard } from '../components/CameraPracticeCard';

export const TextToSignTask: React.FC<TaskRenderContext> = ({ task }) => (
  <CameraPracticeCard
    heading="Arată semnul pentru:"
    prompt={task.expectedLabel || task.prompt}
    showExampleVideo={false}
  />
);
