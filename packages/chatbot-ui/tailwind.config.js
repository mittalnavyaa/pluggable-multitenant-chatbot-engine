/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './src/index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Light mode colors
        'lt-bg':        '#F8FAFC',
        'lt-surface':   '#FFFFFF',
        'lt-border':    '#E2E8F0',
        'lt-text':      '#0F172A',
        'lt-muted':     '#475569',
        'lt-primary':   '#2563EB',
        'lt-primary-h': '#1D4ED8',
        'lt-success':   '#16A34A',
        'lt-warning':   '#D97706',
        'lt-error':     '#DC2626',

        // Dark mode colors
        'dk-bg':        '#020617',
        'dk-surface':   '#0F172A',
        'dk-border':    '#334155',
        'dk-text':      '#F8FAFC',
        'dk-muted':     '#94A3B8',
        'dk-primary':   '#3B82F6',
        'dk-primary-h': '#2563EB',
        'dk-success':   '#4ADE80',
        'dk-warning':   '#FBBF24',
        'dk-error':     '#F87171',
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'Arial', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
