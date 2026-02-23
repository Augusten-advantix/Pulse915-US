/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        colors: {
            transparent: 'transparent',
            current: 'currentColor',
            white: '#ffffff',
            black: '#000000',
            slate: {
                50: '#f8fafc',
                100: '#f1f5f9',
                200: '#e2e8f0',
                300: '#cbd5e1',
                400: '#94a3b8',
                500: '#64748b',
                600: '#475569',
                700: '#334155',
                800: '#1e293b',
                900: '#0f172a',
                950: '#020617',
            },
            emerald: {
                400: '#34d399',
                500: '#10b981',
                600: '#059669',
            },
            rose: {
                400: '#fb7185',
            },
            amber: {
                400: '#fbbf24',
            },
            blue: {
                400: '#60a5fa',
                500: '#3b82f6',
            },
            red: {
                500: '#ef4444',
            },
            cyan: {
                500: '#06b6d4',
            },
            purple: {
                500: '#a855f7',
            },
            pink: {
                500: '#ec4899',
            },
            indigo: {
                500: '#6366f1',
            },
            gradient: {
                'cyan-blue': 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
                'blue-indigo': 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)',
                'indigo-purple': 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
                'purple-pink': 'linear-gradient(135deg, #a855f7 0%, #ec4899 100%)',
            },
        },
        extend: {
            spacing: {
                xs: '0.25rem',
                sm: '0.5rem',
                md: '1rem',
                lg: '1.5rem',
                xl: '2rem',
                '2xl': '3rem',
            },
            borderRadius: {
                sm: '0.375rem',
                md: '0.5rem',
                lg: '0.75rem',
                xl: '1rem',
            },
            fontSize: {
                xs: ['0.75rem', { lineHeight: '1rem' }],
                sm: ['0.875rem', { lineHeight: '1.25rem' }],
                base: ['1rem', { lineHeight: '1.5rem' }],
                lg: ['1.125rem', { lineHeight: '1.75rem' }],
                xl: ['1.25rem', { lineHeight: '1.75rem' }],
                '2xl': ['1.5rem', { lineHeight: '2rem' }],
                '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
                '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
            },
            backdropBlur: {
                sm: '4px',
                md: '12px',
            },
            animation: {
                spin: 'spin 0.8s cubic-bezier(0.4, 0, 0.2, 1) infinite',
                pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            },
            keyframes: {
                spin: {
                    to: { transform: 'rotate(360deg)' },
                },
                pulse: {
                    '0%, 100%': { opacity: '1' },
                    '50%': { opacity: '0.5' },
                },
            },
        },
    },
    plugins: [],
}
