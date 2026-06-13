import { EditAnalysis } from "@/components/edit-analysis";

export default async function EditAnalysisPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <EditAnalysis id={id} />;
}
