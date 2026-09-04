import { isOpportunitiesPublic } from "@/lib/feature-flags";

export type NavItemId =
  | "dashboard"
  | "classroom"
  | "courses"
  | "events"
  | "opportunities"
  | "explore"
  | "certificates"
  | "users"
  | "payments"
  | "analytics"
  | "settings"
  | "insights"
  | "referrals";

export type NavItem = {
  title: string;
  href: string;
  icon: NavItemId;
  badge?: string;
};

export const marketingNav = [
  { title: "Our Programs", href: "/programs" },
  { title: "Events", href: "/events" },
  { title: "Opportunities", href: "/opportunities" },
  { title: "Community", href: "/community" },
  { title: "Insights", href: "/insights" },
  { title: "About us", href: "/about" },
] as const;

export const studentNav: NavItem[] = [
  { title: "Dashboard", href: "/dashboard", icon: "dashboard" },
  { title: "Classroom", href: "/classroom", icon: "classroom" },
  { title: "My Courses", href: "/my-courses", icon: "courses" },
  { title: "Billing", href: "/dashboard/billing", icon: "payments" },
  { title: "My Events", href: "/my-events", icon: "events" },
  { title: "Opportunities", href: "/opportunities", icon: "opportunities" },
  { title: "Saved", href: "/my-opportunities", icon: "opportunities" },
  { title: "Explore", href: "/explore", icon: "explore" },
  { title: "Certificates", href: "/certificates", icon: "certificates" },
];

export const adminNav: NavItem[] = [
  { title: "Dashboard", href: "/admin", icon: "dashboard" },
  { title: "Featured cohort", href: "/admin/cohort", icon: "classroom" },
  { title: "Users", href: "/admin/users", icon: "users" },
  { title: "Payments", href: "/admin/payments", icon: "payments" },
  { title: "Billing", href: "/admin/billing", icon: "payments" },
  { title: "Courses", href: "/admin/courses", icon: "courses" },
  { title: "Events", href: "/admin/events", icon: "events" },
  { title: "Opportunities", href: "/admin/opportunities", icon: "opportunities" },
  { title: "Referrals", href: "/admin/referrals", icon: "referrals" },
  { title: "Insights", href: "/admin/insights", icon: "insights" },
  { title: "Certificates", href: "/admin/certificates", icon: "certificates" },
  { title: "Analytics", href: "/admin/analytics", icon: "analytics" },
  { title: "Settings", href: "/admin/settings", icon: "settings" },
];

export const operationsNav: NavItem[] = [
  { title: "Events", href: "/admin/events", icon: "events" },
  { title: "Courses", href: "/admin/courses", icon: "courses" },
];

export const editorNav: NavItem[] = [
  { title: "Insights", href: "/admin/insights", icon: "insights" },
];

export const partnerNav: NavItem[] = [
  { title: "Overview", href: "/partner", icon: "dashboard" },
];

export const studioNav: NavItem[] = [
  { title: "My articles", href: "/studio", icon: "insights" },
];

export const staffNav: NavItem[] = [
  { title: "Classroom", href: "/staff", icon: "classroom" },
];

export function publicMarketingNav() {
  if (isOpportunitiesPublic()) return marketingNav;
  return marketingNav.filter((item) => item.href !== "/opportunities");
}

export function publicStudentNav(): NavItem[] {
  if (isOpportunitiesPublic()) return studentNav;
  return studentNav.filter(
    (item) => item.href !== "/opportunities" && item.href !== "/my-opportunities",
  );
}
