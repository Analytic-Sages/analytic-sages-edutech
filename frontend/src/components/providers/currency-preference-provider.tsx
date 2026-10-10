"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { formatPrice as formatBasePrice } from "@/lib/mock-data";

export const DISPLAY_CURRENCIES = [
  { code: "USD", label: "US dollar" },
  { code: "NGN", label: "Nigerian naira" },
  { code: "GHS", label: "Ghanaian cedi" },
  { code: "KES", label: "Kenyan shilling" },
  { code: "ZAR", label: "South African rand" },
  { code: "GBP", label: "British pound" },
  { code: "EUR", label: "Euro" },
  { code: "CAD", label: "Canadian dollar" },
  { code: "AUD", label: "Australian dollar" },
  { code: "INR", label: "Indian rupee" },
  { code: "RWF", label: "Rwandan franc" },
  { code: "UGX", label: "Ugandan shilling" },
  { code: "TZS", label: "Tanzanian shilling" },
  { code: "XOF", label: "West African CFA franc" },
] as const;

export type DisplayCurrency = (typeof DISPLAY_CURRENCIES)[number]["code"];

type RatePayload = {
  base: "USD";
  rates: Record<string, number>;
  updatedAt: string | null;
  nextUpdateAt: string | null;
  source: string;
  sourceUrl: string;
};

type CurrencyPreferenceValue = {
  currency: DisplayCurrency;
  setCurrency: (currency: DisplayCurrency) => void;
  rates: Record<string, number> | null;
  updatedAt: string | null;
  formatDisplayPrice: (amount: number, baseCurrency?: string) => string;
  formatBasePrice: (amount: number, baseCurrency?: string) => string;
  isConverted: (baseCurrency?: string) => boolean;
};

const STORAGE_KEY = "analytic-sages-display-currency";
const DEFAULT_CURRENCY: DisplayCurrency = "USD";

const REGION_CURRENCY: Record<string, DisplayCurrency> = {
  NG: "NGN",
  GH: "GHS",
  KE: "KES",
  ZA: "ZAR",
  GB: "GBP",
  IE: "EUR",
  DE: "EUR",
  FR: "EUR",
  ES: "EUR",
  IT: "EUR",
  NL: "EUR",
  PT: "EUR",
  RW: "RWF",
  UG: "UGX",
  TZ: "TZS",
  IN: "INR",
  AU: "AUD",
  CA: "CAD",
};

const LOCALE_BY_CURRENCY: Record<DisplayCurrency, string> = {
  USD: "en-US",
  NGN: "en-NG",
  GHS: "en-GH",
  KES: "en-KE",
  ZAR: "en-ZA",
  GBP: "en-GB",
  EUR: "en-IE",
  CAD: "en-CA",
  AUD: "en-AU",
  INR: "en-IN",
  RWF: "rw-RW",
  UGX: "en-UG",
  TZS: "sw-TZ",
  XOF: "fr-SN",
};

const ZERO_DECIMAL_DISPLAY = new Set<DisplayCurrency>([
  "NGN",
  "KES",
  "UGX",
  "TZS",
  "RWF",
  "XOF",
  "INR",
]);

const CurrencyPreferenceContext = createContext<CurrencyPreferenceValue | null>(null);

function isDisplayCurrency(value: string): value is DisplayCurrency {
  return DISPLAY_CURRENCIES.some((currency) => currency.code === value);
}

function inferCurrencyFromLocale(locale: string): DisplayCurrency {
  const normalized = locale.replace("_", "-");
  const region = normalized.split("-")[1]?.toUpperCase();
  return (region && REGION_CURRENCY[region]) || DEFAULT_CURRENCY;
}

function formatCurrency(amount: number, currency: DisplayCurrency): string {
  return new Intl.NumberFormat(LOCALE_BY_CURRENCY[currency], {
    style: "currency",
    currency,
    maximumFractionDigits: ZERO_DECIMAL_DISPLAY.has(currency) ? 0 : 2,
  }).format(amount);
}

export function CurrencyPreferenceProvider({ children }: { children: ReactNode }) {
  const [currency, setCurrencyState] = useState<DisplayCurrency>(DEFAULT_CURRENCY);
  const [rates, setRates] = useState<Record<string, number> | null>(null);
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    // Read browser-only preferences after mount to avoid server/client hydration mismatches.
    // Deferring the state update also keeps it out of the synchronous effect body.
    Promise.resolve().then(() => {
      if (cancelled) return;

      let preferredCurrency = DEFAULT_CURRENCY;
      try {
        const saved = window.localStorage.getItem(STORAGE_KEY);
        preferredCurrency =
          saved && isDisplayCurrency(saved)
            ? saved
            : inferCurrencyFromLocale(window.navigator.language);
      } catch {
        preferredCurrency = inferCurrencyFromLocale(window.navigator.language);
      }

      if (!cancelled) setCurrencyState(preferredCurrency);
    });

    fetch("/currency-rates", { headers: { Accept: "application/json" } })
      .then(async (response) => {
        if (!response.ok) throw new Error("Exchange rates unavailable");
        return (await response.json()) as RatePayload;
      })
      .then((payload) => {
        if (!cancelled && payload.base === "USD" && payload.rates?.USD === 1) {
          setRates(payload.rates);
          setUpdatedAt(payload.updatedAt);
        }
      })
      .catch(() => {
        // Keep the base-currency price visible if the rate service is unavailable.
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const setCurrency = useCallback((nextCurrency: DisplayCurrency) => {
    setCurrencyState(nextCurrency);
    try {
      window.localStorage.setItem(STORAGE_KEY, nextCurrency);
    } catch {
      // Currency selection still works for the current page if storage is blocked.
    }
  }, []);

  const formatBase = useCallback((amount: number, baseCurrency = "USD") => {
    return formatBasePrice(amount, baseCurrency);
  }, []);

  const converted = useCallback(
    (amount: number, baseCurrency = "USD") => {
      if (!Number.isFinite(amount) || amount < 0) return formatBasePrice(amount, baseCurrency);
      const source = baseCurrency.toUpperCase();
      if (source === currency) return formatCurrency(amount, currency);
      if (!rates || !isDisplayCurrency(source) || !rates[source] || !rates[currency]) {
        return formatBasePrice(amount, source);
      }
      const amountInUsd = source === "USD" ? amount : amount / rates[source];
      const result = amountInUsd * rates[currency];
      return formatCurrency(result, currency);
    },
    [currency, rates],
  );

  const isConverted = useCallback(
    (baseCurrency = "USD") => {
      const source = baseCurrency.toUpperCase();
      return (
        source !== currency &&
        isDisplayCurrency(source) &&
        Boolean(rates?.[source]) &&
        Boolean(rates?.[currency])
      );
    },
    [currency, rates],
  );

  const value = useMemo(
    () => ({
      currency,
      setCurrency,
      rates,
      updatedAt,
      formatDisplayPrice: converted,
      formatBasePrice: formatBase,
      isConverted,
    }),
    [currency, setCurrency, rates, updatedAt, converted, formatBase, isConverted],
  );

  return (
    <CurrencyPreferenceContext.Provider value={value}>
      {children}
    </CurrencyPreferenceContext.Provider>
  );
}

export function useCurrencyPreference() {
  const value = useContext(CurrencyPreferenceContext);
  if (!value) {
    throw new Error("useCurrencyPreference must be used within CurrencyPreferenceProvider");
  }
  return value;
}
