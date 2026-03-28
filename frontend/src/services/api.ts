// API Service for RSLlingo Backend
// This service handles all API calls to the backend

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Types
export interface AuthResponse {
  success: boolean;
  message: string;
  data: User;
}

export interface User {
  id: string;
  displayName: string;
  email: string;
  xp: number;
  dailyStreak: number;
  level: number;
  levelProgress: number;
  badges: string[];
  completedLessons: string[];
  isAdmin?: boolean;
}


export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

// Prototype identity storage (no auth token)
const getCurrentUserId = (): string | null => {
  return localStorage.getItem('userId');
};

const setCurrentUserId = (userId: string): void => {
  localStorage.setItem('userId', userId);
};

const clearCurrentUserId = (): void => {
  localStorage.removeItem('userId');
};

// Generic fetch wrapper
async function apiFetch<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Add prototype user identity header if available
  const userId = getCurrentUserId();
  if (userId) {
    headers['X-User-Id'] = userId;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  const rawBody = await response.text();
  let data: any = null;

  if (rawBody) {
    try {
      data = JSON.parse(rawBody);
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    const detail = data?.detail;
    const detailMessage =
      Array.isArray(detail)
        ? detail
          .map((d) => {
            const loc = Array.isArray(d?.loc) ? d.loc.join('.') : 'body';
            const msg = d?.msg || 'Invalid request';
            return `${loc}: ${msg}`;
          })
          .join('; ')
        : detail;

    const errorMessage =
      data?.message ||
      detailMessage ||
      (rawBody && !data ? rawBody : '') ||
      `Request failed (${response.status})`;
    throw new Error(errorMessage);
  }

  if (data === null) {
    throw new Error('Server returned an invalid response format');
  }

  return data as T;
}

// Authentication APIs
export const authAPI = {
  register: async (
    displayName: string,
    email: string,
    password: string
  ): Promise<AuthResponse> => {
    const response = await apiFetch<AuthResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ displayName, email, password }),
    });

    if (response.data.id) {
      setCurrentUserId(response.data.id);
    }

    return response;
  },

  login: async (email: string, password: string): Promise<AuthResponse> => {
    const response = await apiFetch<AuthResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (response.data.id) {
      setCurrentUserId(response.data.id);
    }

    return response;
  },

  logout: (): void => {
    clearCurrentUserId();
  },

  isAuthenticated: (): boolean => {
    return !!getCurrentUserId();
  },
};

// User APIs
export const userAPI = {
  getProfile: async (): Promise<ApiResponse<{ user: User }>> => {
    return apiFetch('/user/profile');
  },

  updateProfile: async (name: string): Promise<ApiResponse<{ user: User }>> => {
    return apiFetch('/user/profile', {
      method: 'PUT',
      body: JSON.stringify({ name }),
    });
  },



  completeLesson: async (data: {
    lessonId: string;
    unitId: string;
    xpEarned: number;
    tasksCompleted: number;
    totalTasks: number;
    mistakes: number;
    previousBadges?: string[];
  }): Promise<ApiResponse<{ user: User; newBadges: string[] }>> => {
    return apiFetch('/user/complete-lesson', {
      method: 'POST',
      body: JSON.stringify({
        ...data,
        previousBadges: data.previousBadges ?? [],
      }),
    });
  },

  getProgress: async (): Promise<ApiResponse<{ progress: any[] }>> => {
    return apiFetch('/user/progress');
  },

  getLeaderboard: async (limit: number = 10): Promise<ApiResponse<{ leaderboard: any[] }>> => {
    return apiFetch(`/user/leaderboard?limit=${limit}`);
  },

};

// Lesson APIs
export const lessonAPI = {
  getLearningPath: async (): Promise<ApiResponse<{ learningPath: any[] }>> => {
    return apiFetch('/lessons/learning-path');
  },

  getLesson: async (lessonId: string): Promise<ApiResponse<{ lesson: any; unit: any }>> => {
    return apiFetch(`/lessons/lesson/${lessonId}`);
  },

  getAchievements: async (): Promise<ApiResponse<{ achievements: any[] }>> => {
    return apiFetch('/lessons/achievements');
  },
};

// Sign Recognition APIs
export interface SignPrediction {
  sign: string;
  confidence: number;
}

export interface SignRecognitionResponse {
  success: boolean;
  prediction: string;
  confidence: number;
  all_predictions: SignPrediction[];
  target_label?: string;
  target_confidence?: number | null;
  target_rank?: number | null;
  idle_confidence?: number | null;
  selected_window?: {
    start_ratio: number;
    end_ratio: number;
  };
  required_sequence_length?: number;
  required_feature_size?: number;
  error?: string;
}

export interface SignStatusResponse {
  success: boolean;
  model_loaded: boolean;
  model_exists?: boolean;
  model_path: string;
  feature_scaler_path?: string;
  classes: string[];
  classes_count: number;
  required_sequence_length?: number;
  required_feature_size?: number;
  feature_scaler_available?: boolean;
  model_error?: string | null;
}

export const signAPI = {
  // Check if model is loaded and ready
  getStatus: async (): Promise<SignStatusResponse> => {
    return apiFetch('/sign/status');
  },

  // Get list of registered sign classes
  getClasses: async (): Promise<{ success: boolean; classes: string[] }> => {
    return apiFetch('/sign/classes');
  },

  // Recognise sign from landmarks sequence
  recognise: async (
    landmarks: number[][],
    options?: {
      targetLabel?: string;
      topK?: number;
    }
  ): Promise<SignRecognitionResponse> => {
    return apiFetch('/sign/recognise', {
      method: 'POST',
      body: JSON.stringify({
        landmarks,
        targetLabel: options?.targetLabel,
        topK: options?.topK,
      }),
    });
  },
};

// Export all APIs
export const api = {
  auth: authAPI,
  user: userAPI,
  lesson: lessonAPI,
  sign: signAPI,
};

export default api;
