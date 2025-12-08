/**
 * Nebue - Tailwind Configuration
 * Paleta de cores violet/indigo moderna + Dark Mode
 */

module.exports = {
    // ⭐ DARK MODE HABILITADO
    darkMode: 'class', // Usa a classe 'dark' no <html> para ativar
    
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
            // 🎨 CORES PRINCIPAIS (Violet/Indigo)
            colors: {
                // Fundos Escuros (Dark Mode)
                'bg-primary': '#0f172a',      // slate-950
                'bg-secondary': '#1e293b',    // slate-900
                'bg-tertiary': '#334155',     // slate-800

                // Textos
                'text-primary': '#f1f5f9',    // slate-100
                'text-secondary': '#cbd5e1',  // slate-300
                'text-muted': '#64748b',      // slate-500

                // Estados
                'success': '#10b981',         // emerald-500
                'error': '#ef4444',           // red-500
                'warning': '#f59e0b',         // amber-500
                'info': '#3b82f6',            // blue-500
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
                'pulse-ring': {
                    '0%': {
                        transform: 'scale(1)',
                        opacity: '0.8',
                    },
                    '100%': {
                        transform: 'scale(1.5)',
                        opacity: '0',
                    },
                },
            },
            animation: {
                'slide-in-right': 'slide-in-right 0.3s ease-out',
                'pulse-ring': 'pulse-ring 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
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