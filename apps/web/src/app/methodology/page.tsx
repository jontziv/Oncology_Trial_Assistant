import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";

export default function MethodologyPage() {
  return (
    <AppShell
      title="Methodology"
      description="The product separates sourced trial facts, user edits, deterministic analysis, and generated narrative."
      action={
        <Button asChild variant="secondary">
          <Link href="/analyses">Back to analyses</Link>
        </Button>
      }
    >
      <div className="grid gap-5 md:grid-cols-3">
        {[
          [
            "1. Source",
            "Current public records are retrieved through official APIs and stored with retrieval time, record ID, field locators, and source version.",
          ],
          [
            "2. Compute",
            "Risk factors are deterministic, versioned, decomposed, and explicit about missing-data behavior.",
          ],
          [
            "3. Synthesize",
            "The language model may summarize computed results but cannot create scores, trial facts, sources, or statistical claims.",
          ],
        ].map(([title, copy]) => (
          <article
            key={title}
            className="rounded-2xl border border-[var(--line)] bg-white p-6 shadow-sm"
          >
            <h2 className="font-semibold">{title}</h2>
            <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{copy}</p>
          </article>
        ))}
      </div>
      <div className="mt-6 rounded-3xl border border-[var(--line)] bg-white p-7 shadow-sm">
        <h2 className="text-xl font-semibold">Illustrative scoring model</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-5">
          {[
            ["Eligibility", "25%"],
            ["Competition", "25%"],
            ["Enrollment duration", "20%"],
            ["Geography", "20%"],
            ["Endpoints", "10%"],
          ].map(([label, weight]) => (
            <div key={label} className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs text-[var(--muted)]">{label}</p>
              <p className="mt-2 text-2xl font-semibold">{weight}</p>
            </div>
          ))}
        </div>
        <p className="mt-6 text-sm leading-7 text-[var(--muted)]">
          Comparable trials are ranked with structured indication, biomarker,
          molecule class, intervention, phase, design, endpoint, geography, and
          eligibility features. Requested target countries receive a visible
          preference in country feasibility ranking. US state opportunity also
          uses indication-matched 2018–2022 NPCR/SEER incidence context. Posted
          trial-result endpoints are preferred over planned endpoints when
          available. Missing data lowers confidence and receives a neutral risk
          value. Every result includes inputs, weights, sensitivity, sources,
          and limitations.
        </p>
      </div>
    </AppShell>
  );
}
