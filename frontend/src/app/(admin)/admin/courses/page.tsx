import { Plus } from "lucide-react";
import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button-link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { courses, formatPrice } from "@/lib/mock-data";

export const metadata = { title: "Manage Courses" };

export default function AdminCoursesPage() {
  return (
    <div>
      <PageHeader
        title="Courses"
        description="Create and manage course content"
        action={
          <ButtonLink
            href="/admin/courses/new"
            className="gap-2 bg-brand-orange text-white hover:bg-brand-orange/90"
          >
            <Plus className="size-4" />
            New Course
          </ButtonLink>
        }
      />
      <div className="rounded-xl border shadow-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Course</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Students</TableHead>
              <TableHead>Price</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {courses.map((course) => (
              <TableRow key={course.id}>
                <TableCell className="font-medium">{course.title}</TableCell>
                <TableCell>{course.category}</TableCell>
                <TableCell>{course.studentsCount.toLocaleString()}</TableCell>
                <TableCell>
                  {course.comingSoon
                    ? "Launching soon"
                    : formatPrice(course.price, course.currency)}
                </TableCell>
                <TableCell>
                  <Badge
                    className={
                      course.comingSoon
                        ? "bg-brand-orange/10 text-brand-orange"
                        : "bg-success/10 text-success"
                    }
                  >
                    {course.comingSoon ? "Coming soon" : "Published"}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
