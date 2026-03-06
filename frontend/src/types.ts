export enum Screen {
  Splash,
  Auth,
  Home,
  Learn,
  Profile,
  Achievements,
  Lesson,
  Admin,
}

export enum TaskType {
  RepeatSign = 'REPEAT_SIGN',
  TextToSign = 'TEXT_TO_SIGN',
  SignToText = 'SIGN_TO_TEXT',
  VideoMultipleChoice = 'VIDEO_MULTIPLE_CHOICE',
}

export interface TaskOption {
  id: string;
  text?: string;
  videoUrl?: string; // Placeholder for video/image thumbnail
  isCorrect: boolean;
}

export interface Task {
  id: string;
  type: TaskType;
  prompt: string; // e.g., "Mulțumesc" or "Perform this sign"
  videoUrl?: string; // Video of the sign to be performed/recognized
  expectedLabel?: string; // Expected AI label for camera tasks
  minConfidence?: number; // Confidence threshold for passing camera tasks
  options?: TaskOption[];

}

export interface Lesson {
  id: string;
  title: string;
  tasks: Task[];
  xp: number;
}

export interface Unit {
  id: string;
  title: string;
  lessons: Lesson[];
}



// FIX: Moved IconName from components/Icon.tsx to resolve a type error and make it centrally available.
export type IconName =
  'home' | 'learn' | 'profile' | 'achievements' |
  'xp' | 'streak' | 'lock' | 'book' | 'trophy' | 'play' | 'close' | 'avatar' |
  'freq-daily' | 'freq-few' | 'freq-once' |
  'len-short' | 'len-medium' | 'len-long' |
  'xp-relaxed' | 'xp-normal' | 'xp-serious' |
  'logout' | 'heart' | 'check' |
  'camera' | 'edit' | 'trash' | 'plus' | 'star' | 'medal' | 'target' | 'fire' | 'upload' | 'menu' | 'eye' | 'graduation-cap' |
  'zoom-in' | 'zoom-out' | 'quiz' | 'add' | 'chevron-down' | 'chevron-right' | 'mascot';

export interface Achievement {
  id: string | number;
  achievementId?: string;
  title: string;
  description: string;
  icon: IconName | string;
  conditionType?: 'lessons_completed' | 'unit_completed' | 'xp_threshold' | 'streak' | 'manual';
  conditionValue?: string;
}



export interface User {
  id: string;
  displayName: string;
  email: string;
  xp: number;
  dailyStreak: number;
  level: number;
  levelProgress: number; // Percentage
  badges: string[]; // Array of Achievement IDs
  completedLessons: string[];
  isAdmin?: boolean;
}

export interface LeaderboardEntry {
  userId: string;
  name: string;
  xp: number;
  level: number;
}
