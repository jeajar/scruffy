import { createRootRoute, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/router-devtools";

export const Route = createRootRoute({
  component: () => (
    <div className="min-h-full">
      <Outlet />
      {import.meta.env.DEV && <TanStackRouterDevtools />}
    </div>
  ),
});
