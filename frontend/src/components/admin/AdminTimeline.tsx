
import React from 'react';
import { Unit, DraggedItem, EditorState, ItemType } from './AdminTypes';
import { TaskType } from '@/types';
import { Icon } from '@/components/ui/Icon';
import { resolveLessonMediaUrl } from '@/media/lessonMediaRegistry';

interface AdminTimelineProps {
    units: Unit[];
    activeLessonId: string | null;
    handleDragStart: (e: React.DragEvent, type: 'unit' | 'lesson' | 'task', id: string, index: number, parentId?: string) => void;
    handleDragOver: (e: React.DragEvent) => void;
    handleDrop: (e: React.DragEvent, targetType: 'unit' | 'lesson' | 'task', targetIndex: number, targetParentId?: string) => void;
    setEditorState: (state: EditorState | null) => void;
    draggedItem: DraggedItem | null;
    editorState: EditorState | null;
    handleDelete: (type: ItemType, id: string) => void;
}

export const AdminTimeline: React.FC<AdminTimelineProps> = ({
    units,
    activeLessonId,
    handleDragStart,
    handleDragOver,
    handleDrop,
    setEditorState,
    draggedItem,
    editorState,
    handleDelete
}) => {
    return (
        <div className="h-72 bg-dark-200 border-t border-dark-300 flex flex-col shrink-0">
            <div className="h-10 bg-dark-300 border-b border-dark-400 flex items-center px-4 justify-between shrink-0">
                <div
                    className="text-xs font-bold text-white/70 flex items-center gap-2 cursor-pointer hover:text-white transition-colors"
                    onClick={() => {
                        const currentLesson = units.flatMap(u => u.lessons).find(l => l.lessonId === activeLessonId);
                        if (currentLesson) {
                            setEditorState({ mode: 'edit', type: 'lesson', data: currentLesson });
                        }
                    }}
                >
                    <Icon name="play" className="w-3 h-3" />
                    Tasks: {units.flatMap(u => u.lessons).find(l => l.lessonId === activeLessonId)?.title}
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setEditorState({ mode: 'create', type: 'task', data: { orderIndex: 999 }, parentId: activeLessonId! })}
                        className="text-xs bg-primary text-white px-3 py-1.5 rounded hover:bg-primary-dark transition-colors font-bold flex items-center gap-1"
                    >
                        <Icon name="plus" className="w-3 h-3" /> Add Task
                    </button>
                </div>
            </div>
            <div className="flex-1 overflow-x-auto p-4 flex items-center gap-2 relative">
                {units.flatMap(u => u.lessons).find(l => l.lessonId === activeLessonId)?.tasks?.sort((a, b) => a.orderIndex - b.orderIndex).map((task, idx) => {
                    const src = resolveLessonMediaUrl(task.signVideoUrl);
                    return (
                        <div
                            key={task.id}
                            draggable
                            onDragStart={(e) => handleDragStart(e, 'task', task.id, idx, activeLessonId!)}
                            onDragOver={handleDragOver}
                            onDrop={(e) => handleDrop(e, 'task', idx, activeLessonId!)}
                            onClick={() => setEditorState({ mode: 'edit', type: 'task', data: task })}
                            className={`
                                w-48 h-36 rounded-lg border-2 flex flex-col overflow-hidden cursor-pointer transition-all group relative shrink-0 mt-4
                                ${editorState?.data.id === task.id ? 'border-primary ring-2 ring-primary/30 z-10 scale-105 shadow-xl' : 'border-dark-400 bg-dark-300 hover:border-light-400 opacity-90 hover:opacity-100'}
                                ${draggedItem?.id === task.id ? 'opacity-30' : ''}
                            `}
                        >
                            <div className="h-24 bg-black relative">
                                {src ? (
                                    <video src={src} className="w-full h-full object-cover opacity-60" />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center">
                                        <Icon name="camera" className="w-6 h-6 text-white/20" />
                                    </div>
                                )}
                                <div className="absolute top-1 left-1 bg-black/50 text-white text-[10px] px-1.5 rounded font-mono backdrop-blur-sm">
                                    #{idx + 1}
                                </div>
                                <div className="absolute bottom-1 right-1">
                                    <Icon name={task.type === TaskType.RepeatSign ? 'camera' : 'learn'} className="w-4 h-4 text-white/70" />
                                </div>
                            </div>
                            <div className="flex-1 p-2 flex flex-col justify-center bg-dark-300">
                                <div className="text-[10px] font-bold text-primary uppercase truncate mb-0.5">{task.type.replace(/_/g, ' ')}</div>
                                <div className="text-xs text-white/90 truncate font-medium">{task.promptText}</div>
                            </div>

                            <div className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                    onClick={(e) => { e.stopPropagation(); handleDelete('task', task.id); }}
                                    className="p-1 bg-red-500 text-white rounded hover:bg-red-600 shadow-sm"
                                >
                                    <Icon name="trash" className="w-3 h-3" />
                                </button>
                            </div>
                        </div>
                    );
                })}

                <button
                    onClick={() => setEditorState({ mode: 'create', type: 'task', data: { orderIndex: 999 }, parentId: activeLessonId! })}
                    className="w-16 h-36 mt-4 rounded-lg border-2 border-dashed border-dark-400 hover:border-primary hover:bg-dark-300 flex items-center justify-center text-dark-400 hover:text-primary transition-all shrink-0"
                >
                    <Icon name="plus" className="w-6 h-6" />
                </button>
            </div>
        </div>
    );
};
