import { createBrowserClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";

let client: SupabaseClient | null = null;

export function getSupabaseBrowserClient() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key) {
    return null;
  }
  client ??= createBrowserClient(url, key);
  return client;
}

export function isDemoMode() {
  return process.env.NEXT_PUBLIC_DEMO_MODE !== "false";
}
