"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Building2,
  ClipboardList,
  FileText,
  LayoutDashboard,
  LogOut,
  Settings,
} from "lucide-react";
import type { ReactNode } from "react";

import { useAdminSession } from "@/components/admin/AdminSessionProvider";

type NavItem = {
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
  visible: boolean;
};

type AdminShellProps = {
  children: ReactNode;
};

export function AdminShell({ children }: AdminShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { profile, logout, hasPermission, hasRole } = useAdminSession();

  const navItems: NavItem[] = [
    {
      href: "/admin/dashboard",
      label: "Dashboard",
      icon: LayoutDashboard,
      visible: hasPermission("view"),
    },
    {
      href: "/admin/reports",
      label: "Inbox",
      icon: ClipboardList,
      visible: hasPermission("view"),
    },
    {
      href: "/admin/audit",
      label: "Audit log",
      icon: FileText,
      visible: hasRole("hoh", "asst_head"),
    },
    {
      href: "/admin/settings",
      label: "Settings",
      icon: Settings,
      visible:
        hasPermission("manage_categories") ||
        hasPermission("manage_escalation_contacts") ||
        hasPermission("manage_admins"),
    },
  ];

  function handleLogout() {
    logout();
    router.replace("/admin/login");
  }

  return (
    <div className="min-h-screen bg-paper text-ink">
      <div className="mx-auto flex min-h-screen max-w-7xl">
        <aside className="hidden w-64 shrink-0 border-r border-ink/10 bg-white/40 p-6 lg:block">
          <div className="mb-8 flex items-center gap-3">
            <Building2 className="text-sage" size={22} />
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-ink/50">
                Hospi Feedback
              </p>
              <p className="font-semibold text-ink">Admin</p>
            </div>
          </div>
          <nav className="space-y-1">
            {navItems
              .filter((item) => item.visible)
              .map((item) => {
                const Icon = item.icon;
                const active = pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                      active
                        ? "bg-ink text-paper"
                        : "text-ink/70 hover:bg-ink/5 hover:text-ink"
                    }`}
                  >
                    <Icon size={18} />
                    {item.label}
                  </Link>
                );
              })}
          </nav>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="border-b border-ink/10 bg-white/50 px-4 py-4 sm:px-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm text-ink/60">Signed in as</p>
                <p className="font-semibold text-ink">
                  {profile?.full_name ?? "Admin"}
                </p>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                className="inline-flex items-center gap-2 rounded-lg border border-ink/15 px-3 py-2 text-sm font-medium text-ink hover:bg-white/70"
              >
                <LogOut size={16} />
                Sign out
              </button>
            </div>
            <nav className="mt-4 flex gap-2 overflow-x-auto lg:hidden">
              {navItems
                .filter((item) => item.visible)
                .map((item) => {
                  const active = pathname.startsWith(item.href);
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium ${
                        active
                          ? "bg-ink text-paper"
                          : "bg-white/70 text-ink/70 ring-1 ring-ink/10"
                      }`}
                    >
                      {item.label}
                    </Link>
                  );
                })}
            </nav>
          </header>
          <main className="flex-1 px-4 py-6 sm:px-6">{children}</main>
        </div>
      </div>
    </div>
  );
}
