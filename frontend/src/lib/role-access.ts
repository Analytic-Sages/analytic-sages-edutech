/** Canonical staff/learner access map — keep aligned with backend deps + navigation. */

export type AppRole =
  | "admin"
  | "editor"
  | "author"
  | "instructor"
  | "operations"
  | "partnerships"
  | "student";

export type RoleAccess = {
  label: string;
  home: string;
  summary: string;
  areas: string[];
  can: string[];
  cannot: string[];
};

export const STAFF_ROLES: AppRole[] = [
  "admin",
  "operations",
  "partnerships",
  "editor",
  "author",
  "instructor",
];

export function isStaffRole(role: string): boolean {
  return STAFF_ROLES.includes(role as AppRole);
}

export const ROLE_ACCESS: Record<AppRole, RoleAccess> = {
  admin: {
    label: "Admin",
    home: "/admin",
    summary: "Full admin console — users, payments, catalog, opportunities, insights, settings.",
    areas: [
      "Dashboard",
      "Featured cohort",
      "Users",
      "Payments",
      "Billing",
      "Courses",
      "Events",
      "Opportunities",
      "Insights",
      "Certificates",
      "Analytics",
      "Settings",
    ],
    can: [
      "Invite and change staff roles",
      "Publish opportunities and manage sources",
      "Manage payments and tuition billing",
      "Publish Insights as an editor",
      "Manage events and course catalog",
      "View analytics and settings",
    ],
    cannot: ["Nothing staff-restricted — this is the full console"],
  },
  operations: {
    label: "Operations",
    home: "/admin/events",
    summary: "Events, catalog, Opportunities Hub, and Insights publishing.",
    areas: ["Events", "Courses", "Opportunities", "Insights"],
    can: [
      "Create and publish public events",
      "Manage course catalog / instructors attachment",
      "Publish and manage opportunities",
      "Review and publish Insights articles",
    ],
    cannot: [
      "Users, payments, billing",
      "Analytics and settings",
    ],
  },
  partnerships: {
    label: "Grant manager",
    home: "/admin/opportunities",
    summary: "Opportunities Hub only — grants and partnerships listings.",
    areas: ["Opportunities"],
    can: ["Publish and manage opportunities", "Manage opportunity sources"],
    cannot: [
      "Users, payments, billing",
      "Events / courses ops",
      "Insights publishing",
      "Analytics and settings",
    ],
  },
  editor: {
    label: "Editor",
    home: "/admin/insights",
    summary: "Insights editorial — review and publish author submissions.",
    areas: ["Insights"],
    can: ["Review pending Insights", "Publish and unpublish articles"],
    cannot: [
      "Users, payments, billing",
      "Events / courses ops",
      "Opportunities admin",
      "Analytics and settings",
    ],
  },
  author: {
    label: "Author",
    home: "/studio",
    summary: "Insights writer studio — draft and submit; cannot publish.",
    areas: ["My articles (Studio)"],
    can: ["Write Insights drafts", "Submit articles for editorial review"],
    cannot: [
      "Publish Insights",
      "Access /admin console pages",
      "Users, payments, opportunities admin",
    ],
  },
  instructor: {
    label: "Instructor",
    home: "/staff",
    summary: "Classroom staff portal for live sessions and cohort teaching.",
    areas: ["Classroom (Staff)"],
    can: ["Open staff classroom tools", "Join teaching sessions for assigned cohorts"],
    cannot: [
      "Admin dashboard (/admin)",
      "Users, payments, billing",
      "Publish Insights or manage opportunities",
    ],
  },
  student: {
    label: "Student",
    home: "/dashboard",
    summary: "Learner dashboard — courses, classroom, billing, opportunities.",
    areas: [
      "Dashboard",
      "Classroom",
      "My Courses",
      "Billing",
      "My Events",
      "Opportunities",
      "Certificates",
    ],
    can: ["Learn enrolled courses", "Join classroom sessions", "Save opportunities"],
    cannot: ["Any admin or staff console"],
  },
};

export function roleAccess(role: string): RoleAccess {
  if (role in ROLE_ACCESS) return ROLE_ACCESS[role as AppRole];
  return {
    label: role,
    home: "/dashboard",
    summary: "Unknown role",
    areas: [],
    can: [],
    cannot: [],
  };
}
