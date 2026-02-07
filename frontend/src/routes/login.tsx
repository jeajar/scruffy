import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState, useEffect, useCallback, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { createPin, checkPin, type PinResponse } from "@/lib/api";
import { Footer } from "@/components/layout/Footer";

export const Route = createFileRoute("/login")({
  component: LoginPage,
  validateSearch: (search: Record<string, unknown>): { return_url?: string } => ({
    return_url: typeof search.return_url === "string" ? search.return_url : undefined,
  }),
});

type LoginState = "idle" | "waiting" | "success" | "error";

function LoginPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { return_url } = Route.useSearch();
  const [state, setState] = useState<LoginState>("idle");
  const [pinData, setPinData] = useState<PinResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pollCount, setPollCount] = useState(0);
  const authPopupRef = useRef<Window | null>(null);

  const MAX_POLLS = 120; // 2 minutes at 1 second intervals

  const createPinMutation = useMutation({
    mutationFn: createPin,
    onSuccess: (data) => {
      setPinData(data);
      setState("waiting");
      // Open Plex auth in new window (keep ref so we can close it after sign-in)
      const isNarrow = window.innerWidth < 640;
      const popupFeatures = isNarrow
        ? `width=${window.innerWidth},height=${window.innerHeight},left=0,top=0`
        : "width=600,height=700";
      authPopupRef.current = window.open(
        data.auth_url,
        "_blank",
        popupFeatures
      );
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Failed to create PIN");
      setState("error");
    },
  });

  const handleLogin = () => {
    setError(null);
    setPollCount(0);
    createPinMutation.mutate();
  };

  const handleCancel = useCallback(() => {
    if (authPopupRef.current && !authPopupRef.current.closed) {
      authPopupRef.current.close();
      authPopupRef.current = null;
    }
    setState("idle");
    setPinData(null);
    setPollCount(0);
  }, []);

  // Poll for PIN claim
  useEffect(() => {
    if (state !== "waiting" || !pinData) return;

    const pollInterval = setInterval(async () => {
      setPollCount((prev) => {
        if (prev >= MAX_POLLS) {
          clearInterval(pollInterval);
          if (authPopupRef.current && !authPopupRef.current.closed) {
            authPopupRef.current.close();
            authPopupRef.current = null;
          }
          setError("Authentication timed out. Please try again.");
          setState("error");
          return prev;
        }
        return prev + 1;
      });

      try {
        const result = await checkPin(pinData.pin_id);

        if (result.authenticated && result.session_token) {
          clearInterval(pollInterval);

          // Close the Plex sign-in popup (it stays on Plex's "Thanks!" page; we close from opener)
          if (authPopupRef.current && !authPopupRef.current.closed) {
            authPopupRef.current.close();
            authPopupRef.current = null;
          }

          // Set the session cookie
          const secure = window.location.protocol === "https:" ? "; secure" : "";
          document.cookie = `${result.cookie_name}=${result.session_token}; max-age=${result.max_age}; path=/${secure}; samesite=lax`;

          setState("success");

          // Invalidate auth query and redirect
          await queryClient.invalidateQueries({ queryKey: ["auth"] });

          setTimeout(() => {
            // Rewrite /extend?request_id=X to /?extend=X so user lands on home with modal
            const extendMatch = return_url?.match(/^\/extend\?request_id=(\d+)$/);
            if (extendMatch) {
              const requestId = Number(extendMatch[1]);
              navigate({ to: "/", search: { extend: requestId } });
            } else {
              navigate({ to: return_url || "/" });
            }
          }, 1000);
        } else if (!result.authenticated && result.error) {
          clearInterval(pollInterval);
          if (authPopupRef.current && !authPopupRef.current.closed) {
            authPopupRef.current.close();
            authPopupRef.current = null;
          }
          const message =
            result.error === "not_imported"
              ? "Your Plex account is not imported on this server. Ask an admin to import users from Plex in Overseerr."
              : result.error;
          setError(message);
          setState("error");
        }
      } catch {
        // Ignore poll errors, will retry
      }
    }, 1000);

    return () => clearInterval(pollInterval);
  }, [state, pinData, navigate, queryClient, return_url]);

  return (
    <div className="min-h-full flex flex-col">
      <div className="flex flex-1 flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <img
            className="mx-auto h-24 w-auto"
            src="/static/scruffy.png"
            alt="Scruffy"
          />
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-white">
            Scruffy
          </h2>
          <p className="mt-2 text-center text-sm text-gray-400">
            Media Retention Manager
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <Card className="bg-scruffy-dark border-gray-700">
            <CardHeader>
              <CardTitle className="text-center text-white">Sign In</CardTitle>
              <CardDescription className="text-center">
                Sign in with your Plex account to view media requests and
                deletion schedules.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {state === "idle" && (
                <>
                  <Button
                    variant="plex"
                    className="w-full"
                    size="lg"
                    onClick={handleLogin}
                    disabled={createPinMutation.isPending}
                  >
                    <svg
                      className="w-5 h-5 mr-2"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                    >
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
                    </svg>
                    {createPinMutation.isPending
                      ? "Connecting..."
                      : "Sign in with Plex"}
                  </Button>

                  <div className="relative">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-600" />
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="bg-scruffy-dark px-2 text-gray-400">
                        How it works
                      </span>
                    </div>
                  </div>

                  <div className="text-sm text-gray-400 space-y-2">
                    <p>1. Click the button above</p>
                    <p>2. Sign in with your Plex account in the popup</p>
                    <p>3. You'll be redirected back automatically</p>
                  </div>
                </>
              )}

              {state === "waiting" && (
                <div className="text-center space-y-4">
                  <div className="flex justify-center">
                    <div className="plex-spinner" />
                  </div>
                  <p className="text-gray-300">
                    Waiting for Plex authentication...
                  </p>
                  <p className="text-sm text-gray-500">
                    Complete the sign-in in the Plex window that opened.
                    {pollCount > 0 && (
                      <span className="block mt-1">
                        ({pollCount}s elapsed)
                      </span>
                    )}
                  </p>
                  <Button
                    variant="ghost"
                    onClick={handleCancel}
                    className="text-gray-400 hover:text-white"
                  >
                    Cancel
                  </Button>
                </div>
              )}

              {state === "success" && (
                <div className="text-center space-y-4">
                  <div className="flex justify-center">
                    <CheckCircle2 className="w-12 h-12 text-green-500" />
                  </div>
                  <p className="text-gray-300">Authentication successful!</p>
                  <p className="text-sm text-gray-500">Redirecting...</p>
                </div>
              )}

              {state === "error" && (
                <div className="text-center space-y-4">
                  <div className="flex justify-center">
                    <AlertCircle className="w-12 h-12 text-red-500" />
                  </div>
                  <p className="text-gray-300">{error || "Authentication failed"}</p>
                  <Button
                    variant="plex"
                    onClick={() => {
                      setState("idle");
                      setError(null);
                    }}
                  >
                    Try again
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <p className="mt-6 text-center text-xs text-gray-500">
            <em>"I've never seen him so proud."</em>
          </p>
        </div>
      </div>
      <Footer />
    </div>
  );
}
