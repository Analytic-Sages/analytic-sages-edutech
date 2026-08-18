import { ClassroomScheduleContent } from "@/components/classroom/classroom-schedule-content";

export const metadata = {
  title: "Staff classroom",
  description: "Join Cohort 9 live sessions as Analytic Sages staff.",
};

export default function StaffClassroomPage() {
  return <ClassroomScheduleContent audience="staff" />;
}
