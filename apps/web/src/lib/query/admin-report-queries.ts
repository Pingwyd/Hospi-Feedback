import {
  queryOptions,
  type QueryClient,
} from "@tanstack/react-query";

import { listAdminReports } from "@/lib/api/admin-reports";

export type AdminReportsListFilters = {
  status: string;
  keyword: string;
  limit?: number;
};

/** Session-scoped freshness for inbox filter combinations (back/forward cache hits). */
export const ADMIN_REPORTS_LIST_STALE_MS = 5 * 60 * 1000;

export const adminReportKeys = {
  all: ["admin", "reports"] as const,
  lists: () => [...adminReportKeys.all, "list"] as const,
  list: (filters: AdminReportsListFilters) =>
    [...adminReportKeys.lists(), filters] as const,
};

export function adminReportsListQueryOptions(filters: AdminReportsListFilters) {
  const limit = filters.limit ?? 100;
  return queryOptions({
    queryKey: adminReportKeys.list({ ...filters, limit }),
    queryFn: () =>
      listAdminReports({
        status: filters.status || undefined,
        keyword: filters.keyword || undefined,
        limit,
      }),
    staleTime: ADMIN_REPORTS_LIST_STALE_MS,
  });
}

export function invalidateAdminReportLists(queryClient: QueryClient): Promise<void> {
  return queryClient.invalidateQueries({ queryKey: adminReportKeys.all });
}
