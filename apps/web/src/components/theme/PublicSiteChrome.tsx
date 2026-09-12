"use client";

import { usePathname } from "next/navigation";

import { ThemeToggle } from "@/components/theme/ThemeToggle";

export function PublicSiteChrome() {
  const pathname = usePathname();

  if (pathname.startsWith("/admin")) {
    return null;
  }

  return (
    <div className="pointer-events-none fixed right-0 top-0 z-40 p-4 sm:p-6">
      <div className="pointer-events-auto">
        <ThemeToggle />
      </div>
    </div>
  );
}
