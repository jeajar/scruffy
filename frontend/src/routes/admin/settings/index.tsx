import { createFileRoute, Navigate } from "@tanstack/react-router";

export const Route = createFileRoute("/admin/settings/")({
  component: SettingsIndexRedirect,
});

function SettingsIndexRedirect() {
  return <Navigate to="/admin/settings/schedules" />;
}
