import { useNavigate } from 'react-router-dom';
import { logout } from '../src/auth/authService';
import { SearchBar } from './SearchBar.jsx';

export function TopNavbar({ activePage, onMenuClick }) {
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <header className="top-navbar">
      <div className="top-navbar__left">
        {/* Hamburger — visible on mobile only */}
        <button
          className="top-navbar__hamburger"
          type="button"
          onClick={onMenuClick}
          aria-label="Open navigation menu"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
          </svg>
        </button>
        <div className="top-navbar__title">
          <span className="top-navbar__eyebrow">Enterprise AI Chatbot Platform</span>
          <h1>{activePage}</h1>
        </div>
      </div>
      <div className="top-navbar__actions">
        <SearchBar placeholder="Search products, documents, or settings" hideLabel />
        <button className="top-navbar__icon-btn" type="button" aria-label="Notifications">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <path d="M9 2a5 5 0 0 1 5 5v3l1.5 2H2.5L4 10V7a5 5 0 0 1 5-5Z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round"/>
            <path d="M7 14a2 2 0 0 0 4 0" stroke="currentColor" strokeWidth="1.5"/>
          </svg>
          <span className="top-navbar__badge" aria-label="2 notifications">2</span>
        </button>
        <span className="top-navbar__avatar" aria-label="Ops Admin">OP</span>
        <button className="top-navbar__logout-btn" type="button" onClick={handleLogout}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M6 2H3a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3M11 11l3-3-3-3M14 8H6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span className="top-navbar__logout-label">Logout</span>
        </button>
      </div>
    </header>
  );
}
