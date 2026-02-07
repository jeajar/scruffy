import { useQuery } from "@tanstack/react-query";
import { getMediaList } from "@/lib/api";

export function useMedia() {
  const { data, isLoading, error, refetch, isFetched } = useQuery({
    queryKey: ["media"],
    queryFn: getMediaList,
    staleTime: 1000 * 60, // 1 minute
    refetchInterval: 1000 * 60 * 5, // Auto-refresh every 5 minutes
  });

  return {
    media: data?.media ?? [],
    count: data?.count ?? 0,
    overseerrUrl: data?.overseerr_url ?? null,
    extensionDays: data?.extension_days ?? 7,
    isLoading,
    isFetched,
    error,
    refetch,
  };
}
