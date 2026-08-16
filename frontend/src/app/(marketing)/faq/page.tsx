import { HomeFaqSection } from "@/components/marketing/home-faq-section";

export const metadata = {
  title: "FAQ",
  description:
    "Frequently asked questions about Analytic Sages courses, payments, enrollment, and learning.",
};

export default function FaqPage() {
  return (
    <div className="pb-8">
      <HomeFaqSection />
    </div>
  );
}
