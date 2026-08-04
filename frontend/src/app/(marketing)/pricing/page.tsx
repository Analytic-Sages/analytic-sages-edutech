import { Check } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const plans = [
  {
    name: "Single Course",
    price: "From ₦75,000",
    description: "Pay per course. Lifetime access to purchased content.",
    features: [
      "Full course access",
      "Downloadable resources",
      "Quizzes & assessments",
      "Verified certificate",
      "Community access",
    ],
    cta: "Browse Courses",
    href: "/courses",
    highlighted: false,
  },
  {
    name: "Professional",
    price: "₦249,000",
    period: "/year",
    description: "Unlimited access to all current and future courses.",
    features: [
      "Everything in Single Course",
      "All premium courses",
      "Priority support",
      "Live session recordings",
      "Early access to new courses",
    ],
    cta: "Get Started",
    href: "/register",
    highlighted: true,
  },
  {
    name: "Teams",
    price: "Custom",
    description: "For companies training engineers and analysts at scale.",
    features: [
      "Volume licensing",
      "Team progress dashboard",
      "Custom learning paths",
      "Dedicated account manager",
      "Invoice billing",
    ],
    cta: "Contact Sales",
    href: "/contact",
    highlighted: false,
  },
];

export const metadata = { title: "Pricing" };

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <PageHeader
        title="Simple, transparent pricing"
        description="Invest in skills that translate to real career outcomes"
        className="text-center [&_h1]:mx-auto [&_p]:mx-auto"
      />
      <div className="mt-12 grid gap-8 lg:grid-cols-3">
        {plans.map((plan) => (
          <Card
            key={plan.name}
            className={cn(
              "relative flex flex-col shadow-card",
              plan.highlighted && "border-brand-navy ring-2 ring-brand-navy"
            )}
          >
            {plan.highlighted && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-brand-orange px-3 py-0.5 text-xs font-medium text-white">
                Most Popular
              </div>
            )}
            <CardHeader>
              <CardTitle>{plan.name}</CardTitle>
              <div className="mt-2">
                <span className="font-heading text-3xl font-bold">{plan.price}</span>
                {plan.period && (
                  <span className="text-muted-foreground">{plan.period}</span>
                )}
              </div>
              <p className="text-sm text-muted-foreground">{plan.description}</p>
            </CardHeader>
            <CardContent className="flex-1">
              <ul className="space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2 text-sm">
                    <Check className="mt-0.5 size-4 shrink-0 text-success" />
                    {feature}
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <ButtonLink
                href={plan.href}
                className={cn(
                  "w-full",
                  plan.highlighted
                    ? "bg-brand-orange text-white hover:bg-brand-orange/90"
                    : "bg-brand-navy text-white hover:bg-brand-navy/90"
                )}
              >
                {plan.cta}
              </ButtonLink>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}
