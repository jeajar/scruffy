import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
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
import { useAuth } from "@/hooks/useAuth";
import { requestExtend } from "@/lib/api";
import { Footer } from "@/components/layout/Footer";

export const Route = createFileRoute("/extend")({
  component: ExtendPage,
  validateSearch: (search: Record<string, unknown>) => ({
    request_id: search.request_id ? Number(search.request_id) : undefined,
  }),
});

type ExtendState = "loading" | "success" | "error" | "extending";

function ExtendPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { request_id } = Route.useSearch();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [state, setState] = useState<ExtendState>("loading");
  const [error, setError] = useState<string | null>(null);

  const extendMutation = useMutation({
    mutationFn: (id: number) => requestExtend(id),
    onSuccess: () => {
      setState("success");
      queryClient.invalidateQueries({ queryKey: ["media"] });
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Failed to request extension");
      setState("error");
    },
  });

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated && request_id) {
      const returnUrl = `/extend?request_id=${request_id}`;
      navigate({
        to: "/login",
        search: { return_url: returnUrl },
        replace: true,
      });
    }
  }, [authLoading, isAuthenticated, request_id, navigate]);

  // Process extension when authenticated
  useEffect(() => {
    if (authLoading || !isAuthenticated || !request_id) return;
    if (state !== "loading") return;

    setState("extending");
    extendMutation.mutate(request_id);
  }, [authLoading, isAuthenticated, request_id, state]);

  const handleGoHome = () => {
    navigate({ to: "/" });
  };

  if (authLoading || (!isAuthenticated && request_id)) {
    return (
      <div className="min-h-full flex flex-col items-center justify-center">
        <div className="plex-spinner" />
        <p className="mt-4 text-gray-400">Redirecting to sign in...</p>
      </div>
    );
  }

  if (!request_id) {
    return (
      <div className="min-h-full flex flex-col">
        <div className="flex flex-1 flex-col justify-center py-12 sm:px-6 lg:px-8">
          <div className="sm:mx-auto sm:w-full sm:max-w-md">
            <Card className="bg-scruffy-dark border-gray-700">
              <CardHeader>
                <CardTitle className="text-center text-white">
                  Invalid Link
                </CardTitle>
                <CardDescription className="text-center">
                  This extension link is invalid. Please use the link from your
                  reminder email.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  variant="plex"
                  className="w-full"
                  onClick={handleGoHome}
                >
                  Go to Media Requests
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

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
            Request Extension
          </h2>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <Card className="bg-scruffy-dark border-gray-700">
            <CardHeader>
              <CardTitle className="text-center text-white">
                {state === "extending" && "Processing..."}
                {state === "success" && "Extension Granted"}
                {state === "error" && "Unable to Extend"}
              </CardTitle>
              <CardDescription className="text-center">
                {state === "extending" &&
                  "Requesting more time for this media..."}
                {state === "success" &&
                  "You've been granted more time. Scruffy will hold off on deletion."}
                {state === "error" && error}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {state === "extending" && (
                <div className="flex justify-center">
                  <div className="plex-spinner" />
                </div>
              )}

              {state === "success" && (
                <div className="text-center space-y-4">
                  <div className="flex justify-center">
                    <CheckCircle2 className="w-12 h-12 text-green-500" />
                  </div>
                  <Button
                    variant="plex"
                    className="w-full"
                    onClick={handleGoHome}
                  >
                    View Media Requests
                  </Button>
                </div>
              )}

              {state === "error" && (
                <div className="text-center space-y-4">
                  <div className="flex justify-center">
                    <AlertCircle className="w-12 h-12 text-red-500" />
                  </div>
                  <Button
                    variant="plex"
                    className="w-full"
                    onClick={handleGoHome}
                  >
                    Go to Media Requests
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
      <Footer />
    </div>
  );
}
