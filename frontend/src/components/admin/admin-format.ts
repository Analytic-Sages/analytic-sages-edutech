import { formatPrice } from "@/lib/mock-data";

export function formatAdminDate(iso: string | null | undefined) {
  if (!iso) return "—";
  try {
    return new Intl.DateTimeFormat(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(iso));
  } catch {
    return iso;
  }
}

export function initialsFor(name: string | null, email: string) {
  const source = (name || email).trim();
  const parts = source.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
  }
  return source.slice(0, 2).toUpperCase();
}

export function paymentStatusClass(status: string) {
  if (status === "confirmed") return "bg-success/10 text-success";
  if (status === "pending" || status === "confirming") return "bg-warning/10 text-warning";
  return "bg-destructive/10 text-destructive";
}

export function formatMoneyList(
  rows: Array<{ currency: string; confirmed_amount: number; pending_amount?: number }>,
  field: "confirmed_amount" | "pending_amount" = "confirmed_amount"
) {
  if (!rows.length) return formatPrice(0, "USD");
  return rows.map((row) => formatPrice(row[field] ?? 0, row.currency)).join(" · ");
}
