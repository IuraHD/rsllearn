import React from 'react';

type Pose = 'wave' | 'celebrate' | 'learning' | 'default' | 'wink' | 'sad' | 'walking';

interface MascotProps {
  pose?: Pose;
  className?: string;
}

export const Mascot: React.FC<MascotProps> = ({ pose = 'default', className }) => {
  // Common colors
  const colors = {
    fur: '#FFFFFF',
    furShadow: '#E2E8F0',
    furDark: '#CBD5E0',
    outline: '#2D3748',
    eyes: '#2D3748',
    nose: '#FF7675',
    cheeks: '#FAB1A0',
    scarf: '#6C5CE7',
    scarfShadow: '#5849BE',
    innerEar: '#FFD1D1'
  };

  // Animation styles
  const animations = `
    @keyframes blink {
      0%, 90%, 100% { transform: scaleY(1); }
      95% { transform: scaleY(0.1); }
    }
    @keyframes tailWag {
      0%, 100% { transform: rotate(0deg); }
      50% { transform: rotate(10deg); }
    }
    @keyframes wave {
      0%, 100% { transform: rotate(0deg); }
      50% { transform: rotate(-20deg); }
    }
    @keyframes float {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-5px); }
    }
    @keyframes walk {
      0% { transform: rotate(-20deg); }
      50% { transform: rotate(20deg); }
      100% { transform: rotate(-20deg); }
    }
    .eye-blink { transform-origin: center; animation: blink 4s infinite; }
    .tail-wag { transform-origin: bottom left; animation: tailWag 2s ease-in-out infinite; }
    .paw-wave { transform-origin: bottom right; animation: wave 1s ease-in-out infinite; }
    .body-float { animation: float 3s ease-in-out infinite; }
    .leg-walk-a { animation: walk 1s ease-in-out infinite; }
    .leg-walk-b { animation: walk 1s ease-in-out infinite; animation-delay: -0.5s; }
  `;

  const renderWalkingLegs = (layer: 'far' | 'near') => {
    if (pose !== 'walking') return null;

    const legStyle = {
      strokeLinecap: 'round' as const,
      strokeLinejoin: 'round' as const,
    };

    if (layer === 'far') {
      return (
        <g>
           {/* Far Back Leg (Pair A) */}
           <g className="leg-walk-a" style={{ transformOrigin: '50px 175px' }}>
             <path d="M50 175 L 50 215" stroke={colors.furDark} strokeWidth="12" {...legStyle} />
           </g>
           {/* Far Front Leg (Pair B) */}
           <g className="leg-walk-b" style={{ transformOrigin: '130px 175px' }}>
             <path d="M130 175 L 130 215" stroke={colors.furDark} strokeWidth="12" {...legStyle} />
           </g>
        </g>
      );
    }

    if (layer === 'near') {
      return (
        <g>
           {/* Near Back Leg (Pair B) */}
           <g className="leg-walk-b" style={{ transformOrigin: '50px 175px' }}>
             <path d="M50 175 L 50 215" stroke={colors.outline} strokeWidth="14" {...legStyle} />
             <path d="M50 175 L 50 215" stroke={colors.fur} strokeWidth="10" {...legStyle} />
           </g>
           {/* Near Front Leg (Pair A) */}
           <g className="leg-walk-a" style={{ transformOrigin: '130px 175px' }}>
             <path d="M130 175 L 130 215" stroke={colors.outline} strokeWidth="14" {...legStyle} />
             <path d="M130 175 L 130 215" stroke={colors.fur} strokeWidth="10" {...legStyle} />
           </g>
        </g>
      );
    }
  };

  const renderBody = () => {
    if (pose === 'walking') {
      return (
        <g>
          {/* Tail - Extended and curved up */}
          <path d="M25 155 C 5 145, 0 100, 35 80" fill="none" stroke={colors.outline} strokeWidth="10" strokeLinecap="round" className="tail-wag" />
          {/* Body */}
          <ellipse cx="90" cy="155" rx="75" ry="50" fill={colors.fur} stroke={colors.outline} strokeWidth="4" />
          {/* Scarf */}
          <path d="M115 135 Q 135 155, 145 135 L 145 145 Q 135 165, 115 145 Z" fill={colors.scarf} stroke={colors.outline} strokeWidth="3" />
          <path d="M125 145 L 120 175 L 135 170 L 135 145" fill={colors.scarf} stroke={colors.outline} strokeWidth="3" />
        </g>
      );
    }

    return (
    <g className={pose === 'celebrate' ? 'body-float' : ''}>
      {/* Tail */}
      <path
        d="M130 160 Q 160 160, 160 130 Q 160 100, 130 110"
        fill="none"
        stroke={colors.outline}
        strokeWidth="12"
        strokeLinecap="round"
        className="tail-wag"
      />

      {/* Main Body */}
      <ellipse cx="100" cy="140" rx="60" ry="55" fill={colors.fur} stroke={colors.outline} strokeWidth="4" />

      {/* Body Shadow/Highlight */}
      <ellipse cx="100" cy="140" rx="50" ry="45" fill="none" stroke={colors.furShadow} strokeWidth="2" opacity="0.5" />

      {/* Scarf */}
      <path d="M60 160 Q 100 190, 140 160 L 140 170 Q 100 200, 60 170 Z" fill={colors.scarf} stroke={colors.outline} strokeWidth="3" />
      <path d="M110 170 L 120 200 L 135 195 L 130 165" fill={colors.scarf} stroke={colors.outline} strokeWidth="3" />
    </g>
    );
  };

  const renderHead = () => (
    <g className={pose === 'celebrate' ? 'body-float' : ''}>
      {/* Ears */}
      <path d="M55 60 L 35 20 L 85 40 Z" fill={colors.fur} stroke={colors.outline} strokeWidth="4" strokeLinejoin="round" />
      <path d="M145 60 L 165 20 L 115 40 Z" fill={colors.fur} stroke={colors.outline} strokeWidth="4" strokeLinejoin="round" />

      {/* Inner Ears */}
      <path d="M58 55 L 45 30 L 75 45 Z" fill={colors.innerEar} />
      <path d="M142 55 L 155 30 L 125 45 Z" fill={colors.innerEar} />

      {/* Head Shape */}
      <ellipse cx="100" cy="90" rx="70" ry="60" fill={colors.fur} stroke={colors.outline} strokeWidth="4" />

      {/* Cheeks */}
      <circle cx="55" cy="105" r="8" fill={colors.cheeks} opacity="0.6" />
      <circle cx="145" cy="105" r="8" fill={colors.cheeks} opacity="0.6" />
    </g>
  );

  const renderFace = () => {
    const eyeBase = (
      <g>
        <ellipse cx="70" cy="90" rx="8" ry="10" fill={colors.eyes} className={pose !== 'wink' ? 'eye-blink' : ''} />
        <circle cx="73" cy="86" r="3" fill="white" className={pose !== 'wink' ? 'eye-blink' : ''} />
      </g>
    );

    const rightEye = pose === 'wink' ? (
      <path d="M120 90 Q 130 95, 140 90" fill="none" stroke={colors.eyes} strokeWidth="4" strokeLinecap="round" />
    ) : (
      <g>
        <ellipse cx="130" cy="90" rx="8" ry="10" fill={colors.eyes} className="eye-blink" />
        <circle cx="133" cy="86" r="3" fill="white" className="eye-blink" />
      </g>
    );

    const mouth = pose === 'sad'
      ? <path d="M90 120 Q 100 110, 110 120" fill="none" stroke={colors.outline} strokeWidth="3" strokeLinecap="round" />
      : <path d="M90 115 Q 100 125, 110 115" fill="none" stroke={colors.outline} strokeWidth="3" strokeLinecap="round" />;

    return (
      <g className={pose === 'celebrate' ? 'body-float' : ''}>
        {eyeBase}
        {rightEye}

        {/* Nose */}
        <path d="M95 105 L 105 105 L 100 112 Z" fill={colors.nose} />

        {/* Mouth */}
        {mouth}
        <path d="M100 112 L 100 115" fill="none" stroke={colors.outline} strokeWidth="2" />

        {/* Whiskers */}
        <g stroke={colors.outline} strokeWidth="2" opacity="0.4">
          <path d="M40 95 L 20 90" />
          <path d="M40 105 L 20 110" />
          <path d="M160 95 L 180 90" />
          <path d="M160 105 L 180 110" />
        </g>
      </g>
    );
  };

  const renderPaws = () => {
    if (pose === 'walking') {
      return null;
    }

    if (pose === 'wave') {
      return (
        <g>
          {/* Left Paw (Down) */}
          <ellipse cx="70" cy="180" rx="15" ry="12" fill={colors.fur} stroke={colors.outline} strokeWidth="3" />
          {/* Right Paw (Waving) */}
          <g className="paw-wave" style={{ transformBox: 'fill-box' }}>
            <ellipse cx="150" cy="120" rx="15" ry="12" fill={colors.fur} stroke={colors.outline} strokeWidth="3" />
            <path d="M150 132 L 150 160" fill="none" stroke={colors.outline} strokeWidth="3" />
          </g>
        </g>
      );
    }

    if (pose === 'celebrate') {
      return (
        <g className="body-float">
          {/* Both Paws Up */}
          <ellipse cx="50" cy="120" rx="15" ry="12" fill={colors.fur} stroke={colors.outline} strokeWidth="3" transform="rotate(-20 50 120)" />
          <ellipse cx="150" cy="120" rx="15" ry="12" fill={colors.fur} stroke={colors.outline} strokeWidth="3" transform="rotate(20 150 120)" />
        </g>
      );
    }

    // Default sitting paws
    return (
      <g>
        <ellipse cx="80" cy="185" rx="15" ry="12" fill={colors.fur} stroke={colors.outline} strokeWidth="3" />
        <ellipse cx="120" cy="185" rx="15" ry="12" fill={colors.fur} stroke={colors.outline} strokeWidth="3" />
      </g>
    );
  };

  const renderAccessories = () => {
    if (pose === 'learning' || pose === 'walking') {
      return (
        <g>
          {/* Glasses */}
          <circle cx="70" cy="90" r="14" fill="none" stroke={colors.outline} strokeWidth="2" />
          <circle cx="130" cy="90" r="14" fill="none" stroke={colors.outline} strokeWidth="2" />
          <path d="M84 90 L 116 90" fill="none" stroke={colors.outline} strokeWidth="2" />
        </g>
      );
    }
    return null;
  };

  return (
    <svg viewBox="0 0 200 220" className={className} xmlns="http://www.w3.org/2000/svg">
      <style>{animations}</style>
      {renderWalkingLegs('far')}
      {renderBody()}
      <g transform={pose === 'walking' ? "translate(30, -10)" : ""}>
        {renderHead()}
        {renderFace()}
        {renderAccessories()}
      </g>
      {renderPaws()}
      {renderWalkingLegs('near')}
    </svg>
  );
};
