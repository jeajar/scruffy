import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getAuthStatus, logout as logoutApi, type User } from "@/lib/api";

export function useAuth() {
  const queryClient = useQueryClient();

  const {
    data,
    isLoading,
    error,
    refetch: checkAuth,
  } = useQuery({
    queryKey: ["auth"],
    queryFn: getAuthStatus,
    staleTime: 1000 * 60 * 5, // 5 minutes
    retry: false,
  });

  const logoutMutation = useMutation({
    mutationFn: logoutApi,
    onSuccess: () => {
      queryClient.setQueryData(["auth"], { authenticated: false });
      queryClient.invalidateQueries({ queryKey: ["media"] });
    },
  });

  return {
    user: data?.user as User | undefined,
    isAuthenticated: data?.authenticated ?? false,
    isAdmin: data?.isAdmin ?? false,
    isLoading,
    error,
    checkAuth,
    logout: logoutMutation.mutate,
    isLoggingOut: logoutMutation.isPending,
  };
}
