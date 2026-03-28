import React, { useState, useCallback, useEffect } from 'react';
import { Navigate, Route, Routes, useLocation, useNavigate, useParams } from 'react-router-dom';
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

const screenToPath = (screen: Screen): string => {
  switch (screen) {
    case Screen.Home:
      return '/home';
    case Screen.Learn:
      return '/learn';
    case Screen.Profile:
      return '/profile';
    case Screen.Achievements:
      return '/achievements';
    case Screen.Admin:
      return '/admin';
    case Screen.Auth:
      return '/auth/login';
    case Screen.Splash:
    default:
      return '/';
  }
};

const pathToScreen = (pathname: string): Screen => {
  if (pathname.startsWith('/auth/')) return Screen.Auth;
  if (pathname.startsWith('/learn/lesson/')) return Screen.Lesson;
  if (pathname === '/learn') return Screen.Learn;
  if (pathname === '/profile') return Screen.Profile;
  if (pathname === '/achievements') return Screen.Achievements;
  if (pathname === '/admin') return Screen.Admin;
  if (pathname === '/home') return Screen.Home;
  return Screen.Splash;
};

const LoadingScreen: React.FC = () => (
  <div className="min-h-screen flex items-center justify-center bg-light-200">
    <div className="flex flex-col items-center gap-4">
      <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
      <p className="text-dark-300 font-bold animate-pulse">Se încarcă...</p>
    </div>
  </div>
);

const LessonRoute: React.FC<{ onExit: (updatedUser: User) => void }> = ({ onExit }) => {
  const params = useParams<{ lessonId: string }>();
  const lessonId = params.lessonId;

  if (!lessonId) {
    return <Navigate to="/learn" replace />;
  }

  return <LessonScreen lessonId={lessonId} onExit={onExit} />;
};

const AppRoutes: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isMenuCollapsed, setIsMenuCollapsed] = useState(false);

  const currentScreen = pathToScreen(location.pathname);

  useEffect(() => {
    const checkSession = async () => {
      if (api.auth.isAuthenticated()) {
        try {
          const response = await api.user.getProfile();
          if (response.success && response.data) {
            setUser(response.data.user);
          } else {
            api.auth.logout();
          }
        } catch (error) {
          console.error('Session check failed:', error);
          api.auth.logout();
        }
      }
      setIsLoading(false);
    };

    checkSession();
  }, []);

  const navigateToScreen = useCallback((screen: Screen) => {
    navigate(screenToPath(screen));
  }, [navigate]);

  const handleSplashNavigate = useCallback((target: 'login' | 'signup') => {
    navigate(target === 'login' ? '/auth/login' : '/auth/signup');
  }, [navigate]);

  const handleAuthSuccess = useCallback((nextUser: User) => {
    setUser(nextUser);
    navigate('/home', { replace: true });
  }, [navigate]);

  const handleStartLesson = useCallback((lessonId: string) => {
    navigate(`/learn/lesson/${lessonId}`);
  }, [navigate]);

  const handleLogout = useCallback(() => {
    api.auth.logout();
    setUser(null);
    navigate('/', { replace: true });
  }, [navigate]);

  const handleCompleteLesson = useCallback((updatedUser: User) => {
    if (updatedUser) {
      setUser(updatedUser);
    }
    navigate('/learn', { replace: true });
  }, [navigate]);

  if (isLoading) {
    return <LoadingScreen />;
  }

  const showNav = !!user && currentScreen !== Screen.Lesson && currentScreen !== Screen.Splash && currentScreen !== Screen.Auth;

  return (
    <div className="font-sans bg-light-200 min-h-screen text-dark-200 selection:bg-primary/20 selection:text-primary-dark">
      {showNav && (
        <Navigation
          activeScreen={currentScreen}
          setScreen={navigateToScreen}
          isCollapsed={isMenuCollapsed}
          onToggleCollapse={() => setIsMenuCollapsed((value) => !value)}
          user={user}
        />
      )}

      <main className={`min-h-screen transition-all duration-300 ${showNav ? (isMenuCollapsed ? 'md:ml-24' : 'md:ml-72') : ''} ${showNav ? 'pb-32 md:pb-0' : ''}`}>
        {!user ? (
          <Routes>
            <Route path="/" element={<SplashScreen onNavigate={handleSplashNavigate} />} />
            <Route path="/auth/login" element={<AuthScreen key="login" initialMode="login" onAuthSuccess={handleAuthSuccess} />} />
            <Route path="/auth/signup" element={<AuthScreen key="signup" initialMode="signup" onAuthSuccess={handleAuthSuccess} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        ) : (
          <Routes>
            <Route path="/" element={<Navigate to="/home" replace />} />
            <Route path="/auth/*" element={<Navigate to="/home" replace />} />
            <Route
              path="/home"
              element={<HomeScreen user={user} onContinueLesson={() => navigate('/learn')} setScreen={navigateToScreen} />}
            />
            <Route path="/learn" element={<LearnScreen user={user} onStartLesson={handleStartLesson} />} />
            <Route path="/learn/lesson/:lessonId" element={<LessonRoute onExit={handleCompleteLesson} />} />
            <Route path="/profile" element={<ProfileScreen user={user} onLogout={handleLogout} onUserUpdate={setUser} />} />
            <Route path="/achievements" element={<AchievementsScreen user={user} />} />
            <Route
              path="/admin"
              element={user.isAdmin ? <AdminScreen user={user} onBack={() => navigate('/home')} /> : <Navigate to="/home" replace />}
            />
            <Route path="*" element={<Navigate to="/home" replace />} />
          </Routes>
        )}
      </main>
    </div>
  );
};

const App: React.FC = () => <AppRoutes />;

export default App;
