"use client";

import { useCurrencyPreference } from "@/components/providers/currency-preference-provider";
import { cn } from "@/lib/utils";

type CurrencyPriceProps = {
  amount: number;
  baseCurrency?: string;
  className?: string;
  showBasePrice?: boolean;
};

export function CurrencyPrice({
  amount,
  baseCurrency = "USD",
  className,
  showBasePrice = true,
}: CurrencyPriceProps) {
  const { currency, updatedAt, formatDisplayPrice, formatBasePrice, isConverted } =
    useCurrencyPreference();
  const converted = isConverted(baseCurrency);
  const displayPrice = formatDisplayPrice(amount, baseCurrency);
  const basePrice = formatBasePrice(amount, baseCurrency);

  return (
    <span className="inline-flex flex-col items-start gap-1">
      <span className={cn(className)}>
        {converted ? "≈ " : ""}
        {displayPrice}
      </span>
      {converted && showBasePrice ? (
        <span className="text-xs font-normal leading-relaxed text-muted-foreground">
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
        <span className="text-[11px] text-muted-foreground">
          Exchange-rate source: <a href="https://www.exchangerate-api.com" target="_blank" rel="noreferrer" className="underline underline-offset-2">ExchangeRate-API</a>
        </span>
      ) : null}
      {currency === baseCurrency ? null : null}
    </span>
  );
}
