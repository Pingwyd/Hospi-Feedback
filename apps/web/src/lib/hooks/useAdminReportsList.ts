"use client";

import { useQuery } from "@tanstack/react-query";

import {
  adminReportsListQueryOptions,
  type AdminReportsListFilters,
} from "@/lib/query/admin-report-queries";

export function useAdminReportsList(filters: AdminReportsListFilters) {
  return useQuery(adminReportsListQueryOptions(filters));
}
