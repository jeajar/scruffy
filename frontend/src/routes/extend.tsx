import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/hooks/useAuth";
import { Footer } from "@/components/layout/Footer";

export const Route = createFileRoute("/extend")({
  component: ExtendPage,
  validateSearch: (search: Record<string, unknown>) => ({
    request_id: search.request_id ? Number(search.request_id) : undefined,
  }),
});

function ExtendPage() {
  const navigate = useNavigate();
  const { request_id } = Route.useSearch();
  const { isAuthenticated, isLoading: authLoading } = useAuth();

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

  // When authenticated, redirect to home with extend param to open the modal
  useEffect(() => {
    if (authLoading || !isAuthenticated || !request_id) return;
    navigate({ to: "/", search: { extend: request_id }, replace: true });
  }, [authLoading, isAuthenticated, request_id, navigate]);

  const handleGoHome = () => {
    navigate({ to: "/", search: { extend: undefined } });
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
    <div className="min-h-full flex flex-col items-center justify-center">
      <div className="plex-spinner" />
      <p className="mt-4 text-gray-400">Redirecting to media requests...</p>
    </div>
  );
}
