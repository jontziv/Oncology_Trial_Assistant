"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowLeft,
  BookOpen,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { AppShell } from "@/components/app-shell";
import { MetricBar } from "@/components/metric-bar";
import { Button } from "@/components/ui/button";
import { api, ApiError } from "@/lib/api";

function scoreColor(score: number) {
  if (score >= 65) return "text-red-700 bg-red-50 border-red-200";
  if (score >= 35) return "text-amber-800 bg-amber-50 border-amber-200";
  return "text-emerald-800 bg-emerald-50 border-emerald-200";
}

export function AnalysisResults({ id }: { id: string }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const analysis = useQuery({
    queryKey: ["analysis", id],
    queryFn: () => api.getAnalysis(id),
  });
  const results = useQuery({
    queryKey: ["results", id],
    queryFn: () => api.getResults(id),
  });
  const rerun = useMutation({
    mutationFn: () => api.runAnalysis(id, true),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["results", id] });
      queryClient.invalidateQueries({ queryKey: ["analysis", id] });
    },
  });

  const missingRun =
    results.isError &&
    results.error instanceof ApiError &&
    results.error.status === 404;

  useEffect(() => {
    if (missingRun) {
      router.replace(`/analyses/${id}/edit`);
    }
  }, [id, missingRun, router]);

  return (
    <AppShell
      title="Feasibility results"
      description={
        analysis.data
          ? `${analysis.data.title} · ${analysis.data.trial.nct_id}`
          : "Loading analysis context..."
      }
      action={
        <div className="flex gap-2">
          <Button asChild variant="secondary">
            <Link href={`/analyses/${id}/edit`}>
              <ArrowLeft size={16} aria-hidden="true" /> Protocol
            </Link>
          </Button>
          <Button onClick={() => rerun.mutate()} disabled={rerun.isPending}>
            <RefreshCw size={16} aria-hidden="true" />
            {rerun.isPending ? "Re-running..." : "Refresh analysis"}
          </Button>
        </div>
      }
    >
      {results.isLoading ? (
        <div className="rounded-2xl border border-[var(--line)] bg-white p-10">
          <p className="font-semibold">
            Retrieving evidence and computing metrics...
          </p>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Comparable trials, geography, and PubMed evidence are processed
            synchronously for this proof of concept.
          </p>
        </div>
      ) : missingRun ? (
        <div className="rounded-2xl border border-[var(--line)] bg-white p-10">
          <p className="font-semibold">No completed run yet.</p>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Returning to the protocol so you can run the analysis.
          </p>
        </div>
      ) : results.isError ? (
        <div
          role="alert"
          className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-900"
        >
          {results.error.message}
        </div>
      ) : results.data ? (
        <ResultSections result={results.data} />
      ) : null}
    </AppShell>
  );
}

function ResultSections({
  result,
}: {
  result: Awaited<ReturnType<typeof api.getResults>>;
}) {
  const maxDensity = Math.max(
    1,
    ...result.competition.regions.map((item) => item.weighted_density),
  );
  return (
    <div className="space-y-7">
      <section className="grid gap-5 lg:grid-cols-[0.7fr_1.3fr]">
        <div
          className={`rounded-3xl border p-7 ${scoreColor(result.overall_score)}`}
        >
          <p className="text-xs font-bold uppercase tracking-[0.16em]">
            Illustrative enrollment risk
          </p>
          <div className="mt-5 flex items-end gap-3">
            <span className="text-6xl font-semibold tracking-[-0.06em]">
              {result.overall_score.toFixed(0)}
            </span>
            <span className="pb-2 text-lg font-semibold">/ 100</span>
          </div>
          <p className="mt-4 text-xl font-semibold capitalize">
            {result.risk_band} risk
          </p>
          <p className="mt-2 text-sm">
            {result.confidence_label} confidence · sensitivity{" "}
            {result.sensitivity_low.toFixed(0)}–
            {result.sensitivity_high.toFixed(0)}
          </p>
        </div>

        <div className="rounded-3xl border border-[var(--line)] bg-white p-7 shadow-sm">
          <h2 className="text-xl font-semibold">Risk decomposition</h2>
          <div className="mt-6 space-y-5">
            {result.components.map((item) => (
              <div key={item.key}>
                <div className="mb-2 flex items-center justify-between gap-4 text-sm">
                  <span className="font-semibold">{item.label}</span>
                  <span>
                    {item.score.toFixed(0)} · weight{" "}
                    {(item.weight * 100).toFixed(0)}%
                  </span>
                </div>
                <MetricBar value={item.score} tone="risk" />
                <p className="mt-2 text-xs leading-5 text-[var(--muted)]">
                  {item.rationale}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {(result.warnings ?? []).length ? (
        <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
          <h2 className="flex items-center gap-2 font-semibold text-amber-950">
            <AlertTriangle size={18} aria-hidden="true" /> Data limitations
          </h2>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-amber-950">
            {(result.warnings ?? []).map((warning) => (
              <li key={warning}>• {warning}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="grid gap-5 md:grid-cols-3">
        <MetricCard
          label="Eligibility burden"
          value={`${result.eligibility.score.toFixed(0)}/100`}
          detail={`${result.eligibility.criterion_count} parsed criteria · ${result.eligibility.band} burden`}
        />
        <MetricCard
          label="Enrollment-duration proxy"
          value={
            result.timeline.projected_enrollment_months
              ? `${result.timeline.projected_enrollment_months.toFixed(1)} mo`
              : result.timeline.median_months
                ? `${result.timeline.median_months.toFixed(1)} mo`
                : "Insufficient data"
          }
          detail={
            result.timeline.median_participants_per_month
              ? `${result.timeline.median_participants_per_month.toFixed(1)} participants/month · ${result.timeline.throughput_cohort_size} actual-enrollment comparators`
              : `${result.timeline.cohort_size} usable comparable intervals`
          }
        />
        <MetricCard
          label="Endpoint comparability"
          value={`${result.endpoints.score.toFixed(0)}%`}
          detail={`${result.endpoints.comparable_count} of ${result.endpoints.cohort_size} use ${result.endpoints.target_family}`}
        />
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        <div className="rounded-3xl border border-[var(--line)] bg-white p-6 shadow-sm">
          <h2 className="font-semibold">Eligibility drivers</h2>
          <div className="mt-4 space-y-3">
            {result.eligibility.factors.map((factor) => (
              <div key={factor.label} className="rounded-xl bg-slate-50 p-3">
                <div className="flex justify-between gap-3 text-sm font-semibold">
                  <span>{factor.label}</span>
                  <span>+{factor.points.toFixed(1)}</span>
                </div>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  {factor.evidence}
                </p>
              </div>
            ))}
          </div>
        </div>
        <div className="rounded-3xl border border-[var(--line)] bg-white p-6 shadow-sm">
          <h2 className="font-semibold">Endpoint precedent</h2>
          <p className="mt-2 text-xs leading-5 text-[var(--muted)]">
            Registered primary outcomes are used unless a comparable trial has
            posted result outcomes.
          </p>
          <div className="mt-4 space-y-3">
            {Object.entries(result.endpoints.cohort_distribution).map(
              ([family, count]) => (
                <div
                  key={family}
                  className="flex items-center justify-between rounded-xl bg-slate-50 p-3 text-sm"
                >
                  <span className="capitalize">{family}</span>
                  <span className="font-semibold">{count}</span>
                </div>
              ),
            )}
          </div>
        </div>
        <div className="rounded-3xl border border-[var(--line)] bg-white p-6 shadow-sm">
          <h2 className="font-semibold">Enrollment benchmark</h2>
          <dl className="mt-4 space-y-3 text-sm">
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Target enrollment</dt>
              <dd className="font-semibold">
                {result.timeline.target_enrollment}
              </dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Comparator median</dt>
              <dd className="font-semibold">
                {result.timeline.median_enrollment?.toFixed(0) ?? "Unavailable"}
              </dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-[var(--muted)]">Projected proxy</dt>
              <dd className="font-semibold">
                {result.timeline.projected_enrollment_months
                  ? `${result.timeline.projected_enrollment_months.toFixed(1)} months`
                  : "Unavailable"}
              </dd>
            </div>
          </dl>
          <p className="mt-5 text-xs leading-5 text-[var(--muted)]">
            {result.timeline.limitation}
          </p>
        </div>
      </section>

      <section className="rounded-3xl border border-[var(--line)] bg-white p-7 shadow-sm">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">Competing-trial heatmap</h2>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Active comparable sites by US state; darker tiles indicate higher
              weighted registered competition.
            </p>
          </div>
          <p className="text-sm font-semibold">
            {result.competition.active_trial_count} active trials ·{" "}
            {result.competition.active_us_site_count} US sites
          </p>
        </div>
        <div className="mt-6 grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
          {result.competition.regions.map((item) => {
            const intensity = item.weighted_density / maxDensity;
            return (
              <div
                key={item.region}
                className="rounded-xl border border-emerald-900/10 p-3"
                style={{
                  backgroundColor: `color-mix(in srgb, var(--brand) ${Math.round(
                    12 + intensity * 72,
                  )}%, white)`,
                  color: intensity > 0.55 ? "white" : "var(--ink)",
                }}
              >
                <p className="text-xs font-bold">{item.region}</p>
                <p className="mt-2 text-2xl font-semibold">
                  {item.active_site_count}
                </p>
                <p className="text-[10px]">active sites</p>
              </div>
            );
          })}
        </div>
      </section>

      <section className="rounded-3xl border border-[var(--line)] bg-white p-7 shadow-sm">
        <h2 className="text-xl font-semibold">
          State, country, and candidate-site opportunity
        </h2>
        <div className="mt-5 overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead className="border-b border-[var(--line)] text-xs uppercase tracking-wider text-[var(--muted)]">
              <tr>
                <th className="py-3">Region</th>
                <th>Level</th>
                <th>Opportunity</th>
                <th>Historical trials</th>
                <th>Active competing sites</th>
                <th>Candidate facilities</th>
              </tr>
            </thead>
            <tbody>
              {result.geography.map((item) => (
                <tr
                  key={item.region}
                  className="border-b border-[var(--line)] last:border-0"
                >
                  <td className="py-4 font-semibold">{item.region}</td>
                  <td className="capitalize">{item.level}</td>
                  <td className="w-48 pr-6">
                    <div className="mb-1 text-xs">
                      {item.opportunity_score.toFixed(0)}/100
                    </div>
                    <MetricBar value={item.opportunity_score} />
                  </td>
                  <td>{item.historical_trial_count}</td>
                  <td>{item.active_competing_sites}</td>
                  <td className="max-w-sm text-xs leading-5 text-[var(--muted)]">
                    {item.candidate_facilities.join(", ") ||
                      "No normalized facility history"}
                    {item.disease_burden_rate != null
                      ? ` · incidence ${item.disease_burden_rate.toFixed(1)}/100k`
                      : ""}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-2">
        <div className="rounded-3xl border border-[var(--line)] bg-white p-7 shadow-sm">
          <h2 className="text-xl font-semibold">What I would change</h2>
          <div className="mt-5 space-y-5">
            {result.recommendations.map((item, index) => (
              <article
                key={`${item.category}-${index}`}
                className="border-b border-[var(--line)] pb-5 last:border-0 last:pb-0"
              >
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold uppercase">
                    {item.priority}
                  </span>
                  <span className="text-xs font-semibold text-[var(--brand)]">
                    {item.category}
                  </span>
                </div>
                <h3 className="mt-3 text-sm font-semibold">
                  {item.recommendation}
                </h3>
                <p className="mt-2 text-xs leading-5 text-[var(--muted)]">
                  Benefit: {item.expected_benefit} Tradeoff: {item.tradeoff}
                </p>
              </article>
            ))}
          </div>
        </div>

        <div className="rounded-3xl border border-[var(--line)] bg-slate-950 p-7 text-slate-100 shadow-sm">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-emerald-300">
            Feasibility memo · {result.memo.generated_by}
          </p>
          <h2 className="mt-4 text-xl font-semibold">Executive summary</h2>
          <p className="mt-3 text-sm leading-7 text-slate-300">
            {result.memo.executive_summary}
          </p>
          <h3 className="mt-6 text-sm font-semibold">Key risks</h3>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-300">
            {result.memo.key_risks.map((risk) => (
              <li key={risk}>• {risk}</li>
            ))}
          </ul>
          <p className="mt-6 text-xs text-slate-400">
            Citations:{" "}
            {result.memo.citation_ids.length
              ? result.memo.citation_ids.map((sourceId, index) => {
                  const source = result.sources.find(
                    (item) => item.source_id === sourceId,
                  );
                  return (
                    <span key={sourceId}>
                      {index > 0 ? ", " : ""}
                      {source && source.url.startsWith("http") ? (
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noreferrer"
                          className="underline hover:text-white"
                        >
                          {sourceId}
                        </a>
                      ) : (
                        sourceId
                      )}
                    </span>
                  );
                })
              : "No external citations"}
          </p>
        </div>
      </section>

      <section className="rounded-3xl border border-[var(--line)] bg-white p-7 shadow-sm">
        <h2 className="text-xl font-semibold">Comparable trial cohort</h2>
        <div className="mt-5 grid gap-3">
          {result.similar_trials.map((trial) => (
            <article
              key={trial.nct_id}
              className="grid gap-3 rounded-2xl border border-[var(--line)] p-4 md:grid-cols-[1fr_auto] md:items-center"
            >
              <div>
                <a
                  href={trial.source.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs font-bold text-[var(--brand)] hover:underline"
                >
                  {trial.nct_id} <ExternalLink className="inline" size={12} />
                </a>
                <h3 className="mt-1 text-sm font-semibold">{trial.title}</h3>
                <p className="mt-2 text-xs text-[var(--muted)]">
                  Matched: {(trial.matched_features ?? []).join(", ")}
                </p>
              </div>
              <div className="min-w-28 text-right">
                <p className="text-2xl font-semibold">
                  {trial.similarity_score.toFixed(0)}%
                </p>
                <p className="text-[10px] uppercase text-[var(--muted)]">
                  similarity
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {(result.publications ?? []).length > 0 ? (
        <section className="rounded-3xl border border-[var(--line)] bg-white p-7 shadow-sm">
          <h2 className="flex items-center gap-2 text-xl font-semibold">
            <BookOpen
              size={20}
              className="text-[var(--brand)]"
              aria-hidden="true"
            />
            Related publications
          </h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            PubMed records retrieved via NCBI E-utilities for the trial
            indication and intervention.
          </p>
          <div className="mt-5 grid gap-3 md:grid-cols-2">
            {(result.publications ?? []).map((pub) => (
              <a
                key={pub.pmid}
                href={pub.url}
                target="_blank"
                rel="noreferrer"
                className="rounded-xl border border-[var(--line)] p-4 transition hover:border-[var(--brand)]"
              >
                <p className="text-[10px] font-bold uppercase text-[var(--brand)]">
                  PMID {pub.pmid}
                  {pub.journal ? ` · ${pub.journal}` : ""}
                </p>
                <p className="mt-2 text-sm font-semibold leading-5">
                  {pub.title}
                </p>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  {(pub.authors ?? []).slice(0, 3).join(", ")}
                  {(pub.authors ?? []).length > 3 ? " et al." : ""}
                  {pub.publication_date ? ` · ${pub.publication_date}` : ""}
                </p>
              </a>
            ))}
          </div>
        </section>
      ) : null}

      <section className="rounded-3xl border border-[var(--line)] bg-white p-7 shadow-sm">
        <h2 className="flex items-center gap-2 text-xl font-semibold">
          <BookOpen
            size={20}
            className="text-[var(--brand)]"
            aria-hidden="true"
          />
          Evidence sources
        </h2>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {result.sources.map((source) => {
            const content = (
              <>
                <p className="text-[10px] font-bold uppercase text-[var(--brand)]">
                  {source.source_id}
                </p>
                <p className="mt-2 text-sm font-semibold">{source.title}</p>
                <p className="mt-1 text-xs text-[var(--muted)]">
                  {source.locator}
                </p>
              </>
            );
            const className =
              "rounded-xl border border-[var(--line)] p-4 transition hover:border-[var(--brand)]";
            return source.url.startsWith("http") ? (
              <a
                key={source.source_id}
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className={className}
              >
                {content}
              </a>
            ) : (
              <div key={source.source_id} className={className}>
                {content}
              </div>
            );
          })}
        </div>
      </section>

      <p className="text-center text-xs text-[var(--muted)]">
        Methodology {result.methodology_version}. Illustrative decision support,
        not a validated enrollment prediction.
      </p>
    </div>
  );
}

function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="rounded-2xl border border-[var(--line)] bg-white p-6 shadow-sm">
      <p className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
        {label}
      </p>
      <p className="mt-4 text-3xl font-semibold tracking-[-0.04em]">{value}</p>
      <p className="mt-2 text-xs leading-5 text-[var(--muted)]">{detail}</p>
    </article>
  );
}
