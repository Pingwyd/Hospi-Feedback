import Link from "next/link";

import { StatusPanel } from "@/components/status/StatusPanel";

type StatusTicketPageProps = {
  params: Promise<{ ticketCode: string }>;
};

export default async function StatusTicketPage({ params }: StatusTicketPageProps) {
  const { ticketCode } = await params;
  const normalized = decodeURIComponent(ticketCode).toUpperCase();

  return (
    <main className="mx-auto max-w-2xl px-6 py-12 md:py-16">
      <StatusPanel ticketCode={normalized} />
      <p className="mt-8 text-center text-xs text-ink/50">
        <Link href="/report" className="font-medium text-sage underline">
          Submit a new report
        </Link>
      </p>
    </main>
  );
}
