import { useState, useEffect } from 'react';
import { api } from '@/services/api';
import { Achievement } from '@/types';

export const useAchievements = () => {
    const [achievements, setAchievements] = useState<Achievement[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAchievements = async () => {
            try {
                const response = await api.lesson.getAchievements();
                if (response.success && response.data) {
                    setAchievements(response.data.achievements);
                }
            } catch (err: any) {
                console.error('Failed to fetch achievements', err);
                setError(err.message || 'Failed to fetch achievements');
            } finally {
                setIsLoading(false);
            }
        };

        fetchAchievements();
    }, []);

    return { achievements, isLoading, error };
};
