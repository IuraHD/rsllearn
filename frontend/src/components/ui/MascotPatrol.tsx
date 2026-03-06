
import React, { useState, useEffect } from 'react';
import { Mascot } from './Mascot';

export const MascotPatrol: React.FC = () => {
    const [step, setStep] = useState(0);
    // 0: Sit Left
    // 1: Walk Right
    // 2: Sit Right
    // 3: Turn Left
    // 4: Walk Left
    // 5: Turn Right

    useEffect(() => {
        let timer: ReturnType<typeof setTimeout>;

        // Random sit duration between 5000ms and 15000ms
        const getSitDuration = () => Math.floor(Math.random() * 10000) + 5000;
        const walkDuration = 8000;

        switch (step) {
            case 0: // Sit Left
                timer = setTimeout(() => setStep(1), getSitDuration());
                break;
            case 1: // Walk Right
                timer = setTimeout(() => setStep(2), walkDuration);
                break;
            case 2: // Sit Right
                timer = setTimeout(() => setStep(3), getSitDuration());
                break;
            case 3: // Turn Left
                timer = setTimeout(() => setStep(4), 50);
                break;
            case 4: // Walk Left
                timer = setTimeout(() => setStep(5), walkDuration);
                break;
            case 5: // Turn Right
                timer = setTimeout(() => setStep(0), 50);
                break;
        }
        return () => clearTimeout(timer);
    }, [step]);

    const getStyle = () => {
        const baseStyle: React.CSSProperties = {
            height: '100px',
            position: 'absolute',
            bottom: 0,
            width: '100px',
            zIndex: 10
        };
        const transition = 'transform 8s linear';

        switch (step) {
            case 0: return { ...baseStyle, transform: 'translateX(10vw) scaleX(1)' };
            case 1: return { ...baseStyle, transform: 'translateX(80vw) scaleX(1)', transition };
            case 2: return { ...baseStyle, transform: 'translateX(80vw) scaleX(1)' };
            case 3: return { ...baseStyle, transform: 'translateX(80vw) scaleX(-1)' };
            case 4: return { ...baseStyle, transform: 'translateX(10vw) scaleX(-1)', transition };
            case 5: return { ...baseStyle, transform: 'translateX(10vw) scaleX(1)' };
            default: return baseStyle;
        }
    };

    const isWalking = step === 1 || step === 4;

    return (
        <div className="absolute top-0 left-0 w-full pointer-events-none overflow-hidden" style={{ height: '100px', transform: 'translateY(-100%)' }}>
            <div style={getStyle()} className="relative">
                {isWalking ? (
                    <div className="absolute inset-0">
                        <div className="animate-mascot-walk-cycle w-full h-full">
                            <Mascot pose="walking" className="w-full h-full" />
                        </div>
                    </div>
                ) : (
                    <div className="absolute inset-0 animate-mascot-sit-down origin-bottom">
                        <div className="w-full h-full translate-y-2">
                            <Mascot pose="learning" className="w-full h-full" />
                        </div>
                    </div>
                )}
            </div>
            <style>{`
                @keyframes mascot-walk-cycle {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-3px); }
                }
                @keyframes mascot-sit-down {
                    0% { transform: scaleY(1.1) translateY(-5px); }
                    100% { transform: scaleY(1) translateY(0); }
                }
                .animate-mascot-walk-cycle {
                    animation: mascot-walk-cycle 0.4s ease-in-out infinite;
                }
                .animate-mascot-sit-down {
                    animation: mascot-sit-down 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
                }
            `}</style>
        </div>
    );
};
