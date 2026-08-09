import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Server } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAdminSettings } from "@/hooks/useAdminSettings";
import {
  testServiceConnection,
  type AdminSettings,
  type AdminSettingsUpdate,
} from "@/lib/api";

export const Route = createFileRoute("/admin/settings/services")({
  component: ServicesPage,
});

const SERVICE_LABELS = {
  overseerr: "Seerr",
  radarr: "Radarr",
  sonarr: "Sonarr",
} as const;

function ServicesPage() {
  const { settings, isLoading, update, isUpdating, updateError } =
    useAdminSettings();

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
      await update(body);
    } catch {
      // Error handled by mutation
    }
  };

  const handleTestService = async (
    service: "overseerr" | "radarr" | "sonarr"
  ) => {
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
          Configure Seerr, Radarr, and Sonarr URLs and API keys.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {isLoading || !services ? (
          <div className="plex-spinner" />
        ) : (
          <>
            {(["overseerr", "radarr", "sonarr"] as const).map((svc) => (
              <div key={svc} className="space-y-2">
                <label className="block text-sm font-medium text-gray-300">
                  {SERVICE_LABELS[svc]}
                </label>
                <div className="flex gap-2">
                  <Input
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
                    placeholder={`${SERVICE_LABELS[svc]} URL`}
                  />
                  <Input
                    id={`${svc}-api-key`}
                    type="password"
                    value={apiKeys[svc]}
                    onChange={(e) =>
                      setApiKeys((k) => ({ ...k, [svc]: e.target.value }))
                    }
                    placeholder={
                      services[svc].api_key_set ? "••••••••" : "API key"
                    }
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
            {updateError && (
              <p className="text-sm text-red-400">
                {updateError instanceof Error
                  ? updateError.message
                  : "Failed to save"}
              </p>
            )}
            <Button
              onClick={handleSaveServices}
              disabled={isUpdating}
              className="bg-scruffy-teal hover:bg-scruffy-teal/90"
            >
              {isUpdating ? "Saving..." : "Save Services"}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}
