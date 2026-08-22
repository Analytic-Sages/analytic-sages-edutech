import { Badge } from "@/components/ui/badge";
import { catalogIsFree, catalogOfferBadgeLabel } from "@/lib/catalog-price";
import { cn } from "@/lib/utils";

type Props = {
  price: number;
  currency?: string;
  isFree?: boolean;
  is_free?: boolean;
  comingSoon?: boolean;
};

export function CatalogOfferBadges({ price, currency, isFree, is_free, comingSoon }: Props) {
  const offer = { price, currency, isFree, is_free, comingSoon };
  const free = catalogIsFree(offer);

  return (
    <Badge
      className={cn(
        "absolute top-3 left-3 max-w-[calc(100%-1.5rem)] shadow-sm",
        free ? "bg-brand-orange text-white" : "bg-brand-navy text-white"
      )}
    >
      {catalogOfferBadgeLabel(offer)}
    </Badge>
  );
}
