/**
 * Nebue - Tailwind Configuration
 * Paleta de cores douradas para gestão financeira premium
 */

module.exports = {
    content: [
        /**
         * HTML. Paths to Django template files that will contain Tailwind CSS classes.
         */

        /*  Templates within theme app (<tailwind_app_name>/templates), e.g. base.html. */
        '../templates/**/*.html',

        /*
         * Main templates directory of the project (BASE_DIR/templates).
         * Adjust the following line to match your project structure.
         */
        '../../templates/**/*.html',

        /*
         * Templates in other django apps (BASE_DIR/<any_app_name>/templates).
         * Adjust the following line to match your project structure.
         */
        '../../**/templates/**/*.html',

        /**
         * JS: If you use Tailwind CSS in JavaScript, uncomment the following lines and make sure
         * patterns match your project structure.
         */
        /* JS 1: Ignore any JavaScript in node_modules folder. */
        // '!../../**/node_modules',
        /* JS 2: Process all JavaScript files in the project. */
        // '../../**/*.js',

        /**
         * Python: If you use Tailwind CSS classes in Python, uncomment the following line
         * and make sure the pattern below matches your project structure.
         */
        // '../../**/*.py'
    ],
    theme: {
        extend: {
            // 🟡 CORES DOURADAS NEBUE
            colors: {
                // Cores Primárias (Dourado)
                'primary': {
                    50: '#FFFBF0',
                    100: '#FFF5DC',
                    200: '#FFEAB8',
                    300: '#FFE094',
                    400: '#F4E4BC',
                    500: '#D4AF37',  // Dourado Principal
                    600: '#B8941E',  // Dourado Escuro
                    700: '#A67C00',  // Dourado Profundo
                    800: '#8A6600',
                    900: '#6E5200',
                },
                
                // Cores de Accent (Dourado Claro)
                'accent': {
                    50: '#FFFEF9',
                    100: '#FFFCF0',
                    200: '#FFF9E0',
                    300: '#FFF5D1',
                    400: '#FFF0C2',
                    500: '#F4E4BC',  // Dourado Claro
                    600: '#E6C75A',  // Dourado Médio
                    700: '#C5A028',
                    800: '#A38320',
                    900: '#826818',
                },

                // Fundos Escuros (manter)
                'bg-primary': '#0f172a',
                'bg-secondary': '#1e293b',
                'bg-tertiary': '#334155',

                // Textos (manter)
                'text-primary': '#f1f5f9',
                'text-secondary': '#cbd5e1',
                'text-muted': '#64748b',

                // Estados (manter)
                'success': '#10b981',
                'error': '#ef4444',
                'warning': '#f59e0b',
                'info': '#3b82f6',
            },

            // Animações
            keyframes: {
                'slide-in-right': {
                    '0%': {
                        transform: 'translateX(100%)',
                        opacity: '0',
                    },
                    '100%': {
                        transform: 'translateX(0)',
                        opacity: '1',
                    },
                },
            },
            animation: {
                'slide-in-right': 'slide-in-right 0.3s ease-out',
            },
        },
    },
    plugins: [
        /**
         * '@tailwindcss/forms' is the forms plugin that provides a minimal styling
         * for forms. If you don't like it or have own styling for forms,
         * comment the line below to disable '@tailwindcss/forms'.
         */
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/aspect-ratio'),
    ],
}