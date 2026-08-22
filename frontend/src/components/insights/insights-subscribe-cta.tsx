"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api";
import { subscribeInsights } from "@/lib/insights";

export function InsightsSubscribeCta() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [subscribed, setSubscribed] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    const value = email.trim();
    if (!value) {
      setError("Enter your email address.");
      return;
    }
    setPending(true);
    try {
      await subscribeInsights(value);
      setSubscribed(value);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : "We could not add you to the list. Please try again.",
      );
    } finally {
      setPending(false);
    }
  }

  if (subscribed) {
    return (
      <aside className="rounded-2xl border bg-card p-6 sm:p-8">
        <p className="font-heading text-xl font-bold">You're on the list</p>
        <p className="mt-2 max-w-xl text-sm text-muted-foreground">
          We will email new Insights to <span className="font-medium text-foreground">{subscribed}</span>{" "}
          when they are published. Custom updates may also come from Analytic Sages. You can
          unsubscribe from any of those emails.
        </p>
      </aside>
    );
  }

  return (
    <aside className="rounded-2xl border bg-card p-6 sm:p-8">
      <p className="font-heading text-xl font-bold">Build. Learn. Stay ahead.</p>
      <p className="mt-2 max-w-xl text-sm text-muted-foreground">
        Get new Analytic Sages Insights by email when they are published. No account required.
      </p>
      <form className="mt-4 flex flex-col gap-2 sm:flex-row" onSubmit={onSubmit} noValidate>
        <Input
          type="email"
          name="email"
          autoComplete="email"
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          aria-label="Email"
          aria-invalid={error ? true : undefined}
          disabled={pending}
          required
        />
        <Button type="submit" disabled={pending}>
          {pending ? "Subscribing…" : "Subscribe"}
        </Button>
      </form>
      {error ? <p className="mt-2 text-sm text-destructive">{error}</p> : null}
      <p className="mt-3 text-xs text-muted-foreground">
        By subscribing you agree we may email you Insights and occasional Analytic Sages updates.
        See our{" "}
        <Link href="/privacy" className="underline underline-offset-2 hover:text-foreground">
          Privacy Policy
        </Link>
        . Unsubscribe anytime.
      </p>
    </aside>
  );
}
