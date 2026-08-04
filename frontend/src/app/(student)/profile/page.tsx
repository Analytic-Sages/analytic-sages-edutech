import { PageHeader } from "@/components/layout/page-header";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";

export const metadata = { title: "Profile" };

export default function ProfilePage() {
  return (
    <div className="mx-auto max-w-2xl">
      <PageHeader title="Profile" description="Manage your personal information" />
      <Card className="shadow-card">
        <CardHeader className="flex flex-row items-center gap-4">
          <Avatar className="size-16">
            <AvatarFallback className="bg-brand-navy text-lg text-white">AO</AvatarFallback>
          </Avatar>
          <div>
            <CardTitle>Ada Okonkwo</CardTitle>
            <p className="text-sm text-muted-foreground">ada@example.com</p>
          </div>
          <Button variant="outline" size="sm" className="ml-auto">
            Change Photo
          </Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <Separator />
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="firstName">First Name</Label>
              <Input id="firstName" defaultValue="Ada" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="lastName">Last Name</Label>
              <Input id="lastName" defaultValue="Okonkwo" />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" defaultValue="ada@example.com" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="bio">Bio</Label>
            <Input id="bio" placeholder="Tell us about yourself" />
          </div>
          <Button className="bg-brand-navy text-white hover:bg-brand-navy/90">
            Save Changes
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
