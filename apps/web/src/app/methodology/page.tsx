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
            "Future risk factors will be deterministic, versioned, decomposed, and explicit about missing-data behavior.",
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
    </AppShell>
  );
}
