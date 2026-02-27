import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { getJobRuns } from "@/lib/api";
import type { PageSize } from "@/hooks/usePageSize";

const QUERY_KEY = ["admin", "jobs"];

export function useJobRuns(enabled: boolean, page: number, pageSize: PageSize) {
  const query = useQuery({
    queryKey: [...QUERY_KEY, { page, pageSize }],
    queryFn: () =>
      getJobRuns({
        page,
        pageSize,
      }),
    enabled,
    placeholderData: keepPreviousData,
    staleTime: 1000 * 60, // 1 minute
  });

  const items = query.data?.items;

  return {
    jobRuns: Array.isArray(items) ? items : [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading || (!query.data && !query.error && enabled),
    error: query.error
      ? query.error instanceof Error
        ? query.error.message
        : "Failed to load job runs"
      : null,
    refetch: query.refetch,
  };
}
