import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Film,
  Tv,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  MoreVertical,
  Clock,
  ExternalLink,
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
import { type MediaItem } from "@/lib/api";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { RequestExtensionModal } from "@/components/RequestExtensionModal";

export const Route = createFileRoute("/")({
  component: HomePage,
  validateSearch: (search: Record<string, unknown>) => ({
    extend: search.extend ? Number(search.extend) : undefined,
  }),
});

function HomePage() {
  const navigate = useNavigate();
  const { extend } = Route.useSearch();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { media, count, overseerrUrl, extensionDays, isLoading: mediaLoading, isFetched, refetch } = useMedia();
  const [extendModalRequestId, setExtendModalRequestId] = useState<number | null>(null);
  const [extendModalItem, setExtendModalItem] = useState<MediaItem | undefined>(undefined);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate({ to: "/login", search: {} });
    }
  }, [authLoading, isAuthenticated, navigate]);

  // Open extension modal when extend search param is present (e.g. from email link after login)
  useEffect(() => {
    if (extend != null && !isNaN(extend) && isAuthenticated) {
      const item = media.find(
        (m) => m.request.id === extend || m.request.request_id === extend
      );
      setExtendModalRequestId(extend);
      setExtendModalItem(item);
    }
  }, [extend, isAuthenticated, media]);

  const handleExtendModalOpenChange = (open: boolean) => {
    if (!open) {
      setExtendModalRequestId(null);
      setExtendModalItem(undefined);
      if (extend != null) {
        navigate({ to: "/", search: { extend: undefined } });
      }
    }
  };

  const handleOpenExtendModal = (item: MediaItem) => {
    const requestId = item.request.id ?? item.request.request_id;
    setExtendModalRequestId(requestId);
    setExtendModalItem(item);
  };

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
                          <TableHead className="text-white font-semibold w-12">
                            <span className="sr-only">Actions</span>
                          </TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody className="bg-scruffy-darker">
                        {media.map((item) => (
                          <MediaRow
                            key={`${item.request.id ?? item.request.request_id}-${item.media.id}`}
                            item={item}
                            overseerrUrl={overseerrUrl}
                            onOpenExtendModal={handleOpenExtendModal}
                          />
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

      <RequestExtensionModal
        open={extendModalRequestId != null}
        onOpenChange={handleExtendModalOpenChange}
        requestId={extendModalRequestId ?? 0}
        item={extendModalItem}
        extensionDays={extensionDays}
        onSuccess={refetch}
      />
      </div>
    </Layout>
  );
}

function MediaRowActions({
  item,
  overseerrUrl,
  mediaType,
  tmdbId,
  isExtended,
  onRequestExtension,
}: {
  item: MediaItem;
  overseerrUrl: string | null;
  mediaType: string;
  tmdbId: number | null | undefined;
  isExtended: boolean;
  onRequestExtension?: (item: MediaItem) => void;
}) {
  const handleRequestExtension = () => {
    if (isExtended) return;
    onRequestExtension?.(item);
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-gray-400 hover:text-white"
        >
          <MoreVertical className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="bg-scruffy-dark border-gray-700">
        {overseerrUrl && tmdbId && (
          <DropdownMenuItem
            asChild
            className="text-gray-300 focus:bg-gray-700 focus:text-white"
          >
            <a
              href={`${overseerrUrl}/${mediaType}/${tmdbId}`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Open in Overseerr
            </a>
          </DropdownMenuItem>
        )}
        <DropdownMenuItem
          onClick={handleRequestExtension}
          disabled={isExtended}
          className="text-gray-300 focus:bg-gray-700 focus:text-white"
        >
          <Clock className="h-4 w-4 mr-2" />
          {isExtended ? "Already extended" : "Request extension"}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function MediaRow({
  item,
  overseerrUrl,
  onOpenExtendModal,
}: {
  item: MediaItem;
  overseerrUrl: string | null;
  onOpenExtendModal?: (item: MediaItem) => void;
}) {
  const { media, request, retention } = item;
  const isExtended = request.extended ?? retention.extended ?? false;

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
        <div className="flex items-center gap-2">
          <Badge variant={request.type === "movie" ? "movie" : "tv"}>
            {request.type === "movie" ? "Movie" : "TV Show"}
          </Badge>
          {isExtended && (
            <Badge variant="secondary" className="gap-1">
              <Clock className="h-3 w-3" />
              Extended
            </Badge>
          )}
        </div>
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
      <TableCell className="w-12">
        <MediaRowActions
          item={item}
          overseerrUrl={overseerrUrl}
          mediaType={request.type}
          tmdbId={request.tmdb_id}
          isExtended={isExtended}
          onRequestExtension={onOpenExtendModal}
        />
      </TableCell>
    </TableRow>
  );
}

