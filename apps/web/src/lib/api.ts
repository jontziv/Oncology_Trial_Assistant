import type {
  Analysis,
  TrialDraft,
  TrialSearchResponse,
} from "@oncology/api-client";
import { getSupabaseBrowserClient, isDemoMode } from "@/lib/supabase";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const DEMO_USER_ID = "00000000-0000-0000-0000-000000000001";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code?: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");

  if (isDemoMode()) {
    headers.set("X-Demo-User-Id", DEMO_USER_ID);
  } else {
    const supabase = getSupabaseBrowserClient();
    const session = await supabase?.auth.getSession();
    const accessToken = session?.data.session?.access_token;
    if (accessToken) {
      headers.set("Authorization", `Bearer ${accessToken}`);
    }
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const error = payload?.error;
    throw new ApiError(
      error?.message ??
        payload?.detail ??
        "The request could not be completed.",
      response.status,
      error?.code,
    );
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  searchTrials: (query: string) =>
    request<TrialSearchResponse>(
      `/v1/trials?query=${encodeURIComponent(query)}`,
    ),
  getTrial: (nctId: string) => request<TrialDraft>(`/v1/trials/${nctId}`),
  listAnalyses: () => request<Analysis[]>("/v1/analyses"),
  getAnalysis: (id: string) => request<Analysis>(`/v1/analyses/${id}`),
  createAnalysis: (payload: { title?: string; trial: TrialDraft }) =>
    request<Analysis>("/v1/analyses", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateAnalysis: (
    id: string,
    payload: { title?: string; trial?: TrialDraft },
  ) =>
    request<Analysis>(`/v1/analyses/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteAnalysis: (id: string) =>
    request<void>(`/v1/analyses/${id}`, { method: "DELETE" }),
};
