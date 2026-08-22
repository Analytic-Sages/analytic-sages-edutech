import { formatPrice } from "@/lib/mock-data";

export type CatalogPriceInput = {
  price: number;
  currency?: string;
  isFree?: boolean;
  is_free?: boolean;
  comingSoon?: boolean;
};

export function catalogIsFree(course: CatalogPriceInput): boolean {
  if (course.isFree === true || course.is_free === true) return true;
  // Upcoming self-paced catalog items are paid unless marked free.
  if (course.comingSoon) return false;
  return course.price === 0;
}

export function catalogPriceLabel(course: CatalogPriceInput): string {
  if (catalogIsFree(course)) return "FREE";
  if (course.price > 0) return formatPrice(course.price, course.currency ?? "USD");
  return "Paid";
}

/** Overlay badge: FREE | PAID · $35 | PAID · COMING SOON */
export function catalogOfferBadgeLabel(course: CatalogPriceInput): string {
  if (catalogIsFree(course)) return "FREE";
  if (course.price > 0) return `PAID · ${formatPrice(course.price, course.currency ?? "USD")}`;
  if (course.comingSoon) return "PAID · COMING SOON";
  return "PAID";
}

/** Footer amount/status next to the catalog CTA. */
export function catalogFooterPriceLabel(course: CatalogPriceInput): string {
  if (catalogIsFree(course)) return "FREE";
  if (course.comingSoon) return "Launching soon";
  return catalogPriceLabel(course);
}

export function catalogBrowseCta(course: CatalogPriceInput): string {
  if (catalogIsFree(course)) return "Start Learning";
  if (course.comingSoon) return "View Details";
  return "View Course";
}
