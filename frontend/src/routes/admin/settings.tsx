import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Clock, Settings } from "lucide-react";
import { Layout } from "@/components/layout";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import { LoadingScreen } from "@/components/ui/loading-screen";
import { getAdminSettings, updateAdminSettings } from "@/lib/api";

export const Route = createFileRoute("/admin/settings")({
  component: AdminSettingsPage,
});

function AdminSettingsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { isAuthenticated, isAdmin, isLoading: authLoading } = useAuth();
  const { data: settings, isLoading } = useQuery({
    queryKey: ["admin-settings"],
    queryFn: getAdminSettings,
    enabled: !!isAdmin,
  });
  const updateMutation = useMutation({
    mutationFn: updateAdminSettings,
    onSuccess: (data) => {
      queryClient.setQueryData(["admin-settings"], data);
    },
  });

  const [extensionDays, setExtensionDays] = useState<string>("");

  useEffect(() => {
    if (settings?.extension_days != null) {
      setExtensionDays(String(settings.extension_days));
    }
  }, [settings?.extension_days]);

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

  const handleSave = async () => {
    const days = parseInt(extensionDays, 10);
    if (isNaN(days) || days < 1 || days > 365) {
      return;
    }
    try {
      await updateMutation.mutateAsync({ extension_days: days });
    } catch {
      // Error handled by mutation
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
              Settings
            </h1>
            <p className="mt-2 text-sm text-gray-400">
              Configure Scruffy application settings.
            </p>
          </div>
        </div>

        <div className="mt-8">
          <Card className="bg-scruffy-dark border-gray-700 max-w-xl">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Extension Settings
              </CardTitle>
              <CardDescription>
                When a user requests "more time" on a media request, how many
                extra days should be added to the retention period?
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
                      className="block w-24 rounded-md border border-gray-600 bg-scruffy-darker px-3 py-2 text-white placeholder-gray-500 focus:border-scruffy-teal focus:ring-1 focus:ring-scruffy-teal"
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
                    onClick={handleSave}
                    disabled={
                      updateMutation.isPending ||
                      extensionDays === "" ||
                      parseInt(extensionDays, 10) === settings?.extension_days
                    }
                    className="bg-scruffy-teal hover:bg-scruffy-teal/90"
                  >
                    {updateMutation.isPending ? "Saving..." : "Save"}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
