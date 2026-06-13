"use client";

import type { TrialDraft, TrialSearchResult } from "@oncology/api-client";
import { useMutation } from "@tanstack/react-query";
import { ArrowRight, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AnalysisForm } from "@/components/analysis-form";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { FieldLabel, Input } from "@/components/ui/field";
import { api } from "@/lib/api";

export default function NewAnalysisPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<TrialSearchResult[]>([]);
  const [trial, setTrial] = useState<TrialDraft | null>(null);
  const [error, setError] = useState("");
  const router = useRouter();

  const lookup = useMutation({
    mutationFn: async () => {
      setError("");
      const normalized = query.trim();
      if (/^NCT\d{8}$/i.test(normalized)) {
        return {
          trial: await api.getTrial(normalized.toUpperCase()),
          items: [],
        };
      }
      const response = await api.searchTrials(normalized);
      return { trial: null, items: response.items };
    },
    onSuccess: ({ trial: imported, items }) => {
      if (imported) {
        setTrial(imported);
      }
      setResults(items);
    },
    onError: (caught: Error) => setError(caught.message),
  });

  const create = useMutation({
    mutationFn: api.createAnalysis,
    onSuccess: (analysis) => router.push(`/analyses/${analysis.id}/edit`),
    onError: (caught: Error) => setError(caught.message),
  });

  async function importResult(item: TrialSearchResult) {
    setError("");
    try {
      setTrial(await api.getTrial(item.nct_id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Import failed.");
    }
  }

  return (
    <AppShell
      title={trial ? "Review imported study" : "Create an analysis"}
      description={
        trial
          ? "Confirm the source values and make any protocol-specific edits before saving."
          : "Find a public study by NCT ID or search terms. Nothing is saved until you review the imported fields."
      }
    >
      {!trial ? (
        <div className="grid gap-7 lg:grid-cols-[0.8fr_1.2fr]">
          <section className="rounded-2xl border border-[var(--line)] bg-white p-6 shadow-sm">
            <h2 className="text-xl font-semibold">Find a study</h2>
            <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
              Try an NCT ID, “metastatic NSCLC phase 2,” or a biomarker and
              intervention.
            </p>
            <form
              className="mt-6"
              onSubmit={(event) => {
                event.preventDefault();
                if (query.trim().length >= 2) lookup.mutate();
              }}
            >
              <FieldLabel required htmlFor="trial-query">
                NCT ID or search
              </FieldLabel>
              <div className="flex gap-2">
                <Input
                  id="trial-query"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="NCT04267848"
                  minLength={2}
                  required
                />
                <Button type="submit" disabled={lookup.isPending}>
                  <Search size={16} aria-hidden="true" />
                  {lookup.isPending ? "Searching" : "Search"}
                </Button>
              </div>
            </form>
            {error ? (
              <p
                role="alert"
                className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-800"
              >
                {error}
              </p>
            ) : null}
          </section>

          <section aria-live="polite">
            {results.length ? (
              <div className="overflow-hidden rounded-2xl border border-[var(--line)] bg-white shadow-sm">
                <div className="border-b border-[var(--line)] px-5 py-4">
                  <h2 className="font-semibold">Search results</h2>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    Select a study to retrieve its complete current record.
                  </p>
                </div>
                {results.map((item) => (
                  <article
                    key={item.nct_id}
                    className="flex items-center justify-between gap-5 border-b border-[var(--line)] px-5 py-4 last:border-0"
                  >
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs font-bold text-[var(--brand)]">
                          {item.nct_id}
                        </span>
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-bold">
                          {item.overall_status.replaceAll("_", " ")}
                        </span>
                      </div>
                      <h3 className="mt-2 text-sm font-semibold">
                        {item.title}
                      </h3>
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        {item.phases.join(", ") || "Phase not reported"} ·{" "}
                        {item.us_site_count} US sites
                      </p>
                    </div>
                    <Button
                      variant="secondary"
                      onClick={() => importResult(item)}
                    >
                      Import <ArrowRight size={15} aria-hidden="true" />
                    </Button>
                  </article>
                ))}
              </div>
            ) : (
              <div className="grid min-h-64 place-items-center rounded-2xl border border-dashed border-slate-300 p-8 text-center text-sm leading-6 text-[var(--muted)]">
                Search results will appear here with status, phase, and US site
                context.
              </div>
            )}
          </section>
        </div>
      ) : (
        <>
          {error ? (
            <p
              role="alert"
              className="mb-5 rounded-xl bg-red-50 p-3 text-sm text-red-800"
            >
              {error}
            </p>
          ) : null}
          <AnalysisForm
            trial={trial}
            pending={create.isPending}
            onSubmit={async (payload) => {
              await create.mutateAsync(payload);
            }}
          />
        </>
      )}
    </AppShell>
  );
}
