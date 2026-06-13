const RENDER_API_URL = (
  process.env.API_SERVER_URL ?? "https://oncology-trial-assistant.onrender.com"
).replace(/\/+$/, "");

const FORWARDED_HEADERS = [
  "authorization",
  "content-type",
  "idempotency-key",
  "x-demo-user-id",
];

export const dynamic = "force-dynamic";
export const maxDuration = 60;

async function forward(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  if (path[0] !== "v1" && path[0] !== "health") {
    return Response.json(
      { error: { message: "Unsupported API path." } },
      { status: 404 },
    );
  }

  const requestUrl = new URL(request.url);
  const upstreamUrl = new URL(`${RENDER_API_URL}/${path.join("/")}`);
  upstreamUrl.search = requestUrl.search;

  const headers = new Headers();
  for (const name of FORWARDED_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  const hasBody = !["GET", "HEAD"].includes(request.method);
  try {
    const upstream = await fetch(upstreamUrl, {
      method: request.method,
      headers,
      body: hasBody ? await request.arrayBuffer() : undefined,
      cache: "no-store",
    });

    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        "Content-Type":
          upstream.headers.get("content-type") ?? "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return Response.json(
      {
        error: {
          code: "API_UNREACHABLE",
          message: "The Render API is temporarily unreachable.",
        },
      },
      { status: 502 },
    );
  }
}

export const GET = forward;
export const POST = forward;
export const PATCH = forward;
export const DELETE = forward;
export const OPTIONS = forward;
