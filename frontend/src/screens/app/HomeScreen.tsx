import React, { useEffect, useState } from 'react';
import { Screen, User, IconName, Achievement } from '@/types';
import { Mascot } from '@/components/ui/Mascot';
import { Icon } from '@/components/ui/Icon';
import { AchievementIcon } from '@/components/ui/AchievementIcon';
import { Leaderboard } from '@/components/home/Leaderboard';
import { UserAvatar } from '@/components/ui/UserAvatar';
import { api } from '@/services/api';
import { useAchievements } from '@/hooks/useAchievements';

interface HomeScreenProps {
    user: User;
    onContinueLesson: () => void;
    setScreen: (screen: Screen) => void;
}

const StatCard: React.FC<{ icon: IconName; value: string; label: string; className?: string; color?: string }> = ({ icon, value, label, className, color = 'text-primary' }) => (
    <div className={`bg-white p-5 rounded-2xl shadow-subtle flex items-center gap-4 transition-transform hover:scale-[1.02] ${className}`}>
        <div className={`p-3 rounded-xl bg-opacity-10 ${color.replace('text-', 'bg-')}`}>
            <Icon name={icon} className={`w-7 h-7 ${color}`} />
        </div>
        <div>
            <div className="font-black text-xl text-dark-100 leading-tight">{value}</div>
            <div className="text-xs font-bold text-dark-300 uppercase tracking-wide mt-1">{label}</div>
        </div>
    </div>
);

export const HomeScreen: React.FC<HomeScreenProps> = ({ user, onContinueLesson, setScreen }) => {
    const { achievements, isLoading: isLoadingAchievements } = useAchievements();

    const recentBadges = achievements.filter(ach => user.badges.includes(ach.achievementId || ach.id)).slice(-3).reverse();
    const xpForNextLevel = 1000;
    const currentLevelXp = Math.floor((user.levelProgress / 100) * xpForNextLevel);

    const getProgressBarColor = () => {
        if (user.levelProgress < 33) return 'bg-accent-red';
        if (user.levelProgress < 66) return 'bg-accent-orange';
        return 'bg-accent-green';
    };

    return (
        <div className="p-6 md:p-10 animate-pop-in max-w-7xl mx-auto">
            <header className="flex justify-between items-center mb-10">
                <div>
                    <p className="text-lg font-medium text-dark-300 mb-1">Bine ai revenit,</p>
                    <h1 className="text-4xl font-black text-dark-100 tracking-tight">{user.displayName}</h1>
                </div>
                <button
                    onClick={() => setScreen(Screen.Profile)}
                    className="group relative w-16 h-16 rounded-full p-1 bg-gradient-to-br from-primary to-accent-blue shadow-lg hover:shadow-glow transition-all duration-300"
                >
                    <div className="w-full h-full bg-white rounded-full flex items-center justify-center border-4 border-transparent group-hover:border-white/50 transition-all overflow-hidden">
                        <UserAvatar
                            name={user.displayName}
                            className="w-full h-full"
                            textClassName="text-lg"
                        />
                    </div>
                </button>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Column */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Hero Card */}
                    <div className="bg-gradient-primary p-8 rounded-3xl shadow-lifted text-white flex items-center justify-between relative overflow-hidden group">
                        <div className="absolute top-0 right-0 w-64 h-64 bg-white opacity-10 rounded-full blur-3xl transform translate-x-1/3 -translate-y-1/3 group-hover:scale-110 transition-transform duration-700"></div>
                        <div className="absolute bottom-0 left-0 w-48 h-48 bg-accent-yellow opacity-10 rounded-full blur-2xl transform -translate-x-1/3 translate-y-1/3"></div>

                        <div className="relative z-10 max-w-md">
                            <div className="inline-block px-3 py-1 rounded-full bg-white/20 font-bold text-xs mb-3 backdrop-blur-sm border border-white/10">
                                LECȚIA URMĂTOARE
                            </div>
                            <h2 className="text-3xl font-black mb-2 leading-tight">Hai să învățăm!</h2>
                            <p className="text-lg font-medium text-white/90 mb-8 leading-relaxed">Continuă-ți aventura în RSL și deblochează noi orizonturi.</p>
                            <button
                                onClick={onContinueLesson}
                                className="bg-white text-primary-dark font-bold py-3.5 px-8 rounded-xl text-lg shadow-lg transition-all transform hover:scale-105 hover:shadow-xl active:scale-95 flex items-center gap-2"
                            >
                                <Icon name="play" className="w-5 h-5" />
                                Continuă
                            </button>
                        </div>
                        <div className="hidden md:block relative z-10">
                            <Icon name="graduation-cap" className="w-32 h-32 text-accent-yellow drop-shadow-lg transform rotate-12 group-hover:rotate-0 transition-transform duration-500" />
                        </div>
                    </div>

                    {/* Progress Section */}
                    <div className="bg-white p-8 rounded-3xl shadow-subtle border border-light-300/50">
                        <div className="flex justify-between items-end mb-4">
                            <div>
                                <h2 className="text-xl font-black text-dark-100 mb-1">Progres Nivel {user.level}</h2>
                                <p className="text-dark-300 text-sm font-medium">Continuă așa!</p>
                            </div>
                            <span className="font-black text-2xl text-primary">{currentLevelXp} <span className="text-base text-dark-300 font-bold">/ {xpForNextLevel} XP</span></span>
                        </div>
                        <div className="w-full bg-light-200 rounded-full h-6 shadow-inner overflow-hidden">
                            <div
                                className={`h-full rounded-full transition-all duration-1000 ease-out relative ${getProgressBarColor()}`}
                                style={{ width: `${user.levelProgress}%` }}
                            >
                                <div className="absolute inset-0 bg-white/20 animate-shimmer" style={{ backgroundSize: '200% 100%' }}></div>
                            </div>
                        </div>
                        <p className="text-right text-sm font-bold text-dark-300 mt-3">
                            Încă <span className="text-primary">{xpForNextLevel - currentLevelXp} XP</span> până la nivelul următor!
                        </p>
                    </div>

                    {/* Mascot Tip */}
                    <div className="bg-primary/5 p-6 rounded-3xl flex items-center gap-6 border border-primary/10">
                        <Mascot pose="wave" className="w-24 h-32 flex-shrink-0 drop-shadow-md" />
                        <div>
                            <h2 className="text-lg font-black text-primary mb-2">Lingoșel spune:</h2>
                            <p className="text-lg text-dark-200 font-medium italic leading-relaxed">"Fiecare semn învățat este un pas înainte spre o lume mai incluzivă!"</p>
                        </div>
                    </div>
                </div>

                {/* Side Column */}
                <div className="space-y-8">
                    <div className="grid grid-cols-2 lg:grid-cols-1 gap-4">
                        <StatCard icon="star" value={user.xp.toLocaleString()} label="XP Total" color="text-accent-yellow" />
                        <StatCard icon="target" value={`${user.dailyStreak} zile`} label="Serie Zilnică" color="text-accent-red" />
                    </div>

                    <div className="bg-white p-6 rounded-3xl shadow-subtle border border-light-300/50">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-black text-dark-100">Realizări</h2>
                            <button onClick={() => setScreen(Screen.Achievements)} className="text-primary font-bold text-sm hover:underline">Vezi tot</button>
                        </div>

                        {user.badges.length > 0 ? (
                            <div className="grid grid-cols-3 gap-4">
                                {recentBadges.map(badge => (
                                    <div key={badge.id} className="aspect-square bg-light-200 rounded-2xl flex items-center justify-center p-3 group relative cursor-help transition-all hover:bg-primary/10">
                                        <AchievementIcon name={String(badge.icon)} className="w-full h-full text-accent-orange drop-shadow-sm transition-transform group-hover:scale-110" />

                                        {/* Tooltip */}
                                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-max max-w-[150px] bg-dark-100 text-white text-xs font-bold py-2 px-3 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-20 text-center shadow-xl">
                                            {badge.title}
                                            <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-dark-100"></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-4">
                                <Icon name="lock" className="w-10 h-10 text-dark-300/30 mx-auto mb-2" />
                                <p className="text-dark-300 font-medium text-sm">Continuă să înveți pentru a debloca realizări!</p>
                            </div>
                        )}
                    </div>

                    {/* Leaderboard Section */}
                    <Leaderboard currentUserId={user.id} />

                </div>
            </div>
        </div>
    );
};
