/** URL filter state and API param mapping for the admin report inbox. */

export const REPORT_INBOX_STATUS_PARAM = "status";
export const REPORT_INBOX_KEYWORD_PARAM = "q";
export const REPORT_INBOX_TYPE_PARAM = "type";
export const REPORT_INBOX_SEVERITY_PARAM = "severity";
export const REPORT_INBOX_FROM_PARAM = "from";
export const REPORT_INBOX_TO_PARAM = "to";
export const REPORT_INBOX_KEYWORD_DEBOUNCE_MS = 350;

export type ReportInboxUrlFilters = {
  status: string;
  keyword: string;
  type: string;
  severity: string;
  from: string;
  to: string;
};

export function readReportInboxFilters(
  searchParams: Pick<URLSearchParams, "get">,
): ReportInboxUrlFilters {
  return {
    status: searchParams.get(REPORT_INBOX_STATUS_PARAM) ?? "",
    keyword: searchParams.get(REPORT_INBOX_KEYWORD_PARAM) ?? "",
    type: searchParams.get(REPORT_INBOX_TYPE_PARAM) ?? "",
    severity: searchParams.get(REPORT_INBOX_SEVERITY_PARAM) ?? "",
    from: searchParams.get(REPORT_INBOX_FROM_PARAM) ?? "",
    to: searchParams.get(REPORT_INBOX_TO_PARAM) ?? "",
  };
}

/** Map URL calendar dates (YYYY-MM-DD) to API created_at bounds (UTC day). */
export function reportInboxDateToApiBounds(from: string, to: string): {
  created_from?: string;
  created_to?: string;
} {
  const datePattern = /^\d{4}-\d{2}-\d{2}$/;
  const result: { created_from?: string; created_to?: string } = {};
  if (from && datePattern.test(from)) {
    result.created_from = `${from}T00:00:00.000Z`;
  }
  if (to && datePattern.test(to)) {
    result.created_to = `${to}T23:59:59.999Z`;
  }
  return result;
}

export function reportInboxFiltersToListApi(filters: ReportInboxUrlFilters): {
  status?: string;
  keyword?: string;
  report_type?: string;
  severity?: string;
  created_from?: string;
  created_to?: string;
} {
  const dates = reportInboxDateToApiBounds(filters.from, filters.to);
  return {
    status: filters.status || undefined,
    keyword: filters.keyword || undefined,
    report_type: filters.type || undefined,
    severity: filters.severity || undefined,
    ...dates,
  };
}
