import { PageHeader } from "@/components/layout/page-header";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const users = [
  { name: "Ada Okonkwo", email: "ada@example.com", role: "Student", courses: 2, joined: "2025-01-15" },
  { name: "James Adeyemi", email: "james@example.com", role: "Student", courses: 1, joined: "2025-02-20" },
  { name: "Fatima Bello", email: "fatima@example.com", role: "Instructor", courses: 3, joined: "2024-11-01" },
  { name: "Admin User", email: "admin@analyticsages.com", role: "Admin", courses: 0, joined: "2024-06-01" },
];

export const metadata = { title: "Users" };

export default function AdminUsersPage() {
  return (
    <div>
      <PageHeader title="Users" description="Manage students, instructors, and admins" />
      <div className="rounded-xl border shadow-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>User</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Courses</TableHead>
              <TableHead>Joined</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.email}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <Avatar className="size-8">
                      <AvatarFallback className="bg-brand-navy text-xs text-white">
                        {user.name.split(" ").map((n) => n[0]).join("")}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium">{user.name}</p>
                      <p className="text-xs text-muted-foreground">{user.email}</p>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{user.role}</Badge>
                </TableCell>
                <TableCell>{user.courses}</TableCell>
                <TableCell className="text-muted-foreground">{user.joined}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
