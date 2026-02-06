import { useState } from "react";
import { Film, Tv } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { requestExtend, type MediaItem } from "@/lib/api";
import { formatDate } from "@/lib/utils";

interface RequestExtensionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  requestId: number;
  item?: MediaItem;
  extensionDays?: number;
  onSuccess?: () => void;
}

export function RequestExtensionModal({
  open,
  onOpenChange,
  requestId,
  item,
  extensionDays = 7,
  onSuccess,
}: RequestExtensionModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await requestExtend(requestId);
      onSuccess?.();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to request extension");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen && !isLoading) {
      setError(null);
    }
    onOpenChange(nextOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent showClose={!isLoading}>
        <DialogHeader>
          <DialogTitle>Request Extension</DialogTitle>
          <DialogDescription>
            {item ? (
              <>
                Request more time for this media. Scruffy will hold off on
                deletion.
              </>
            ) : (
              <>Request extension for this media.</>
            )}
          </DialogDescription>
        </DialogHeader>

        {item && (
          <div className="flex gap-4 py-2">
            <div className="h-20 w-14 flex-shrink-0">
              {item.media.poster ? (
                <img
                  className="h-20 w-14 rounded object-cover"
                  src={item.media.poster}
                  alt={item.media.title}
                />
              ) : (
                <div className="h-20 w-14 rounded bg-gray-700 flex items-center justify-center">
                  {item.request.type === "movie" ? (
                    <Film className="h-6 w-6 text-gray-500" />
                  ) : (
                    <Tv className="h-6 w-6 text-gray-500" />
                  )}
                </div>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-white truncate">
                {item.media.title}
              </div>
              {item.media.seasons && item.media.seasons.length > 0 && (
                <div className="text-sm text-gray-400">
                  {item.media.seasons.length === 1 ? "Season:" : "Seasons:"}{" "}
                  {item.media.seasons.join(", ")}
                </div>
              )}
              <div className="flex items-center gap-2 mt-1">
                <Badge
                  variant={item.request.type === "movie" ? "movie" : "tv"}
                  className="text-xs"
                >
                  {item.request.type === "movie" ? "Movie" : "TV Show"}
                </Badge>
                <Badge variant={item.retention.days_left <= 0 ? "danger" : "warning"}>
                  {item.retention.days_left <= 0
                    ? "Due for deletion"
                    : `${item.retention.days_left} days left`}
                </Badge>
              </div>
              <div className="mt-2 text-sm text-gray-400">
                After extension: new deletion date{" "}
                <span className="font-medium text-green-400">
                  {formatDate(
                    (() => {
                      const d = new Date();
                      d.setDate(d.getDate() + item.retention.days_left + extensionDays);
                      return d.toISOString();
                    })()
                  )}
                </span>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-md bg-red-900/30 border border-red-800 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="ghost"
            onClick={() => handleOpenChange(false)}
            disabled={isLoading}
            className="text-gray-300 hover:text-white"
          >
            Cancel
          </Button>
          <Button
            variant="plex"
            onClick={handleConfirm}
            disabled={isLoading}
            className="min-w-[100px]"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="plex-spinner h-4 w-4" />
                Requesting...
              </span>
            ) : (
              "OK"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
