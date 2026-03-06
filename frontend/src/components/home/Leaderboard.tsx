import React, { useState, useEffect } from 'react';
import { api } from '@/services/api';
import { LeaderboardEntry } from '@/types';
import { Icon } from '@/components/ui/Icon';
import { UserAvatar } from '@/components/ui/UserAvatar';

interface LeaderboardProps {
    currentUserId: string;
}

export const Leaderboard: React.FC<LeaderboardProps> = ({ currentUserId }) => {
    const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchLeaderboard = async () => {
            try {
                const response = await api.user.getLeaderboard();
                if (response.success && response.data) {
                    setEntries(response.data.leaderboard);
                }
            } catch (error) {
                console.error("Failed to fetch leaderboard:", error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchLeaderboard();
    }, []);

    if (isLoading) {
        return (
            <div className="bg-white rounded-3xl p-6 shadow-subtle border-2 border-light-300">
                <div className="animate-pulse flex space-x-4">
                    <div className="flex-1 space-y-4 py-1">
                        <div className="h-4 bg-light-300 rounded w-3/4"></div>
                        <div className="space-y-3">
                            <div className="h-4 bg-light-300 rounded"></div>
                            <div className="h-4 bg-light-300 rounded w-5/6"></div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-3xl p-6 shadow-subtle border-2 border-light-300">
            <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-accent-orange/10 flex items-center justify-center">
                    <Icon name="trophy" className="w-6 h-6 text-accent-orange" />
                </div>
                <h2 className="text-xl font-black text-dark-100">Clasament (XP)</h2>
            </div>

            <div className="space-y-3">
                {entries.map((entry, index) => {
                    const isCurrentUser = entry.userId === currentUserId;
                    const rank = index + 1;

                    let rankDisplay;
                    if (rank === 1) rankDisplay = <span className="text-accent-orange font-black text-lg">1</span>;
                    else if (rank === 2) rankDisplay = <span className="text-dark-300 font-black text-lg">2</span>;
                    else if (rank === 3) rankDisplay = <span className="text-accent-orange/50 font-black text-lg">3</span>;
                    else rankDisplay = <span className="text-dark-300 font-bold">{rank}</span>;

                    return (
                        <div
                            key={entry.userId}
                            className={`flex items-center gap-4 p-3 rounded-2xl transition-colors ${isCurrentUser ? 'bg-primary/10 border border-primary/20' : 'hover:bg-light-100'
                                }`}
                        >
                            <div className="w-8 text-center">{rankDisplay}</div>
                            <UserAvatar name={entry.name} level={entry.level} size="sm" />
                            <div className="flex-grow">
                                <div className={`font-bold ${isCurrentUser ? 'text-primary' : 'text-dark-100'}`}>
                                    {entry.name}{isCurrentUser ? ' (Tu)' : ''}
                                </div>
                            </div>
                            <div className="font-black text-accent-orange">{entry.xp} XP</div>
                        </div>
                    );
                })}
                {entries.length === 0 && (
                    <div className="text-center text-dark-300 py-4 font-bold">
                        Fără utilizatori
                    </div>
                )}
            </div>
        </div>
    );
};
