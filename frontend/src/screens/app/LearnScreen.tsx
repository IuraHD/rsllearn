import React, { useState, useEffect } from 'react';
import { Unit, User } from '@/types';
import { Icon } from '@/components/ui/Icon';
import { api } from '@/services/api';
import { MascotPatrol } from '@/components/ui/MascotPatrol';

const PageHeader: React.FC<{ title: string }> = ({ title }) => (
    <div className="bg-gradient-primary pt-12 pb-24 text-white relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
            <div className="absolute top-[-50%] left-[-20%] w-[800px] h-[800px] bg-white opacity-5 rounded-full blur-3xl"></div>
            <div className="absolute bottom-[-20%] right-[-10%] w-[400px] h-[400px] bg-accent-blue opacity-20 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10 text-center px-6">
            <h1 className="text-4xl font-black tracking-tight mb-2 drop-shadow-md">{title}</h1>
            <p className="text-primary-light font-medium text-lg">Urmează calea spre cunoaștere</p>
        </div>

        <div className="absolute bottom-0 left-0 w-full overflow-hidden leading-none transform translate-y-1">
            <svg viewBox="0 0 1200 120" preserveAspectRatio="none" className="relative block w-full h-[60px]">
                <path d="M0,0 C150,100 350,0 500,50 C650,100 850,10 1000,60 C1150,110 1200,50 1200,50 L1200,120 L0,120 Z" className="fill-light-200"></path>
            </svg>
        </div>
    </div>
);

const UnitCard: React.FC<{ unit: Unit; isUnlocked: boolean; progress: number; onStartLesson: (lessonId: string) => void; index: number; nextLessonId?: string }> = ({ unit, isUnlocked, progress, onStartLesson, index, nextLessonId }) => {

    const getIconName = () => {
        if (!isUnlocked) return 'lock';
        return 'book';
    }
    const getTheme = () => {
        if (!isUnlocked) return { bg: 'bg-light-100', iconBg: 'bg-light-300', iconColor: 'text-dark-300', border: 'border-light-300' };

        const themes = [
            { bg: 'bg-white', iconBg: 'bg-accent-blue/10', iconColor: 'text-accent-blue', border: 'border-accent-blue/30' },
            { bg: 'bg-white', iconBg: 'bg-accent-green/10', iconColor: 'text-accent-green', border: 'border-accent-green/30' },
            { bg: 'bg-white', iconBg: 'bg-primary/10', iconColor: 'text-primary', border: 'border-primary/30' }
        ];
        return themes[index % themes.length];
    }

    const theme = getTheme();

    const handleStart = () => {
        if (nextLessonId) {
            onStartLesson(nextLessonId);
        } else if (unit.lessons && unit.lessons.length > 0) {
            onStartLesson(unit.lessons[0].id);
        }
    }

    return (
        <button
            onClick={isUnlocked ? handleStart : undefined}
            disabled={!isUnlocked}
            className={`w-full p-6 rounded-3xl shadow-subtle flex items-center gap-6 text-left transition-all duration-300 border-2 relative overflow-hidden group
                ${theme.bg} ${theme.border}
                ${isUnlocked ? 'hover:scale-[1.02] hover:shadow-lifted cursor-pointer' : 'opacity-70 cursor-not-allowed grayscale-[0.5]'}
            `}
            aria-label={`Începe unitatea: ${unit.title}`}
        >
            {isUnlocked && <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/50 to-transparent translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-1000 pointer-events-none"></div>}

            <div className={`w-20 h-20 rounded-2xl flex items-center justify-center shrink-0 shadow-inner transition-transform duration-300 group-hover:scale-110 ${theme.iconBg}`}>
                <Icon name={getIconName()} className={`w-10 h-10 ${theme.iconColor}`} />
            </div>

            <div className="flex-grow z-10">
                <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-bold text-dark-300 uppercase tracking-wider">Unitatea {index + 1}</span>
                    {isUnlocked && <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-1 rounded-lg">{Math.round(progress)}%</span>}
                </div>
                <h3 className={`font-black text-xl mb-3 leading-tight ${isUnlocked ? 'text-dark-100' : 'text-dark-300'}`}>
                    {unit.title}
                </h3>
                <div className="w-full bg-light-300 rounded-full h-3 overflow-hidden">
                    <div
                        className={`h-full rounded-full transition-all duration-1000 ease-out ${isUnlocked ? 'bg-gradient-to-r from-primary to-accent-blue' : 'bg-dark-300'}`}
                        style={{ width: `${isUnlocked ? progress : 0}%` }}
                    ></div>
                </div>
            </div>

            {isUnlocked && (
                <div className="w-12 h-12 rounded-full bg-primary text-white flex items-center justify-center shadow-lg shadow-primary/30 transform translate-x-4 opacity-0 group-hover:translate-x-0 group-hover:opacity-100 transition-all duration-300">
                    <Icon name="play" className="w-6 h-6 ml-1" />
                </div>
            )}
        </button>
    );
};

interface LearnScreenProps {
    user: User;
    onStartLesson: (lessonId: string) => void;
}

export const LearnScreen: React.FC<LearnScreenProps> = ({ user, onStartLesson }) => {
    const [units, setUnits] = useState<Unit[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchLearningPath = async () => {
            try {
                const response = await api.lesson.getLearningPath();
                if (response.success && response.data) {
                    // Map backend data to frontend types
                    const mappedUnits: Unit[] = response.data.learningPath.map((u: any) => ({
                        id: u.id,
                        title: u.title,
                        lessons: u.lessons.map((l: any) => ({
                            id: l.id,
                            title: l.title,
                            xp: l.xp,
                            tasks: []
                        }))
                    }));
                    setUnits(mappedUnits);
                }
            } catch (error) {
                console.error('Failed to fetch learning path:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchLearningPath();
    }, []);

    const getUnitProgress = (unit: Unit) => {
        if (!unit.lessons || unit.lessons.length === 0) return 0;
        const completedInUnit = unit.lessons.filter(lesson => user.completedLessons.includes(lesson.id)).length;
        return (completedInUnit / unit.lessons.length) * 100;
    };

    const getNextLessonId = (unit: Unit) => {
        if (!unit.lessons || unit.lessons.length === 0) return undefined;
        const firstUncompleted = unit.lessons.find(lesson => !user.completedLessons.includes(lesson.id));
        return firstUncompleted ? firstUncompleted.id : unit.lessons[0].id;
    };

    if (isLoading) {
        return (
            <div className="flex-grow flex items-center justify-center bg-light-100">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
                    <p className="text-dark-300 font-medium animate-pulse">Se încarcă lecțiile...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex-grow bg-light-100 pb-24">
            <PageHeader title="Învață" />

            <div className="max-w-2xl mx-auto px-6 -mt-10 relative z-20 space-y-6">
                {units.length === 0 ? (
                    <div className="text-center py-10 bg-white rounded-3xl shadow-subtle">
                        <Icon name="book" className="w-16 h-16 text-dark-300 mx-auto mb-4 opacity-50" />
                        <h3 className="text-xl font-bold text-dark-100 mb-2">Nu există lecții disponibile</h3>
                        <p className="text-dark-300">Revin-o mai târziu pentru conținut nou.</p>
                    </div>
                ) : (
                    units.map((unit, index) => (
                        <UnitCard
                            key={unit.id}
                            unit={unit}
                            isUnlocked={true}
                            progress={getUnitProgress(unit)}
                            onStartLesson={onStartLesson}
                            index={index}
                            nextLessonId={getNextLessonId(unit)}
                        />
                    ))
                )}
                <div className="relative mt-20">
                    <MascotPatrol />
                    <div className="border-t border-light-300 pt-8 pb-12 flex flex-col items-center gap-4">
                        <div className="w-12 h-12 bg-white rounded-2xl shadow-subtle flex items-center justify-center opacity-50">
                            <Icon name="mascot" className="w-6 h-6 text-dark-300" />
                        </div>
                        <p className="text-dark-300 font-bold text-xs uppercase tracking-widest opacity-40">Creat cu ❤️ pentru RSL</p>
                    </div>
                </div>
            </div>
        </div>
    );
};
