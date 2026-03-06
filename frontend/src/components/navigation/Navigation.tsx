import React from 'react';
import { Screen, User, IconName } from '@/types';
import { Icon } from '@/components/ui/Icon';

interface NavItemProps {
    iconName: IconName;
    label: string;
    isActive: boolean;
    onClick: () => void;
}

const BottomNavItem: React.FC<NavItemProps> = ({ iconName, label, isActive, onClick }) => (
    <button onClick={onClick} className="flex flex-col items-center justify-center flex-1 h-full relative group">
        <div className={`p-1.5 rounded-xl transition-all duration-300 ${isActive ? 'bg-primary/10 -translate-y-1' : 'group-hover:bg-light-200'}`}>
            <Icon name={iconName} className={`w-6 h-6 transition-colors duration-300 ${isActive ? 'text-primary' : 'text-dark-300 group-hover:text-primary'}`} />
        </div>
        <span className={`text-[10px] font-bold mt-1 transition-colors duration-300 ${isActive ? 'text-primary' : 'text-dark-300 group-hover:text-primary'}`}>
            {label}
        </span>
        {isActive && <div className="absolute bottom-2 w-1 h-1 bg-primary rounded-full"></div>}
    </button>
);

interface NavigationProps {
    activeScreen: Screen;
    setScreen: (screen: Screen) => void;
    isCollapsed: boolean;
    onToggleCollapse: () => void;
    user: User | null;
}

export const Navigation: React.FC<NavigationProps> = ({ activeScreen, setScreen, isCollapsed, onToggleCollapse, user }) => {
    const navItems: { screen: Screen; iconName: IconName; label: string }[] = [
        { screen: Screen.Home, iconName: 'home', label: 'Acasă' },
        { screen: Screen.Learn, iconName: 'learn', label: 'Învață' },
        { screen: Screen.Achievements, iconName: 'achievements', label: 'Realizări' },
        { screen: Screen.Profile, iconName: 'profile', label: 'Profil' },
    ];

    if (user?.isAdmin) {
        navItems.push({ screen: Screen.Admin, iconName: 'lock', label: 'Admin' });
    }

    return (
        <>
            {/* Bottom Nav for Mobile */}
            <nav className="md:hidden fixed bottom-6 left-4 right-4 h-20 bg-white/90 backdrop-blur-lg border border-white/20 flex items-center px-2 z-50 rounded-3xl shadow-lifted">
                {navItems.map(item => (
                    <BottomNavItem
                        key={item.label}
                        iconName={item.iconName}
                        label={item.label}
                        isActive={activeScreen === item.screen}
                        onClick={() => setScreen(item.screen)}
                    />
                ))}
            </nav>
            {/* Side Nav for Tablet/Desktop */}
            <nav className={`hidden md:flex flex-col fixed top-0 left-0 h-full bg-white border-r border-light-300 p-4 space-y-2 z-50 transition-all duration-300 ${isCollapsed ? 'w-24' : 'w-72'}`}>
                <div className={`flex items-center gap-3 px-2 mb-8 ${isCollapsed ? 'justify-center' : ''}`}>
                    <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center shadow-lg shadow-primary/30 flex-shrink-0">
                        <span className="text-white font-black text-xl">R</span>
                    </div>
                    {!isCollapsed && <span className="text-2xl font-black text-dark-100 tracking-tight whitespace-nowrap">RSLlingo</span>}
                </div>

                <div className="space-y-2">
                    {navItems.map(item => (
                        <button
                            key={item.label}
                            onClick={() => setScreen(item.screen)}
                            className={`flex items-center w-full p-4 rounded-2xl transition-all duration-200 group relative overflow-hidden ${activeScreen === item.screen ? 'bg-primary/10 text-primary' : 'text-dark-200 hover:bg-light-200'} ${isCollapsed ? 'justify-center' : ''}`}
                            title={isCollapsed ? item.label : ''}
                        >
                            {activeScreen === item.screen && <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-primary rounded-r-full"></div>}
                            <Icon name={item.iconName} className={`w-6 h-6 transition-transform duration-300 ${activeScreen === item.screen ? 'scale-110' : 'group-hover:scale-110'} ${!isCollapsed ? 'mr-4' : ''}`} />
                            {!isCollapsed && <span className="font-bold text-md tracking-wide">{item.label}</span>}
                        </button>
                    ))}
                </div>

                <div className="mt-auto pt-6 border-t border-light-300 space-y-4">
                    {!isCollapsed && (
                        <div className="bg-gradient-to-br from-primary/10 to-accent-blue/10 p-4 rounded-2xl">
                            <p className="text-xs font-bold text-dark-300 uppercase mb-2">Sfatul zilei</p>
                            <p className="text-sm font-medium text-dark-200 italic">"Exersează în fața oglinzii pentru a-ți corecta postura."</p>
                        </div>
                    )}
                    <button
                        onClick={onToggleCollapse}
                        className="w-full p-2 flex items-center justify-center text-dark-300 hover:bg-light-200 rounded-xl transition-colors"
                        title={isCollapsed ? "Expand Menu" : "Collapse Menu"}
                    >
                        <Icon name={isCollapsed ? "menu" : "close"} className="w-5 h-5" />
                    </button>
                </div>
            </nav>
        </>
    );
};
