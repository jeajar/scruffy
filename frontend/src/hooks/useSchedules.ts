import {
  useQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import {
  getSchedules,
  createSchedule,
  updateSchedule,
  deleteSchedule,
  runScheduleNow,
  type ScheduleCreate,
  type ScheduleUpdate,
} from "@/lib/api";

const QUERY_KEY = ["admin", "schedules"];

export function useSchedules(enabled: boolean) {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: QUERY_KEY,
    queryFn: getSchedules,
    enabled,
    staleTime: 1000 * 60, // 1 minute
  });

  const createMutation = useMutation({
    mutationFn: (body: ScheduleCreate) => createSchedule(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: ScheduleUpdate }) =>
      updateSchedule(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteSchedule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const runNowMutation = useMutation({
    mutationFn: (id: number) => runScheduleNow(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  return {
    schedules: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error
      ? query.error instanceof Error
        ? query.error.message
        : "Failed to load schedules"
      : null,
    refetch: query.refetch,
    createSchedule: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
    updateSchedule: (id: number, body: ScheduleUpdate) =>
      updateMutation.mutateAsync({ id, body }),
    isUpdating: updateMutation.isPending,
    deleteSchedule: deleteMutation.mutateAsync,
    isDeleting: deleteMutation.isPending,
    runScheduleNow: runNowMutation.mutateAsync,
    runningId:
      runNowMutation.isPending && runNowMutation.variables !== undefined
        ? runNowMutation.variables
        : null,
  };
}
