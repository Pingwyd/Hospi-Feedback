import { ReportDetailPanel } from "@/components/admin/ReportDetailPanel";

type AdminReportDetailPageProps = {
  params: Promise<{ id: string }>;
};

export default async function AdminReportDetailPage({
  params,
}: AdminReportDetailPageProps) {
  const { id } = await params;
  return <ReportDetailPanel reportId={id} />;
}
