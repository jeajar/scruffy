import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Mail } from "lucide-react";
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
  type AdminSettingsUpdate,
} from "@/lib/api";

export const Route = createFileRoute("/admin/settings/notifications")({
  component: NotificationsPage,
});

const inputClass =
  "block w-full rounded-md border border-gray-600 bg-scruffy-darker px-3 py-2 text-white placeholder-gray-500 focus:border-scruffy-teal focus:ring-1 focus:ring-scruffy-teal";

function NotificationsPage() {
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

  const [email, setEmail] = useState<
    NonNullable<typeof settings>["notifications"]["email"] | null
  >(null);
  const [smtpPassword, setSmtpPassword] = useState("");

  useEffect(() => {
    if (settings?.notifications?.email) {
      setEmail(settings.notifications.email);
    }
  }, [settings?.notifications?.email]);

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

  return (
    <Card className="bg-scruffy-dark border-gray-700 w-full">
      <CardHeader>
        <CardTitle className="text-white flex items-center gap-2">
          <Mail className="h-5 w-5" />
          Notifications
        </CardTitle>
        <CardDescription>
          Configure email notifications for reminders and deletion notices.
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
  );
}
