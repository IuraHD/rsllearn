import React from 'react';
import { Mascot } from '@/components/ui/Mascot';

interface SplashScreenProps {
  onNavigate: (target: 'login' | 'signup') => void;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onNavigate }) => {
  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-primary-dark via-primary to-accent overflow-hidden relative">
      {/* Decorative Blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-secondary/30 rounded-full blur-3xl animate-pulse-slow"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-accent/30 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }}></div>

      <div className="flex-grow flex flex-col items-center justify-center z-10 p-6 text-center">
        <div className="mb-8 animate-bounce-slight">
          <Mascot pose="wave" className="w-64 h-64 drop-shadow-glow" />
        </div>

        <h1 className="text-6xl font-display font-black text-white mb-4 drop-shadow-md tracking-tight">
          RSLlingo
        </h1>
        <p className="text-xl font-medium text-white/90 max-w-sm mx-auto font-sans leading-relaxed">
          Învață Limba Semnelor Române,<br />un semn pe rând.
        </p>
      </div>

      <div className="space-y-4 z-10 w-full max-w-md mx-auto mb-12 px-6">
        <button
          onClick={() => onNavigate('signup')}
          className="w-full bg-white text-primary-dark font-display font-bold py-4 px-6 rounded-2xl text-lg shadow-card hover:shadow-glow hover:-translate-y-1 transition-all duration-300 transform"
        >
          Să începem
        </button>
        <button
          onClick={() => onNavigate('login')}
          className="w-full bg-white/10 backdrop-blur-md text-white font-display font-bold py-4 px-6 rounded-2xl text-lg border-2 border-white/20 hover:bg-white/20 hover:border-white/40 transition-all duration-300"
        >
          Am deja un cont
        </button>
      </div>
    </div>
  );
};