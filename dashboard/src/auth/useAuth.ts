import { useState } from 'react';
import { isAuthenticated, login, logout } from './authService';

export function useAuth() {
  const [authenticated, setAuthenticated] = useState<boolean>(isAuthenticated);

  function handleLogin(username: string, password: string): boolean {
    const success = login(username, password);
    if (success) setAuthenticated(true);
    return success;
  }

  function handleLogout(): void {
    logout();
    setAuthenticated(false);
  }

  return { authenticated, handleLogin, handleLogout };
}
