
import { TaskType } from '@/types';

export interface Task {
    id: string;
    taskId: string;
    lessonId: string;
    type: TaskType;
    promptText: string;
    orderIndex: number;
    options: any[];
    signVideoUrl?: string;
    expectedLabel?: string;
    minConfidence?: number;

}

export interface Lesson {
    id: string;
    lessonId: string;
    unitId: string;
    title: string;
    description: string;
    orderIndex: number;
    xpRewardBase: number;
    isPublished: boolean;
    tasks: Task[];
}


export interface Unit {
    id: string;
    unitId: string;
    title: string;
    description: string;
    orderIndex: number;
    isPublished: boolean;
    lessons: Lesson[];
}

export type EditorMode = 'create' | 'edit';
export type ItemType = 'unit' | 'lesson' | 'task' | 'achievement';

export interface Achievement {
    id: string;
    achievementId?: string;
    title: string;
    description: string;
    icon: string;
    conditionType?: string;
    conditionValue?: string;
}

export interface EditorState {
    mode: EditorMode;
    type: ItemType;
    data: any;
    parentId?: string;
}

export interface DraggedItem {
    type: 'unit' | 'lesson' | 'task';
    id: string;
    index: number;
    parentId?: string;
}
