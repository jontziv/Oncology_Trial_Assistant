import { afterEach, describe, expect, it, vi } from "vitest";
import { GET } from "@/app/api/backend/[...path]/route";

describe("backend API relay", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("forwards API paths, query parameters, and allowed headers", async () => {
    const upstreamFetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(Response.json({ items: [] }));
    const request = new Request(
      "https://web.example/api/backend/v1/trials?query=NSCLC",
      {
        headers: {
          "X-Demo-User-Id": "00000000-0000-0000-0000-000000000001",
        },
      },
    );

    const response = await GET(request, {
      params: Promise.resolve({ path: ["v1", "trials"] }),
    });

    expect(response.status).toBe(200);
    expect(upstreamFetch).toHaveBeenCalledOnce();
    const [url, init] = upstreamFetch.mock.calls[0] ?? [];
    expect(String(url)).toBe(
      "https://oncology-trial-assistant.onrender.com/v1/trials?query=NSCLC",
    );
    expect(new Headers(init?.headers).get("x-demo-user-id")).toBe(
      "00000000-0000-0000-0000-000000000001",
    );
  });

  it("rejects paths outside the application API", async () => {
    const response = await GET(
      new Request("https://web.example/api/backend/not-allowed"),
      {
        params: Promise.resolve({ path: ["not-allowed"] }),
      },
    );

    expect(response.status).toBe(404);
  });
});
