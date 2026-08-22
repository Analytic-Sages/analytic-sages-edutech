import { redirect } from "next/navigation";

type Props = { params: Promise<{ slug: string }> };

export default async function BlogSlugRedirect({ params }: Props) {
  const { slug } = await params;
  redirect(`/insights/${slug}`);
}
