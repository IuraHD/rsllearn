import React, { useState } from 'react';
import { api } from '@/services/api';
import { User } from '@/types';
import { Icon } from '@/components/ui/Icon';

type AuthMode = 'signup' | 'login';

interface AuthScreenProps {
  initialMode: AuthMode;
  onAuthSuccess: (user: User) => void;
}

export const AuthScreen: React.FC<AuthScreenProps> = ({ initialMode, onAuthSuccess }) => {
  const [mode, setMode] = useState<AuthMode>(initialMode);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      if (mode === 'signup') {
        if (!name) {
          setError("Te rog introdu un nume.");
          setIsLoading(false);
          return;
        }
        const response = await api.auth.register(name, email, password);
        if (response.success && response.data) {
          onAuthSuccess(response.data);
        }
      } else {
        const response = await api.auth.login(email, password);
        if (response.success && response.data) {
          onAuthSuccess(response.data);
        }
      }
    } catch (err: any) {
      setError(err.message || "A apărut o eroare. Te rog încearcă din nou.");
    } finally {
      setIsLoading(false);
    }
  };

  const isSignup = mode === 'signup';

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-dark via-primary to-accent flex flex-col justify-center items-center p-4 relative overflow-hidden">
      {/* Background Decor */}
      <div className="absolute top-[-10%] left-[-10%] w-96 h-96 bg-secondary/20 rounded-full blur-3xl animate-pulse-slow"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-accent/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }}></div>

      <div className="w-full max-w-md z-10">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-display font-black text-white mb-2 drop-shadow-md">
            {isSignup ? 'Creează un Cont' : 'Bine ai revenit!'}
          </h1>
          <p className="text-white/80 font-medium font-sans text-lg">
            {isSignup ? 'Începe aventura ta în lumea semnelor.' : 'Continuă de unde ai rămas.'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white/95 backdrop-blur-xl p-8 rounded-3xl shadow-card border border-white/50 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-secondary via-primary to-accent"></div>

          {error && (
            <div className="bg-red-50 text-red-500 p-4 rounded-xl text-sm font-bold flex items-center gap-3 mb-6 border border-red-100 animate-bounce-slight">
              <Icon name="close" className="w-5 h-5 flex-shrink-0" />
              {error}
            </div>
          )}

          {isSignup && (
            <div className="mb-5">
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 ml-1">Nume</label>
              <input
                type="text"
                placeholder="Cum te numeşti?"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full p-4 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all font-sans font-medium"
                required
                disabled={isLoading}
              />
            </div>
          )}
          <div className="mb-5">
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 ml-1">Email</label>
            <input
              type="email"
              placeholder="adresa@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full p-4 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all font-sans font-medium"
              required
              disabled={isLoading}
            />
          </div>
          <div className="mb-8">
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-2 ml-1">Parolă</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full p-4 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all font-sans font-medium"
              required
              disabled={isLoading}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className={`w-full bg-gradient-to-r from-primary to-primary-dark text-white font-display font-bold py-4 px-6 rounded-xl shadow-lg hover:shadow-glow hover:-translate-y-0.5 transition-all duration-300 ${isLoading ? 'opacity-70 cursor-not-allowed' : ''}`}
          >
            {isLoading ? (
              <div className="flex items-center justify-center gap-2">
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Se procesează...</span>
              </div>
            ) : (isSignup ? 'Creează Cont' : 'Intră în Cont')}
          </button>

          <div className="flex items-center my-8">
            <div className="flex-grow border-t border-gray-200"></div>
            <span className="flex-shrink mx-4 text-gray-400 text-xs font-bold uppercase tracking-widest">sau</span>
            <div className="flex-grow border-t border-gray-200"></div>
          </div>

          <button
            type="button"
            disabled={isLoading}
            onClick={() => alert("Google Auth not implemented in this demo")}
            className="w-full bg-white text-gray-700 font-bold py-3.5 px-6 rounded-xl border border-gray-200 flex items-center justify-center gap-3 hover:bg-gray-50 hover:border-gray-300 transition-all shadow-sm"
          >
            <svg className="w-5 h-5" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8c-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039L38.802 9.92C34.553 6.08 29.613 4 24 4C12.955 4 4 12.955 4 24s8.955 20 20 20s20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z"></path><path fill="#FF3D00" d="m6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.841-5.841C34.553 6.08 29.613 4 24 4C16.318 4 9.656 8.337 6.306 14.691z"></path><path fill="#4CAF50" d="m24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238A11.91 11.91 0 0 1 24 36c-5.222 0-9.618-3.6-11.283-8.393l-6.522 5.025C9.505 39.556 16.227 44 24 44z"></path><path fill="#1976D2" d="M43.611 20.083H42V20H24v8h11.303c-.792 2.237-2.231 4.166-4.087 5.571l6.19 5.238C41.382 36.141 44 30.638 44 24c0-1.341-.138-2.65-.389-3.917z"></path></svg>
            Continuă cu Google
          </button>
        </form>

        <p className="text-center mt-8 text-white/80 font-medium">
          {isSignup ? 'Ai deja cont?' : 'Nu ai cont?'}
          <button onClick={() => { setMode(isSignup ? 'login' : 'signup'); setError(null); }} className="font-bold text-white ml-2 hover:underline drop-shadow-sm">
            {isSignup ? 'Intră în cont' : 'Înregistrează-te'}
          </button>
        </p>
      </div>
    </div>
  );
};