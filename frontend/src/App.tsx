import React, { useState, useCallback, useEffect } from 'react';
import { Screen, User } from '@/types';
import { HomeScreen } from '@/screens/app/HomeScreen';
import { LearnScreen } from '@/screens/app/LearnScreen';
import { LessonScreen } from '@/screens/app/LessonScreen';
import { SplashScreen } from '@/screens/auth/SplashScreen';
import { AuthScreen } from '@/screens/auth/AuthScreen';
import { ProfileScreen } from '@/screens/app/ProfileScreen';
import { AchievementsScreen } from '@/screens/app/AchievementsScreen';
import { AdminScreen } from '@/screens/admin/AdminScreen';
import { Navigation } from '@/components/navigation/Navigation';
import { api } from '@/services/api';

const App: React.FC = () => {
    const [currentScreen, setCurrentScreen] = useState<Screen>(Screen.Splash);
    const [authMode, setAuthMode] = useState<'login' | 'signup'>('signup');
    const [user, setUser] = useState<User | null>(null);
    const [activeLessonId, setActiveLessonId] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isMenuCollapsed, setIsMenuCollapsed] = useState(false); // Lifted state for layout adjustment

    // Check for existing session on mount
    useEffect(() => {
        const checkSession = async () => {
            if (api.auth.isAuthenticated()) {
                try {
                    const response = await api.user.getProfile();
                    if (response.success && response.data) {
                        setUser(response.data.user);
                        setCurrentScreen(Screen.Home);
                    } else {
                        api.auth.logout();
                    }
                } catch (error) {
                    console.error("Session check failed:", error);
                    api.auth.logout();
                }
            }
            setIsLoading(false);
        };
        checkSession();
    }, []);

    const handleSplashNavigate = useCallback((target: 'login' | 'signup') => {
        setAuthMode(target);
        setCurrentScreen(Screen.Auth);
    }, []);

    const handleAuthSuccess = useCallback((user: User) => {
        setUser(user);
        setCurrentScreen(Screen.Home);
    }, []);



    const handleStartLesson = useCallback((lessonId: string) => {
        setActiveLessonId(lessonId);
        setCurrentScreen(Screen.Lesson);
    }, []);

    const handleLogout = useCallback(() => {
        api.auth.logout();
        setUser(null);
        setCurrentScreen(Screen.Splash);
    }, []);

    const handleCompleteLesson = useCallback((updatedUser: User) => {
        if (updatedUser) {
            setUser(updatedUser);
        }
        setCurrentScreen(Screen.Learn);
        setActiveLessonId(null);
    }, []);

    const renderScreen = () => {
        if (isLoading) {
            return (
                <div className="min-h-screen flex items-center justify-center bg-light-200">
                    <div className="flex flex-col items-center gap-4">
                        <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
                        <p className="text-dark-300 font-bold animate-pulse">Se încarcă...</p>
                    </div>
                </div>
            );
        }

        if (!user) {
            switch (currentScreen) {
                case Screen.Splash:
                    return <SplashScreen onNavigate={handleSplashNavigate} />;
                case Screen.Auth:
                    return <AuthScreen initialMode={authMode} onAuthSuccess={handleAuthSuccess} />;
                default:
                    return <SplashScreen onNavigate={handleSplashNavigate} />;
            }
        }

        switch (currentScreen) {
            case Screen.Home:
                return <HomeScreen user={user} onContinueLesson={() => setCurrentScreen(Screen.Learn)} setScreen={setCurrentScreen} />;
            case Screen.Learn:
                return <LearnScreen user={user} onStartLesson={handleStartLesson} />;
            case Screen.Profile:
                return <ProfileScreen user={user} onLogout={handleLogout} onUserUpdate={setUser} />;
            case Screen.Achievements:
                return <AchievementsScreen user={user} />;
            case Screen.Admin:
                return (user?.isAdmin)
                    ? <AdminScreen user={user} onBack={() => setCurrentScreen(Screen.Home)} />
                    : <HomeScreen user={user} onContinueLesson={() => setCurrentScreen(Screen.Learn)} setScreen={setCurrentScreen} />;
            case Screen.Lesson:
                return activeLessonId ? <LessonScreen lessonId={activeLessonId} onExit={handleCompleteLesson} /> : <LearnScreen user={user} onStartLesson={handleStartLesson} />;
            default:
                return <HomeScreen user={user} onContinueLesson={() => setCurrentScreen(Screen.Learn)} setScreen={setCurrentScreen} />;
        }
    };

    const showNav = user && currentScreen !== Screen.Lesson && currentScreen !== Screen.Splash && currentScreen !== Screen.Auth;

    return (
        <div className="font-sans bg-light-200 min-h-screen text-dark-200 selection:bg-primary/20 selection:text-primary-dark">
            {showNav && (
                <Navigation
                    activeScreen={currentScreen}
                    setScreen={setCurrentScreen}
                    isCollapsed={isMenuCollapsed}
                    onToggleCollapse={() => setIsMenuCollapsed(!isMenuCollapsed)}
                    user={user}
                />
            )}
            <main className={`min-h-screen transition-all duration-300 ${showNav ? (isMenuCollapsed ? 'md:ml-24' : 'md:ml-72') : ''} ${showNav ? "pb-32 md:pb-0" : ""}`}>
                {renderScreen()}
            </main>
        </div>
    );
};



export default App;
