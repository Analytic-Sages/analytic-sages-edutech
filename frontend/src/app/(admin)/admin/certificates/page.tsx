import { ComingSoonPanel } from "@/components/admin/coming-soon-panel";
import { PageHeader } from "@/components/layout/page-header";

export const metadata = { title: "Certificates" };

export default function AdminCertificatesPage() {
  return (
    <div>
      <PageHeader title="Certificates" description="Certificate issuing is not live yet." />
      <ComingSoonPanel
        title="Coming soon"
        description="No certificates are being issued. This page no longer shows sample cards."
      />
    </div>
  );
}
