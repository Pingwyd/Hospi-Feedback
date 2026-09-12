"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  clearAdminSession,
  getAdminAccessToken,
} from "@/lib/auth/admin-session";
import { fetchAdminProfile, type AdminProfile } from "@/lib/api/admin-fetch";

type RefreshProfileOptions = {
  /** Skip page-level loading when a profile is already rendered (tab refocus). */
  background?: boolean;
};

type AdminSessionContextValue = {
  profile: AdminProfile | null;
  loading: boolean;
  refreshProfile: (options?: RefreshProfileOptions) => Promise<void>;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
  hasRole: (...roles: string[]) => boolean;
};

const AdminSessionContext = createContext<AdminSessionContextValue | null>(null);

export function AdminSessionProvider({ children }: { children: ReactNode }) {
  const [profile, setProfile] = useState<AdminProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshProfile = useCallback(async (options?: RefreshProfileOptions) => {
    const token = getAdminAccessToken();
    if (!token) {
      setProfile(null);
      setLoading(false);
      return;
    }
    if (!options?.background) {
      setLoading(true);
    }
    try {
      const nextProfile = await fetchAdminProfile();
      setProfile(nextProfile);
    } catch {
      clearAdminSession();
      setProfile(null);
    } finally {
      if (!options?.background) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void refreshProfile();
  }, [refreshProfile]);

  // Re-check profile when tab regains focus (token may have been cleared elsewhere).
  useEffect(() => {
    function onFocus() {
      void refreshProfile({ background: true });
    }
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [refreshProfile]);

  const logout = useCallback(() => {
    clearAdminSession();
    setProfile(null);
  }, []);

  const value = useMemo<AdminSessionContextValue>(
    () => ({
      profile,
      loading,
      refreshProfile,
      logout,
      hasPermission: (permission: string) =>
        profile?.permissions.includes(permission) ?? false,
      hasRole: (...roles: string[]) =>
        profile?.role ? roles.includes(profile.role) : false,
    }),
    [profile, loading, refreshProfile, logout],
  );

  return (
    <AdminSessionContext.Provider value={value}>
      {children}
    </AdminSessionContext.Provider>
  );
}

export function useAdminSession(): AdminSessionContextValue {
  const context = useContext(AdminSessionContext);
  if (!context) {
    throw new Error("useAdminSession must be used within AdminSessionProvider.");
  }
  return context;
}
