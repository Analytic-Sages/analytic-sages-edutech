import { ComingSoonPanel } from "@/components/admin/coming-soon-panel";
import { PageHeader } from "@/components/layout/page-header";

export const metadata = { title: "Settings" };

export default function AdminSettingsPage() {
  return (
    <div>
      <PageHeader title="Platform Settings" description="Admin settings are not live yet." />
      <ComingSoonPanel
        title="Coming soon"
        description="This screen cannot change platform name, email, or other production settings."
      />
    </div>
  );
}
