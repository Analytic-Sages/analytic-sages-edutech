import { CertificateCard } from "@/components/course/certificate-card";
import { PageHeader } from "@/components/layout/page-header";
import { EmptyState } from "@/components/shared/empty-state";
import { certificates } from "@/lib/mock-data";
import { Award } from "lucide-react";

export const metadata = { title: "Certificates" };

export default function CertificatesPage() {
  return (
    <div>
      <PageHeader
        title="Certificates"
        description="Your verified credentials and achievements"
      />
      {certificates.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {certificates.map((cert) => (
            <CertificateCard key={cert.id} certificate={cert} />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<Award className="size-5" />}
          title="No certificates yet"
          description="Complete a course and pass all assessments to earn your first certificate."
          action={{ label: "Explore Courses", href: "/explore" }}
        />
      )}
    </div>
  );
}
