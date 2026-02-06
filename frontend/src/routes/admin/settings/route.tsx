import { createFileRoute, Link, Outlet, useNavigate, useRouterState } from "@tanstack/react-router";
import { useEffect } from "react";
import { Settings, Server, Mail, Clock, CalendarClock } from "lucide-react";
import { Layout } from "@/components/layout";
import { useAuth } from "@/hooks/useAuth";
import { LoadingScreen } from "@/components/ui/loading-screen";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/admin/settings")({
  component: SettingsLayoutPage,
});

const navItems = [
  { to: "/admin/settings/schedules", label: "Schedules", icon: CalendarClock },
  { to: "/admin/settings/services", label: "Services", icon: Server },
  { to: "/admin/settings/notifications", label: "Notifications", icon: Mail },
  { to: "/admin/settings/retention", label: "Retention", icon: Clock },
] as const;

function SettingsLayoutPage() {
  const navigate = useNavigate();
  const { isAuthenticated, isAdmin, isLoading: authLoading } = useAuth();
  const routerState = useRouterState();
  const pathname = routerState.location.pathname;

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate({ to: "/login", search: {} });
      return;
    }
    if (!authLoading && isAuthenticated && !isAdmin) {
      navigate({ to: "/", search: { extend: undefined } });
      return;
    }
  }, [authLoading, isAuthenticated, isAdmin, navigate]);

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

        <div className="mt-8 flex flex-col sm:flex-row gap-8">
          <nav className="flex sm:flex-col gap-1 min-w-[200px]">
            {navItems.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className={cn(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  pathname === to
                    ? "bg-gray-700 text-white"
                    : "text-gray-300 hover:bg-gray-700/50 hover:text-white"
                )}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            ))}
          </nav>
          <main className="flex-1 min-w-0">
            <Outlet />
          </main>
        </div>
      </div>
    </Layout>
  );
}
