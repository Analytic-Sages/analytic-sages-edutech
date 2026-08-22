import { CookiePreferencesCard } from "@/components/account/cookie-preferences-card";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

export const metadata = { title: "Settings" };

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader title="Settings" description="Manage your account preferences" />
      <CookiePreferencesCard />
      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Notifications</CardTitle>
          <CardDescription>Choose what updates you receive</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { label: "New lesson announcements", defaultChecked: true },
            { label: "Assignment deadlines", defaultChecked: true },
            { label: "Live class reminders", defaultChecked: true },
            { label: "Marketing emails", defaultChecked: false },
          ].map((item) => (
            <div key={item.label} className="flex items-center justify-between">
              <Label htmlFor={item.label}>{item.label}</Label>
              <input
                id={item.label}
                type="checkbox"
                defaultChecked={item.defaultChecked}
                className="size-4 rounded border-border accent-brand-navy"
              />
            </div>
          ))}
        </CardContent>
      </Card>
      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Password</CardTitle>
          <CardDescription>Update your password</CardDescription>
        </CardHeader>
        <CardContent>
          <ButtonLink href="/forgot-password" variant="outline">
            Change Password
          </ButtonLink>
        </CardContent>
      </Card>
      <Card className="border-destructive/30 shadow-card">
        <CardHeader>
          <CardTitle className="text-destructive">Danger Zone</CardTitle>
          <CardDescription>Permanently delete your account and all data</CardDescription>
        </CardHeader>
        <CardContent>
          <Separator className="mb-4" />
          <Button variant="destructive">Delete Account</Button>
        </CardContent>
      </Card>
    </div>
  );
}
