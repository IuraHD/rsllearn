import React, { useState } from 'react';
import { User, IconName } from '@/types';
import { Icon } from '@/components/ui/Icon';
import { Mascot } from '@/components/ui/Mascot';
import { UserAvatar } from '@/components/ui/UserAvatar';
import { api } from '@/services/api';

interface ProfileScreenProps {
    user: User;
    onLogout: () => void;
    onUserUpdate: (updatedUser: User) => void;
}

const PageHeader: React.FC = () => (
    <div className="bg-primary pt-8 pb-20 text-light-100 relative overflow-hidden">
        <div className="absolute bottom-0 left-0 w-full leading-none">
            <svg className="relative block w-full h-[60px] md:h-[100px]" data-name="Layer 1" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 120" preserveAspectRatio="none">
                <path d="M321.39,56.44c58-10.79,114.16-30.13,172-41.86,82.39-16.72,168.19-17.73,250.45-.39C823.78,31,906.67,72,985.66,92.83c70.05,18.48,146.53,26.09,214.34,3V0H0V46.29C47,76.38,103.48,105.2,169.1,106.62,223.83,107.8,275.69,81.72,321.39,56.44Z" className="fill-primary-dark opacity-20"></path>
                <path d="M985.66,92.83C906.67,72,823.78,31,743.84,14.19c-82.26-17.34-168.06-16.33-250.45.39-57.84,11.73-114,31.07-172,41.86C275.69,81.72,223.83,107.8,169.1,106.62,103.48,105.2,47,76.38,0,46.29V120H1200V95.8C1132.19,118.92,1055.71,111.31,985.66,92.83Z" className="fill-light-200"></path>
            </svg>
        </div>
    </div>
);

const StatCard: React.FC<{ icon: IconName; value: number | string; label: string; }> = ({ icon, value, label }) => (
    <div className="flex items-center p-4 bg-light-100 rounded-xl shadow-subtle border border-light-300">
        <div className="bg-primary-light/20 p-2 rounded-lg mr-4">
            <Icon name={icon} className="w-7 h-7 text-primary" />
        </div>
        <div>
            <div className="text-xl font-black text-dark-100">{value}</div>
            <div className="text-sm font-bold text-dark-200">{label}</div>
        </div>
    </div>
);

export const ProfileScreen: React.FC<ProfileScreenProps> = ({ user, onLogout, onUserUpdate }) => {
    // Edit Profile State
    const [isEditingName, setIsEditingName] = useState(false);
    const [tempName, setTempName] = useState(user.displayName);

    const handleSaveName = async () => {
        if (!tempName.trim()) return;
        try {
            const response = await api.user.updateProfile(tempName.trim());
            if (response.success && response.data?.user) {
                onUserUpdate(response.data.user);
                setTempName(response.data.user.displayName);
            }
            setIsEditingName(false);
        } catch (error) {
            console.error('Failed to update name:', error);
            alert('Nu am putut actualiza numele.');
        }
    };

    return (
        <div className="bg-light-200 min-h-screen">
            <PageHeader />
            <div className="p-4 md:p-6 -mt-24 space-y-6 animate-pop-in max-w-4xl mx-auto">
                <header className="text-center">
                    <div className="w-28 h-28 rounded-full border-8 border-light-200 shadow-lifted mx-auto mb-3 overflow-hidden">
                        <UserAvatar
                            name={user.displayName}
                            className="w-full h-full"
                            textClassName="text-5xl"
                        />
                    </div>
                    {isEditingName ? (
                        <div className="flex items-center justify-center gap-2 mb-1">
                            <input
                                type="text"
                                value={tempName}
                                onChange={(e) => setTempName(e.target.value)}
                                className="text-xl font-bold text-center border-b-2 border-primary focus:outline-none bg-transparent w-48"
                                autoFocus
                            />
                            <button onClick={handleSaveName} className="p-1 text-green-600 hover:bg-green-50 rounded-full">
                                <Icon name="check" className="w-6 h-6" />
                            </button>
                            <button onClick={() => setIsEditingName(false)} className="p-1 text-red-500 hover:bg-red-50 rounded-full">
                                <Icon name="close" className="w-6 h-6" />
                            </button>
                        </div>
                    ) : (
                        <div className="flex items-center justify-center gap-2 mb-1 group">
                            <h1 className="text-2xl font-black text-dark-100">{user.displayName}</h1>
                            <button onClick={() => { setTempName(user.displayName); setIsEditingName(true); }} className="opacity-0 group-hover:opacity-100 transition-opacity text-dark-300 hover:text-primary">
                                <Icon name="edit" className="w-5 h-5" />
                            </button>
                        </div>
                    )}
                    <p className="text-md font-semibold text-dark-200">{user.email}</p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                        <h2 className="text-lg font-bold text-dark-100 px-1">Statistici</h2>
                        <StatCard icon="xp" value={user.xp.toLocaleString()} label="XP Total" />
                        <StatCard icon="streak" value={user.dailyStreak} label="Serie Zile" />
                        <StatCard icon="book" value={`${user.levelProgress}%`} label={`Progres Nivel ${user.level}`} />
                    </div>

                    <div className="space-y-3">
                        <button
                            onClick={onLogout}
                            className="w-full flex items-center justify-center gap-3 bg-light-100 text-accent-red font-bold py-3 px-6 rounded-xl text-lg border-2 border-light-300 transition-colors hover:bg-accent-red/10"
                        >
                            <Icon name="logout" className="w-6 h-6" />
                            <span>Deconectare</span>
                        </button>
                    </div>
                </div>
            </div>


        </div>
    );
};
