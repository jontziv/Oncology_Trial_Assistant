export function MetricBar({
  value,
  tone = "brand",
}: {
  value: number;
  tone?: "brand" | "risk";
}) {
  const color =
    tone === "risk"
      ? value >= 65
        ? "bg-red-600"
        : value >= 35
          ? "bg-amber-500"
          : "bg-emerald-600"
      : "bg-[var(--brand)]";
  return (
    <div
      className="h-2 overflow-hidden rounded-full bg-slate-100"
      role="img"
      aria-label={`${value.toFixed(1)} out of 100`}
    >
      <div
        className={`h-full rounded-full ${color}`}
        style={{ width: `${Math.max(0, Math.min(value, 100))}%` }}
      />
    </div>
  );
}
