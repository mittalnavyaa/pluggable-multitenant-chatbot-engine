import { ADMIN_CREDENTIALS, SESSION_KEY } from './authConfig';

/** Returns true if a valid session exists */
export function isAuthenticated(): boolean {
  return sessionStorage.getItem(SESSION_KEY) === 'true';
}

/** Validates credentials and creates a session. Returns true on success. */
export function login(username: string, password: string): boolean {
  if (
    username.trim() === ADMIN_CREDENTIALS.username &&
    password === ADMIN_CREDENTIALS.password
  ) {
    sessionStorage.setItem(SESSION_KEY, 'true');
    return true;
  }
  return false;
}

/** Clears the session */
export function logout(): void {
  sessionStorage.removeItem(SESSION_KEY);
}
