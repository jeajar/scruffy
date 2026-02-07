import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { Fragment, useEffect, useState } from "react";
import { ChevronDown, ChevronRight, ListChecks, RefreshCw } from "lucide-react";
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
import type { JobRun, JobRunSummary } from "@/lib/api";

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

function JobRunSummaryContent({ summary }: { summary: JobRunSummary }) {
  const hasReminders = summary.reminders && summary.reminders.length > 0;
  const hasDeletions = summary.deletions && summary.deletions.length > 0;
  const hasCheck = summary.items_checked !== undefined;

  if (!hasReminders && !hasDeletions && !hasCheck) {
    return <span className="text-gray-500 text-sm">No details</span>;
  }

  return (
    <div className="text-sm text-gray-300 space-y-3">
      {hasCheck && (
        <div>
          <span className="font-medium text-gray-400">Items checked: </span>
          {summary.items_checked}
          {summary.needing_attention !== undefined && summary.needing_attention > 0 && (
            <span className="ml-2 text-gray-400">
              ({summary.needing_attention} needing attention)
            </span>
          )}
        </div>
      )}
      {hasReminders && (
        <div>
          <span className="font-medium text-gray-400">Reminders sent: </span>
          <ul className="list-disc list-inside mt-1 space-y-0.5">
            {summary.reminders!.map((r, i) => (
              <li key={i}>
                {r.title} → {r.email} ({r.days_left} days left)
              </li>
            ))}
          </ul>
        </div>
      )}
      {hasDeletions && (
        <div>
          <span className="font-medium text-gray-400">Deleted: </span>
          <ul className="list-disc list-inside mt-1 space-y-0.5">
            {summary.deletions!.map((d, i) => (
              <li key={i}>
                {d.title} (was requested by {d.email})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function JobsPage() {
  const navigate = useNavigate();
  const { isAuthenticated, isAdmin, isLoading: authLoading } = useAuth();
  const { jobRuns, isLoading, error, refetch } = useJobRuns(!!isAdmin);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate({ to: "/login", search: {} });
      return;
    }
    if (!authLoading && isAuthenticated && !isAdmin) {
      navigate({ to: "/", search: { extend: undefined } });
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
            <CardHeader className="flex flex-col items-stretch gap-4 sm:flex-row sm:items-start sm:justify-between">
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
                <div className="overflow-x-auto -mx-4 sm:mx-0">
                  <Table className="min-w-[500px]">
                    <TableHeader>
                      <TableRow className="border-gray-700 hover:bg-transparent">
                        <TableHead className="text-gray-400 w-10 sticky left-0 z-10 bg-scruffy-dark"></TableHead>
                      <TableHead className="text-gray-400">Job Type</TableHead>
                      <TableHead className="text-gray-400">Date</TableHead>
                      <TableHead className="text-gray-400">Status</TableHead>
                      <TableHead className="text-gray-400">Error</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {jobRuns.map((run: JobRun) => (
                      <Fragment key={run.id}>
                        <TableRow
                          className="border-gray-700 hover:bg-gray-800/50"
                        >
                          <TableCell className="w-10 py-2 sticky left-0 z-10 bg-scruffy-darker">
                            {run.summary != null &&
                            (run.summary.reminders?.length ||
                              run.summary.deletions?.length ||
                              run.summary.items_checked !== undefined) ? (
                              <Button
                                variant="ghost"
                                size="icon"
                                className="min-h-[44px] min-w-[44px] text-gray-400 hover:text-white"
                                onClick={() =>
                                  setExpandedId((id) =>
                                    id === run.id ? null : run.id
                                  )
                                }
                                aria-label={
                                  expandedId === run.id
                                    ? "Collapse details"
                                    : "Expand details"
                                }
                              >
                                {expandedId === run.id ? (
                                  <ChevronDown className="h-4 w-4" />
                                ) : (
                                  <ChevronRight className="h-4 w-4" />
                                )}
                              </Button>
                            ) : (
                              <span className="w-8 inline-block" />
                            )}
                          </TableCell>
                          <TableCell className="text-white font-medium">
                            {jobTypeLabel(run.job_type)}
                          </TableCell>
                          <TableCell className="text-gray-300">
                            {formatDate(run.finished_at)}
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={
                                run.success ? "default" : "destructive"
                              }
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
                        {expandedId === run.id && run.summary && (
                          <TableRow
                            key={`${run.id}-detail`}
                            className="border-gray-700 bg-gray-800/30"
                          >
                            <TableCell
                              colSpan={5}
                              className="py-3 pl-12 pr-4 align-top"
                            >
                              <JobRunSummaryContent summary={run.summary} />
                            </TableCell>
                          </TableRow>
                        )}
                      </Fragment>
                    ))}
                  </TableBody>
                </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
