"use client";

import { Beaker, LogIn, UserPlus } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { FieldLabel, Input } from "@/components/ui/field";
import { getSupabaseBrowserClient, isDemoMode } from "@/lib/supabase";

type AuthMode = "sign-in" | "sign-up";

export default function SignInPage() {
  const [mode, setMode] = useState<AuthMode>("sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (isDemoMode()) return;
    const supabase = getSupabaseBrowserClient();
    void supabase?.auth.getSession().then(({ data }) => {
      if (data.session) router.replace("/analyses");
    });
  }, [router]);

  function destination() {
    const requested = new URLSearchParams(window.location.search).get("next");
    return requested?.startsWith("/analyses") ? requested : "/analyses";
  }

  async function authenticate(event: React.FormEvent) {
    event.preventDefault();
    if (isDemoMode()) {
      router.push("/analyses");
      return;
    }
    const supabase = getSupabaseBrowserClient();
    if (!supabase) {
      setMessage("Supabase authentication is not configured.");
      return;
    }
    setPending(true);
    setMessage("");
    const result =
      mode === "sign-in"
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({
            email,
            password,
            options: {
              emailRedirectTo: `${window.location.origin}${destination()}`,
            },
          });
    setPending(false);
    if (result.error) {
      setMessage(result.error.message);
      return;
    }
    if (result.data.session) {
      router.replace(destination());
      return;
    }
    setMessage("Check your email to confirm your account, then sign in.");
  }

  return (
    <main className="grid min-h-screen place-items-center px-5 py-12">
      <div className="w-full max-w-md rounded-3xl border border-[var(--line)] bg-white p-8 shadow-[0_24px_80px_rgb(29_55_47/12%)]">
        <div className="grid size-12 place-items-center rounded-2xl bg-[var(--brand)] text-white">
          <Beaker size={22} aria-hidden="true" />
        </div>
        <h1 className="mt-7 text-3xl font-semibold tracking-[-0.03em]">
          Sign in to your workspace
        </h1>
        <p className="mt-3 text-sm leading-6 text-[var(--muted)]">
          Access saved analyses and continue reviewing public trial evidence.
        </p>
        <form onSubmit={authenticate} className="mt-7">
          {!isDemoMode() ? (
            <div className="space-y-5">
              <div>
                <FieldLabel required htmlFor="email">
                  Work email
                </FieldLabel>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </div>
              <div>
                <FieldLabel required htmlFor="password">
                  Password
                </FieldLabel>
                <Input
                  id="password"
                  type="password"
                  autoComplete={
                    mode === "sign-in" ? "current-password" : "new-password"
                  }
                  minLength={8}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </div>
            </div>
          ) : (
            <div className="rounded-xl bg-amber-50 p-4 text-sm leading-6 text-amber-950">
              Demo mode uses an isolated local portfolio account.
            </div>
          )}
          <Button type="submit" className="mt-5 w-full" disabled={pending}>
            {mode === "sign-in" ? (
              <LogIn size={16} aria-hidden="true" />
            ) : (
              <UserPlus size={16} aria-hidden="true" />
            )}
            {isDemoMode()
              ? "Enter demo workspace"
              : pending
                ? mode === "sign-in"
                  ? "Signing in..."
                  : "Creating account..."
                : mode === "sign-in"
                  ? "Sign in"
                  : "Create account"}
          </Button>
          {!isDemoMode() ? (
            <button
              type="button"
              className="mt-4 w-full text-sm font-semibold text-[var(--brand)] hover:underline"
              onClick={() => {
                setMode(mode === "sign-in" ? "sign-up" : "sign-in");
                setMessage("");
              }}
            >
              {mode === "sign-in"
                ? "Need an account? Create one"
                : "Already have an account? Sign in"}
            </button>
          ) : null}
          {message ? (
            <p className="mt-4 text-sm text-[var(--muted)]" role="status">
              {message}
            </p>
          ) : null}
        </form>
      </div>
    </main>
  );
}
