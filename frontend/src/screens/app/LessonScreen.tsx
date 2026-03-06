import React, { useState, useEffect } from 'react';
import { Task, Lesson, User } from '@/types';
import { Mascot } from '@/components/ui/Mascot';
import { CameraOverlay } from '@/components/camera/CameraOverlay';
import { Icon } from '@/components/ui/Icon';
import { api } from '@/services/api';
import { evaluateSelectionTask, getTaskTypeModule, isCameraTaskType, isCheckDisabledForTask } from '@/lesson/taskTypeModules';

const ProgressBar: React.FC<{ progress: number }> = ({ progress }) => (
    <div className="w-full bg-light-300 rounded-full h-4 shadow-inner overflow-hidden relative">
        <div
            className="bg-gradient-to-r from-primary to-accent-blue h-full rounded-full transition-all duration-500 ease-out relative"
            style={{ width: `${progress}%` }}
        >
            <div className="absolute inset-0 bg-white/20 animate-shimmer" style={{ backgroundSize: '200% 100%' }}></div>
        </div>
    </div>
);

interface LessonCompleteScreenProps {
    xp: number;
    onContinue: () => void;
    isLoading?: boolean;
}

const LessonCompleteScreen: React.FC<LessonCompleteScreenProps> = ({ xp, onContinue, isLoading }) => {
    return (
        <div className="flex-grow flex flex-col items-center justify-center bg-gradient-to-b from-accent-orange to-[#FF8A65] text-center p-4 sm:p-6 animate-pop-in relative min-h-[100dvh] overflow-hidden">
            {/* Confetti-like background elements */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                {[...Array(20)].map((_, i) => (
                    <div key={i} className="absolute w-3 h-3 bg-white rounded-full animate-float" style={{
                        left: `${Math.random() * 100}%`,
                        top: `${Math.random() * 100}%`,
                        animationDelay: `${Math.random() * 2}s`,
                        opacity: 0.3
                    }}></div>
                ))}
            </div>

            <div className="relative z-10 flex flex-col items-center mb-8 sm:mb-10">
                <div className="relative">
                    <div className="absolute inset-0 bg-white/30 blur-3xl rounded-full transform scale-150"></div>
                    <Mascot pose="celebrate" className="w-40 h-48 sm:w-56 sm:h-64 drop-shadow-2xl relative z-10" />
                </div>
                <h1 className="text-4xl sm:text-5xl font-black text-white mt-6 drop-shadow-lg tracking-tight">Felicitări!</h1>
                <p className="text-white/90 text-base sm:text-xl font-medium mt-2">Ai completat lecția cu succes!</p>
            </div>

            <div className="bg-white p-6 sm:p-8 rounded-3xl w-full max-w-md mx-auto shadow-lifted animate-slide-up" style={{ animationDelay: '0.2s' }}>
                <p className="font-bold text-dark-300 uppercase tracking-wider mb-4">Recompensă Totală</p>
                <div className="bg-accent-yellow/10 border-2 border-accent-yellow/30 rounded-2xl p-5 sm:p-6 mb-6 flex items-center justify-center gap-4">
                    <Icon name="xp" className="w-10 h-10 sm:w-12 sm:h-12 text-accent-yellow drop-shadow-sm" />
                    <span className="text-4xl sm:text-5xl font-black text-dark-100">+{xp}</span>
                </div>
                <button
                    onClick={onContinue}
                    disabled={isLoading}
                    className={`w-full bg-primary text-white font-bold py-3 sm:py-4 px-6 rounded-xl text-base sm:text-lg shadow-lg shadow-primary/30 uppercase tracking-wide transition-all transform ${isLoading ? 'opacity-70 cursor-not-allowed' : 'hover:scale-105 hover:shadow-glow active:scale-95'}`}
                >
                    {isLoading ? (
                        <div className="flex items-center justify-center gap-2">
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                            <span>Se salvează...</span>
                        </div>
                    ) : 'Continuă'}
                </button>
            </div>
        </div>
    );
};

import { MascotPatrol } from '@/components/ui/MascotPatrol';

export const LessonScreen: React.FC<{ lessonId: string; onExit: (updatedUser: User) => void }> = ({ lessonId, onExit }) => {
    const [lesson, setLesson] = useState<Lesson | null>(null);
    const [unitId, setUnitId] = useState<string>('');
    const [isLoading, setIsLoading] = useState(true);
    const [taskIndex, setTaskIndex] = useState(0);
    const [progress, setProgress] = useState(0);
    const [selectedOption, setSelectedOption] = useState<string | null>(null);
    const [feedback, setFeedback] = useState<'correct' | 'incorrect' | null>(null);
    const [showCamera, setShowCamera] = useState(false);
    const [isComplete, setIsComplete] = useState(false);
    const [mistakes, setMistakes] = useState(0);
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        const fetchLesson = async () => {
            try {
                const response = await api.lesson.getLesson(lessonId);
                if (response.success && response.data) {
                    const backendLesson = response.data.lesson;
                    const backendUnit = response.data.unit;

                    const mappedLesson: Lesson = {
                        id: backendLesson.id,
                        title: backendLesson.title,
                        xp: backendLesson.xp ?? backendLesson.xpRewardBase ?? 0,
                        tasks: backendLesson.tasks.map((t: any) => ({
                            id: t.taskId || t.id,
                            type: t.type,
                            prompt: t.prompt ?? t.promptText ?? '',
                            videoUrl: t.videoUrl ?? t.video_url ?? t.signVideoUrl ?? t.mediaUrl,
                            expectedLabel: t.expectedLabel ?? t.expected_label,
                            minConfidence: t.minConfidence ?? t.min_confidence,

                            options: (typeof t.options === 'string' ? JSON.parse(t.options) : t.options)?.map((o: any) => ({
                                ...o,
                                text: o.text || o.labelText
                            }))
                        }))
                    };

                    setLesson(mappedLesson);
                    setUnitId(backendUnit.id);
                }
            } catch (error) {
                console.error('Failed to fetch lesson:', error);
            } finally {
                setIsLoading(false);
            }
        };

        fetchLesson();
    }, [lessonId]);

    const currentTask = lesson?.tasks[taskIndex];

    useEffect(() => {
        if (lesson) {
            setProgress((taskIndex / lesson.tasks.length) * 100);
        }
    }, [taskIndex, lesson]);

    const handleNextTask = () => {
        if (!lesson) return;
        setFeedback(null);
        setSelectedOption(null);
        if (taskIndex < lesson.tasks.length - 1) {
            setTaskIndex(taskIndex + 1);
        } else {
            setIsComplete(true);
            setProgress(100);
        }
    };

    const handleCheckAnswer = () => {
        if (!currentTask) return;

        if (feedback) {
            handleNextTask();
            return;
        }

        if (isCameraTaskType(currentTask.type)) {
            setShowCamera(true);
            return;
        }

        const result = evaluateSelectionTask(currentTask, selectedOption);
        if (result.isCorrect) {
            setFeedback('correct');
        } else {
            setFeedback('incorrect');
            setMistakes(m => m + 1);
        }
    };

    const handleCameraComplete = (success: boolean, score: number) => {
        setShowCamera(false);
        if (success) {
            setFeedback('correct');
        } else {
            setFeedback('incorrect');
            setMistakes(m => m + 1);
        }
    };

    const handleFinishLesson = async () => {
        if (!lesson) return;
        setIsSubmitting(true);
        try {
            const response = await api.user.completeLesson({
                lessonId: lesson.id,
                unitId: unitId,
                xpEarned: lesson.xp,
                tasksCompleted: lesson.tasks.length,
                totalTasks: lesson.tasks.length,
                mistakes
            });

            if (response.success && response.data) {
                onExit(response.data.user);
            } else {
                console.error("Failed to save lesson progress");
                const profile = await api.user.getProfile();
                if (profile.data) onExit(profile.data.user);
            }
        } catch (error) {
            console.error("Error completing lesson:", error);
            try {
                const profile = await api.user.getProfile();
                if (profile.data) onExit(profile.data.user);
            } catch (e) {
                console.error("Critical failure", e);
            }
        } finally {
            setIsSubmitting(false);
        }
    };

    const renderTask = (task: Task) => {
        const module = getTaskTypeModule(task.type);
        return module.render({
            task,
            selectedOption,
            feedback,
            onSelectOption: (optionId: string) => setSelectedOption(optionId)
        });
    };

    const getCorrectAnswerLabel = (task: Task) => {
        const correctOption = task.options?.find((o) => o.isCorrect);
        if (!correctOption) return 'N/A';
        if (correctOption.text) return correctOption.text;
        if (correctOption.videoUrl) return 'Varianta video corectă';
        return 'Răspuns corect';
    };

    if (isLoading) {
        return (
            <div className="flex-grow flex items-center justify-center bg-light-100">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
                    <p className="text-dark-300 font-medium animate-pulse">Se încarcă lecția...</p>
                </div>
            </div>
        );
    }

    if (!lesson || !currentTask) {
        return (
            <div className="flex-grow flex items-center justify-center bg-light-100">
                <div className="text-center p-8">
                    <Icon name="close" className="w-16 h-16 text-red-400 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-dark-100 mb-2">Eroare la încărcare</h3>
                    <p className="text-dark-300 mb-6">Nu am putut încărca lecția. Te rugăm să încerci din nou.</p>
                    <button onClick={() => onExit(null as any)} className="bg-primary text-white px-6 py-3 rounded-xl font-bold">
                        Înapoi la meniu
                    </button>
                </div>
            </div>
        );
    }

    if (isComplete) {
        return <LessonCompleteScreen xp={lesson.xp} onContinue={handleFinishLesson} isLoading={isSubmitting} />;
    }

    const isCheckDisabled = isCheckDisabledForTask(currentTask, selectedOption, feedback);

    return (
        <div className="flex flex-col min-h-[100dvh] bg-light-200 md:items-center overflow-hidden">
            {showCamera && (
                <CameraOverlay
                    prompt={currentTask.prompt}
                    expectedLabel={currentTask.expectedLabel}
                    minConfidence={currentTask.minConfidence}
                    onComplete={handleCameraComplete}
                    onClose={() => setShowCamera(false)}
                />
            )}

            <div className="w-full max-w-4xl flex flex-col flex-grow min-h-0 p-4 sm:p-6 relative z-10">
                <header className="flex items-center gap-3 sm:gap-6 mb-4 sm:mb-8">
                    <button onClick={() => onExit(null as any)} className="text-dark-300 hover:text-dark-100 transition-colors p-2 hover:bg-white rounded-full">
                        <Icon name="close" className="w-8 h-8" />
                    </button>
                    <ProgressBar progress={progress} />
                    <div className="flex items-center gap-2 font-bold text-accent-red bg-white px-3 py-1.5 rounded-full shadow-sm">
                        <Icon name="heart" className="w-5 h-5 fill-current" />
                        <span>{5 - mistakes}</span>
                    </div>
                </header>

                <main className="flex-grow min-h-0 flex flex-col justify-start md:justify-center overflow-y-auto">
                    {renderTask(currentTask)}
                </main>
            </div>

            <footer className={`w-full border-t-2 transition-colors duration-300 relative z-20
                ${feedback === 'correct' ? 'bg-accent-green/10 border-accent-green/20' : ''}
                ${feedback === 'incorrect' ? 'bg-accent-red/10 border-accent-red/20' : ''}
                ${!feedback ? 'bg-white border-light-300' : ''}
            `}>
                <MascotPatrol />
                <div className="max-w-4xl mx-auto p-4 sm:p-6 flex items-center justify-between">
                    {feedback ? (
                        <div className="flex items-center gap-4">
                            <div className={`w-14 h-14 rounded-full flex items-center justify-center ${feedback === 'correct' ? 'bg-accent-green text-white' : 'bg-accent-red text-white'}`}>
                                <Icon name={feedback === 'correct' ? 'check' : 'close'} className="w-8 h-8" />
                            </div>
                            <div>
                                <h3 className={`text-2xl font-black ${feedback === 'correct' ? 'text-accent-green' : 'text-accent-red'}`}>
                                    {feedback === 'correct' ? 'Excelent!' : 'Greșit...'}
                                </h3>
                                {feedback === 'incorrect' && <p className="text-dark-200 font-medium">Răspunsul corect era: <span className="font-bold">{getCorrectAnswerLabel(currentTask)}</span></p>}
                            </div>
                        </div>
                    ) : (
                        <div className="hidden md:block"></div> // Spacer
                    )}

                    <button
                        onClick={handleCheckAnswer}
                        disabled={isCheckDisabled}
                        className={`font-black py-3 sm:py-4 px-6 sm:px-10 rounded-2xl text-base sm:text-lg uppercase tracking-wide transition-all shadow-lg transform
                            ${isCheckDisabled ? 'bg-light-300 text-dark-300 cursor-not-allowed shadow-none' : 'hover:scale-105 active:scale-95'}
                            ${!isCheckDisabled && !feedback ? 'bg-primary text-white shadow-primary/30' : ''}
                            ${feedback === 'correct' ? 'bg-accent-green text-white shadow-accent-green/30' : ''}
                            ${feedback === 'incorrect' ? 'bg-accent-red text-white shadow-accent-red/30' : ''}
                            ml-auto w-full md:w-auto
                        `}
                    >
                        {feedback ? "Continuă" : "Verifică"}
                    </button>
                </div>
            </footer>
        </div>
    );
};
