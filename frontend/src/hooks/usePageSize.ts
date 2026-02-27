import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "scruffy_page_size";

export type PageSize = 25 | 50 | null;

function parseStoredPageSize(value: string | null): PageSize {
  if (value === "25") return 25;
  if (value === "50") return 50;
  if (value === "all") return null;
  return 25;
}

export function usePageSize() {
  const [pageSize, setPageSizeState] = useState<PageSize>(() => {
    if (typeof window === "undefined") {
      return 25;
    }
    return parseStoredPageSize(window.localStorage.getItem(STORAGE_KEY));
  });

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    window.localStorage.setItem(
      STORAGE_KEY,
      pageSize === null ? "all" : String(pageSize)
    );
  }, [pageSize]);

  const setPageSize = useCallback((value: PageSize) => {
    setPageSizeState(value);
  }, []);

  return [pageSize, setPageSize] as const;
}