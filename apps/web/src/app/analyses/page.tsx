"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowRight, FilePlus2, MapPin, Trash2 } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

export default function AnalysesPage() {
  const queryClient = useQueryClient();
  const analyses = useQuery({
    queryKey: ["analyses"],
    queryFn: api.listAnalyses,
  });
  const remove = useMutation({
    mutationFn: api.deleteAnalysis,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["analyses"] }),
  });

  return (
    <AppShell
      title="Saved analyses"
      description="Review imported trial designs and continue from the latest saved version."
      action={
        <Button asChild>
          <Link href="/analyses/new">
            <FilePlus2 size={16} aria-hidden="true" /> New analysis
          </Link>
        </Button>
      }
    >
      {analyses.isLoading ? (
        <div className="rounded-2xl border border-[var(--line)] bg-white p-8 text-sm text-[var(--muted)]">
          Loading your workspace...
        </div>
      ) : analyses.isError ? (
        <div
          role="alert"
          className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-900"
        >
          {analyses.error.message}
        </div>
      ) : analyses.data?.length ? (
        <div className="overflow-hidden rounded-2xl border border-[var(--line)] bg-white shadow-sm">
          <div className="hidden grid-cols-[1.4fr_0.7fr_0.7fr_auto] gap-4 border-b border-[var(--line)] bg-slate-50 px-6 py-3 text-xs font-bold uppercase tracking-wider text-[var(--muted)] md:grid">
            <span>Analysis</span>
            <span>Study</span>
            <span>Updated</span>
            <span>Actions</span>
          </div>
          {analyses.data.map((analysis) => (
            <article
              key={analysis.id}
              className="grid gap-4 border-b border-[var(--line)] px-6 py-5 last:border-0 md:grid-cols-[1.4fr_0.7fr_0.7fr_auto] md:items-center"
            >
              <div>
                <h2 className="font-semibold">{analysis.title}</h2>
                <p className="mt-1 line-clamp-1 text-sm text-[var(--muted)]">
                  {analysis.trial.title}
                </p>
              </div>
              <div>
                <p className="text-sm font-semibold">{analysis.trial.nct_id}</p>
                <p className="mt-1 flex items-center gap-1 text-xs text-[var(--muted)]">
                  <MapPin size={13} aria-hidden="true" />
                  {
                    (analysis.trial.sites ?? []).filter(
                      (site) => site.country === "United States",
                    ).length
                  }{" "}
                  US sites
                </p>
              </div>
              <p className="text-sm text-[var(--muted)]">
                {formatDate(analysis.updated_at!)}
              </p>
              <div className="flex items-center gap-1">
                <Button asChild variant="ghost">
                  <Link
                    href={
                      analysis.latest_run?.result
                        ? `/analyses/${analysis.id!}/results`
                        : `/analyses/${analysis.id!}/edit`
                    }
                  >
                    {analysis.latest_run?.result ? "Results" : "Protocol"}{" "}
                    <ArrowRight size={15} aria-hidden="true" />
                  </Link>
                </Button>
                <Button
                  variant="danger"
                  aria-label={`Delete ${analysis.title}`}
                  disabled={remove.isPending}
                  onClick={() => {
                    if (window.confirm(`Delete "${analysis.title}"?`)) {
                      remove.mutate(analysis.id!);
                    }
                  }}
                >
                  <Trash2 size={16} aria-hidden="true" />
                </Button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div className="rounded-3xl border border-dashed border-slate-300 bg-white/60 px-6 py-16 text-center">
          <FilePlus2
            className="mx-auto text-[var(--brand)]"
            size={28}
            aria-hidden="true"
          />
          <h2 className="mt-5 text-xl font-semibold">No saved analyses yet</h2>
          <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-[var(--muted)]">
            Import a ClinicalTrials.gov study to create your first structured
            feasibility workspace.
          </p>
          <Button asChild className="mt-6">
            <Link href="/analyses/new">Start an analysis</Link>
          </Button>
        </div>
      )}
    </AppShell>
  );
}
