import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useCallback, useEffect, useState } from "react";
import {
  Plus,
  Play,
  Pencil,
  Trash2,
  Settings,
  RefreshCw,
} from "lucide-react";
import { Layout } from "@/components/layout";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAuth } from "@/hooks/useAuth";
import { LoadingScreen } from "@/components/ui/loading-screen";
import {
  getSchedules,
  createSchedule,
  updateSchedule,
  deleteSchedule,
  runScheduleNow,
  type Schedule,
  type ScheduleCreate,
} from "@/lib/api";

export const Route = createFileRoute("/admin/schedules")({
  component: AdminSchedulesPage,
});

function AdminSchedulesPage() {
  const navigate = useNavigate();
  const { isAuthenticated, isAdmin, isLoading: authLoading } = useAuth();
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [runningId, setRunningId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<ScheduleCreate>({
    job_type: "check",
    cron_expression: "0 */6 * * *",
    enabled: true,
  });

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate({ to: "/login" });
      return;
    }
    if (!authLoading && isAuthenticated && !isAdmin) {
      navigate({ to: "/" });
      return;
    }
  }, [authLoading, isAuthenticated, isAdmin, navigate]);

  const loadSchedules = useCallback(async () => {
    if (!isAdmin) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getSchedules();
      setSchedules(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load schedules");
    } finally {
      setLoading(false);
    }
  }, [isAdmin]);

  useEffect(() => {
    if (isAdmin) loadSchedules();
  }, [isAdmin, loadSchedules]);

  const handleCreate = async () => {
    try {
      const created = await createSchedule(form);
      setSchedules((prev) => [...prev, created]);
      setShowForm(false);
      setForm({ job_type: "check", cron_expression: "0 */6 * * *", enabled: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create");
    }
  };

  const handleUpdate = async (id: number, patch: { job_type?: "check" | "process"; cron_expression?: string; enabled?: boolean }) => {
    try {
      const updated = await updateSchedule(id, patch);
      setSchedules((prev) => prev.map((s) => (s.id === id ? updated : s)));
      setEditingId(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this schedule?")) return;
    try {
      await deleteSchedule(id);
      setSchedules((prev) => prev.filter((s) => s.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete");
    }
  };

  const handleRunNow = async (id: number) => {
    setRunningId(id);
    try {
      await runScheduleNow(id);
    } finally {
      setRunningId(null);
    }
  };

  if (authLoading || (!isAdmin && isAuthenticated)) {
    return <LoadingScreen />;
  }
  if (!isAuthenticated) {
    return null;
  }

  return (
    <Layout>
      <div className="px-4 sm:px-0">
        <div className="sm:flex sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-white flex items-center gap-2">
              <Settings className="h-7 w-7" />
              Scheduled Jobs
            </h1>
            <p className="mt-2 text-sm text-gray-400">
              Configure when Scruffy runs check and process jobs (Overseerr-style).
            </p>
          </div>
          <div className="mt-4 sm:mt-0">
            <Button
              onClick={() => {
                setShowForm(!showForm);
                setEditingId(null);
              }}
              variant="default"
              className="bg-scruffy-teal hover:bg-scruffy-teal/90"
            >
              <Plus className="h-4 w-4 mr-2" />
              Add schedule
            </Button>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-lg bg-red-900/20 border border-red-800 text-red-200 px-4 py-3 text-sm">
            {error}
          </div>
        )}

        {showForm && (
          <Card className="mt-6 bg-scruffy-dark border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">New schedule</CardTitle>
              <CardDescription className="text-gray-400">
                Cron: minute hour day month day-of-week (e.g. 0 */6 * * * = every 6 hours)
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-4 items-end">
                <label className="flex flex-col gap-1">
                  <span className="text-sm text-gray-400">Job</span>
                  <select
                    className="rounded-md bg-scruffy-darker border border-gray-600 text-white px-3 py-2 min-w-[120px]"
                    value={form.job_type}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, job_type: e.target.value as "check" | "process" }))
                    }
                  >
                    <option value="check">Check</option>
                    <option value="process">Process</option>
                  </select>
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-sm text-gray-400">Cron</span>
                  <input
                    type="text"
                    className="rounded-md bg-scruffy-darker border border-gray-600 text-white px-3 py-2 font-mono w-40"
                    value={form.cron_expression}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, cron_expression: e.target.value }))
                    }
                    placeholder="0 */6 * * *"
                  />
                </label>
                <label className="flex items-center gap-2 text-gray-300">
                  <input
                    type="checkbox"
                    checked={form.enabled ?? true}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, enabled: e.target.checked }))
                    }
                  />
                  <span className="text-sm">Enabled</span>
                </label>
                <Button onClick={handleCreate} className="bg-scruffy-teal hover:bg-scruffy-teal/90">
                  Create
                </Button>
                <Button variant="ghost" onClick={() => setShowForm(false)}>
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="mt-8">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 text-gray-500 animate-spin" />
            </div>
          ) : schedules.length === 0 && !showForm ? (
            <div className="rounded-lg border-2 border-dashed border-gray-700 p-12 text-center">
              <Settings className="mx-auto h-12 w-12 text-gray-500" />
              <h3 className="mt-4 text-lg font-medium text-white">No schedules</h3>
              <p className="mt-2 text-sm text-gray-400">
                Add a schedule to run check or process automatically (e.g. every 6 hours or daily).
              </p>
            </div>
          ) : (
            <div className="overflow-hidden shadow ring-1 ring-gray-700 sm:rounded-lg">
              <Table>
                <TableHeader className="bg-scruffy-dark">
                  <TableRow className="border-gray-700">
                    <TableHead className="text-white font-semibold pl-6">Job</TableHead>
                    <TableHead className="text-white font-semibold">Cron</TableHead>
                    <TableHead className="text-white font-semibold">Status</TableHead>
                    <TableHead className="text-white font-semibold text-right pr-6">
                      Actions
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className="bg-scruffy-darker">
                  {schedules.map((s) => (
                    <TableRow key={s.id} className="border-gray-700">
                      <TableCell className="pl-6">
                        {editingId === s.id ? (
                          <select
                            className="rounded bg-scruffy-dark border border-gray-600 text-white px-2 py-1 text-sm"
                            value={s.job_type}
                            onChange={(e) =>
                              handleUpdate(s.id, {
                                job_type: e.target.value as "check" | "process",
                              })
                            }
                          >
                            <option value="check">Check</option>
                            <option value="process">Process</option>
                          </select>
                        ) : (
                          <Badge variant={s.job_type === "process" ? "movie" : "tv"}>
                            {s.job_type}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-gray-300 font-mono text-sm">
                        {editingId === s.id ? (
                          <input
                            type="text"
                            className="rounded bg-scruffy-dark border border-gray-600 text-white px-2 py-1 font-mono w-36"
                            defaultValue={s.cron_expression}
                            onBlur={(e) => {
                              const v = e.target.value.trim();
                              if (v && v !== s.cron_expression)
                                handleUpdate(s.id, { cron_expression: v });
                            }}
                            onKeyDown={(e) => {
                              if (e.key === "Enter")
                                handleUpdate(s.id, {
                                  cron_expression: (e.target as HTMLInputElement).value.trim(),
                                });
                            }}
                          />
                        ) : (
                          s.cron_expression
                        )}
                      </TableCell>
                      <TableCell>
                        {editingId === s.id ? (
                          <label className="flex items-center gap-2 text-gray-300 text-sm">
                            <input
                              type="checkbox"
                              checked={s.enabled}
                              onChange={(e) =>
                                handleUpdate(s.id, { enabled: e.target.checked })
                              }
                            />
                            Enabled
                          </label>
                        ) : (
                          <Badge variant={s.enabled ? "safe" : "secondary"}>
                            {s.enabled ? "Enabled" : "Disabled"}
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right pr-6">
                        {editingId === s.id ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setEditingId(null)}
                          >
                            Done
                          </Button>
                        ) : (
                          <span className="inline-flex gap-2">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-gray-400 hover:text-white"
                              onClick={() => handleRunNow(s.id)}
                              disabled={runningId === s.id}
                              title="Run now"
                            >
                              {runningId === s.id ? (
                                <RefreshCw className="h-4 w-4 animate-spin" />
                              ) : (
                                <Play className="h-4 w-4" />
                              )}
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-gray-400 hover:text-white"
                              onClick={() => setEditingId(s.id)}
                              title="Edit"
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="text-gray-400 hover:text-red-400"
                              onClick={() => handleDelete(s.id)}
                              title="Delete"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>

        <p className="mt-6 text-xs text-gray-500">
          Check = scan media and retention. Process = send reminders and delete media per policy.
          Use the same cron format as crontab (e.g. 0 4 * * * = daily at 4:00).
        </p>
      </div>
    </Layout>
  );
}
