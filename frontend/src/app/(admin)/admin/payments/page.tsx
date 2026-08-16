import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const payments = [
  { id: "PAY-001", student: "Ada Okonkwo", course: "Python for Blockchain Analytics", amount: "₦79,000", provider: "Paystack", status: "Success", date: "2026-03-01" },
  { id: "PAY-002", student: "James Adeyemi", course: "Quantitative Trading with Python", amount: "$150", provider: "NOWPayments", status: "Success", date: "2026-03-02" },
  { id: "PAY-003", student: "Chidi Nwosu", course: "Applied AI for Blockchain", amount: "₦95,000", provider: "Paystack", status: "Pending", date: "2026-03-03" },
];

export const metadata = { title: "Payments" };

export default function AdminPaymentsPage() {
  return (
    <div>
      <PageHeader title="Payments" description="Track all course purchases and transactions" />
      <div className="rounded-xl border shadow-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Student</TableHead>
              <TableHead>Course</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Provider</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {payments.map((payment) => (
              <TableRow key={payment.id}>
                <TableCell className="font-mono text-xs">{payment.id}</TableCell>
                <TableCell>{payment.student}</TableCell>
                <TableCell>{payment.course}</TableCell>
                <TableCell className="font-medium">{payment.amount}</TableCell>
                <TableCell>{payment.provider}</TableCell>
                <TableCell>
                  <Badge
                    className={
                      payment.status === "Success"
                        ? "bg-success/10 text-success"
                        : "bg-warning/10 text-warning"
                    }
                  >
                    {payment.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-muted-foreground">{payment.date}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
