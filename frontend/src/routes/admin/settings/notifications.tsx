import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Mail } from "lucide-react";
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
import type { AdminSettingsUpdate } from "@/lib/api";

export const Route = createFileRoute("/admin/settings/notifications")({
  component: NotificationsPage,
});

function NotificationsPage() {
  const { settings, isLoading, update, isUpdating } = useAdminSettings();

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
      await update(body);
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
                <Input
                  type="text"
                  value={email.smtp_host}
                  onChange={(ev) =>
                    setEmail((prev) =>
                      prev ? { ...prev, smtp_host: ev.target.value } : null
                    )
                  }
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  SMTP Port
                </label>
                <Input
                  type="number"
                  value={email.smtp_port}
                  onChange={(ev) =>
                    setEmail((prev) =>
                      prev
                        ? {
                            ...prev,
                            smtp_port: parseInt(ev.target.value, 10) || 25,
                          }
                        : null
                    )
                  }
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                SMTP Username
              </label>
              <Input
                type="text"
                value={email.smtp_username || ""}
                onChange={(ev) =>
                  setEmail((prev) =>
                    prev
                      ? { ...prev, smtp_username: ev.target.value || null }
                      : null
                  )
                }
                autoComplete="off"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                SMTP Password
              </label>
              <Input
                id="smtp-password"
                type="password"
                value={smtpPassword}
                onChange={(e) => setSmtpPassword(e.target.value)}
                placeholder={
                  email.smtp_password_set ? "••••••••" : "Leave blank to keep"
                }
                autoComplete="new-password"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                From Email
              </label>
              <Input
                type="email"
                value={email.smtp_from_email}
                onChange={(ev) =>
                  setEmail((prev) =>
                    prev ? { ...prev, smtp_from_email: ev.target.value } : null
                  )
                }
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
                      prev ? { ...prev, smtp_ssl_tls: ev.target.checked } : null
                    )
                  }
                  className="rounded border-gray-600 bg-scruffy-darker"
                />
                <label htmlFor="smtp-ssl" className="text-sm text-gray-300">
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
              disabled={isUpdating}
              className="bg-scruffy-teal hover:bg-scruffy-teal/90"
            >
              {isUpdating ? "Saving..." : "Save Email"}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  );
}
