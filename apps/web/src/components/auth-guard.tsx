"use client";

import type { Session } from "@supabase/supabase-js";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { getSupabaseBrowserClient, isDemoMode } from "@/lib/supabase";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null | undefined>(
    isDemoMode() ? null : undefined,
  );
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (isDemoMode()) return;

    const supabase = getSupabaseBrowserClient();
    if (!supabase) {
      router.replace("/sign-in");
      return;
    }

    let active = true;
    void supabase.auth.getSession().then(({ data }) => {
      if (!active) return;
      setSession(data.session);
      if (!data.session) {
        router.replace(`/sign-in?next=${encodeURIComponent(pathname)}`);
      }
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (!active) return;
      setSession(nextSession);
      if (!nextSession) {
        router.replace("/sign-in");
      }
    });

    return () => {
      active = false;
      subscription.unsubscribe();
    };
  }, [pathname, router]);

  if (isDemoMode()) return children;

  if (session === undefined || session === null) {
    return (
      <main className="grid min-h-screen place-items-center px-5">
        <p className="text-sm text-[var(--muted)]">Checking your session...</p>
      </main>
    );
  }

  return children;
}
