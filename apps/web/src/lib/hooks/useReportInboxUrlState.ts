"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  readReportInboxFilters,
  REPORT_INBOX_FROM_PARAM,
  REPORT_INBOX_KEYWORD_DEBOUNCE_MS,
  REPORT_INBOX_KEYWORD_PARAM,
  REPORT_INBOX_SEVERITY_PARAM,
  REPORT_INBOX_STATUS_PARAM,
  REPORT_INBOX_TO_PARAM,
  REPORT_INBOX_TYPE_PARAM,
} from "@/lib/report-inbox-filters";

export {
  REPORT_INBOX_FROM_PARAM,
  REPORT_INBOX_KEYWORD_DEBOUNCE_MS,
  REPORT_INBOX_KEYWORD_PARAM,
  REPORT_INBOX_SEVERITY_PARAM,
  REPORT_INBOX_STATUS_PARAM,
  REPORT_INBOX_TO_PARAM,
  REPORT_INBOX_TYPE_PARAM,
  readReportInboxFilters,
  type ReportInboxUrlFilters,
} from "@/lib/report-inbox-filters";

function setOrDeleteParam(params: URLSearchParams, key: string, value: string) {
  if (value) {
    params.set(key, value);
  } else {
    params.delete(key);
  }
}

export function useReportInboxUrlState() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const filters = readReportInboxFilters(searchParams);
  const { status, keyword, type, severity, from, to } = filters;
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
        setOrDeleteParam(params, REPORT_INBOX_STATUS_PARAM, nextStatus);
      });
    },
    [replaceSearchParams],
  );

  const setType = useCallback(
    (nextType: string) => {
      replaceSearchParams((params) => {
        setOrDeleteParam(params, REPORT_INBOX_TYPE_PARAM, nextType);
      });
    },
    [replaceSearchParams],
  );

  const setSeverity = useCallback(
    (nextSeverity: string) => {
      replaceSearchParams((params) => {
        setOrDeleteParam(params, REPORT_INBOX_SEVERITY_PARAM, nextSeverity);
      });
    },
    [replaceSearchParams],
  );

  const setFrom = useCallback(
    (nextFrom: string) => {
      replaceSearchParams((params) => {
        setOrDeleteParam(params, REPORT_INBOX_FROM_PARAM, nextFrom);
      });
    },
    [replaceSearchParams],
  );

  const setTo = useCallback(
    (nextTo: string) => {
      replaceSearchParams((params) => {
        setOrDeleteParam(params, REPORT_INBOX_TO_PARAM, nextTo);
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
        setOrDeleteParam(params, REPORT_INBOX_KEYWORD_PARAM, trimmedDraft);
      });
    }, REPORT_INBOX_KEYWORD_DEBOUNCE_MS);

    return () => {
      window.clearTimeout(timer);
    };
  }, [keyword, keywordDraft, replaceSearchParams]);

  return {
    status,
    keyword,
    type,
    severity,
    from,
    to,
    keywordDraft,
    setKeywordDraft,
    setStatus,
    setType,
    setSeverity,
    setFrom,
    setTo,
  };
}
