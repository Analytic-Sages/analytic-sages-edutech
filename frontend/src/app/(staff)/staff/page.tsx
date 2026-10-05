import { InstructorDashboardContent } from "@/components/classroom/instructor-dashboard-content";

export const metadata = {
  title: "Instructor dashboard",
  description: "Manage your assigned cohorts, students, sessions and attendance.",
};

export default function StaffClassroomPage() {
  return <InstructorDashboardContent />;
}
