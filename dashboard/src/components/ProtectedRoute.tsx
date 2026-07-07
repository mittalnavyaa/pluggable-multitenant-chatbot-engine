import { Navigate } from 'react-router-dom';
import { isAuthenticated } from '../auth/authService';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/** Wraps any route — redirects to /login if no valid session exists */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}
