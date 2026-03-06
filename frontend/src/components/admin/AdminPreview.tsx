
import React, { useEffect, useMemo, useState } from 'react';
import { EditorState } from './AdminTypes';
import { Icon } from '@/components/ui/Icon';
import { Task, TaskOption, TaskType } from '@/types';
import { getTaskTypeModule } from '@/lesson/taskTypeModules';
import type { TaskFeedback } from '@/lesson/taskModuleTypes';

interface AdminPreviewProps {
    editorState: EditorState | null;
}

const taskTypeLabel: Record<TaskType, string> = {
    [TaskType.RepeatSign]: 'Repeat Sign',
    [TaskType.TextToSign]: 'Text to Sign',
    [TaskType.SignToText]: 'Sign to Text',
    [TaskType.VideoMultipleChoice]: 'Video Multiple Choice',
};

const normalizeOptions = (raw: any): TaskOption[] | undefined => {
    if (!Array.isArray(raw)) return undefined;
    return raw.map((o: any, idx: number) => ({
        id: String(o?.id ?? idx),
        text: o?.text ?? o?.labelText ?? o?.label_text,
        videoUrl: o?.videoUrl ?? o?.video_url,
        isCorrect: !!(o?.isCorrect ?? o?.is_correct),
    }));
};

export const AdminPreview: React.FC<AdminPreviewProps> = ({ editorState }) => {
    const task = editorState?.type === 'task' ? editorState.data : null;

    const [selectedOption, setSelectedOption] = useState<string | null>(null);
    const [feedback, setFeedback] = useState<TaskFeedback>(null);

    // When switching tasks, reset any selection/feedback so the preview starts "fresh".
    useEffect(() => {
        setSelectedOption(null);
        setFeedback(null);
    }, [task?.id, task?.taskId, task?.type]);

    const previewTask: Task | null = useMemo(() => {
        if (!task?.type) return null;
        return {
            id: String(task.taskId || task.id || 'preview'),
            type: task.type,
            prompt: String(task.promptText || ''),
            videoUrl: task.signVideoUrl,
            expectedLabel: task.expectedLabel,
            minConfidence: typeof task.minConfidence === 'number' ? task.minConfidence : undefined,
            options: normalizeOptions(task.options),
        };
    }, [task]);

    return (
        <div className="flex-1 bg-light-200 flex flex-col p-6 md:p-8 overflow-y-auto">
            {previewTask ? (
                <div className="w-full max-w-4xl mx-auto flex flex-col gap-4 min-h-0">
                    <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold text-primary uppercase tracking-wider bg-white px-2 py-1 rounded-full border border-light-300 shadow-sm">
                            {taskTypeLabel[previewTask.type]}
                        </span>
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-dark-300 font-semibold">Lesson Preview</span>
                            <button
                                type="button"
                                className="text-xs font-bold text-primary hover:text-primary-dark px-2 py-1 rounded-lg bg-white border border-light-300"
                                onClick={() => { setSelectedOption(null); setFeedback(null); }}
                                title="Reset selection"
                            >
                                Reset
                            </button>
                        </div>
                    </div>

                    <div className="flex-grow min-h-0 flex flex-col justify-start md:justify-center">
                        {getTaskTypeModule(previewTask.type).render({
                            task: previewTask,
                            selectedOption,
                            feedback,
                            onSelectOption: (optionId: string) => setSelectedOption(optionId),
                        })}
                    </div>
                </div>
            ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-center text-dark-300/60">
                    <Icon name="learn" className="w-16 h-16 mb-4 opacity-40" />
                    <p className="font-bold text-sm">Select a task to preview</p>
                </div>
            )}
        </div>
    );
};
