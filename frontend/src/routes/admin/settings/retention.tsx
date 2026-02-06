import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getAdminSettings, updateAdminSettings } from "@/lib/api";

export const Route = createFileRoute("/admin/settings/retention")({
  component: RetentionPage,
});

const inputClass =
  "block w-24 rounded-md border border-gray-600 bg-scruffy-darker px-3 py-2 text-white placeholder-gray-500 focus:border-scruffy-teal focus:ring-1 focus:ring-scruffy-teal";

function RetentionPage() {
  const queryClient = useQueryClient();
  const { data: settings, isLoading } = useQuery({
    queryKey: ["admin-settings"],
    queryFn: getAdminSettings,
  });
  const updateMutation = useMutation({
    mutationFn: updateAdminSettings,
    onSuccess: (data) => {
      queryClient.setQueryData(["admin-settings"], data);
    },
  });

  const [retentionDays, setRetentionDays] = useState<string>("");
  const [reminderDays, setReminderDays] = useState<string>("");
  const [extensionDays, setExtensionDays] = useState<string>("");

  useEffect(() => {
    if (settings?.retention_days != null) {
      setRetentionDays(String(settings.retention_days));
    }
  }, [settings?.retention_days]);

  useEffect(() => {
    if (settings?.reminder_days != null) {
      setReminderDays(String(settings.reminder_days));
    }
  }, [settings?.reminder_days]);

  useEffect(() => {
    if (settings?.extension_days != null) {
      setExtensionDays(String(settings.extension_days));
    }
  }, [settings?.extension_days]);

  const handleSaveRetention = async () => {
    const retention = parseInt(retentionDays, 10);
    const reminder = parseInt(reminderDays, 10);
    if (isNaN(retention) || retention < 1 || retention > 365) return;
    if (isNaN(reminder) || reminder < 1 || reminder > 365) return;
    if (reminder >= retention) return;
    try {
      await updateMutation.mutateAsync({
        retention_days: retention,
        reminder_days: reminder,
      });
    } catch {
      // Error handled by mutation
    }
  };

  const handleSaveExtension = async () => {
    const days = parseInt(extensionDays, 10);
    if (isNaN(days) || days < 1 || days > 365) return;
    try {
      await updateMutation.mutateAsync({ extension_days: days });
    } catch {
      // Error handled by mutation
    }
  };

  const retentionValid =
    !isNaN(parseInt(retentionDays, 10)) &&
    parseInt(retentionDays, 10) >= 1 &&
    parseInt(retentionDays, 10) <= 365;
  const reminderValid =
    !isNaN(parseInt(reminderDays, 10)) &&
    parseInt(reminderDays, 10) >= 1 &&
    parseInt(reminderDays, 10) <= 365 &&
    parseInt(reminderDays, 10) < parseInt(retentionDays, 10);

  return (
    <div className="space-y-8 w-full">
      {/* Base Retention */}
      <Card className="bg-scruffy-dark border-gray-700 w-full">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Base Retention
          </CardTitle>
          <CardDescription>
            How long to keep media before deletion, and when to send reminders.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <div className="plex-spinner" />
          ) : (
            <>
              <div>
                <label
                  htmlFor="retention-days"
                  className="block text-sm font-medium text-gray-300 mb-1"
                >
                  Retention days
                </label>
                <input
                  id="retention-days"
                  type="number"
                  min={1}
                  max={365}
                  value={retentionDays}
                  onChange={(e) => setRetentionDays(e.target.value)}
                  className={inputClass}
                />
                <p className="mt-1 text-xs text-gray-500">
                  Days to keep media before deletion (1–365)
                </p>
              </div>
              <div>
                <label
                  htmlFor="reminder-days"
                  className="block text-sm font-medium text-gray-300 mb-1"
                >
                  Reminder days before deletion
                </label>
                <input
                  id="reminder-days"
                  type="number"
                  min={1}
                  max={365}
                  value={reminderDays}
                  onChange={(e) => setReminderDays(e.target.value)}
                  className={inputClass}
                />
                <p className="mt-1 text-xs text-gray-500">
                  Send reminder when this many days remain (must be less than
                  retention days)
                </p>
              </div>
              {updateMutation.isError && (
                <p className="text-sm text-red-400">
                  {updateMutation.error instanceof Error
                    ? updateMutation.error.message
                    : "Failed to save"}
                </p>
              )}
              <Button
                onClick={handleSaveRetention}
                disabled={
                  updateMutation.isPending ||
                  !retentionValid ||
                  !reminderValid ||
                  (parseInt(retentionDays, 10) === settings?.retention_days &&
                    parseInt(reminderDays, 10) === settings?.reminder_days)
                }
                className="bg-scruffy-teal hover:bg-scruffy-teal/90"
              >
                {updateMutation.isPending ? "Saving..." : "Save Base Retention"}
              </Button>
            </>
          )}
        </CardContent>
      </Card>

      {/* Extension Settings */}
      <Card className="bg-scruffy-dark border-gray-700 w-full">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Extension Settings
          </CardTitle>
          <CardDescription>
            When a user requests "more time" on a media request, how many extra
            days should be added to the retention period?
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoading ? (
            <div className="plex-spinner" />
          ) : (
            <>
              <div>
                <label
                  htmlFor="extension-days"
                  className="block text-sm font-medium text-gray-300 mb-1"
                >
                  Extension days
                </label>
                <input
                  id="extension-days"
                  type="number"
                  min={1}
                  max={365}
                  value={extensionDays}
                  onChange={(e) => setExtensionDays(e.target.value)}
                  className={inputClass}
                />
                <p className="mt-1 text-xs text-gray-500">
                  Days to add when a user requests an extension (1–365)
                </p>
              </div>
              {updateMutation.isError && (
                <p className="text-sm text-red-400">
                  {updateMutation.error instanceof Error
                    ? updateMutation.error.message
                    : "Failed to save"}
                </p>
              )}
              <Button
                onClick={handleSaveExtension}
                disabled={
                  updateMutation.isPending ||
                  extensionDays === "" ||
                  parseInt(extensionDays, 10) === settings?.extension_days
                }
                className="bg-scruffy-teal hover:bg-scruffy-teal/90"
              >
                {updateMutation.isPending ? "Saving..." : "Save Extension"}
              </Button>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
