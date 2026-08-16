import { RequireAuth } from "@/components/auth/require-auth";
import { ClassroomRoom } from "@/components/classroom/classroom-room";

type Props = {
  params: Promise<{ sessionId: string }>;
};

export default async function ClassroomSessionPage({ params }: Props) {
  const { sessionId } = await params;
  return (
    <RequireAuth>
      <ClassroomRoom sessionId={sessionId} />
    </RequireAuth>
  );
}
