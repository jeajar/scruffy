import { useQuery } from "@tanstack/react-query";
import { getJobRuns } from "@/lib/api";

const QUERY_KEY = ["admin", "jobs"];

export function useJobRuns(enabled: boolean) {
  const query = useQuery({
    queryKey: QUERY_KEY,
    queryFn: getJobRuns,
    enabled,
    staleTime: 1000 * 60, // 1 minute
  });

  return {
    jobRuns: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error
      ? query.error instanceof Error
        ? query.error.message
        : "Failed to load job runs"
      : null,
    refetch: query.refetch,
  };
}
