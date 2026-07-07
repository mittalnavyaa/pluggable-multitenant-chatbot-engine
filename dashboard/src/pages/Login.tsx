import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/useAuth';
import '../styles/login.css';

export function Login() {
  const { handleLogin } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');

    if (!username.trim() || !password) {
      setError('Please enter both username and password.');
      return;
    }

    setLoading(true);

    // Small delay to show loading state — feels more real
    await new Promise((res) => setTimeout(res, 600));

    const success = handleLogin(username, password);

    if (success) {
      navigate('/', { replace: true });
    } else {
      setError('Invalid username or password.');
      setLoading(false);
    }
  }

  return (
    <div className="login-shell">
      <div className="login-card">

        {/* Brand */}
        <div className="login-card__brand">
          <span className="login-card__mark">AI</span>
          <div className="login-card__brand-text">
            <strong>Chatbot Platform</strong>
            <span>Internal Operations</span>
          </div>
        </div>

        <h1 className="login-card__heading">Admin Login</h1>
        <p className="login-card__sub">Sign in to access the dashboard.</p>

        <form className="login-form" onSubmit={handleSubmit} noValidate>

          {/* Username */}
          <div className="login-field">
            <label htmlFor="username">Username</label>
            <div className="login-field__input-wrap">
              <input
                id="username"
                type="text"
                autoComplete="username"
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className={error ? 'is-error' : ''}
                disabled={loading}
              />
            </div>
          </div>

          {/* Password */}
          <div className="login-field">
            <label htmlFor="password">Password</label>
            <div className="login-field__input-wrap">
              <input
                id="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className={error ? 'is-error' : ''}
                disabled={loading}
              />
              <button
                type="button"
                className="login-field__toggle"
                onClick={() => setShowPassword((v) => !v)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={-1}
              >
                {showPassword ? (
                  /* Eye-off icon */
                  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                    <path d="M2 2l14 14M7.5 7.6A2.5 2.5 0 0 0 10.4 10.5M5.2 5.3C3.5 6.4 2.2 7.9 1.5 9c1.2 2.4 4 5 7.5 5a8 8 0 0 0 3.8-1L5.2 5.3ZM9 4c3.5 0 6.3 2.6 7.5 5a10 10 0 0 1-1.8 2.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
                  </svg>
                ) : (
                  /* Eye icon */
                  <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                    <ellipse cx="9" cy="9" rx="7.5" ry="4.5" stroke="currentColor" strokeWidth="1.4"/>
                    <circle cx="9" cy="9" r="2.5" stroke="currentColor" strokeWidth="1.4"/>
                  </svg>
                )}
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="login-error" role="alert">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                <circle cx="8" cy="8" r="6.5" stroke="currentColor" strokeWidth="1.4"/>
                <path d="M8 5v3.5M8 10.5v.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/>
              </svg>
              {error}
            </div>
          )}

          {/* Submit */}
          <button className="login-btn" type="submit" disabled={loading}>
            {loading ? (
              <>
                <span className="login-spinner" aria-hidden="true" />
                Signing in…
              </>
            ) : (
              'Sign In'
            )}
          </button>

        </form>
      </div>
    </div>
  );
}
