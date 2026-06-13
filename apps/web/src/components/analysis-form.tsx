"use client";

import type { TrialDraft } from "@oncology/api-client";
import { zodResolver } from "@hookform/resolvers/zod";
import { ExternalLink, Save, ShieldCheck } from "lucide-react";
import { useForm } from "react-hook-form";
import { Button } from "@/components/ui/button";
import {
  FieldError,
  FieldLabel,
  Input,
  Select,
  Textarea,
} from "@/components/ui/field";
import {
  analysisFormSchema,
  type AnalysisFormValues,
  formToTrial,
  trialToForm,
} from "@/lib/analysis-form";

export function AnalysisForm({
  trial,
  analysisTitle,
  submitLabel = "Save analysis",
  pending,
  onSubmit,
}: {
  trial: TrialDraft;
  analysisTitle?: string;
  submitLabel?: string;
  pending?: boolean;
  onSubmit: (payload: { title: string; trial: TrialDraft }) => Promise<void>;
}) {
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
  } = useForm<AnalysisFormValues>({
    resolver: zodResolver(analysisFormSchema),
    defaultValues: trialToForm(trial, analysisTitle),
  });

  async function submit(values: AnalysisFormValues) {
    await onSubmit({
      title: values.analysisTitle,
      trial: formToTrial(values, trial),
    });
  }

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-7">
      <section className="overflow-hidden rounded-2xl border border-[var(--line)] bg-white shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[var(--line)] px-6 py-5">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--brand)]">
              Imported source
            </p>
            <h2 className="mt-1 text-xl font-semibold">{trial.nct_id}</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Retrieved {new Date(trial.source.retrieved_at).toLocaleString()}
            </p>
          </div>
          <a
            href={trial.source.url}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--brand)] hover:underline"
          >
            View source <ExternalLink size={15} aria-hidden="true" />
          </a>
        </div>
        <div className="grid gap-5 p-6 md:grid-cols-2">
          <div className="md:col-span-2">
            <FieldLabel required htmlFor="analysisTitle">
              Analysis title
            </FieldLabel>
            <Input id="analysisTitle" {...register("analysisTitle")} />
            <FieldError message={errors.analysisTitle?.message} />
          </div>
          <div className="md:col-span-2">
            <FieldLabel required htmlFor="title">
              Study title
            </FieldLabel>
            <Input id="title" {...register("title")} />
            <FieldError message={errors.title?.message} />
          </div>
          <div>
            <FieldLabel required htmlFor="indication">
              Indication
            </FieldLabel>
            <Input id="indication" {...register("indication")} />
            <FieldError message={errors.indication?.message} />
          </div>
          <div>
            <FieldLabel required htmlFor="phases">
              Phase
            </FieldLabel>
            <Input id="phases" {...register("phases")} />
            <FieldError message={errors.phases?.message} />
          </div>
          <div>
            <FieldLabel required htmlFor="overallStatus">
              Recruitment status
            </FieldLabel>
            <Select id="overallStatus" {...register("overallStatus")}>
              {[
                "NOT_YET_RECRUITING",
                "RECRUITING",
                "ENROLLING_BY_INVITATION",
                "ACTIVE_NOT_RECRUITING",
                "COMPLETED",
                "SUSPENDED",
                "TERMINATED",
                "WITHDRAWN",
                "UNKNOWN",
              ].map((status) => (
                <option key={status} value={status}>
                  {status.replaceAll("_", " ")}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <FieldLabel htmlFor="biomarker">Biomarker</FieldLabel>
            <Input
              id="biomarker"
              placeholder="e.g. EGFR, PD-L1"
              {...register("biomarker")}
            />
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-[var(--line)] bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Intervention and enrollment</h2>
        <div className="mt-5 grid gap-5 md:grid-cols-3">
          <div>
            <FieldLabel required htmlFor="interventionName">
              Intervention
            </FieldLabel>
            <Input id="interventionName" {...register("interventionName")} />
            <FieldError message={errors.interventionName?.message} />
          </div>
          <div>
            <FieldLabel required htmlFor="interventionType">
              Intervention type
            </FieldLabel>
            <Input id="interventionType" {...register("interventionType")} />
            <FieldError message={errors.interventionType?.message} />
          </div>
          <div>
            <FieldLabel required htmlFor="enrollment">
              Planned enrollment
            </FieldLabel>
            <Input
              id="enrollment"
              type="number"
              min={1}
              {...register("enrollment", { valueAsNumber: true })}
            />
            <FieldError message={errors.enrollment?.message} />
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-[var(--line)] bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold">Eligibility and endpoint</h2>
        <div className="mt-5 grid gap-5">
          <div>
            <FieldLabel required htmlFor="eligibilityCriteria">
              Eligibility criteria
            </FieldLabel>
            <Textarea
              id="eligibilityCriteria"
              rows={10}
              {...register("eligibilityCriteria")}
            />
            <FieldError message={errors.eligibilityCriteria?.message} />
          </div>
          <div className="grid gap-5 md:grid-cols-2">
            <div>
              <FieldLabel required htmlFor="primaryEndpoint">
                Primary endpoint
              </FieldLabel>
              <Input id="primaryEndpoint" {...register("primaryEndpoint")} />
              <FieldError message={errors.primaryEndpoint?.message} />
            </div>
            <div>
              <FieldLabel htmlFor="primaryEndpointTimeFrame">
                Endpoint time frame
              </FieldLabel>
              <Input
                id="primaryEndpointTimeFrame"
                {...register("primaryEndpointTimeFrame")}
              />
            </div>
          </div>
        </div>
      </section>

      <div className="sticky bottom-4 flex items-center justify-between gap-4 rounded-2xl border border-[var(--line)] bg-white/95 p-4 shadow-xl backdrop-blur">
        <p className="flex items-center gap-2 text-xs text-[var(--muted)]">
          <ShieldCheck
            size={16}
            className="text-[var(--brand)]"
            aria-hidden="true"
          />
          {isDirty ? "Unsaved edits" : "Source values unchanged"}
        </p>
        <Button type="submit" disabled={pending}>
          <Save size={16} aria-hidden="true" />
          {pending ? "Saving..." : submitLabel}
        </Button>
      </div>
    </form>
  );
}
