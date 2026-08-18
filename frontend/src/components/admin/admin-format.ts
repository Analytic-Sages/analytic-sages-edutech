import { formatPrice } from "@/lib/mock-data";
import { initialsFor } from "@/lib/user-display";

export { initialsFor };

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
