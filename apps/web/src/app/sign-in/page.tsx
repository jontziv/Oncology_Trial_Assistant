"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Beaker, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FieldLabel, Input } from "@/components/ui/field";
import { getSupabaseBrowserClient, isDemoMode } from "@/lib/supabase";

export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);
  const router = useRouter();

  async function signIn(event: React.FormEvent) {
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
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/analyses` },
    });
    setPending(false);
    setMessage(
      error ? error.message : "Check your email for a secure sign-in link.",
    );
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
        <form onSubmit={signIn} className="mt-7">
          {!isDemoMode() ? (
            <div>
              <FieldLabel required htmlFor="email">
                Work email
              </FieldLabel>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>
          ) : (
            <div className="rounded-xl bg-amber-50 p-4 text-sm leading-6 text-amber-950">
              Demo mode uses an isolated local portfolio account.
            </div>
          )}
          <Button type="submit" className="mt-5 w-full" disabled={pending}>
            <Mail size={16} aria-hidden="true" />
            {isDemoMode()
              ? "Enter demo workspace"
              : pending
                ? "Sending..."
                : "Email sign-in link"}
          </Button>
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
