
import React from 'react';
import { Unit, Achievement, DraggedItem, EditorState, ItemType } from './AdminTypes';
import { Icon } from '@/components/ui/Icon';
import { AchievementIcon } from '@/components/ui/AchievementIcon';

interface AdminSidebarProps {
    isSidebarOpen: boolean;
    setIsSidebarOpen: (isOpen: boolean) => void;
    activeTab: 'content' | 'achievements';
    setActiveTab: (tab: 'content' | 'achievements') => void;
    setEditorState: (state: EditorState | null) => void;
    units: Unit[];
    achievements: Achievement[];
    draggedItem: DraggedItem | null;
    handleDragStart: (e: React.DragEvent, type: 'unit' | 'lesson' | 'task', id: string, index: number, parentId?: string) => void;
    handleDragOver: (e: React.DragEvent) => void;
    handleDrop: (e: React.DragEvent, targetType: 'unit' | 'lesson' | 'task', targetIndex: number, targetParentId?: string) => void;
    toggleExpand: (id: string) => void;
    expandedItems: Set<string>;
    handleDelete: (type: ItemType, id: string) => void;
    activeLessonId: string | null;
    setActiveLessonId: (id: string | null) => void;
}

export const AdminSidebar: React.FC<AdminSidebarProps> = ({
    isSidebarOpen,
    setIsSidebarOpen,
    activeTab,
    setActiveTab,
    setEditorState,
    units,
    achievements,
    draggedItem,
    handleDragStart,
    handleDragOver,
    handleDrop,
    toggleExpand,
    expandedItems,
    handleDelete,
    activeLessonId,
    setActiveLessonId
}) => {
    return (
        <div className={`${isSidebarOpen ? 'w-full md:w-80' : 'w-0'} bg-white border-r border-light-300 flex flex-col transition-all duration-300 overflow-hidden absolute md:relative z-30 h-full shadow-2xl md:shadow-none shrink-0`}>
            {/* Sidebar Header */}
            <div className="p-4 border-b border-light-300 bg-light-50 sticky top-0 z-10">
                <div className="flex justify-between items-center mb-4">
                    <h2 className="text-lg font-black text-dark-100 flex items-center gap-2">
                        <Icon name="lock" className="w-5 h-5 text-primary" />
                        Course Builder
                    </h2>
                    <button onClick={() => setIsSidebarOpen(false)} className="p-2 hover:bg-light-200 rounded-lg text-dark-300 md:hidden">
                        <Icon name="close" className="w-5 h-5" />
                    </button>
                </div>

                <div className="flex gap-2 mb-4">
                    <button
                        onClick={() => setActiveTab('content')}
                        className={`flex-1 py-1.5 rounded-lg font-bold text-xs transition-colors ${activeTab === 'content' ? 'bg-primary text-white' : 'bg-white text-dark-300 border border-light-300'}`}
                    >
                        Units
                    </button>
                    <button
                        onClick={() => {
                            setActiveTab('achievements');
                            setActiveLessonId(null);
                        }}
                        className={`flex-1 py-1.5 rounded-lg font-bold text-xs transition-colors ${activeTab === 'achievements' ? 'bg-primary text-white' : 'bg-white text-dark-300 border border-light-300'}`}
                    >
                        Achievements
                    </button>
                </div>

                {activeTab === 'content' ? (
                    <button
                        onClick={() => setEditorState({ mode: 'create', type: 'unit', data: {} })}
                        className="w-full bg-white border-2 border-dashed border-primary/30 text-primary py-2 rounded-xl font-bold hover:bg-primary/5 transition-colors flex items-center justify-center gap-2 text-sm"
                    >
                        <Icon name="plus" className="w-4 h-4" />
                        New Unit
                    </button>
                ) : (
                    <button
                        onClick={() => setEditorState({ mode: 'create', type: 'achievement', data: {} })}
                        className="w-full bg-white border-2 border-dashed border-primary/30 text-primary py-2 rounded-xl font-bold hover:bg-primary/5 transition-colors flex items-center justify-center gap-2 text-sm"
                    >
                        <Icon name="plus" className="w-4 h-4" />
                        New Achievement
                    </button>
                )}
            </div>

            <div className="flex-grow overflow-y-auto p-2 space-y-2">
                {activeTab === 'content' ? (
                    units.map((unit, index) => (
                        <div
                            key={unit.id}
                            className={`border border-light-200 rounded-lg overflow-hidden bg-white ${draggedItem?.id === unit.id ? 'opacity-50 border-dashed border-primary' : ''}`}
                            draggable
                            onDragStart={(e) => handleDragStart(e, 'unit', unit.id, index)}
                            onDragOver={handleDragOver}
                            onDrop={(e) => handleDrop(e, 'unit', index)}
                        >
                            {/* Unit Header */}
                            <div className="p-3 bg-light-50 flex items-center justify-between group cursor-pointer hover:bg-light-100" onClick={() => toggleExpand(unit.unitId)}>
                                <div className="flex items-center gap-2 flex-1 min-w-0">
                                    <div className={`transition-transform duration-200 ${expandedItems.has(unit.unitId) ? 'rotate-90' : ''}`}>
                                        <Icon name="play" className="w-3 h-3 text-dark-300" />
                                    </div>
                                    <div className="truncate">
                                        <span className="font-bold text-dark-200 text-sm">Unit {unit.orderIndex}</span>
                                        <span className="text-xs text-dark-300 ml-2 truncate">{unit.title}</span>
                                    </div>
                                </div>
                                <div className="flex items-center gap-1">
                                    <button
                                        onClick={(e) => { e.stopPropagation(); setEditorState({ mode: 'edit', type: 'unit', data: unit }); }}
                                        className="p-1.5 hover:bg-white rounded text-dark-300 hover:text-primary"
                                    >
                                        <Icon name="edit" className="w-3.5 h-3.5" />
                                    </button>
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleDelete('unit', unit.id); }}
                                        className="p-1.5 hover:bg-red-50 rounded text-dark-300 hover:text-red-600"
                                    >
                                        <Icon name="trash" className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            </div>

                            {/* Lessons List */}
                            {expandedItems.has(unit.unitId) && (
                                <div className="bg-white border-t border-light-200">
                                    {unit.lessons?.map((lesson, lIndex) => (
                                        <div
                                            key={lesson.id}
                                            className={`pl-8 pr-2 py-2 border-b border-light-100 last:border-0 hover:bg-light-50 cursor-pointer ${activeLessonId === lesson.lessonId ? 'bg-primary/5 border-l-4 border-l-primary pl-[28px]' : ''} ${draggedItem?.id === lesson.id ? 'opacity-50' : ''}`}
                                            draggable
                                            onDragStart={(e) => handleDragStart(e, 'lesson', lesson.id, lIndex, unit.unitId)}
                                            onDragOver={handleDragOver}
                                            onDrop={(e) => handleDrop(e, 'lesson', lIndex, unit.unitId)}
                                            onClick={() => {
                                                setActiveLessonId(lesson.lessonId);
                                                if (lesson.tasks && lesson.tasks.length > 0) {
                                                    const firstTask = [...lesson.tasks].sort((a, b) => a.orderIndex - b.orderIndex)[0];
                                                    setEditorState({ mode: 'edit', type: 'task', data: firstTask });
                                                } else {
                                                    setEditorState({ mode: 'edit', type: 'lesson', data: lesson });
                                                }
                                            }}
                                        >
                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-2 overflow-hidden">
                                                    <Icon name="learn" className={`w-3.5 h-3.5 ${activeLessonId === lesson.lessonId ? 'text-primary' : 'text-dark-300'}`} />
                                                    <span className={`text-sm truncate ${activeLessonId === lesson.lessonId ? 'font-bold text-primary' : 'text-dark-200'}`}>
                                                        {lesson.title}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-1">
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); setEditorState({ mode: 'edit', type: 'lesson', data: lesson }); }}
                                                        className="p-1 hover:bg-light-200 rounded text-dark-300"
                                                    >
                                                        <Icon name="edit" className="w-3 h-3" />
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                    <button
                                        onClick={() => setEditorState({ mode: 'create', type: 'lesson', data: { orderIndex: (unit.lessons?.length || 0) + 1 }, parentId: unit.unitId })}
                                        className="w-full py-2 text-xs font-bold text-dark-300 hover:text-primary hover:bg-light-50 flex items-center justify-center gap-1"
                                    >
                                        <Icon name="plus" className="w-3 h-3" /> Add Lesson
                                    </button>
                                </div>
                            )}
                        </div>
                    ))
                ) : (
                    // Achievements List (Simplified)
                    achievements.map(ach => (
                        <div key={ach.id} className="border border-light-200 rounded-lg p-3 bg-white flex items-center gap-3 cursor-pointer hover:bg-light-50 group" onClick={() => setEditorState({ mode: 'edit', type: 'achievement', data: ach })}>
                            <div className="w-8 h-8 bg-light-100 rounded-full flex items-center justify-center shrink-0">
                                <AchievementIcon name={String(ach.icon || 'trophy')} className="w-4 h-4 text-primary" />
                            </div>
                            <div className="min-w-0 flex-1">
                                <div className="font-bold text-dark-200 text-sm truncate">{ach.title}</div>
                                <div className="text-xs text-dark-300 truncate">{ach.description}</div>
                            </div>
                            <button
                                onClick={(e) => { e.stopPropagation(); handleDelete('achievement', ach.id as string); }}
                                className="p-1.5 hover:bg-red-50 rounded text-dark-300 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                                <Icon name="trash" className="w-4 h-4" />
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
