"use client";

import { Check, Link2 } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ButtonAnchor } from "@/components/ui/button-anchor";
import { absoluteUrl } from "@/lib/seo";

export function ArticleShare({ title, path }: { title: string; path: string }) {
  const [copied, setCopied] = useState(false);
  const url = absoluteUrl(path);
  const encoded = encodeURIComponent(url);
  const text = encodeURIComponent(title);

  async function copy() {
    const toCopy = `${window.location.origin}${path}`;
    await navigator.clipboard.writeText(toCopy);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="flex flex-wrap gap-2">
      <ButtonAnchor variant="outline" size="sm" href={`https://www.linkedin.com/sharing/share-offsite/?url=${encoded}`} target="_blank" rel="noreferrer">
        LinkedIn
      </ButtonAnchor>
      <ButtonAnchor variant="outline" size="sm" href={`https://twitter.com/intent/tweet?url=${encoded}&text=${text}`} target="_blank" rel="noreferrer">
        X
      </ButtonAnchor>
      <ButtonAnchor variant="outline" size="sm" href={`https://wa.me/?text=${encoded}`} target="_blank" rel="noreferrer">
        WhatsApp
      </ButtonAnchor>
      <Button type="button" variant="outline" size="sm" onClick={() => void copy()}>
        {copied ? <Check className="size-3.5" /> : <Link2 className="size-3.5" />}
        {copied ? "Copied" : "Copy link"}
      </Button>
    </div>
  );
}
