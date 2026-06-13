import { CircleAlert } from "lucide-react";

export function Disclaimer() {
  return (
    <aside
      className="flex gap-3 rounded-2xl border border-amber-300/70 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-950"
      aria-label="Product limitation"
    >
      <CircleAlert className="mt-0.5 shrink-0" size={18} aria-hidden="true" />
      <p>
        <strong>Illustrative methodology.</strong> Not a validated prediction,
        clinical decision, regulatory, or site-selection system. Do not enter
        patient data or confidential protocol content.
      </p>
    </aside>
  );
}
