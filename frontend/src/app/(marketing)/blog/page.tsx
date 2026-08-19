import { BlogPageContent } from "@/components/blog/blog-page-content";
import { pageMetadata } from "@/lib/seo";

export const metadata = pageMetadata({
  title: "Blog",
  description:
    "Guides and notes from Analytic Sages on blockchain data, SQL, on-chain analysis, and building with public datasets.",
  path: "/blog",
});

export default function BlogPage() {
  return <BlogPageContent />;
}
