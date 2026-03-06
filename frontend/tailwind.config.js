/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                display: ['Nunito', 'sans-serif'],
            },
            colors: {
                'primary': {
                    DEFAULT: '#6C5CE7', // A more modern, vibrant purple
                    dark: '#5849BE',
                    light: '#A29BFE',
                    surface: '#F0F3FF',
                },
                'accent': {
                    orange: '#FF7675',
                    blue: '#74B9FF',
                    green: '#00B894',
                    red: '#FF7675', // Softened red
                    yellow: '#FDCB6E',
                },
                'light': {
                    100: '#FFFFFF',
                    200: '#F8F9FA', // Very subtle gray for backgrounds
                    300: '#E2E8F0', // Borders
                    400: '#CBD5E0',
                },
                'dark': {
                    100: '#2D3436', // Almost black
                    200: '#636E72', // Dark gray
                    300: '#B2BEC3', // Light gray text
                },
            },
            keyframes: {
                'progress-ring': {
                    '100%': { 'stroke-dashoffset': '0' }
                },
                'pop-in': {
                    '0%': { transform: 'scale(0.9)', opacity: '0' },
                    '100%': { transform: 'scale(1)', opacity: '1' }
                },
                'slide-up': {
                    '0%': { transform: 'translateY(20px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' }
                },
                'float': {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-5px)' }
                },
                'shimmer': {
                    '0%': { backgroundPosition: '-200% 0' },
                    '100%': { backgroundPosition: '200% 0' }
                }
            },
            animation: {
                'progress-ring': 'progress-ring 2s linear forwards',
                'pop-in': 'pop-in 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards',
                'slide-up': 'slide-up 0.5s ease-out forwards',
                'float': 'float 3s ease-in-out infinite',
                'shimmer': 'shimmer 2s infinite linear',
            },
            boxShadow: {
                'subtle': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
                'lifted': '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)',
                'glow': '0 0 15px rgba(108, 92, 231, 0.3)',
                'inner-light': 'inset 0 2px 4px 0 rgba(255, 255, 255, 0.3)',
            },
            backgroundImage: {
                'gradient-primary': 'linear-gradient(135deg, #6C5CE7 0%, #a29bfe 100%)',
                'gradient-surface': 'linear-gradient(180deg, #FFFFFF 0%, #F8F9FA 100%)',
            }
        },
    },
    plugins: [],
}
