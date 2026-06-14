"use client";

import Link from "next/link";
import { Beaker, FileText, LogOut, Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { Disclaimer } from "@/components/disclaimer";
import { Button } from "@/components/ui/button";
import { getSupabaseBrowserClient, isDemoMode } from "@/lib/supabase";

export function AppShell({
  children,
  title,
  description,
  action,
}: {
  children: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  const router = useRouter();

  async function signOut() {
    await getSupabaseBrowserClient()?.auth.signOut();
    router.push("/sign-in");
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--line)] bg-white/85 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
          <Link href="/" className="flex items-center gap-3">
            <span className="grid size-9 place-items-center rounded-xl bg-[var(--brand)] text-white">
              <Beaker size={18} aria-hidden="true" />
            </span>
            <span>
              <span className="block text-sm font-bold">Oncology Trial</span>
              <span className="block text-xs text-[var(--muted)]">
                Feasibility Copilot
              </span>
            </span>
          </Link>
          <nav className="flex items-center gap-1" aria-label="Primary">
            <Button asChild variant="ghost">
              <Link href="/analyses">
                <FileText size={16} aria-hidden="true" /> Analyses
              </Link>
            </Button>
            <Button asChild variant="ghost" className="hidden sm:inline-flex">
              <Link href="/analyses/new">
                <Plus size={16} aria-hidden="true" /> New
              </Link>
            </Button>
            {!isDemoMode() ? (
              <Button variant="ghost" onClick={signOut}>
                <LogOut size={16} aria-hidden="true" /> Sign out
              </Button>
            ) : (
              <span className="ml-2 rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-900">
                Demo mode
              </span>
            )}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-5 py-8 lg:px-8">
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div>
            <h1 className="text-3xl font-semibold tracking-[-0.03em]">
              {title}
            </h1>
            {description ? (
              <p className="mt-2 max-w-3xl text-sm leading-6 text-[var(--muted)]">
                {description}
              </p>
            ) : null}
          </div>
          {action}
        </div>
        <div className="mt-7">
          <Disclaimer />
        </div>
        <div className="mt-8">{children}</div>
      </main>
    </div>
  );
}
