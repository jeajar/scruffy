import { Link, useRouterState } from "@tanstack/react-router";
import { useState } from "react";
import {
  LogOut,
  Menu,
  X,
  Settings,
  CalendarClock,
  Server,
  Mail,
  Clock,
} from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const navLink =
  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-700 hover:text-white transition-colors";

export function Header() {
  const { user, isAdmin, logout, isLoggingOut } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const routerState = useRouterState();
  const pathname = routerState.location.pathname;

  const closeMobileMenu = () => setMobileMenuOpen(false);

  return (
    <nav className="bg-scruffy-dark border-b border-gray-700">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo - always visible */}
          <Link
            to="/"
            className="flex flex-shrink-0 items-center"
            onClick={closeMobileMenu}
          >
            <img
              className="h-10 w-10"
              src="/static/scruffy.png"
              alt="Scruffy"
            />
            <div className="ml-3 hidden sm:block">
              <span className="text-xl font-bold text-white">Scruffy</span>
              <span className="ml-2 text-sm text-gray-400">the Janitor</span>
            </div>
          </Link>

          {/* Right: Avatar (desktop) or Hamburger (mobile) */}
          <div className="flex items-center gap-2">
            {user && (
              <div className="hidden md:block">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      className="relative h-10 w-10 rounded-full"
                    >
                      <Avatar className="h-8 w-8">
                        {user.thumb ? (
                          <AvatarImage src={user.thumb} alt={user.username} />
                        ) : null}
                        <AvatarFallback className="bg-scruffy-teal">
                          {user.username[0].toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent
                    className="w-56 bg-scruffy-dark border-gray-700"
                    align="end"
                    forceMount
                  >
                    <DropdownMenuLabel className="font-normal">
                      <div className="flex flex-col space-y-1">
                        <p className="text-sm font-medium leading-none text-white">
                          {user.username}
                        </p>
                        <p className="text-xs leading-none text-gray-400">
                          {user.email}
                        </p>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator className="bg-gray-700" />
                    {isAdmin && (
                      <DropdownMenuSub>
                        <DropdownMenuSubTrigger className="text-gray-300 focus:bg-gray-700 focus:text-white cursor-pointer">
                          <Settings className="mr-2 h-4 w-4" />
                          Settings
                        </DropdownMenuSubTrigger>
                        <DropdownMenuSubContent
                          className="bg-scruffy-dark border-gray-700"
                          sideOffset={4}
                        >
                          <DropdownMenuItem asChild>
                            <Link
                              to="/admin/settings/schedules"
                              className="flex cursor-pointer items-center gap-2 text-gray-300 focus:bg-gray-700 focus:text-white"
                            >
                              <CalendarClock className="h-4 w-4" />
                              Schedules
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link
                              to="/admin/settings/services"
                              className="flex cursor-pointer items-center gap-2 text-gray-300 focus:bg-gray-700 focus:text-white"
                            >
                              <Server className="h-4 w-4" />
                              Services
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link
                              to="/admin/settings/notifications"
                              className="flex cursor-pointer items-center gap-2 text-gray-300 focus:bg-gray-700 focus:text-white"
                            >
                              <Mail className="h-4 w-4" />
                              Notifications
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem asChild>
                            <Link
                              to="/admin/settings/retention"
                              className="flex cursor-pointer items-center gap-2 text-gray-300 focus:bg-gray-700 focus:text-white"
                            >
                              <Clock className="h-4 w-4" />
                              Retention
                            </Link>
                          </DropdownMenuItem>
                        </DropdownMenuSubContent>
                      </DropdownMenuSub>
                    )}
                    <DropdownMenuItem
                      onClick={() => logout()}
                      disabled={isLoggingOut}
                      className="cursor-pointer text-gray-300 focus:bg-gray-700 focus:text-white"
                    >
                      <LogOut className="mr-2 h-4 w-4" />
                      <span>{isLoggingOut ? "Signing out..." : "Sign out"}</span>
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            )}

            {/* Mobile: hamburger */}
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden text-gray-400 hover:text-white hover:bg-gray-700"
              aria-label="Open menu"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu className="h-6 w-6" />
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile menu overlay */}
      {mobileMenuOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/60 md:hidden"
            aria-hidden
            onClick={closeMobileMenu}
          />
          <div
            className="fixed inset-y-0 right-0 z-50 w-full max-w-xs bg-scruffy-dark border-l border-gray-700 shadow-xl md:hidden flex flex-col"
            role="dialog"
            aria-label="Main menu"
          >
            <div className="flex h-16 items-center justify-between px-4 border-b border-gray-700">
              <span className="text-lg font-semibold text-white">Menu</span>
              <Button
                variant="ghost"
                size="icon"
                aria-label="Close menu"
                onClick={closeMobileMenu}
                className="text-gray-400 hover:text-white"
              >
                <X className="h-6 w-6" />
              </Button>
            </div>
            <nav className="flex flex-1 flex-col gap-1 p-4">
              {user && (
                <>
                  <div className="my-2 h-px bg-gray-700" />
                  <div className="px-3 py-2">
                    <p className="text-sm font-medium text-white truncate">
                      {user.username}
                    </p>
                    <p className="text-xs text-gray-400 truncate">{user.email}</p>
                  </div>
                  {isAdmin && (
                    <div className="flex flex-col gap-0.5">
                      <span className="px-3 py-1 text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Settings
                      </span>
                      <Link
                        to="/admin/settings/schedules"
                        className={cn(
                          navLink,
                          pathname === "/admin/settings/schedules" && "bg-gray-700 text-white"
                        )}
                        onClick={closeMobileMenu}
                      >
                        <CalendarClock className="h-5 w-5" />
                        Schedules
                      </Link>
                      <Link
                        to="/admin/settings/services"
                        className={cn(
                          navLink,
                          pathname === "/admin/settings/services" && "bg-gray-700 text-white"
                        )}
                        onClick={closeMobileMenu}
                      >
                        <Server className="h-5 w-5" />
                        Services
                      </Link>
                      <Link
                        to="/admin/settings/notifications"
                        className={cn(
                          navLink,
                          pathname === "/admin/settings/notifications" && "bg-gray-700 text-white"
                        )}
                        onClick={closeMobileMenu}
                      >
                        <Mail className="h-5 w-5" />
                        Notifications
                      </Link>
                      <Link
                        to="/admin/settings/retention"
                        className={cn(
                          navLink,
                          pathname === "/admin/settings/retention" && "bg-gray-700 text-white"
                        )}
                        onClick={closeMobileMenu}
                      >
                        <Clock className="h-5 w-5" />
                        Retention
                      </Link>
                    </div>
                  )}
                  <Button
                    variant="ghost"
                    className="justify-start gap-2 text-gray-300 hover:bg-gray-700 hover:text-white"
                    onClick={() => {
                      closeMobileMenu();
                      logout();
                    }}
                    disabled={isLoggingOut}
                  >
                    <LogOut className="h-4 w-4" />
                    {isLoggingOut ? "Signing out..." : "Sign out"}
                  </Button>
                </>
              )}
            </nav>
          </div>
        </>
      )}
    </nav>
  );
}
