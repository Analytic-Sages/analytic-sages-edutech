import { Clock } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";

export function ComingSoonPanel({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <EmptyState
      icon={<Clock className="size-6" />}
      title={title}
      description={description}
    />
  );
}
