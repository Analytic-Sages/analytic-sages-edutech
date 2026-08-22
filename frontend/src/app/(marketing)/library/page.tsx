import { redirect } from "next/navigation";

/** Public Library is retired. Content lives in lib/library.ts for internal reuse. */
export default function LibraryPage() {
  redirect("/courses");
}
