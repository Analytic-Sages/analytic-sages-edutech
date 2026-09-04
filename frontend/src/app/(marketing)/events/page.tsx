import { EventsCatalog } from "@/components/events/events-catalog";
import { JsonLd } from "@/components/seo/json-ld";
import { breadcrumbJsonLd, pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Events",
  description:
    "Free Analytic Sages workshops and live sessions for a global learner community. Browse upcoming events and register with your account to join.",
  path: "/events",
});

export default function EventsPage() {
  return (
    <>
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", path: "/" },
          { name: "Events", path: "/events" },
        ])}
      />
      <EventsCatalog />
    </>
  );
}
