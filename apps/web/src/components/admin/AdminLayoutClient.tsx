"use client";

import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";

import { AdminSessionProvider, useAdminSession } from "@/components/admin/AdminSessionProvider";
import { AdminShell } from "@/components/admin/AdminShell";
import { QueryProvider } from "@/components/admin/QueryProvider";
import { SkeletonCard } from "@/components/admin/SkeletonBlock";
import { getAdminAccessToken } from "@/lib/auth/admin-session";

function AdminLayoutInner({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { profile, loading } = useAdminSession();
  const isLoginRoute = pathname === "/admin/login";

  useEffect(() => {
    const token = getAdminAccessToken();
    if (!token && !isLoginRoute) {
      router.replace("/admin/login");
      return;
    }
    if (token && isLoginRoute) {
      router.replace("/admin/dashboard");
    }
  }, [isLoginRoute, router, loading, profile]);

  useEffect(() => {
    const token = getAdminAccessToken();
    if (!isLoginRoute && !loading && !profile && !token) {
      router.replace("/admin/login");
    }
  }, [isLoginRoute, loading, profile, router]);

  if (isLoginRoute) {
    return <>{children}</>;
  }

  const token = getAdminAccessToken();

  if (!profile) {
    if (loading || token) {
      return (
        <div className="min-h-screen bg-paper px-6 py-10">
          <SkeletonCard />
        </div>
      );
    }
    return null;
  }

  return <AdminShell>{children}</AdminShell>;
}

export function AdminLayoutClient({ children }: { children: ReactNode }) {
  return (
    <QueryProvider>
      <AdminSessionProvider>
        <AdminLayoutInner>{children}</AdminLayoutInner>
      </AdminSessionProvider>
    </QueryProvider>
  );
}
