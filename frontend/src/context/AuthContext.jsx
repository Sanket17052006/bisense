import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { api } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadUser = useCallback(async () => {
    const accessToken = localStorage.getItem("bis_access_token");
    const storedUser = localStorage.getItem("bis_user");
    if (accessToken && storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setUser(userData);
      } catch (e) {
        localStorage.removeItem("bis_user");
      }
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  const login = async (email, password) => {
    setError(null);
    try {
      const data = await api.auth.login(email, password);
      localStorage.setItem("bis_access_token", data.access_token);
      localStorage.setItem("bis_refresh_token", data.refresh_token);
      localStorage.setItem("bis_user", JSON.stringify(data.user));
      setUser(data.user);
      return { success: true };
    } catch (err) {
      const msg = err.response?.data?.detail || "Invalid email or password";
      setError(msg);
      return { success: false, error: msg };
    }
  };

  const register = async (name, email, password) => {
    setError(null);
    try {
      const data = await api.auth.register(name, email, password);
      localStorage.setItem("bis_access_token", data.access_token);
      localStorage.setItem("bis_refresh_token", data.refresh_token);
      localStorage.setItem("bis_user", JSON.stringify(data.user));
      setUser(data.user);
      return { success: true };
    } catch (err) {
      const msg = err.response?.data?.detail || "Registration failed";
      setError(msg);
      return { success: false, error: msg };
    }
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem("bis_refresh_token");
    try {
      await api.auth.logout(refreshToken);
    } catch (e) {
      console.warn("Logout API call failed:", e);
    }
    localStorage.removeItem("bis_access_token");
    localStorage.removeItem("bis_refresh_token");
    localStorage.removeItem("bis_user");
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const data = await api.auth.me();
      localStorage.setItem("bis_user", JSON.stringify(data));
      setUser(data);
    } catch (e) {
      await logout();
    }
  };

  const value = {
    user,
    loading,
    error,
    login,
    register,
    logout,
    refreshUser,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}