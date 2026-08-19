import { ComingSoonPanel } from "@/components/admin/coming-soon-panel";
import { PageHeader } from "@/components/layout/page-header";

export const metadata = { title: "Certificates" };

export default function CertificatesPage() {
  return (
    <div>
      <PageHeader
        title="Certificates"
        description="Verified credentials will appear here when issuing is live."
      />
      <ComingSoonPanel
        title="Coming soon"
        description="Platform certificates are not issued yet. Completing a course still gives you the work you can show."
      />
    </div>
  );
}
