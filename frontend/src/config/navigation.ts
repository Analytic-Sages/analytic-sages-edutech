export type NavItemId =
  | "dashboard"
  | "classroom"
  | "courses"
  | "explore"
  | "certificates"
  | "users"
  | "payments"
  | "analytics"
  | "settings";

export type NavItem = {
  title: string;
  href: string;
  icon: NavItemId;
  badge?: string;
};

export const marketingNav = [
  { title: "Instructor-Led", href: "/instructor-led" },
  { title: "Self-Paced", href: "/courses" },
  { title: "Community", href: "/community" },
  { title: "Blog", href: "/blog" },
  { title: "About us", href: "/about" },
] as const;

export const studentNav: NavItem[] = [
  { title: "Dashboard", href: "/dashboard", icon: "dashboard" },
  { title: "Classroom", href: "/classroom", icon: "classroom" },
  { title: "My Courses", href: "/my-courses", icon: "courses" },
  { title: "Explore", href: "/explore", icon: "explore" },
  { title: "Certificates", href: "/certificates", icon: "certificates" },
];

export const adminNav: NavItem[] = [
  { title: "Dashboard", href: "/admin", icon: "dashboard" },
  { title: "Users", href: "/admin/users", icon: "users" },
  { title: "Courses", href: "/admin/courses", icon: "courses" },
  { title: "Payments", href: "/admin/payments", icon: "payments" },
  { title: "Certificates", href: "/admin/certificates", icon: "certificates" },
  { title: "Analytics", href: "/admin/analytics", icon: "analytics" },
  { title: "Settings", href: "/admin/settings", icon: "settings" },
];
