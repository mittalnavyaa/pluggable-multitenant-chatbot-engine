import { useState } from 'react';
import { NavLink } from 'react-router-dom';

const icons = {
  Dashboard: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <rect x="1" y="1" width="6" height="6" rx="1" fill="currentColor" opacity=".9"/>
      <rect x="9" y="1" width="6" height="6" rx="1" fill="currentColor" opacity=".9"/>
      <rect x="1" y="9" width="6" height="6" rx="1" fill="currentColor" opacity=".9"/>
      <rect x="9" y="9" width="6" height="6" rx="1" fill="currentColor" opacity=".9"/>
    </svg>
  ),
  Analytics: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M2 14V8m4 6V4m4 10V9m4 5V6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Conversations: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M14 10c0 1-1 2-2 2H4l-3 3V3c0-1 1-2 2-2h9c1 0 2 1 2 2v7z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  'Knowledge Base': (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M2 13V3a1 1 0 0 1 1-1h5l3 3h3a1 1 0 0 1 1 1v7a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M6 8h4M6 10h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
  Documents: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <rect x="3" y="1" width="10" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.5"/>
      <path d="M6 5h4M6 8h4M6 11h2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
  'Sales Leads': (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M8 7a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm-6 8a6 6 0 0 1 12 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
  Platforms: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <rect x="2" y="2" width="12" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/>
      <rect x="2" y="9" width="12" height="5" rx="1" stroke="currentColor" strokeWidth="1.5"/>
      <circle cx="5" cy="4.5" r="0.75" fill="currentColor"/>
      <circle cx="5" cy="11.5" r="0.75" fill="currentColor"/>
    </svg>
  ),
  Settings: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="2.5" stroke="currentColor" strokeWidth="1.5"/>
      <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3.05 3.05l1.42 1.42M11.53 11.53l1.42 1.42M3.05 12.95l1.42-1.42M11.53 4.47l1.42-1.42" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
  'Overview Dashboard': (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M2 10l4-4 3 3 5-6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <rect x="1" y="1" width="14" height="14" rx="2" stroke="currentColor" strokeWidth="1.5"/>
    </svg>
  ),
  Products: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M2 4h12M2 8h12M2 12h7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
  Branding: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <circle cx="8" cy="8" r="6" stroke="currentColor" strokeWidth="1.5"/>
      <path d="M5 8.5c.8 1.2 5.2 1.2 6 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
      <circle cx="6" cy="6.5" r="1" fill="currentColor"/>
      <circle cx="10" cy="6.5" r="1" fill="currentColor"/>
    </svg>
  ),
  Uploads: (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <path d="M8 11V4M5 7l3-3 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M3 13h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  ),
  'API Keys': (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
      <circle cx="6" cy="8" r="3.5" stroke="currentColor" strokeWidth="1.5"/>
      <path d="M9 8h5M12 6.5V8" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
    </svg>
  )
};

const scaffoldNavItems = [
  { label: 'Dashboard', path: '/' },
  { label: 'Analytics', path: '/analytics' },
  { label: 'Conversations', path: '/conversations' },
  { label: 'Knowledge Base', path: '/knowledge-base' },
  { label: 'Documents', path: '/documents' },
  { label: 'Sales Leads', path: '/sales-leads' },
  { label: 'Platforms', path: '/platforms' },
  { label: 'Settings', path: '/settings' }
];

const platformNavItems = [
  { label: 'Overview Dashboard', path: '/admin' },
  { label: 'Products', path: '/products' },
  { label: 'Branding', path: '/branding' },
  { label: 'Uploads', path: '/uploads' },
  { label: 'API Keys', path: '/api-keys' }
];

export function Sidebar({ activePage, onNavigate, collapsed, mobileOpen, onCollapse, onMobileClose }) {

  function renderNavItem(item) {
    const content = (
      <>
        {icons[item.label]}
        <span className="sidebar__label">{item.label}</span>
      </>
    );

    if (onNavigate) {
      return (
        <button
          key={item.label}
          className={item.label === activePage ? 'is-active' : ''}
          type="button"
          onClick={() => { onNavigate(item.label); onMobileClose?.(); }}
        >
          {content}
        </button>
      );
    }

    return (
      <NavLink
        key={item.label}
        to={item.path}
        className={({ isActive }) =>
          isActive || (item.path === '/products' && activePage === 'Product Details') ? 'is-active' : ''
        }
        onClick={() => onMobileClose?.()}
      >
        {content}
      </NavLink>
    );
  }

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div className="sidebar-backdrop" onClick={onMobileClose} aria-hidden="true" />
      )}

      <aside
        className={[
          'sidebar',
          collapsed ? 'sidebar--collapsed' : '',
          mobileOpen ? 'sidebar--mobile-open' : ''
        ].filter(Boolean).join(' ')}
        aria-label="Dashboard navigation"
      >
        {/* Brand */}
        <div className="sidebar__brand">
          <span className="sidebar__mark" style={{ background: 'var(--color-primary)', color: 'var(--color-text-inverted)', display: 'grid', placeItems: 'center', fontWeight: 'bold' }}>EV</span>
          <span className="sidebar__label sidebar__brand-text">
            <strong>Envoy AI</strong>
            <small>Admin Portal</small>
          </span>
        </div>

        {/* Nav */}
        <nav className="sidebar__nav" style={{ overflowY: 'auto', paddingRight: '4px' }}>
          <span className="sidebar__nav-label sidebar__label" style={{ marginTop: '0px' }}>Scaffold Panels</span>
          {scaffoldNavItems.map(renderNavItem)}

          <span className="sidebar__nav-label sidebar__label" style={{ marginTop: '16px', display: 'block' }}>Active Operations</span>
          {platformNavItems.map(renderNavItem)}
        </nav>

        {/* Footer — collapse toggle only, no user profile */}
        <div className="sidebar__footer">
          <button
            className="sidebar__collapse-btn"
            type="button"
            onClick={onCollapse}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <svg
              width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"
              style={{ transform: collapsed ? 'rotate(180deg)' : 'none', transition: 'transform 0.3s' }}
            >
              <path d="M10 3L5 8l5 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span className="sidebar__label">Collapse</span>
          </button>
        </div>
      </aside>
    </>
  );
}
