import { EventsCatalog } from "@/components/events/events-catalog";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Events",
  description:
    "Free Analytic Sages workshops and live sessions. Browse upcoming events and register with your account to join on YouTube Live.",
  path: "/events",
});

export default function EventsPage() {
  return <EventsCatalog />;
}
