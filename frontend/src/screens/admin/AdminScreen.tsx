
import React, { useState, useEffect } from 'react';
import { Icon } from '@/components/ui/Icon';
import { Unit, Lesson, Task, Achievement, EditorState, DraggedItem, ItemType } from '@/components/admin/AdminTypes';
import { AdminSidebar } from '@/components/admin/AdminSidebar';
import { AdminEditor } from '@/components/admin/AdminEditor';
import { AdminPreview } from '@/components/admin/AdminPreview';
import { AdminTimeline } from '@/components/admin/AdminTimeline';
import { TaskType } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

interface AdminScreenProps {
    user: any;
    onBack: () => void;
}

export const AdminScreen: React.FC<AdminScreenProps> = ({ user, onBack }) => {
    const [units, setUnits] = useState<Unit[]>([]);
    const [achievements, setAchievements] = useState<Achievement[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

    // Editor State
    const [activeTab, setActiveTab] = useState<'content' | 'achievements'>('content');
    const [editorState, setEditorState] = useState<EditorState | null>(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [activeLessonId, setActiveLessonId] = useState<string | null>(null);

    // Initial Data Fetch
    useEffect(() => {
        fetchContent();
        fetchAchievements();
    }, []);

    const fetchContent = async () => {
        try {
            const userId = localStorage.getItem('userId') || user?.id;
            const response = await fetch(`${API_BASE_URL}/admin/content`, {
                headers: userId ? { 'X-User-Id': userId } : {}
            });
            const data = await response.json();
            if (data.success) {
                setUnits(data.data);
            }
        } catch (error) {
            console.error("Failed to fetch content:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchAchievements = async () => {
        try {
            const userId = localStorage.getItem('userId') || user?.id;
            const response = await fetch(`${API_BASE_URL}/admin/achievements`, {
                headers: userId ? { 'X-User-Id': userId } : {}
            });
            const data = await response.json();
            if (data.success) {
                setAchievements(data.data);
            }
        } catch (error) {
            console.error("Failed to fetch achievements:", error);
        }
    };

    const authenticatedFetch = async (url: string, options: RequestInit = {}) => {
        const userId = localStorage.getItem('userId') || user?.id;
        const headers = {
            ...(userId ? { 'X-User-Id': userId } : {}),
            ...options.headers,
        };
        const response = await fetch(`${API_BASE_URL}${url}`, {
            ...options,
            headers
        });
        return response.json();
    };

    const handleSave = async (formData: any) => {
        if (!editorState) return;

        try {
            const { mode, type, data } = editorState;
            let endpoint = '';
            let method = mode === 'create' ? 'POST' : 'PUT';

            if (type === 'unit') endpoint = mode === 'create' ? '/admin/units' : `/admin/units/${data.unitId}`;
            if (type === 'lesson') endpoint = mode === 'create' ? '/admin/lessons' : `/admin/lessons/${data.lessonId}`;
            if (type === 'task') endpoint = mode === 'create' ? '/admin/tasks' : `/admin/tasks/${data.taskId}`;
            if (type === 'achievement') {
                const achId = data.achievementId || data.id;
                endpoint = mode === 'create' ? '/admin/achievements' : `/admin/achievements/${achId}`;
            }

            let payload = { ...formData };
            if (type === 'unit') payload.order_index = parseInt(payload.orderIndex);

            // Uploads are disabled. If the UI still provides a File, block save and ask for a URL.
            if ((type === 'task' || type === 'achievement') && formData.file instanceof File) {
                alert('File uploads are disabled. Please provide a URL instead.');
                return;
            }

            // Handle Video Multiple Choice Options
            if (type === 'task' && payload.type === TaskType.VideoMultipleChoice) {
                for (let i = 0; i < 4; i++) {
                    if (payload[`optionVideo${i}`] instanceof File) {
                        alert('Video uploads are disabled. Please provide option video URLs instead.');
                        return;
                    }
                }

                const options = [];
                for (let i = 0; i < 4; i++) {
                     const isCorrect = parseInt(payload.correctOptionIndex) === i;
                     let videoUrl = data.options?.[i]?.videoUrl || '';
 
                     // Allow editing via string value (including clearing it back to empty string).
                     if (payload[`optionVideo${i}`] !== undefined) {
                         videoUrl = String(payload[`optionVideo${i}`]);
                     }

                    options.push({
                        id: (Date.now() + i).toString(),
                        videoUrl,
                        isCorrect
                    });
                }
                payload.options = JSON.stringify(options);
            }

            // Convert payload to appropriate structure for backend
            if (type === 'lesson' && payload.xpReward) payload.xp = parseInt(payload.xpReward);
            if (type === 'task') {
                payload.prompt = payload.promptText;
                // Ensure options is string if it's an object/array
                if (typeof payload.options === 'object') {
                    payload.options = JSON.stringify(payload.options);
                }
            }

            // Clean up temporary fields
            delete payload.file;
            delete payload.optionVideo0;
            delete payload.optionVideo1;
            delete payload.optionVideo2;
            delete payload.optionVideo3;
            delete payload.correctOptionIndex;

            const res = await authenticatedFetch(endpoint, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.success) {
                // Refresh data
                if (type === 'achievement') {
                    await fetchAchievements();
                } else {
                    await fetchContent();
                }
                setEditorState(null); // Close editor
            } else {
                alert('Error saving: ' + res.detail);
            }

        } catch (error) {
            console.error("Save error:", error);
            alert('Failed to save changes');
        }
    };

    const handleDelete = async (type: ItemType, id: string) => {
        if (!confirm('Are you sure you want to delete this item?')) return;

        try {
            let endpoint = '';
            // Needs ID for backend, which is usually the 'unitId', 'lessonId' etc field, NOT the numeric DB id
            // Finding the item to get its ID
            let itemId = id;
            if (type === 'unit') {
                const u = units.find(u => u.id === id);
                if (u) itemId = u.unitId;
            } else if (type === 'lesson') {
                const l = units.flatMap(u => u.lessons).find(l => l.id === id);
                if (l) itemId = l.lessonId;
            } else if (type === 'task') {
                // For tasks, we usually use the ID directly if it's the uuid
                const t = units.flatMap(u => u.lessons).flatMap(l => l.tasks).find(t => t.id === id);
                if (t) itemId = t.taskId;
            }

            if (type === 'unit') endpoint = `/admin/units/${itemId}`;
            if (type === 'lesson') endpoint = `/admin/lessons/${itemId}`;
            if (type === 'task') endpoint = `/admin/tasks/${itemId}`;
            if (type === 'achievement') endpoint = `/admin/achievements/${id}`;

            const res = await authenticatedFetch(endpoint, { method: 'DELETE' });

            if (res.success) {
                if (type === 'achievement') {
                    await fetchAchievements();
                } else {
                    await fetchContent();
                }
                if (editorState?.data.id === id) setEditorState(null);
            }
        } catch (error) {
            console.error("Delete error:", error);
        }
    };

    const toggleExpand = (id: string) => {
        const newSet = new Set(expandedItems);
        if (newSet.has(id)) newSet.delete(id);
        else newSet.add(id);
        setExpandedItems(newSet);
    };

    // --- Drag and Drop Logic ---
    const [draggedItem, setDraggedItem] = useState<DraggedItem | null>(null);

    const handleDragStart = (e: React.DragEvent, type: 'unit' | 'lesson' | 'task', id: string, index: number, parentId?: string) => {
        e.stopPropagation();
        setDraggedItem({ type, id, index, parentId });
        e.dataTransfer.effectAllowed = 'move';
        // Set invisible drag image to avoid default ghost
        const img = new Image();
        img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
        e.dataTransfer.setDragImage(img, 0, 0);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    };

    const handleDrop = async (e: React.DragEvent, targetType: 'unit' | 'lesson' | 'task', targetIndex: number, targetParentId?: string) => {
        e.preventDefault();
        e.stopPropagation();

        if (!draggedItem) return;
        if (draggedItem.type !== targetType) return; // Strict type matching
        if (draggedItem.index === targetIndex && draggedItem.parentId === targetParentId) return; // No move

        // Optimistic UI Update can be added here, but for now we just call backend

        try {
            await authenticatedFetch('/admin/reorder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: draggedItem.type,
                    id: draggedItem.id, // Should change to real ID logic if needed
                    new_index: targetIndex,
                    parent_id: targetParentId
                })
            });
            await fetchContent(); // Refresh to sync
        } catch (error) {
            console.error("Reorder failed:", error);
            alert("Failed to reorder items");
        }

        setDraggedItem(null);
    };

    const updateEditorData = (updates: any) => {
        if (!editorState) return;
        setEditorState({
            ...editorState,
            data: { ...editorState.data, ...updates }
        });
    };

    return (
        <div className="flex h-screen bg-dark-100 overflow-hidden relative text-dark-100">
            {/* Mobile Backdrop */}
            {isSidebarOpen && (
                <div
                    className="absolute inset-0 bg-black/50 z-20 md:hidden backdrop-blur-sm transition-opacity"
                    onClick={() => setIsSidebarOpen(false)}
                />
            )}

            {/* Sidebar / Tree View */}
            <AdminSidebar
                isSidebarOpen={isSidebarOpen}
                setIsSidebarOpen={setIsSidebarOpen}
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                setEditorState={setEditorState}
                units={units}
                achievements={achievements}
                draggedItem={draggedItem}
                handleDragStart={handleDragStart}
                handleDragOver={handleDragOver}
                handleDrop={handleDrop}
                toggleExpand={toggleExpand}
                expandedItems={expandedItems}
                handleDelete={handleDelete}
                activeLessonId={activeLessonId}
                setActiveLessonId={setActiveLessonId}
            />

            {/* Main Content Area */}
            <div className="flex-grow bg-dark-100 overflow-hidden relative w-full flex flex-col">
                {!isSidebarOpen && (
                    <button
                        onClick={() => setIsSidebarOpen(true)}
                        className="absolute top-4 left-4 bg-white p-2 rounded-lg shadow-md text-dark-200 hover:text-primary z-20"
                        title="Show Menu"
                    >
                        <Icon name="menu" className="w-6 h-6" />
                    </button>
                )}

                {(activeLessonId || activeTab === 'achievements') ? (
                    <div className="flex flex-col h-full">
                        {/* Top Area: Preview + Properties */}
                        <div className="flex-1 flex overflow-hidden">
                             {activeTab === 'content' ? (
                                 <AdminPreview
                                    editorState={editorState}
                                 />
                             ) : (
                                 <div className="flex-1 bg-dark-100 flex items-center justify-center">
                                     <div className="text-dark-300 opacity-20 flex flex-col items-center">
                                         <Icon name="trophy" className="w-32 h-32 mb-6" />
                                        <p className="text-2xl font-bold">Achievements Editor</p>
                                        <p className="text-sm mt-2">Select an achievement to edit details</p>
                                    </div>
                                </div>
                            )}

                            <div className="w-96 bg-white border-l border-light-300 flex flex-col shadow-xl z-10 shrink-0">
                                <div className="h-12 border-b border-light-300 flex items-center px-4 bg-light-50 font-bold text-xs text-dark-300 uppercase tracking-wider justify-between">
                                    <span>Properties</span>
                                    {editorState && (
                                        <button onClick={() => setEditorState(null)} className="text-dark-300 hover:text-dark-100">
                                            <Icon name="close" className="w-4 h-4" />
                                        </button>
                                    )}
                                </div>
                                <div className="flex-1 overflow-y-auto p-4">
                                    {editorState ? (
                                        <AdminEditor
                                            editorState={editorState}
                                            units={units}
                                            onSave={handleSave}
                                            updateEditorData={updateEditorData}
                                            mode={editorState.mode}
                                        />
                                    ) : (
                                        <div className="text-center text-dark-300 mt-10">
                                            <p className="text-sm">No item selected</p>
                                            <p className="text-xs mt-2 opacity-70">Select a task from the task list to edit properties</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {activeTab === 'content' && (
                            <AdminTimeline
                                units={units}
                                activeLessonId={activeLessonId}
                                handleDragStart={handleDragStart}
                                handleDragOver={handleDragOver}
                                handleDrop={handleDrop}
                                setEditorState={setEditorState}
                                draggedItem={draggedItem}
                                editorState={editorState}
                                handleDelete={handleDelete}
                            />
                        )}
                    </div>
                ) : (
                    <div className="h-full p-4 md:p-8 overflow-y-auto bg-light-100">
                        {editorState ? (
                            <div className="max-w-2xl mx-auto bg-white rounded-3xl shadow-lifted p-4 md:p-8 animate-pop-in">
                                <div className="flex items-center justify-between mb-8">
                                    <h2 className="text-2xl font-black text-dark-100">
                                        {editorState.mode === 'create' ? 'Create' : 'Edit'} {editorState.type.charAt(0).toUpperCase() + editorState.type.slice(1)}
                                    </h2>
                                    <button onClick={() => setEditorState(null)} className="p-2 hover:bg-light-200 rounded-full transition-colors">
                                        <Icon name="close" className="w-6 h-6 text-dark-300" />
                                    </button>
                                </div>
                                <div className="max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
                                    <AdminEditor
                                        editorState={editorState}
                                        units={units}
                                        onSave={handleSave}
                                        updateEditorData={updateEditorData}
                                        mode={editorState.mode}
                                    />
                                </div>
                            </div>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-dark-300 opacity-50">
                                <Icon name="edit" className="w-24 h-24 mb-4" />
                                <p className="text-xl font-bold">Select a lesson to edit tasks</p>
                                <p className="text-sm mt-2">Or select a unit to edit properties</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};
