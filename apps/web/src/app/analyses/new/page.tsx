"use client";

import type { TrialDraft, TrialSearchResult } from "@oncology/api-client";
import { useMutation } from "@tanstack/react-query";
import { ArrowRight, ClipboardList, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AnalysisForm } from "@/components/analysis-form";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { FieldError, FieldLabel, Input, Textarea } from "@/components/ui/field";
import { api } from "@/lib/api";
import { createBlankTrialDraft } from "@/lib/analysis-form";

type Mode = "import" | "manual";

function ManualEntryForm({
  onReady,
}: {
  onReady: (trial: TrialDraft) => void;
}) {
  const [indication, setIndication] = useState("");
  const [phases, setPhases] = useState("PHASE2");
  const [moleculeClass, setMoleculeClass] = useState("");
  const [biomarker, setBiomarker] = useState("");
  const [geography, setGeography] = useState("United States");
  const [interventionName, setInterventionName] = useState("");
  const [primaryEndpoint, setPrimaryEndpoint] = useState("Overall Survival");
  const [eligibilityCriteria, setEligibilityCriteria] = useState(
    "Inclusion criteria:\n- \n\nExclusion criteria:\n- ",
  );
  const [error, setError] = useState("");

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!indication.trim()) {
      setError("Indication is required.");
      return;
    }
    if (!phases.trim()) {
      setError("Phase is required.");
      return;
    }
    setError("");
    onReady(
      createBlankTrialDraft({
        indication: indication.trim(),
        phases: phases.trim(),
        moleculeClass: moleculeClass.trim(),
        biomarker: biomarker.trim(),
        geography: geography.trim(),
        interventionName: interventionName.trim(),
        primaryEndpoint: primaryEndpoint.trim(),
        eligibilityCriteria: eligibilityCriteria.trim(),
      }),
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-7">
      <section className="rounded-2xl border border-[var(--line)] bg-white p-6 shadow-sm">
        <h2 className="text-xl font-semibold">Protocol inputs</h2>
        <p className="mt-1 text-sm leading-6 text-[var(--muted)]">
          Enter the key fields that define your trial design. You can refine all
          details on the next screen.
        </p>
        <div className="mt-6 grid gap-5 md:grid-cols-2">
          <div className="md:col-span-2">
            <FieldLabel required htmlFor="m-indication">
              Oncology indication
            </FieldLabel>
            <Input
              id="m-indication"
              value={indication}
              onChange={(e) => setIndication(e.target.value)}
              placeholder="Non-Small Cell Lung Cancer"
              required
            />
          </div>
          <div>
            <FieldLabel required htmlFor="m-phases">
              Phase(s)
            </FieldLabel>
            <Input
              id="m-phases"
              value={phases}
              onChange={(e) => setPhases(e.target.value)}
              placeholder="PHASE2, PHASE3"
            />
            <p className="mt-1 text-xs text-[var(--muted)]">
              Comma-separated e.g. PHASE2 or PHASE1, PHASE2
            </p>
          </div>
          <div>
            <FieldLabel htmlFor="m-molecule-class">Molecule class</FieldLabel>
            <Input
              id="m-molecule-class"
              value={moleculeClass}
              onChange={(e) => setMoleculeClass(e.target.value)}
              placeholder="Tyrosine kinase inhibitor"
            />
          </div>
          <div>
            <FieldLabel htmlFor="m-biomarker">
              Biomarker selection criteria
            </FieldLabel>
            <Input
              id="m-biomarker"
              value={biomarker}
              onChange={(e) => setBiomarker(e.target.value)}
              placeholder="EGFR, ALK"
            />
          </div>
          <div>
            <FieldLabel required htmlFor="m-geography">
              Target geographies
            </FieldLabel>
            <Input
              id="m-geography"
              value={geography}
              onChange={(e) => setGeography(e.target.value)}
              placeholder="United States, Canada"
            />
            <p className="mt-1 text-xs text-[var(--muted)]">
              Comma-separated countries
            </p>
          </div>
          <div>
            <FieldLabel required htmlFor="m-intervention">
              Intervention name
            </FieldLabel>
            <Input
              id="m-intervention"
              value={interventionName}
              onChange={(e) => setInterventionName(e.target.value)}
              placeholder="Osimertinib"
            />
          </div>
          <div>
            <FieldLabel required htmlFor="m-endpoint">
              Primary endpoint
            </FieldLabel>
            <Input
              id="m-endpoint"
              value={primaryEndpoint}
              onChange={(e) => setPrimaryEndpoint(e.target.value)}
              placeholder="Overall Survival"
            />
          </div>
          <div className="md:col-span-2">
            <FieldLabel required htmlFor="m-eligibility">
              Inclusion / exclusion profile
            </FieldLabel>
            <Textarea
              id="m-eligibility"
              rows={8}
              value={eligibilityCriteria}
              onChange={(e) => setEligibilityCriteria(e.target.value)}
            />
          </div>
        </div>
        {error ? (
          <p role="alert" className="mt-4 text-sm text-red-700">
            {error}
          </p>
        ) : null}
      </section>
      <div className="flex justify-end">
        <Button type="submit">
          Review protocol <ArrowRight size={16} aria-hidden="true" />
        </Button>
      </div>
    </form>
  );
}

export default function NewAnalysisPage() {
  const [mode, setMode] = useState<Mode>("import");
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

  const tabs: { id: Mode; label: string; icon: React.ElementType }[] = [
    { id: "import", label: "Import from ClinicalTrials.gov", icon: Search },
    { id: "manual", label: "Enter protocol manually", icon: ClipboardList },
  ];

  return (
    <AppShell
      title={trial ? "Review protocol" : "Create an analysis"}
      description={
        trial
          ? "Confirm the values and make any protocol-specific edits before saving."
          : mode === "import"
            ? "Find a public study by NCT ID or search terms. Nothing is saved until you review the imported fields."
            : "Describe your protocol directly. All fields are editable on the next screen."
      }
    >
      {!trial ? (
        <div className="space-y-6">
          <div className="flex gap-2 rounded-2xl border border-[var(--line)] bg-white p-1.5 shadow-sm">
            {tabs.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => {
                  setMode(id);
                  setError("");
                  setResults([]);
                }}
                className={`flex flex-1 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
                  mode === id
                    ? "bg-[var(--brand)] text-white shadow"
                    : "text-[var(--muted)] hover:text-[var(--ink)]"
                }`}
              >
                <Icon size={15} aria-hidden="true" />
                {label}
              </button>
            ))}
          </div>

          {mode === "import" ? (
            <div className="grid gap-7 lg:grid-cols-[0.8fr_1.2fr]">
              <section className="rounded-2xl border border-[var(--line)] bg-white p-6 shadow-sm">
                <h2 className="text-xl font-semibold">Find a study</h2>
                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                  Try an NCT ID, "metastatic NSCLC phase 2," or a biomarker and
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
                    Search results will appear here with status, phase, and US
                    site context.
                  </div>
                )}
              </section>
            </div>
          ) : (
            <ManualEntryForm onReady={(t) => setTrial(t)} />
          )}
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
