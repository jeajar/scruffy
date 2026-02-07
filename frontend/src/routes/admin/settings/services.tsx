import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Server } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  getAdminSettings,
  updateAdminSettings,
  testServiceConnection,
  type AdminSettings,
  type AdminSettingsUpdate,
} from "@/lib/api";

export const Route = createFileRoute("/admin/settings/services")({
  component: ServicesPage,
});

const inputClass =
  "block w-full rounded-md border border-gray-600 bg-scruffy-darker px-3 py-2 text-white placeholder-gray-500 focus:border-scruffy-teal focus:ring-1 focus:ring-scruffy-teal";

function ServicesPage() {
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

  const [services, setServices] = useState<AdminSettings["services"] | null>(
    null
  );
  const [testStatus, setTestStatus] = useState<
    Record<string, { status: string; message: string } | null>
  >({});
  const [apiKeys, setApiKeys] = useState<{
    overseerr: string;
    radarr: string;
    sonarr: string;
  }>({ overseerr: "", radarr: "", sonarr: "" });

  useEffect(() => {
    if (settings?.services) {
      setServices(settings.services);
    }
  }, [settings?.services]);

  const handleSaveServices = async () => {
    if (!services) return;
    const body: AdminSettingsUpdate = {
      services: {
        overseerr: {
          url: services.overseerr.url,
          api_key: apiKeys.overseerr || undefined,
        },
        radarr: {
          url: services.radarr.url,
          api_key: apiKeys.radarr || undefined,
        },
        sonarr: {
          url: services.sonarr.url,
          api_key: apiKeys.sonarr || undefined,
        },
      },
    };
    try {
      await updateMutation.mutateAsync(body);
    } catch {
      // Error handled by mutation
    }
  };

  const handleTestService = async (service: "overseerr" | "radarr" | "sonarr") => {
    setTestStatus((s) => ({ ...s, [service]: null }));
    try {
      const result = await testServiceConnection(service);
      setTestStatus((s) => ({
        ...s,
        [service]: { status: result.status, message: result.message },
      }));
    } catch (e) {
      setTestStatus((s) => ({
        ...s,
        [service]: {
          status: "failed",
          message: e instanceof Error ? e.message : "Connection failed",
        },
      }));
    }
  };

  return (
    <Card className="bg-scruffy-dark border-gray-700 w-full">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Server className="h-5 w-5" />
          Services
        </CardTitle>
        <CardDescription>
          Configure Overseerr, Radarr, and Sonarr URLs and API keys.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading || !services ? (
          <div className="plex-spinner" />
        ) : (
          <>
            {(["overseerr", "radarr", "sonarr"] as const).map((svc) => (
              <div key={svc} className="space-y-2">
                <label className="block text-sm font-medium text-gray-300 capitalize">
                  {svc}
                </label>
                <div className="flex gap-2">
                  <input
                    type="url"
                    value={services[svc].url}
                    onChange={(e) =>
                      setServices((s) =>
                        s
                          ? {
                              ...s,
                              [svc]: {
                                ...s[svc],
                                url: e.target.value,
                              },
                            }
                          : null
                      )
                    }
                    placeholder={`${svc} URL`}
                    className={inputClass}
                  />
                  <input
                    id={`${svc}-api-key`}
                    type="password"
                    value={apiKeys[svc]}
                    onChange={(e) =>
                      setApiKeys((k) => ({ ...k, [svc]: e.target.value }))
                    }
                    placeholder={
                      services[svc].api_key_set
                        ? "••••••••"
                        : "API key"
                    }
                    className={inputClass}
                    autoComplete="off"
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleTestService(svc)}
                    className="shrink-0 border-gray-600 text-gray-300 hover:bg-gray-700"
                  >
                    Test
                  </Button>
                </div>
                {testStatus[svc] && (
                  <p
                    className={`text-sm ${
                      testStatus[svc]?.status === "ok"
                        ? "text-green-400"
                        : "text-red-400"
                    }`}
                  >
                    {testStatus[svc]?.message}
                  </p>
                )}
              </div>
            ))}
            {updateMutation.isError && (
              <p className="text-sm text-red-400">
                {updateMutation.error instanceof Error
                  ? updateMutation.error.message
                  : "Failed to save"}
              </p>
            )}
            <Button
              onClick={handleSaveServices}
              disabled={updateMutation.isPending}
              className="bg-scruffy-teal hover:bg-scruffy-teal/90"
            >
              {updateMutation.isPending ? "Saving..." : "Save Services"}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}
