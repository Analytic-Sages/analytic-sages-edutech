import { redirect } from "next/navigation";

/** Legacy URL — Instructor-Led is now the primary live training surface. */
export default function ProgramsRedirectPage() {
  redirect("/instructor-led");
}
