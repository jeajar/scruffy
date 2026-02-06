import { createFileRoute, Navigate } from "@tanstack/react-router";

export const Route = createFileRoute("/admin/schedules")({
  component: AdminSchedulesRedirect,
});

function AdminSchedulesRedirect() {
  return <Navigate to="/admin/settings/schedules" />;
}
