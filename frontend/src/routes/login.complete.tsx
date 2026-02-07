import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Footer } from "@/components/layout/Footer";

export const Route = createFileRoute("/login/complete")({
  component: LoginCompletePage,
});

const REDIRECT_DELAY_MS = 1500;

function LoginCompletePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showFallbackLink, setShowFallbackLink] = useState(false);
  const isPopup = typeof window !== "undefined" && !!window.opener;

  useEffect(() => {
    if (isPopup) {
      window.close();
      return;
    }

    let cancelled = false;

    const goHome = () => {
      if (cancelled) return;
      navigate({ to: "/", search: { extend: undefined }, replace: true });
    };

    const run = async () => {
      try {
        await queryClient.refetchQueries({ queryKey: ["auth"] });
      } finally {
        if (!cancelled) goHome();
      }
    };

    run();

    const timeout = window.setTimeout(() => {
      if (!cancelled) setShowFallbackLink(true);
    }, REDIRECT_DELAY_MS);

    return () => {
      cancelled = true;
      window.clearTimeout(timeout);
    };
  }, [navigate, queryClient, isPopup]);

  const handleContinue = () => {
    navigate({ to: "/", search: { extend: undefined }, replace: true });
  };

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
            Signed in
          </h2>
        </div>
        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md text-center">
          <div className="flex justify-center">
            <CheckCircle2 className="w-12 h-12 text-green-500" />
          </div>
          <p className="mt-4 text-gray-300">
            {isPopup
              ? "You can close this window."
              : "Redirecting..."}
          </p>
          {showFallbackLink && !isPopup ? (
            <Button variant="plex" onClick={handleContinue}>
              Continue to app
            </Button>
          ) : null}
        </div>
      </div>
      <Footer />
    </div>
  );
}
