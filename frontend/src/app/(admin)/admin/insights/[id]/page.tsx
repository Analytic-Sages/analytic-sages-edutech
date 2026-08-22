"use client";

import { useParams } from "next/navigation";
import { InsightEditLoader } from "@/components/insights/insight-edit-loader";

export default function AdminInsightEditPage() {
  const params = useParams<{ id: string }>();
  return <InsightEditLoader id={params.id} workspace="admin" />;
}
