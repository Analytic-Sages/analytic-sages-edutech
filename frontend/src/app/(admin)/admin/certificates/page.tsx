import { PageHeader } from "@/components/layout/page-header";
import { CertificateCard } from "@/components/course/certificate-card";
import { certificates } from "@/lib/mock-data";

export const metadata = { title: "Certificates" };

export default function AdminCertificatesPage() {
  return (
    <div>
      <PageHeader title="Certificates" description="View and manage issued certificates" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {certificates.map((cert) => (
          <CertificateCard key={cert.id} certificate={cert} />
        ))}
      </div>
    </div>
  );
}
