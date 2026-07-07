/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './**/*.{js,jsx,ts,tsx}',
    '!./node_modules/**',
  ],
  theme: {
    extend: {
      colors: {
        // ── Light mode exact tokens ──────────────────────────────
        'lt-bg':        '#F8FAFC',   // App Background
        'lt-surface':   '#FFFFFF',   // Surface / Card
        'lt-border':    '#E2E8F0',   // Borders
        'lt-text':      '#0F172A',   // Text Primary
        'lt-muted':     '#475569',   // Text Secondary
        'lt-primary':   '#2563EB',   // Primary Action
        'lt-primary-h': '#1D4ED8',   // Primary Hover
        'lt-success':   '#16A34A',   // Success
        'lt-warning':   '#D97706',   // Warning
        'lt-error':     '#DC2626',   // Error

        // ── Dark mode exact tokens ───────────────────────────────
        'dk-bg':        '#020617',   // App Background
        'dk-surface':   '#0F172A',   // Surface / Card
        'dk-border':    '#334155',   // Borders
        'dk-text':      '#F8FAFC',   // Text Primary
        'dk-muted':     '#94A3B8',   // Text Secondary
        'dk-primary':   '#3B82F6',   // Primary Action
        'dk-primary-h': '#2563EB',   // Primary Hover
        'dk-success':   '#4ADE80',   // Success
        'dk-warning':   '#FBBF24',   // Warning
        'dk-error':     '#F87171',   // Error

        // ── Chart exact tokens ───────────────────────────────────
        'ch-queries':   '#3B82F6',   // Line 1 — Queries
        'ch-sales':     '#8B5CF6',   // Line 2 — Sales
        'ch-resolve':   '#10B981',   // Line 3 — Resolution

        // ── Status subtle backgrounds (derived, WCAG AA) ─────────
        'lt-success-bg': '#DCFCE7',
        'lt-warning-bg': '#FEF3C7',
        'lt-error-bg':   '#FEE2E2',
        'lt-primary-bg': '#DBEAFE',
        'dk-success-bg': '#052E16',
        'dk-warning-bg': '#1C1400',
        'dk-error-bg':   '#1C0A0A',
        'dk-primary-bg': '#0C1A3A',
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Menlo', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'card':      '0 1px 3px 0 rgba(15,23,42,0.07), 0 1px 2px -1px rgba(15,23,42,0.05)',
        'card-hover':'0 8px 24px rgba(15,23,42,0.10)',
        'dk-card':   '0 1px 3px 0 rgba(0,0,0,0.30)',
        'dk-hover':  '0 8px 24px rgba(0,0,0,0.40)',
        'focus':     '0 0 0 3px rgba(37,99,235,0.25)',
        'focus-dk':  '0 0 0 3px rgba(59,130,246,0.30)',
      },
      transitionDuration: {
        DEFAULT: '150ms',
      },
    },
  },
  plugins: [],
};
