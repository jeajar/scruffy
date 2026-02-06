import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { ListChecks, RefreshCw } from "lucide-react";
import { Layout } from "@/components/layout";
import { useAuth } from "@/hooks/useAuth";
import { useJobRuns } from "@/hooks/useJobRuns";
import { LoadingScreen } from "@/components/ui/loading-screen";
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
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { JobRun } from "@/lib/api";

export const Route = createFileRoute("/admin/jobs")({
  component: JobsPage,
});

function formatDate(isoString: string): string {
  const date = new Date(isoString);
  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function jobTypeLabel(jobType: string): string {
  return jobType === "check" ? "Check" : "Process";
}

function JobsPage() {
  const navigate = useNavigate();
  const { isAuthenticated, isAdmin, isLoading: authLoading } = useAuth();
  const { jobRuns, isLoading, error, refetch } = useJobRuns(!!isAdmin);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate({ to: "/login", search: {} });
      return;
    }
    if (!authLoading && isAuthenticated && !isAdmin) {
      navigate({ to: "/" });
      return;
    }
  }, [authLoading, isAuthenticated, isAdmin, navigate]);

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
              <ListChecks className="h-7 w-7" />
              Jobs
            </h1>
            <p className="mt-2 text-sm text-gray-400">
              History of check and process job runs.
            </p>
          </div>
        </div>

        <div className="mt-8">
          <Card className="bg-scruffy-dark border-gray-700 w-full">
            <CardHeader className="flex flex-row items-start justify-between gap-4">
              <div>
                <CardTitle className="text-white">Job Runs</CardTitle>
                <CardDescription>
                  Recent check and process job executions with date and outcome.
                </CardDescription>
              </div>
              <Button
                onClick={() => refetch()}
                variant="outline"
                size="sm"
                className="shrink-0 border-gray-600 text-gray-300 hover:bg-gray-700 hover:text-white"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </CardHeader>
            <CardContent>
              {error && (
                <div className="rounded-lg bg-red-900/20 border border-red-800 text-red-200 px-4 py-3 text-sm mb-4">
                  {error}
                </div>
              )}

              {isLoading ? (
                <p className="text-gray-400 text-sm">Loading...</p>
              ) : jobRuns.length === 0 ? (
                <p className="text-gray-400 text-sm">
                  No job runs recorded yet. Run a check or process job from{" "}
                  <Link
                    to="/admin/settings/schedules"
                    className="text-scruffy-teal hover:underline"
                  >
                    Schedules
                  </Link>{" "}
                  to see history.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="border-gray-700 hover:bg-transparent">
                      <TableHead className="text-gray-400">Job Type</TableHead>
                      <TableHead className="text-gray-400">Date</TableHead>
                      <TableHead className="text-gray-400">Status</TableHead>
                      <TableHead className="text-gray-400">Error</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {jobRuns.map((run: JobRun) => (
                      <TableRow
                        key={run.id}
                        className="border-gray-700 hover:bg-gray-800/50"
                      >
                        <TableCell className="text-white font-medium">
                          {jobTypeLabel(run.job_type)}
                        </TableCell>
                        <TableCell className="text-gray-300">
                          {formatDate(run.finished_at)}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={run.success ? "default" : "destructive"}
                            className={
                              run.success
                                ? "bg-green-600/80 hover:bg-green-600/80"
                                : ""
                            }
                          >
                            {run.success ? "Success" : "Failed"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-gray-400 text-sm max-w-xs truncate">
                          {run.error_message ?? "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
