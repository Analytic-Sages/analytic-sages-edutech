"use client";

import { useCurrencyPreference } from "@/components/providers/currency-preference-provider";
import { cn } from "@/lib/utils";

type CurrencyPriceProps = {
  amount: number;
  baseCurrency?: string;
  className?: string;
  showBasePrice?: boolean;
  tone?: "default" | "inverse";
};

export function CurrencyPrice({
  amount,
  baseCurrency = "USD",
  className,
  showBasePrice = true,
  tone = "default",
}: CurrencyPriceProps) {
  const { updatedAt, formatDisplayPrice, formatBasePrice, isConverted } =
    useCurrencyPreference();
  const converted = isConverted(baseCurrency);
  const displayPrice = formatDisplayPrice(amount, baseCurrency);
  const basePrice = formatBasePrice(amount, baseCurrency);
  const detailTextClass = tone === "inverse" ? "text-white/70" : "text-muted-foreground";

  return (
    <span className="inline-flex flex-col items-start gap-1">
      <span className={cn(className)}>
        {converted ? "≈ " : ""}
        {displayPrice}
      </span>
      {converted && showBasePrice ? (
        <span className={cn("text-xs font-normal leading-relaxed", detailTextClass)}>
          Approximate conversion · Base tuition {basePrice}
          {updatedAt ? (
            <>
              {" "}· Rates updated {new Date(updatedAt).toLocaleDateString(undefined, {
                year: "numeric",
                month: "short",
                day: "numeric",
                timeZone: "UTC",
              })}
            </>
          ) : null}
        </span>
      ) : null}
      {converted && showBasePrice ? (
        <span className={cn("text-[11px]", detailTextClass)}>
          Exchange-rate source: <a href="https://www.exchangerate-api.com" target="_blank" rel="noreferrer" className="underline underline-offset-2">ExchangeRate-API</a>
        </span>
      ) : null}
    </span>
  );
}
