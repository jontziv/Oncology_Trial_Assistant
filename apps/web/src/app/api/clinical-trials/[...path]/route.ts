const CLINICAL_TRIALS_API = "https://clinicaltrials.gov/api/v2";
const ALLOWED_PATH = /^studies(?:\/NCT\d{8})?$/i;

export async function GET(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
) {
  const { path } = await context.params;
  const upstreamPath = path.join("/");

  if (!ALLOWED_PATH.test(upstreamPath)) {
    return Response.json(
      { error: { message: "Unsupported ClinicalTrials.gov path." } },
      { status: 404 },
    );
  }

  const requestUrl = new URL(request.url);
  const upstreamUrl = new URL(`${CLINICAL_TRIALS_API}/${upstreamPath}`);
  requestUrl.searchParams.forEach((value, key) => {
    upstreamUrl.searchParams.append(key, value);
  });

  try {
    const upstream = await fetch(upstreamUrl, {
      headers: {
        Accept: "application/json",
        "User-Agent": "OncologyTrialFeasibilityCopilot/0.1",
      },
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
          message: "ClinicalTrials.gov could not be reached by the relay.",
        },
      },
      { status: 502 },
    );
  }
}
