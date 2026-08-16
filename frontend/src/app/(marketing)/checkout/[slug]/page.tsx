"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Bitcoin, Landmark, Loader2 } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  ApiCourse,
  createCheckout,
  getAccessToken,
  listApiCourses,
  type PaymentProvider,
} from "@/lib/api";
import { formatPrice, getCourseBySlug, isCourseLive } from "@/lib/mock-data";

const providers: {
  id: PaymentProvider;
  name: string;
  description: string;
  icon: typeof Landmark;
}[] = [
  {
    id: "paystack",
    name: "Paystack",
    description: "Cards and bank (NGN / USD)",
    icon: Landmark,
  },
  {
    id: "nowpayments",
    name: "Crypto (NOWPayments)",
    description: "BTC, ETH, USDT, and more",
    icon: Bitcoin,
  },
];

export default function CheckoutPage() {
  const params = useParams<{ slug: string }>();
  const router = useRouter();
  const slug = params.slug;

  const mockCourse = useMemo(() => getCourseBySlug(slug), [slug]);
  const [apiCourse, setApiCourse] = useState<ApiCourse | null>(null);
  const [token] = useState<string | null>(() =>
    typeof window !== "undefined" ? getAccessToken() : null
  );
  const [loadingProvider, setLoadingProvider] = useState<PaymentProvider | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listApiCourses()
      .then((courses) => {
        const match = courses.find((c) => c.slug === slug) ?? null;
        setApiCourse(match);
      })
      .catch(() => {
        // Backend may be offline: fall back to mock catalog for display.
      });
  }, [slug]);

  const title = apiCourse?.title ?? mockCourse?.title ?? "Course";
  const price = apiCourse?.price ?? mockCourse?.price ?? 0;
  const currency = apiCourse?.currency ?? mockCourse?.currency ?? "USD";
  const courseId = apiCourse?.id;
  const comingSoon = mockCourse?.comingSoon ?? !isCourseLive(slug);

  async function handleCheckout(provider: PaymentProvider) {
    setError(null);
    if (comingSoon || !isCourseLive(slug)) {
      setError("This course is launching soon and is not open for enrollment yet.");
      return;
    }
    if (!getAccessToken()) {
      router.push(`/login?next=/checkout/${slug}`);
      return;
    }
    if (!courseId) {
      setError(
        "This course is not available in the API yet. Run `python scripts/seed_courses.py` on the backend."
      );
      return;
    }

    setLoadingProvider(provider);
    try {
      const session = await createCheckout(courseId, provider);
      window.location.assign(session.checkout_url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Checkout failed");
      setLoadingProvider(null);
    }
  }

  if (!mockCourse && !apiCourse) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <PageHeader title="Course not found" description="Choose a course from the catalog." />
        <ButtonLink href="/courses">Browse courses</ButtonLink>
      </div>
    );
  }

  if (comingSoon || !isCourseLive(slug)) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <PageHeader
          title="Launching soon"
          description={`${title} isn’t open for self-paced enrollment yet. Join Instructor-Led Training for live cohorts.`}
        />
        <div className="flex flex-wrap gap-3">
          <ButtonLink href={`/courses/${slug}`}>Back to course</ButtonLink>
          <ButtonLink href="/instructor-led" variant="outline">
            View Instructor-Led Training
          </ButtonLink>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        breadcrumbs={[
          { label: "Courses", href: "/courses" },
          { label: title, href: `/courses/${slug}` },
          { label: "Checkout" },
        ]}
        title="Checkout"
        description="Choose how you want to pay. Access unlocks only after payment is confirmed."
      />

      <Card className="mb-8 shadow-card">
        <CardHeader>
          <CardTitle className="text-xl">{title}</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-between">
          <p className="text-muted-foreground">Amount due</p>
          <p className="font-heading text-2xl font-bold text-brand-navy">
            {formatPrice(price, currency)}
          </p>
        </CardContent>
      </Card>

      {!token && (
        <div className="mb-6 rounded-xl border border-brand-orange/30 bg-brand-orange/5 p-4 text-sm">
          You need to be signed in to checkout.{" "}
          <ButtonLink href={`/login?next=/checkout/${slug}`} variant="link" className="px-1">
            Sign in
          </ButtonLink>
          or{" "}
          <ButtonLink href="/register" variant="link" className="px-1">
            create an account
          </ButtonLink>
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid gap-4">
        {providers.map((provider) => (
          <button
            key={provider.id}
            type="button"
            disabled={loadingProvider !== null}
            onClick={() => handleCheckout(provider.id)}
            className="flex items-center gap-4 rounded-2xl border bg-card p-5 text-left shadow-card transition hover:-translate-y-0.5 hover:shadow-elevated disabled:opacity-60"
          >
            <div className="flex size-12 items-center justify-center rounded-xl bg-brand-navy/10 text-brand-navy">
              {loadingProvider === provider.id ? (
                <Loader2 className="size-5 animate-spin" />
              ) : (
                <provider.icon className="size-5" />
              )}
            </div>
            <div className="flex-1">
              <p className="font-heading text-lg font-semibold">{provider.name}</p>
              <p className="text-sm text-muted-foreground">{provider.description}</p>
            </div>
            <span className="text-sm font-medium text-brand-orange">Pay</span>
          </button>
        ))}
      </div>

      <p className="mt-8 text-sm text-muted-foreground">
        Mock mode is active until live Paystack / NOWPayments keys are configured.
        Enrollment is never unlocked from this page, only from a verified webhook.
      </p>
    </div>
  );
}
