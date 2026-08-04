import { Award, BookOpen, Clock, CreditCard, TrendingUp, Users, type LucideIcon } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type StatsIconId = "users" | "courses" | "clock" | "award" | "trending" | "payments";

const statsIcons: Record<StatsIconId, LucideIcon> = {
  users: Users,
  courses: BookOpen,
  clock: Clock,
  award: Award,
  trending: TrendingUp,
  payments: CreditCard,
};

type StatsCardProps = {
  title: string;
  value: string | number;
  description?: string;
  icon: StatsIconId;
  trend?: string;
  className?: string;
};

export function StatsCard({
  title,
  value,
  description,
  icon,
  trend,
  className,
}: StatsCardProps) {
  const Icon = statsIcons[icon];

  return (
    <Card className={cn("shadow-card", className)}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className="flex size-8 items-center justify-center rounded-lg bg-brand-navy/10">
          <Icon className="size-4 text-brand-navy" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="font-heading text-2xl font-bold">{value}</div>
        {(description || trend) && (
          <p className="mt-1 text-xs text-muted-foreground">
            {trend && <span className="text-success">{trend} </span>}
            {description}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
