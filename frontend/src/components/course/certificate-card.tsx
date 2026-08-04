import { Award, Download, Share2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Certificate } from "@/types/course";

type CertificateCardProps = {
  certificate: Certificate;
};

export function CertificateCard({ certificate }: CertificateCardProps) {
  return (
    <Card className="shadow-card">
      <CardHeader className="flex flex-row items-start justify-between">
        <div className="flex size-10 items-center justify-center rounded-lg bg-brand-navy/10">
          <Award className="size-5 text-brand-navy" />
        </div>
        <Badge variant="outline" className="font-mono text-xs">
          {certificate.certificateId}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <CardTitle className="text-base">{certificate.courseTitle}</CardTitle>
        <p className="text-sm text-muted-foreground">
          Issued {new Date(certificate.issuedAt).toLocaleDateString("en-US", {
            year: "numeric",
            month: "long",
            day: "numeric",
          })}
        </p>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" className="gap-1.5">
            <Download className="size-3.5" />
            Download
          </Button>
          <Button size="sm" variant="ghost" className="gap-1.5">
            <Share2 className="size-3.5" />
            Share
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
