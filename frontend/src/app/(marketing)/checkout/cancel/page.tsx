import { PageHeader } from "@/components/layout/page-header";
import { ButtonLink } from "@/components/ui/button-link";

export const metadata = { title: "Checkout cancelled" };

export default function CheckoutCancelPage() {
  return (
    <div className="mx-auto max-w-lg px-4 py-16 text-center sm:px-6">
      <PageHeader
        title="Checkout cancelled"
        description="No charge was made. You can return to the course and try again when ready."
        className="items-center text-center [&_h1]:mx-auto [&_p]:mx-auto"
      />
      <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
        <ButtonLink href="/courses" className="bg-brand-navy text-white hover:bg-brand-navy/90">
          Browse courses
        </ButtonLink>
        <ButtonLink href="/contact" variant="outline">
          Contact support
        </ButtonLink>
      </div>
    </div>
  );
}
