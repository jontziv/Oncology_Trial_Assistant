import { AnalysisResults } from "@/components/analysis-results";

export default async function AnalysisResultsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <AnalysisResults id={id} />;
}
