import { Badge } from "@/components/ui/badge";
import { BADGE_COPY, type PublicBadge } from "@/lib/opportunities";

export function OpportunityTrustBadge({
  badge,
  showMeaning = false,
}: {
  badge: PublicBadge;
  showMeaning?: boolean;
}) {
  if (badge === "none") return null;
  const copy = BADGE_COPY[badge];
  return (
    <span className="inline-flex flex-col gap-1">
      <Badge className="bg-brand-navy text-white">{copy.label}</Badge>
      {showMeaning ? <span className="text-xs text-muted-foreground">{copy.meaning}</span> : null}
    </span>
  );
}
