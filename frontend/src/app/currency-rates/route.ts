import { NextResponse } from "next/server";

export const revalidate = 86_400;

const SUPPORTED_CURRENCIES = [
  "USD",
  "NGN",
  "GHS",
  "KES",
  "ZAR",
  "GBP",
  "EUR",
  "CAD",
  "AUD",
  "INR",
  "RWF",
  "UGX",
  "TZS",
  "XOF",
] as const;

type ExchangeRateResponse = {
  result?: string;
  base_code?: string;
  rates?: Record<string, number>;
  time_last_update_utc?: string;
  time_next_update_utc?: string;
};

export async function GET() {
  try {
    const response = await fetch("https://open.er-api.com/v6/latest/USD", {
      next: { revalidate: 86_400 },
      headers: { Accept: "application/json" },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: "Exchange rates are temporarily unavailable." },
        { status: 503, headers: { "Cache-Control": "no-store" } },
      );
    }

    const data = (await response.json()) as ExchangeRateResponse;
    if (data.result !== "success" || data.base_code !== "USD" || !data.rates) {
      return NextResponse.json(
        { error: "Exchange-rate provider returned an invalid response." },
        { status: 503, headers: { "Cache-Control": "no-store" } },
      );
    }

    const rates = Object.fromEntries(
      SUPPORTED_CURRENCIES.flatMap((currency) => {
        const rate = data.rates?.[currency];
        return typeof rate === "number" && Number.isFinite(rate) && rate > 0
          ? [[currency, rate]]
          : [];
      }),
    );

    return NextResponse.json(
      {
        base: "USD",
        rates,
        updatedAt: data.time_last_update_utc ?? null,
        nextUpdateAt: data.time_next_update_utc ?? null,
        source: "ExchangeRate-API Open Access",
        sourceUrl: "https://www.exchangerate-api.com",
      },
      {
        headers: {
          "Cache-Control": "public, s-maxage=86400, stale-while-revalidate=3600",
        },
      },
    );
  } catch {
    return NextResponse.json(
      { error: "Exchange rates are temporarily unavailable." },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
}
