"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

export const REPORT_INBOX_STATUS_PARAM = "status";
export const REPORT_INBOX_KEYWORD_PARAM = "q";
export const REPORT_INBOX_KEYWORD_DEBOUNCE_MS = 350;

export type ReportInboxUrlFilters = {
  status: string;
  keyword: string;
};

export function readReportInboxFilters(
  searchParams: Pick<URLSearchParams, "get">,
): ReportInboxUrlFilters {
  return {
    status: searchParams.get(REPORT_INBOX_STATUS_PARAM) ?? "",
    keyword: searchParams.get(REPORT_INBOX_KEYWORD_PARAM) ?? "",
  };
}

export function useReportInboxUrlState() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const { status, keyword } = readReportInboxFilters(searchParams);
  const [keywordDraft, setKeywordDraft] = useState(keyword);

  useEffect(() => {
    setKeywordDraft(keyword);
  }, [keyword]);

  const replaceSearchParams = useCallback(
    (mutator: (params: URLSearchParams) => void) => {
      const params = new URLSearchParams(searchParams.toString());
      mutator(params);
      const query = params.toString();
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  const setStatus = useCallback(
    (nextStatus: string) => {
      replaceSearchParams((params) => {
        if (nextStatus) {
          params.set(REPORT_INBOX_STATUS_PARAM, nextStatus);
        } else {
          params.delete(REPORT_INBOX_STATUS_PARAM);
        }
      });
    },
    [replaceSearchParams],
  );

  useEffect(() => {
    const trimmedDraft = keywordDraft.trim();
    if (trimmedDraft === keyword) {
      return;
    }

    const timer = window.setTimeout(() => {
      replaceSearchParams((params) => {
        if (trimmedDraft) {
          params.set(REPORT_INBOX_KEYWORD_PARAM, trimmedDraft);
        } else {
          params.delete(REPORT_INBOX_KEYWORD_PARAM);
        }
      });
    }, REPORT_INBOX_KEYWORD_DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timer);
    };
  }, [keyword, keywordDraft, replaceSearchParams]);

  return {
    status,
    keyword,
    keywordDraft,
    setKeywordDraft,
    setStatus,
  };
}
