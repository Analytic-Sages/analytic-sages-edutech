import { PageHeader } from "@/components/layout/page-header";
import { ButtonLink } from "@/components/ui/button-link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";

export const metadata = { title: "Create Course" };

export default function CreateCoursePage() {
  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        breadcrumbs={[
          { label: "Admin", href: "/admin" },
          { label: "Courses", href: "/admin/courses" },
          { label: "New Course" },
        ]}
        title="Create Course"
        description="Set up a new course. Add modules and lessons after creating."
      />
      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Course Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="title">Course Title</Label>
            <Input id="title" placeholder="e.g. Python for Blockchain Analytics" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Short Description</Label>
            <Textarea id="description" rows={3} placeholder="Brief course summary for catalog" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Category</Label>
              <Select defaultValue="blockchain">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="blockchain">Blockchain</SelectItem>
                  <SelectItem value="quant">Quantitative Finance</SelectItem>
                  <SelectItem value="data">Data Engineering</SelectItem>
                  <SelectItem value="ml">Machine Learning</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Difficulty</Label>
              <Select defaultValue="intermediate">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="beginner">Beginner</SelectItem>
                  <SelectItem value="intermediate">Intermediate</SelectItem>
                  <SelectItem value="advanced">Advanced</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="price">Price (NGN)</Label>
              <Input id="price" type="number" placeholder="89000" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="duration">Duration</Label>
              <Input id="duration" placeholder="12 weeks" />
            </div>
          </div>
          <Separator />
          <div className="flex gap-3">
            <Button className="bg-brand-navy text-white hover:bg-brand-navy/90">
              Create & Add Modules
            </Button>
            <ButtonLink href="/admin/courses" variant="outline">
              Cancel
            </ButtonLink>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
