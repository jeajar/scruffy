import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import {
  Film,
  Tv,
  Trash2,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { Layout } from "@/components/layout";
import { Badge } from "@/components/ui/badge";
import { LoadingScreen } from "@/components/ui/loading-screen";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useAuth } from "@/hooks/useAuth";
import { useMedia } from "@/hooks/useMedia";
import { formatDate } from "@/lib/utils";
import type { MediaItem } from "@/lib/api";

export const Route = createFileRoute("/")({
  component: HomePage,
});

function HomePage() {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { media, count, isLoading: mediaLoading, isFetched } = useMedia();

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate({ to: "/login" });
    }
  }, [authLoading, isAuthenticated, navigate]);

  // Show full loading screen during initial load (auth check or first media fetch)
  const isInitialLoading = authLoading || (mediaLoading && !isFetched);

  if (isInitialLoading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return null; // Will redirect
  }

  return (
    <Layout>
      <div className="px-4 sm:px-0">
        {/* Header */}
        <div className="sm:flex sm:items-center">
          <div className="sm:flex-auto">
            <h1 className="text-2xl font-semibold text-white">Media Requests</h1>
            <p className="mt-2 text-sm text-gray-400">
              A list of all available media requests and when Scruffy will clean
              them up.
            </p>
          </div>
          <div className="mt-4 sm:ml-16 sm:mt-0 sm:flex-none">
            <Badge variant="secondary" className="text-sm">
              {count} items
            </Badge>
          </div>
        </div>

        {media.length > 0 ? (
          <>
            {/* Media Table */}
            <div className="mt-8 flow-root">
              <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
                <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
                  <div className="overflow-hidden shadow ring-1 ring-gray-700 sm:rounded-lg">
                    <Table>
                      <TableHeader className="bg-scruffy-dark">
                        <TableRow className="border-gray-700 hover:bg-scruffy-dark">
                          <TableHead className="text-white font-semibold pl-6">
                            Media
                          </TableHead>
                          <TableHead className="text-white font-semibold">
                            Type
                          </TableHead>
                          <TableHead className="text-white font-semibold">
                            Available Since
                          </TableHead>
                          <TableHead className="text-white font-semibold">
                            Days Left
                          </TableHead>
                          <TableHead className="text-white font-semibold">
                            Status
                          </TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody className="bg-scruffy-darker">
                        {media.map((item) => (
                          <MediaRow key={item.request.id} item={item} />
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              </div>
            </div>

            {/* Legend */}
            <div className="mt-8 rounded-lg bg-scruffy-dark p-4 border border-gray-700">
              <h3 className="text-sm font-medium text-white mb-3">
                Status Legend
              </h3>
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="flex items-center">
                  <Badge variant="safe" className="mr-2">
                    Green
                  </Badge>
                  <span className="text-gray-400">Safe - plenty of time</span>
                </div>
                <div className="flex items-center">
                  <Badge variant="warning" className="mr-2">
                    Yellow
                  </Badge>
                  <span className="text-gray-400">
                    Warning - reminder period
                  </span>
                </div>
                <div className="flex items-center">
                  <Badge variant="danger" className="mr-2">
                    Red
                  </Badge>
                  <span className="text-gray-400">Due for deletion</span>
                </div>
              </div>
            </div>
          </>
        ) : (
          /* Empty state */
          <div className="mt-8 text-center">
            <div className="rounded-lg border-2 border-dashed border-gray-700 p-12">
              <Film className="mx-auto h-12 w-12 text-gray-500" />
              <h3 className="mt-4 text-lg font-medium text-white">
                No media requests
              </h3>
              <p className="mt-2 text-sm text-gray-400">
                There are no available media requests to display at this time.
              </p>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}

function MediaRow({ item }: { item: MediaItem }) {
  const { media, request, retention } = item;

  const getDaysLeftVariant = () => {
    if (retention.days_left <= 0) return "danger";
    if (retention.remind) return "warning";
    return "safe";
  };

  const getStatusIcon = () => {
    if (retention.delete) {
      return <Trash2 className="h-4 w-4 text-red-400" />;
    }
    if (retention.remind) {
      return <AlertTriangle className="h-4 w-4 text-yellow-400" />;
    }
    return <CheckCircle2 className="h-4 w-4 text-green-400" />;
  };

  const getStatusText = () => {
    if (retention.delete) return "Scheduled for deletion";
    if (retention.remind) return "Reminder sent";
    return "Safe";
  };

  return (
    <TableRow className="border-gray-700 hover:bg-scruffy-dark transition-colors">
      <TableCell className="pl-6">
        <div className="flex items-center">
          <div className="h-16 w-11 flex-shrink-0">
            {media.poster ? (
              <img
                className="h-16 w-11 rounded object-cover"
                src={media.poster}
                alt={media.title}
              />
            ) : (
              <div className="h-16 w-11 rounded bg-gray-700 flex items-center justify-center">
                {request.type === "movie" ? (
                  <Film className="h-6 w-6 text-gray-500" />
                ) : (
                  <Tv className="h-6 w-6 text-gray-500" />
                )}
              </div>
            )}
          </div>
          <div className="ml-4">
            <div className="font-medium text-white">{media.title}</div>
            {media.seasons && media.seasons.length > 0 && (
              <div className="text-sm text-gray-400">
                {media.seasons.length === 1 ? "Season:" : "Seasons:"}{" "}
                {media.seasons.join(", ")}
              </div>
            )}
          </div>
        </div>
      </TableCell>
      <TableCell>
        <Badge variant={request.type === "movie" ? "movie" : "tv"}>
          {request.type === "movie" ? "Movie" : "TV Show"}
        </Badge>
      </TableCell>
      <TableCell className="text-gray-300">
        {formatDate(media.available_since)}
      </TableCell>
      <TableCell>
        <Badge variant={getDaysLeftVariant()}>
          {retention.days_left <= 0
            ? "Due for deletion"
            : `${retention.days_left} days`}
        </Badge>
      </TableCell>
      <TableCell>
        <span className="inline-flex items-center gap-1.5">
          {getStatusIcon()}
          <span
            className={
              retention.delete
                ? "text-red-400"
                : retention.remind
                  ? "text-yellow-400"
                  : "text-green-400"
            }
          >
            {getStatusText()}
          </span>
        </span>
      </TableCell>
    </TableRow>
  );
}

