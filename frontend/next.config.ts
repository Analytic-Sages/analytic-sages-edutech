import type { NextConfig } from "next";

const backendOrigin = (
  process.env.API_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000"
).replace(/\/$/, "");

const nextConfig: NextConfig = {
  turbopack: {
    root: __dirname,
  },
  transpilePackages: [
    "@cloudflare/realtimekit",
    "@cloudflare/realtimekit-react",
    "@cloudflare/realtimekit-react-ui",
    "@cloudflare/realtimekit-ui",
  ],
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "img.youtube.com" },
      { protocol: "https", hostname: "i.ytimg.com" },
    ],
  },
  async redirects() {
    return [
      { source: "/library", destination: "/courses", permanent: true },
      { source: "/blog", destination: "/insights", permanent: true },
      { source: "/blog/:slug", destination: "/insights/:slug", permanent: true },
      {
        source: "/",
        has: [{ type: "host", value: "analyticsages.io" }],
        destination: "https://www.analyticsages.io/",
        permanent: true,
      },
      {
        source: "/:path*",
        has: [{ type: "host", value: "analyticsages.io" }],
        destination: "https://www.analyticsages.io/:path*",
        permanent: true,
      },
    ];
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
