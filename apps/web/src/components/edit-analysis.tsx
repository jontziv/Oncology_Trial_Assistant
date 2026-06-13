"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { AnalysisForm } from "@/components/analysis-form";
import { AppShell } from "@/components/app-shell";
import { api } from "@/lib/api";

export function EditAnalysis({ id }: { id: string }) {
  const [message, setMessage] = useState("");
  const queryClient = useQueryClient();
  const router = useRouter();
  const analysis = useQuery({
    queryKey: ["analysis", id],
    queryFn: () => api.getAnalysis(id),
  });
  const update = useMutation({
    mutationFn: (payload: Parameters<typeof api.updateAnalysis>[1]) =>
      api.updateAnalysis(id, payload),
    onSuccess: (saved) => {
      queryClient.setQueryData(["analysis", id], saved);
      queryClient.invalidateQueries({ queryKey: ["analyses"] });
      setMessage("Analysis saved.");
    },
    onError: (caught: Error) => setMessage(caught.message),
  });
  const analyze = useMutation({
    mutationFn: async (payload: Parameters<typeof api.updateAnalysis>[1]) => {
      await api.updateAnalysis(id, payload);
      return api.runAnalysis(id, true);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["analysis", id] });
      queryClient.invalidateQueries({ queryKey: ["analyses"] });
      router.push(`/analyses/${id}/results`);
    },
    onError: (caught: Error) => setMessage(caught.message),
  });

  return (
    <AppShell
      title="Trial workspace"
      description="Review imported values, preserve the public source, and save your working protocol assumptions."
    >
      {analysis.isLoading ? (
        <div className="rounded-2xl border border-[var(--line)] bg-white p-8 text-sm text-[var(--muted)]">
          Loading analysis...
        </div>
      ) : analysis.isError ? (
        <div
          role="alert"
          className="rounded-2xl border border-red-200 bg-red-50 p-6 text-red-900"
        >
          {analysis.error.message}
        </div>
      ) : analysis.data ? (
        <>
          {message ? (
            <p
              role="status"
              className="mb-5 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900"
            >
              {message}
            </p>
          ) : null}
          <AnalysisForm
            key={analysis.data.updated_at}
            trial={analysis.data.trial}
            analysisTitle={analysis.data.title}
            submitLabel="Save changes"
            pending={update.isPending || analyze.isPending}
            onSubmit={async (payload) => {
              setMessage("");
              await update.mutateAsync(payload);
            }}
            onAnalyze={async (payload) => {
              setMessage("");
              await analyze.mutateAsync(payload);
            }}
          />
        </>
      ) : null}
    </AppShell>
  );
}
