import React from 'react';
import { TaskRenderContext } from '../taskModuleTypes';
import { MediaToTextQuizTaskView } from '../components/MediaToTextQuizTaskView';

export const SignToTextTask: React.FC<TaskRenderContext> = (context) => (
  <MediaToTextQuizTaskView context={context} />
);
