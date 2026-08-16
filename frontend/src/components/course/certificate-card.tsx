"use client";

import { useState } from "react";
import { Award, CheckCircle2, Download, ExternalLink, QrCode, Share2, ShieldCheck } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import type { Certificate } from "@/types/course";

type CertificateCardProps = {
  certificate: Certificate;
};

export function CertificateCard({ certificate }: CertificateCardProps) {
  const [open, setOpen] = useState(false);

  const formattedDate = new Date(certificate.issuedAt).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const handleLinkedInShare = () => {
    const url = `https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&name=${encodeURIComponent(
      certificate.courseTitle
    )}&organizationName=${encodeURIComponent("Analytic Sages")}&issueYear=${new Date(
      certificate.issuedAt
    ).getFullYear()}&issueMonth=${new Date(
      certificate.issuedAt
    ).getMonth() + 1}&certUrl=${encodeURIComponent("https://analyticsages.io/verify/" + certificate.certificateId)}`;
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <>
      <Card className="shadow-card transition-all duration-300 hover:-translate-y-0.5 hover:shadow-elevated">
        <CardHeader className="flex flex-row items-start justify-between">
          <div className="flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-navy to-brand-navy/80 text-white">
            <Award className="size-5" />
          </div>
          <Badge variant="outline" className="font-mono text-[0.7rem] bg-background">
            {certificate.certificateId}
          </Badge>
        </CardHeader>
        <CardContent className="space-y-4">
          <CardTitle className="text-base font-heading line-clamp-2">{certificate.courseTitle}</CardTitle>
          <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
            <ShieldCheck className="size-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>Issued {formattedDate}</span>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger
                render={
                  <Button size="sm" className="bg-brand-navy text-white hover:bg-brand-navy/90 gap-1.5">
                    <ExternalLink className="size-3.5" />
                    View Certificate
                  </Button>
                }
              />
              <DialogContent className="max-w-2xl overflow-hidden p-0">
                <DialogHeader className="border-b bg-muted/40 p-4">
                  <DialogTitle className="flex items-center gap-2 text-base">
                    <Award className="size-5 text-brand-orange" /> Verified Academic Credential
                  </DialogTitle>
                </DialogHeader>

                {/* Printable Certificate Frame */}
                <div className="p-6 sm:p-8">
                  <div className="relative overflow-hidden rounded-2xl border-4 border-double border-brand-navy/20 bg-gradient-to-br from-background via-brand-surface to-brand-warm/30 p-8 shadow-inner text-center">
                    <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-full bg-brand-navy text-white shadow-elevated">
                      <Award className="size-7" />
                    </div>

                    <p className="text-xs font-semibold uppercase tracking-widest text-brand-orange">
                      Analytic Sages Global Blockchain School
                    </p>
                    <h2 className="mt-2 font-heading text-2xl font-bold tracking-tight sm:text-3xl text-foreground">
                      Certificate of Achievement
                    </h2>
                    <p className="mt-2 text-xs text-muted-foreground">This hereby certifies that</p>
                    <p className="mt-1 font-heading text-xl font-bold text-brand-navy dark:text-brand-orange">
                      {certificate.recipientName || "Valued Scholar"}
                    </p>
                    <p className="mt-2 text-xs text-muted-foreground">
                      has successfully mastered the curriculum and demonstrated practical competence in
                    </p>
                    <h3 className="mt-2 font-heading text-lg font-bold text-foreground">
                      {certificate.courseTitle}
                    </h3>

                    <div className="mt-6 flex flex-col items-center justify-between border-t border-border/60 pt-6 sm:flex-row">
                      <div className="text-left text-xs text-muted-foreground">
                        <p className="font-semibold text-foreground">Issued: {formattedDate}</p>
                        <p className="font-mono text-[0.7rem]">ID: {certificate.certificateId}</p>
                      </div>

                      <div className="mt-4 sm:mt-0 flex items-center gap-3 rounded-lg border bg-background/80 p-2 shadow-xs">
                        <QrCode className="size-8 text-brand-navy" />
                        <div className="text-left text-[0.68rem] leading-tight font-mono">
                          <span className="font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                            <CheckCircle2 className="size-3" /> VERIFIED
                          </span>
                          <span className="text-muted-foreground">Onchain Credential</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Actions Bar */}
                  <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
                    <Button variant="outline" size="sm" onClick={handleLinkedInShare} className="gap-1.5 border-blue-500/30 text-blue-600 hover:bg-blue-50 dark:text-blue-400">
                      <Share2 className="size-3.5" />
                      Add to LinkedIn Profile
                    </Button>

                    <Button size="sm" onClick={handlePrint} className="bg-brand-orange text-white hover:bg-brand-orange/90 gap-1.5">
                      <Download className="size-3.5" />
                      Download / Print PDF
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>

            <Button size="sm" variant="outline" onClick={handleLinkedInShare} className="gap-1 text-xs">
              <Share2 className="size-3" />
              Share
            </Button>
          </div>
        </CardContent>
      </Card>
    </>
  );
}

