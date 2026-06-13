import Link from "next/link";
import { ArrowRight, BookOpenText, Database, ShieldCheck } from "lucide-react";
import { Disclaimer } from "@/components/disclaimer";

const capabilities = [
  {
    icon: Database,
    title: "Structured trial workspace",
    copy: "Import a ClinicalTrials.gov study and review normalized protocol fields.",
  },
  {
    icon: BookOpenText,
    title: "Evidence made inspectable",
    copy: "Keep source values, user edits, timestamps, and provenance visible.",
  },
  {
    icon: ShieldCheck,
    title: "Responsible by design",
    copy: "No patient data, no hidden prediction, and no unsupported clinical claims.",
  },
];

export default function Home() {
  return (
    <main className="min-h-screen">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-6 py-7 lg:px-10">
        <div className="flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-xl bg-[var(--brand)] text-sm font-bold text-white">
            OT
          </div>
          <div>
            <p className="text-sm font-semibold">Oncology Trial</p>
            <p className="text-xs text-[var(--muted)]">Feasibility Copilot</p>
          </div>
        </div>
        <Link
          href="/analyses"
          className="rounded-full border border-[var(--line)] bg-white px-5 py-2.5 text-sm font-semibold shadow-sm transition hover:border-[var(--brand)]"
        >
          Open workspace
        </Link>
      </header>

      <section className="mx-auto grid max-w-7xl gap-14 px-6 pb-16 pt-16 lg:grid-cols-[1.25fr_0.75fr] lg:px-10 lg:pt-24">
        <div>
          <p className="mb-5 text-xs font-bold uppercase tracking-[0.2em] text-[var(--brand)]">
            Public evidence, operational clarity
          </p>
          <h1 className="max-w-4xl text-5xl font-semibold leading-[1.05] tracking-[-0.04em] lg:text-7xl">
            Make the first feasibility conversation more rigorous.
          </h1>
          <p className="mt-7 max-w-2xl text-lg leading-8 text-[var(--muted)]">
            A transparent workspace for reviewing oncology trial design,
            comparable public studies, and enrollment risk signals without
            pretending public data can predict the future.
          </p>
          <div className="mt-9 flex flex-wrap gap-4">
            <Link
              href="/analyses/new"
              className="inline-flex items-center gap-2 rounded-full bg-[var(--brand)] px-6 py-3.5 text-sm font-bold text-white shadow-lg shadow-emerald-950/10 transition hover:bg-[var(--brand-dark)]"
            >
              Start an analysis <ArrowRight size={17} aria-hidden="true" />
            </Link>
            <Link
              href="/methodology"
              className="rounded-full px-6 py-3.5 text-sm font-bold text-[var(--brand)] hover:bg-white"
            >
              Read methodology
            </Link>
          </div>
        </div>

        <div className="self-end rounded-3xl border border-[var(--line)] bg-white/85 p-7 shadow-[0_24px_80px_rgb(29_55_47/10%)] backdrop-blur">
          <p className="text-xs font-bold uppercase tracking-[0.16em] text-[var(--muted)]">
            Initial case study
          </p>
          <p className="mt-3 text-2xl font-semibold">US metastatic NSCLC</p>
          <dl className="mt-7 grid grid-cols-2 gap-px overflow-hidden rounded-2xl bg-[var(--line)]">
            {[
              ["Phase", "II"],
              ["Data", "Public"],
              ["Method", "Explainable"],
              ["Purpose", "Decision support"],
            ].map(([term, value]) => (
              <div key={term} className="bg-white p-4">
                <dt className="text-xs text-[var(--muted)]">{term}</dt>
                <dd className="mt-1 text-sm font-bold">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <section className="border-y border-[var(--line)] bg-white/70">
        <div className="mx-auto grid max-w-7xl divide-y divide-[var(--line)] px-6 md:grid-cols-3 md:divide-x md:divide-y-0 lg:px-10">
          {capabilities.map(({ icon: Icon, title, copy }) => (
            <article
              key={title}
              className="py-8 md:px-8 md:first:pl-0 md:last:pr-0"
            >
              <Icon
                className="text-[var(--brand)]"
                size={21}
                aria-hidden="true"
              />
              <h2 className="mt-5 font-semibold">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                {copy}
              </p>
            </article>
          ))}
        </div>
      </section>
      <div className="mx-auto max-w-7xl px-6 py-8 lg:px-10">
        <Disclaimer />
      </div>
    </main>
  );
}
