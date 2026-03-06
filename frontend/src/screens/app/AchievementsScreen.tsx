import React, { useEffect, useState } from 'react';
import { User, Achievement } from '@/types';
import { Icon } from '@/components/ui/Icon';
import { AchievementIcon } from '@/components/ui/AchievementIcon';
import { api } from '@/services/api';
import { useAchievements } from '@/hooks/useAchievements';

interface AchievementsScreenProps {
    user: User;
}

const PageHeader: React.FC<{ title: string }> = ({ title }) => (
    <div className="bg-primary pt-8 pb-16 text-light-100 relative">
        <h1 className="text-3xl font-black text-center">{title}</h1>
        <div className="absolute -bottom-px left-0 w-full overflow-hidden leading-none">
            <svg viewBox="0 0 1200 120" preserveAspectRatio="none" className="relative block w-full h-[50px]">
                <path d="M0,0 C150,130 350,0 500,60 C650,120 850,20 1000,80 C1150,140 1200,60 1200,60 L1200,120 L0,120 Z" className="fill-light-200"></path>
            </svg>
        </div>
    </div>
);

const AchievementCard: React.FC<{ achievement: Achievement, isUnlocked: boolean }> = ({ achievement, isUnlocked }) => {
    return (
        <div className={`p-4 rounded-2xl flex items-center gap-4 transition-all duration-300
            ${isUnlocked ? 'bg-light-100 shadow-subtle border border-light-300' : 'bg-light-100 opacity-50'}`}
        >
            <div className={`p-3 rounded-full transition-colors
                ${isUnlocked ? 'bg-accent-orange' : 'bg-dark-300/80'}`}
            >
                <AchievementIcon name={String(achievement.icon)} className="w-10 h-10 text-white" />
            </div>
            <div className="flex-1">
                <h3 className={`font-black text-lg ${isUnlocked ? 'text-dark-100' : 'text-dark-300'}`}>
                    {achievement.title}
                </h3>
                <p className={`text-sm font-semibold ${isUnlocked ? 'text-dark-200' : 'text-dark-300'}`}>
                    {achievement.description}
                </p>
            </div>
        </div>
    );
}

export const AchievementsScreen: React.FC<AchievementsScreenProps> = ({ user }) => {
    const { achievements, isLoading } = useAchievements();
    const unlockedAchievements = new Set(user.badges);

    return (
        <div className="bg-light-200 min-h-screen">
            <PageHeader title="Realizări" />
            <div className="p-4 md:p-6 -mt-8 animate-pop-in">
                {isLoading ? (
                    <div className="flex justify-center py-12">
                        <div className="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl mx-auto">
                        {achievements.map(ach => (
                            <AchievementCard
                                key={ach.id}
                                achievement={ach}
                                isUnlocked={unlockedAchievements.has(String(ach.id)) || unlockedAchievements.has(ach.achievementId || '')}
                            />
                        ))}
                        {achievements.length === 0 && (
                            <div className="col-span-full text-center py-12 text-dark-300">
                                <Icon name="trophy" className="w-16 h-16 mx-auto mb-4 opacity-20" />
                                <p>Nu există realizări disponibile momentan.</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};
