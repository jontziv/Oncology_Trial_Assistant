import { AuthGuard } from "@/components/auth-guard";

export default function AnalysesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <AuthGuard>{children}</AuthGuard>;
}
