import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAdminSettings, updateAdminSettings } from "@/lib/api";

const QUERY_KEY = ["admin-settings"];

export function useAdminSettings() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: QUERY_KEY,
    queryFn: getAdminSettings,
  });

  const updateMutation = useMutation({
    mutationFn: updateAdminSettings,
    onSuccess: (data) => {
      queryClient.setQueryData(QUERY_KEY, data);
    },
  });

  return {
    settings: query.data,
    isLoading: query.isLoading,
    update: updateMutation.mutateAsync,
    isUpdating: updateMutation.isPending,
    updateError: updateMutation.error,
  };
}
