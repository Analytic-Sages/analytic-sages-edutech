import { Logo } from "@/components/brand/logo";
import { CourseCard } from "@/components/course/course-card";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { courses } from "@/lib/mock-data";

export const metadata = { title: "Design System" };

const swatches = [
  { name: "Brand Navy", class: "bg-brand-navy", hex: "#101A8A" },
  { name: "Brand Orange", class: "bg-brand-orange", hex: "#F58220" },
  { name: "Surface", class: "bg-brand-surface border", hex: "#F8FAFC" },
  { name: "Success", class: "bg-success", hex: "#10B981" },
  { name: "Warning", class: "bg-warning", hex: "#F59E0B" },
  { name: "Danger", class: "bg-destructive", hex: "#EF4444" },
];

export default function DesignSystemPage() {
  return (
    <div className="min-h-screen bg-background p-8 sm:p-12">
      <div className="mx-auto max-w-5xl space-y-16">
        <PageHeader
          title="Analytic Sages Design System"
          description="Internal reference for tokens, typography, and components"
        />

        <section>
          <h2 className="font-heading mb-6 text-xl font-semibold">Brand</h2>
          <div className="flex flex-wrap items-end gap-10">
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Light · colored
              </p>
              <Logo size="lg" href={null} />
            </div>
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Light · black
              </p>
              <Logo size="lg" href={null} tone="mono" />
            </div>
          </div>
          <p className="mt-4 text-muted-foreground">
            Dark mode uses the white mark automatically. Manrope for headings · Inter for body ·
            Navy + Orange palette
          </p>
        </section>

        <section>
          <h2 className="font-heading mb-6 text-xl font-semibold">Colors</h2>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            {swatches.map((swatch) => (
              <div key={swatch.name} className="space-y-2">
                <div className={`h-16 rounded-lg ${swatch.class}`} />
                <p className="text-sm font-medium">{swatch.name}</p>
                <p className="font-mono text-xs text-muted-foreground">{swatch.hex}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="font-heading mb-6 text-xl font-semibold">Typography</h2>
          <div className="space-y-4 rounded-xl border p-6">
            <h1 className="font-heading text-4xl font-bold">Heading 1: Manrope</h1>
            <h2 className="font-heading text-2xl font-semibold">Heading 2: Manrope</h2>
            <p className="text-base">Body text: Inter. Clean, readable, professional.</p>
            <p className="text-sm text-muted-foreground">Secondary text for descriptions and metadata.</p>
          </div>
        </section>

        <section>
          <h2 className="font-heading mb-6 text-xl font-semibold">Buttons</h2>
          <div className="flex flex-wrap gap-3">
            <Button className="bg-brand-navy text-white hover:bg-brand-navy/90">Primary Navy</Button>
            <Button className="bg-brand-orange text-white hover:bg-brand-orange/90">Primary Orange</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Danger</Button>
          </div>
        </section>

        <section>
          <h2 className="font-heading mb-6 text-xl font-semibold">Badges & Progress</h2>
          <div className="flex flex-wrap items-center gap-3">
            <Badge>Default</Badge>
            <Badge variant="outline">Outline</Badge>
            <Badge className="bg-success/10 text-success">Success</Badge>
            <Badge className="bg-brand-orange/10 text-brand-orange">Accent</Badge>
          </div>
          <div className="mt-6 max-w-md space-y-2">
            <Progress value={68} className="h-2" />
            <p className="text-sm text-muted-foreground">68% course progress</p>
          </div>
        </section>

        <section>
          <h2 className="font-heading mb-6 text-xl font-semibold">Form Elements</h2>
          <Card className="max-w-md shadow-card">
            <CardHeader>
              <CardTitle>Input Example</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input placeholder="Email address" />
              <Input placeholder="Disabled" disabled />
            </CardContent>
          </Card>
        </section>

        <section>
          <h2 className="font-heading mb-6 text-xl font-semibold">Skeleton Loaders</h2>
          <div className="space-y-3 max-w-md">
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-32 w-full rounded-xl" />
          </div>
        </section>

        <section>
          <h2 className="font-heading mb-6 text-xl font-semibold">Course Card</h2>
          <div className="max-w-sm">
            <CourseCard course={courses[0]} />
          </div>
        </section>
      </div>
    </div>
  );
}
