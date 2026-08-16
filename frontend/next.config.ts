import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: [
    "@cloudflare/realtimekit",
    "@cloudflare/realtimekit-react",
    "@cloudflare/realtimekit-react-ui",
    "@cloudflare/realtimekit-ui",
  ],
};

export default nextConfig;
