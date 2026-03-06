
import React, { useEffect, useState } from 'react';
import { Unit, EditorState } from './AdminTypes';
import { TaskType } from '@/types';
import { Icon } from '@/components/ui/Icon';
import { AchievementIcon } from '@/components/ui/AchievementIcon';
import { ACHIEVEMENT_ICON_KEYS } from '@/achievements/iconRegistry';
import { signAPI } from '@/services/api';
import { LESSON_MEDIA_KEYS } from '@/media/lessonMediaRegistry';

interface AdminEditorProps {
    editorState: EditorState;
    units: Unit[];
    onSave: (payload: any) => void;
    updateEditorData: (updates: any) => void;
    mode: 'create' | 'edit';
}

export const AdminEditor: React.FC<AdminEditorProps> = ({
    editorState,
    units,
    onSave,
    updateEditorData,
    mode
}) => {
    const { type, data, parentId } = editorState;
    const achievementConditionType = normalizeAchievementConditionType(data.conditionType);

    const isCameraTask = type === 'task' && (data.type === TaskType.TextToSign || data.type === TaskType.RepeatSign);
    const [availableSigns, setAvailableSigns] = useState<string[]>([]);

    function normalizeAchievementConditionType(raw: any): string {
        const v = String(raw || 'manual');
        // Back-compat with old editor values.
        if (v === 'lesson_completion') return 'lessons_completed';
        if (v === 'unit_completion') return 'unit_completed';
        if (v === 'xp_milestone') return 'xp_threshold';
        if (v === 'streak_milestone') return 'streak';
        return v;
    }

    useEffect(() => {
        let cancelled = false;
        if (!isCameraTask) return;

        signAPI.getClasses()
            .then((res) => {
                if (cancelled) return;
                if (res?.success && Array.isArray(res.classes)) {
                    setAvailableSigns([...res.classes].sort((a, b) => a.localeCompare(b, 'ro')));
                }
            })
            .catch(() => {
                if (!cancelled) setAvailableSigns([]);
            });

        return () => {
            cancelled = true;
        };
    }, [isCameraTask]);

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        const payload: any = Object.fromEntries(formData.entries());

        // FormData yields strings; normalize optional fields so backend gets clean values.
        if (type === 'task') {
            if (typeof payload.expectedLabel === 'string') {
                const v = payload.expectedLabel.trim();
                payload.expectedLabel = v ? v : null;
            }
            if (payload.minConfidence !== undefined) {
                const raw = String(payload.minConfidence).trim();
                if (!raw) {
                    payload.minConfidence = null;
                } else {
                    const num = Number(raw);
                    payload.minConfidence = Number.isFinite(num) ? num : null;
                }
            }
        }

        // Checkboxes handling
        if (type === 'unit') {
            payload.isPublished = formData.get('isPublished') === 'on';
        }
        if (type === 'lesson') {
            payload.isPublished = formData.get('isPublished') === 'on';
        }

        // Add parent IDs for creation
        if (mode === 'create') {
            if (type === 'lesson') payload.unitId = parentId;
            if (type === 'task') payload.lessonId = parentId;
        }

        // Handle Video Multiple Choice specific inputs
        if (type === 'task' && payload.type === TaskType.VideoMultipleChoice) {
            payload.correctOptionIndex = formData.get('correctOption');
        }

        // For tasks with dynamic options, ensure they are included in payload from state
        if (type === 'task' && data.options && typeof data.options === 'object' && payload.type !== TaskType.VideoMultipleChoice) {
            payload.options = JSON.stringify(data.options);
        }

        onSave(payload);
    };

    return (
        <form key={data.id || (mode === 'create' ? `create-${type}` : `edit-${type}`)} onSubmit={handleSubmit} className="space-y-4">

            {/* Common Fields */}
            {type !== 'achievement' && (
                <div>
                    <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Order Index</label>
                    <input name="orderIndex" type="number" defaultValue={data.orderIndex} className="w-full p-2 text-sm border border-light-300 rounded-lg" required />
                </div>
            )}

            {/* Unit Fields */}
            {type === 'unit' && (
                <>
                    <div>
                        <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Title</label>
                        <input name="title" defaultValue={data.title} className="w-full p-2 text-sm border border-light-300 rounded-lg font-bold" required />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Description</label>
                        <textarea name="description" defaultValue={data.description} className="w-full p-2 text-sm border border-light-300 rounded-lg" rows={3} />
                    </div>
                    <div className="flex items-center gap-2">
                        <input name="isPublished" type="checkbox" defaultChecked={data.isPublished} className="w-4 h-4 text-green-600 rounded focus:ring-green-600" />
                        <label className="text-sm font-bold text-dark-200">Published</label>
                    </div>
                </>
            )}

            {/* Lesson Fields */}
            {type === 'lesson' && (
                <>
                    <div>
                        <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Title</label>
                        <input
                            name="title"
                            value={data.title || ''}
                            onChange={(e) => updateEditorData({ title: e.target.value })}
                            className="w-full p-2 text-sm border border-light-300 rounded-lg font-bold"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Description</label>
                        <textarea name="description" defaultValue={data.description} className="w-full p-2 text-sm border border-light-300 rounded-lg" rows={3} />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-dark-300 uppercase mb-1">XP Reward</label>
                        <input name="xpReward" type="number" defaultValue={data.xpRewardBase} className="w-full p-2 text-sm border border-light-300 rounded-lg" />
                    </div>
                    <div className="flex items-center gap-2 mt-4">
                        <input name="isPublished" type="checkbox" defaultChecked={data.isPublished} className="w-4 h-4 text-green-600 rounded focus:ring-green-600" />
                        <label className="text-sm font-bold text-dark-200">Published</label>
                    </div>
                </>
            )}

            {/* Task Fields */}
            {type === 'task' && (
                <>
                    <div>
                        <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Task Type</label>
                        <select
                            name="type"
                            value={data.type || TaskType.RepeatSign}
                            className="w-full p-2 text-sm border border-light-300 rounded-lg"
                            onChange={(e) => updateEditorData({ type: e.target.value })}
                        >
                            <option value={TaskType.RepeatSign}>Repeat Sign</option>
                            <option value={TaskType.TextToSign}>Text to Sign</option>
                            <option value={TaskType.SignToText}>Sign to Text</option>
                            <option value={TaskType.VideoMultipleChoice}>Video Multiple Choice</option>
                        </select>
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Prompt Text</label>
                        <input
                            name="promptText"
                            value={data.promptText || ''}
                            onChange={(e) => updateEditorData({ promptText: e.target.value })}
                            className="w-full p-2 text-sm border border-light-300 rounded-lg font-bold"
                            required
                        />
                    </div>


                    {/* Camera-task evaluation settings */}
                    {isCameraTask && (
                        <div className="space-y-3 border-t border-light-300 pt-4">
                            <h4 className="font-bold text-sm text-dark-200">AI Evaluation</h4>
                            <div>
                                <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Trigger Word (Expected Label)</label>
                                <input
                                    name="expectedLabel"
                                    list="available-signs"
                                    value={data.expectedLabel || ''}
                                    onChange={(e) => updateEditorData({ expectedLabel: e.target.value })}
                                    className="w-full p-2 text-sm border border-light-300 rounded-lg font-bold"
                                    placeholder="e.g. La revedere"
                                />
                                <datalist id="available-signs">
                                    {availableSigns.map((s) => (
                                        <option key={s} value={s} />
                                    ))}
                                </datalist>
                                <p className="text-[10px] text-dark-300 mt-1">
                                    This value is compared against the model prediction. Leave blank only if your prompt ends with ': Cuvant'.
                                </p>
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Min Confidence</label>
                                <input
                                    name="minConfidence"
                                    type="number"
                                    min={0}
                                    max={1}
                                    step={0.05}
                                    value={typeof data.minConfidence === 'number' ? String(data.minConfidence) : (data.minConfidence ? String(data.minConfidence) : '')}
                                    onChange={(e) => {
                                        const v = e.target.value;
                                        if (!v) updateEditorData({ minConfidence: undefined });
                                        else {
                                            const n = Number(v);
                                            updateEditorData({ minConfidence: Number.isFinite(n) ? n : undefined });
                                        }
                                    }}
                                    className="w-full p-2 text-sm border border-light-300 rounded-lg"
                                    placeholder="0.7"
                                />
                            </div>
                        </div>
                    )}

                    {/* Main Video (for non-VideoMultipleChoice) */}
                    {data.type !== TaskType.VideoMultipleChoice && (
                        <div>
                            <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Video (Asset Key or URL)</label>
                            {data.signVideoUrl && <div className="text-xs text-green-600 mb-1 truncate">Current: {data.signVideoUrl}</div>}
                            {LESSON_MEDIA_KEYS.length === 0 ? (
                                <div className="p-3 bg-light-50 border border-light-200 rounded-lg text-xs text-dark-300 mb-2">
                                    No videos found in <code>frontend/src/assets/lesson-media</code>. Add at least one <code>.mp4</code>, <code>.webm</code>, or <code>.ogg</code> file there.
                                </div>
                            ) : null}
                            <input
                                name="signVideoUrl"
                                list="available-lesson-media"
                                value={data.signVideoUrl || ''}
                                onChange={(e) => updateEditorData({ signVideoUrl: e.target.value })}
                                className="w-full p-2 text-sm border border-light-300 rounded-lg font-mono"
                                placeholder={LESSON_MEDIA_KEYS.length ? 'e.g. hello.mp4 (or paste a URL)' : 'Paste a URL (e.g. /videos/hello.mp4 or https://...)'}
                            />
                        </div>
                    )}

                    {/* Video Multiple Choice Fields */}
                    {data.type === TaskType.VideoMultipleChoice && (
                        <div className="space-y-4 border-t border-light-300 pt-4">
                            <h4 className="font-bold text-sm text-dark-200">Video Options</h4>
                            {[0, 1, 2, 3].map((idx) => (
                                <div key={idx} className="p-3 border border-light-200 rounded-lg bg-light-50">
                                    <div className="flex justify-between mb-2">
                                        <label className="text-xs font-bold text-dark-300 uppercase">Option {idx + 1}</label>
                                        <div className="flex items-center gap-2">
                                            <input
                                                type="radio"
                                                name="correctOption"
                                                value={idx}
                                                defaultChecked={data.options?.[idx]?.isCorrect}
                                                className="w-4 h-4 text-green-600 focus:ring-green-600"
                                            />
                                            <label className="text-xs font-bold text-green-700">Correct?</label>
                                        </div>
                                    </div>
                                    {data.options?.[idx]?.videoUrl && (
                                        <div className="text-xs text-blue-600 mb-1 truncate">
                                            Current: {String(data.options[idx].videoUrl)}
                                        </div>
                                    )}
                                    <input
                                        name={`optionVideo${idx}`}
                                        list="available-lesson-media"
                                        defaultValue={data.options?.[idx]?.videoUrl || ''}
                                        className="w-full p-2 text-xs border border-light-300 rounded-lg font-mono"
                                        placeholder={LESSON_MEDIA_KEYS.length ? 'e.g. hello.mp4 (or paste a URL)' : 'Paste a URL'}
                                    />
                                </div>
                            ))}
                        </div>
                    )}

                    {LESSON_MEDIA_KEYS.length > 0 && (
                        <datalist id="available-lesson-media">
                            {LESSON_MEDIA_KEYS.map((k) => (
                                <option key={k} value={k} />
                            ))}
                        </datalist>
                    )}

                    {/* Dynamic Options Editor (Replaces JSON) */}
                    {data.type === TaskType.SignToText && (
                        <div className="space-y-3 border-t border-light-300 pt-4">
                            <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Answer Options</label>
                            {(data.options || []).map((option: any, idx: number) => (
                                <div key={idx} className="flex items-center gap-2">
                                    <input
                                        type="radio"
                                        name="correctOption"
                                        checked={option.isCorrect}
                                        onChange={() => {
                                            const newOptions = (data.options || []).map((o: any, i: number) => ({ ...o, isCorrect: i === idx }));
                                            updateEditorData({ options: newOptions });
                                        }}
                                        className="w-4 h-4 text-green-600 focus:ring-green-600 shrink-0"
                                        title="Mark as correct answer"
                                    />
                                    <input
                                        type="text"
                                        value={option.text || ''}
                                        onChange={(e) => {
                                            const newOptions = [...(data.options || [])];
                                            newOptions[idx] = { ...newOptions[idx], text: e.target.value };
                                            updateEditorData({ options: newOptions });
                                        }}
                                        className="flex-1 p-2 text-sm border border-light-300 rounded-lg"
                                        placeholder={`Option ${idx + 1}`}
                                    />
                                    <button
                                        type="button"
                                        onClick={() => {
                                            const newOptions = data.options.filter((_: any, i: number) => i !== idx);
                                            updateEditorData({ options: newOptions });
                                        }}
                                        className="p-2 text-red-400 hover:text-red-600"
                                        title="Remove option"
                                    >
                                        <Icon name="trash" className="w-4 h-4" />
                                    </button>
                                </div>
                            ))}
                            <button
                                type="button"
                                onClick={() => {
                                    const newOptions = [...(data.options || []), { id: Date.now().toString(), text: '', isCorrect: false }];
                                    updateEditorData({ options: newOptions });
                                }}
                                className="text-xs font-bold text-primary hover:text-primary-dark flex items-center gap-1 mt-2"
                            >
                                <Icon name="plus" className="w-3 h-3" /> Add Option
                            </button>
                        </div>
                    )}
                </>
            )}

            {/* Achievement Fields */}
            {type === 'achievement' && (
                <>
                    <div>
                        <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Title</label>
                        <input
                            name="title"
                            value={data.title || ''}
                            onChange={(e) => updateEditorData({ title: e.target.value })}
                            className="w-full p-2 text-sm border border-light-300 rounded-lg font-bold"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Description</label>
                        <textarea
                            name="description"
                            value={data.description || ''}
                            onChange={(e) => updateEditorData({ description: e.target.value })}
                            className="w-full p-2 text-sm border border-light-300 rounded-lg"
                            rows={3}
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Icon</label>
                        <div className="space-y-2">
                            {ACHIEVEMENT_ICON_KEYS.length === 0 ? (
                                <div className="p-3 bg-light-50 border border-light-200 rounded-lg text-xs text-dark-300">
                                    No SVG icons found in <code>frontend/src/assets/achievements</code>. Add at least one <code>.svg</code> file there.
                                </div>
                            ) : (
                                <>
                                    <select
                                        name="icon"
                                        value={data.icon || ACHIEVEMENT_ICON_KEYS[0] || ''}
                                        onChange={(e) => updateEditorData({ icon: e.target.value })}
                                        className="w-full p-2 text-sm border border-light-300 rounded-lg"
                                        required
                                    >
                                        {data.icon && !ACHIEVEMENT_ICON_KEYS.includes(String(data.icon)) && (
                                            <option value={data.icon}>(Legacy) {String(data.icon)}</option>
                                        )}
                                        {ACHIEVEMENT_ICON_KEYS.map((key) => (
                                            <option key={key} value={key}>
                                                {key}
                                            </option>
                                        ))}
                                    </select>

                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 bg-white rounded-lg border border-light-200 flex items-center justify-center">
                                            <AchievementIcon name={String(data.icon || ACHIEVEMENT_ICON_KEYS[0] || 'trophy')} className="w-6 h-6 text-primary" />
                                        </div>
                                        <div className="text-xs text-dark-300 truncate flex-1">
                                            Stored value: <span className="font-mono">{String(data.icon || ACHIEVEMENT_ICON_KEYS[0] || '')}</span>
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>

                    <div className="border-t border-light-300 pt-4 mt-4">
                        <h3 className="font-bold text-dark-100 mb-3 text-sm">Unlock Condition</h3>

                        {/*
                          NOTE: achievement `conditionType` values are persisted in the DB and must match
                          the backend achievement evaluation logic (see `backend/app/services/achievement_service.py`).
                        */}
                        <div className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Condition Type</label>
                                <select
                                    name="conditionType"
                                    value={achievementConditionType}
                                    onChange={(e) => updateEditorData({ conditionType: e.target.value })}
                                    className="w-full p-2 text-sm border border-light-300 rounded-lg"
                                >
                                    {achievementConditionType && !['manual', 'lessons_completed', 'unit_completed', 'xp_threshold', 'streak'].includes(achievementConditionType) && (
                                        <option value={achievementConditionType}>(Legacy) {achievementConditionType}</option>
                                    )}
                                    <option value="manual">Manual / Hidden</option>
                                    <option value="lessons_completed">Lessons Completed</option>
                                    <option value="unit_completed">Unit Completed</option>
                                    <option value="xp_threshold">XP Threshold</option>
                                    <option value="streak">Streak (Days)</option>
                                </select>
                            </div>

                            {achievementConditionType === 'unit_completed' && (
                                <div>
                                    <label className="block text-xs font-bold text-dark-300 uppercase mb-1">Target Unit</label>
                                    <select
                                        name="conditionValue"
                                        value={data.conditionValue || ''}
                                        onChange={(e) => updateEditorData({ conditionValue: e.target.value })}
                                        className="w-full p-2 text-sm border border-light-300 rounded-lg"
                                    >
                                        <option value="">-- Select Unit --</option>
                                        {units.map(u => (
                                            <option key={u.id} value={u.unitId}>
                                                Unit {u.orderIndex}: {u.title}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            )}

                            {(achievementConditionType === 'xp_threshold' || achievementConditionType === 'streak' || achievementConditionType === 'lessons_completed') && (
                                <div>
                                    <label className="block text-xs font-bold text-dark-300 uppercase mb-1">
                                        {achievementConditionType === 'xp_threshold' ? 'Required XP' : achievementConditionType === 'streak' ? 'Required Streak (Days)' : 'Required Lessons'}
                                    </label>
                                    <input
                                        name="conditionValue"
                                        type="number"
                                        value={data.conditionValue || ''}
                                        onChange={(e) => updateEditorData({ conditionValue: e.target.value })}
                                        className="w-full p-2 text-sm border border-light-300 rounded-lg"
                                        placeholder="e.g. 100"
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}

            <div className="pt-4">
                <button type="submit" className="w-full bg-primary text-white py-3 rounded-xl font-bold hover:bg-primary-dark transition-colors shadow-lg shadow-primary/20">
                    {mode === 'create' ? 'Create' : 'Save Changes'}
                </button>
            </div>
        </form>
    );
};
