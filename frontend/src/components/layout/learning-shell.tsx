"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import {
  operationsNav,
  publicStudentNav,
  staffNav,
  type NavItem,
} from "@/config/navigation";
import { getMe } from "@/lib/api";

/**
 * Students see the learner menu. Instructors and operations keep their staff
 * menu, which also links back to the learner dashboard and the live class.
 */
function withLearnerLinks(staffItems: NavItem[]): NavItem[] {
  const hrefs = new Set(staffItems.map((item) => item.href));
  return [...staffItems, ...publicStudentNav().filter((item) => !hrefs.has(item.href))];
}

export function LearningShell({ children }: { children: React.ReactNode }) {
  const [nav, setNav] = useState<NavItem[]>(publicStudentNav());

  useEffect(() => {
    let cancelled = false;
    getMe()
      .then((user) => {
        if (cancelled) return;
        if (user.role === "operations") setNav(withLearnerLinks(operationsNav));
        else if (user.role === "instructor") setNav(withLearnerLinks(staffNav));
      })
      .catch(() => {
        if (!cancelled) setNav(publicStudentNav());
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return <AppShell nav={nav}>{children}</AppShell>;
}
