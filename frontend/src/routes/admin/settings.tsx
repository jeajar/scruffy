import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Clock, Mail, Server, Settings } from "lucide-react";
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
import {
  getAdminSettings,
  updateAdminSettings,
  testServiceConnection,
  type AdminSettings,
  type AdminSettingsUpdate,
} from "@/lib/api";

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
  const [services, setServices] = useState<AdminSettings["services"] | null>(
    null
  );
  const [email, setEmail] = useState<AdminSettings["notifications"]["email"] | null>(
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
    if (settings?.extension_days != null) {
      setExtensionDays(String(settings.extension_days));
    }
  }, [settings?.extension_days]);

  useEffect(() => {
    if (settings?.services) {
      setServices(settings.services);
    }
  }, [settings?.services]);

  useEffect(() => {
    if (settings?.notifications?.email) {
      setEmail(settings.notifications.email);
    }
  }, [settings?.notifications?.email]);

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

  const handleSaveExtension = async () => {
    const days = parseInt(extensionDays, 10);
    if (isNaN(days) || days < 1 || days > 365) return;
    try {
      await updateMutation.mutateAsync({ extension_days: days });
    } catch {
      // Error handled by mutation
    }
  };

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

  const [smtpPassword, setSmtpPassword] = useState("");

  const handleSaveEmail = async () => {
    if (!email) return;
    const body: AdminSettingsUpdate = {
      notifications: {
        email: {
          enabled: email.enabled,
          smtp_host: email.smtp_host,
          smtp_port: email.smtp_port,
          smtp_username: email.smtp_username || undefined,
          smtp_password: smtpPassword || undefined,
          smtp_from_email: email.smtp_from_email,
          smtp_ssl_tls: email.smtp_ssl_tls,
          smtp_starttls: email.smtp_starttls,
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

  const inputClass =
    "block w-full rounded-md border border-gray-600 bg-scruffy-darker px-3 py-2 text-white placeholder-gray-500 focus:border-scruffy-teal focus:ring-1 focus:ring-scruffy-teal";

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

        <div className="mt-8 space-y-8">
          {/* Services */}
          <Card className="bg-scruffy-dark border-gray-700 max-w-xl">
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

          {/* Notifications */}
          <Card className="bg-scruffy-dark border-gray-700 max-w-xl">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Mail className="h-5 w-5" />
                Notifications
              </CardTitle>
              <CardDescription>
                Configure email notifications for reminders and deletion
                notices.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {isLoading || !email ? (
                <div className="plex-spinner" />
              ) : (
                <>
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="email-enabled"
                      checked={email.enabled}
                      onChange={(ev) =>
                        setEmail((prev) =>
                          prev ? { ...prev, enabled: ev.target.checked } : null
                        )
                      }
                      className="rounded border-gray-600 bg-scruffy-darker"
                    />
                    <label
                      htmlFor="email-enabled"
                      className="text-sm font-medium text-gray-300"
                    >
                      Enable email notifications
                    </label>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        SMTP Host
                      </label>
                      <input
                        type="text"
                        value={email.smtp_host}
                        onChange={(ev) =>
                          setEmail((prev) =>
                            prev ? { ...prev, smtp_host: ev.target.value } : null
                          )
                        }
                        className={inputClass}
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-1">
                        SMTP Port
                      </label>
                      <input
                        type="number"
                        value={email.smtp_port}
                        onChange={(ev) =>
                          setEmail((prev) =>
                            prev
                              ? { ...prev, smtp_port: parseInt(ev.target.value, 10) || 25 }
                              : null
                          )
                        }
                        className={inputClass}
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      SMTP Username
                    </label>
                    <input
                      type="text"
                      value={email.smtp_username || ""}
                      onChange={(ev) =>
                        setEmail((prev) =>
                          prev ? { ...prev, smtp_username: ev.target.value || null } : null
                        )
                      }
                      className={inputClass}
                      autoComplete="off"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      SMTP Password
                    </label>
                    <input
                      id="smtp-password"
                      type="password"
                      value={smtpPassword}
                      onChange={(e) => setSmtpPassword(e.target.value)}
                      placeholder={
                        email.smtp_password_set ? "••••••••" : "Leave blank to keep"
                      }
                      className={inputClass}
                      autoComplete="new-password"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-1">
                      From Email
                    </label>
                    <input
                      type="email"
                      value={email.smtp_from_email}
                      onChange={(ev) =>
                        setEmail((prev) =>
                          prev ? { ...prev, smtp_from_email: ev.target.value } : null
                        )
                      }
                      className={inputClass}
                    />
                  </div>
                  <div className="flex gap-4">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="smtp-ssl"
                        checked={email.smtp_ssl_tls}
                        onChange={(ev) =>
                          setEmail((prev) =>
                            prev
                              ? { ...prev, smtp_ssl_tls: ev.target.checked }
                              : null
                          )
                        }
                        className="rounded border-gray-600 bg-scruffy-darker"
                      />
                      <label
                        htmlFor="smtp-ssl"
                        className="text-sm text-gray-300"
                      >
                        SSL/TLS
                      </label>
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="smtp-starttls"
                        checked={email.smtp_starttls}
                        onChange={(ev) =>
                          setEmail((prev) =>
                            prev
                              ? { ...prev, smtp_starttls: ev.target.checked }
                              : null
                          )
                        }
                        className="rounded border-gray-600 bg-scruffy-darker"
                      />
                      <label
                        htmlFor="smtp-starttls"
                        className="text-sm text-gray-300"
                      >
                        STARTTLS
                      </label>
                    </div>
                  </div>
                  <Button
                    onClick={handleSaveEmail}
                    disabled={updateMutation.isPending}
                    className="bg-scruffy-teal hover:bg-scruffy-teal/90"
                  >
                    {updateMutation.isPending ? "Saving..." : "Save Email"}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>

          {/* Extension Settings */}
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
                    onClick={handleSaveExtension}
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
