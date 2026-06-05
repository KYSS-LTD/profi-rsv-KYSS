import { useQuery, useQueryClient } from '@tanstack/react-query';
import { createContext, ReactNode, useContext, useEffect, useState } from 'react';
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { CurrentUser } from '../entities/saas/types';
import { getMe, logout as logoutRequest } from '../shared/api/authV2';
import { AUTH_TOKEN_EVENT, clearAccessToken, getAccessToken } from '../shared/auth/token';
import { Loader } from '../shared/ui/Loader';

type AuthContextValue = {
  user?: CurrentUser;
  isAuthenticated: boolean;
  isLoading: boolean;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [token, setToken] = useState(() => getAccessToken());
  const hasToken = Boolean(token);

  useEffect(() => {
    const syncToken = () => setToken(getAccessToken());
    window.addEventListener(AUTH_TOKEN_EVENT, syncToken);
    window.addEventListener('storage', syncToken);
    return () => {
      window.removeEventListener(AUTH_TOKEN_EVENT, syncToken);
      window.removeEventListener('storage', syncToken);
    };
  }, []);
  const meQuery = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: getMe,
    enabled: hasToken,
    retry: false,
  });

  async function logout() {
    try {
      await logoutRequest();
    } finally {
      clearAccessToken();
      queryClient.clear();
      setToken(null);
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user: meQuery.data,
        isAuthenticated: Boolean(meQuery.data),
        isLoading: hasToken && meQuery.isLoading,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return value;
}

export function ProtectedRoute() {
  const auth = useAuth();
  const location = useLocation();

  if (auth.isLoading) {
    return <div className="p-6"><Loader text="Проверяем сессию..." /></div>;
  }

  if (!auth.isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (auth.user?.must_change_password && location.pathname !== '/auth/change-password') {
    return <Navigate to="/auth/change-password" replace />;
  }

  return <Outlet />;
}
