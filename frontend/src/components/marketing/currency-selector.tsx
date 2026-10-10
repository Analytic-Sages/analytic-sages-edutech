"use client";

import {
  DISPLAY_CURRENCIES,
  useCurrencyPreference,
} from "@/components/providers/currency-preference-provider";

export function CurrencySelector() {
  const { currency, setCurrency } = useCurrencyPreference();

  return (
    <label className="inline-flex items-center gap-2 text-sm text-muted-foreground">
      <span className="hidden xl:inline">Display currency</span>
      <span className="sr-only">Display currency</span>
      <select
        aria-label="Display currency"
        value={currency}
        onChange={(event) => setCurrency(event.target.value as typeof currency)}
        className="h-9 max-w-[6.5rem] rounded-md border border-border bg-background px-2 text-sm font-medium text-foreground outline-none focus-visible:ring-2 focus-visible:ring-brand-orange"
      >
        {DISPLAY_CURRENCIES.map((item) => (
          <option key={item.code} value={item.code}>
            {item.code}
          </option>
        ))}
      </select>
    </label>
  );
}
