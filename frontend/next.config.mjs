/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.mobile.de",
      },
      {
        protocol: "https",
        hostname: "**.autoscout24.com",
      },
      {
        protocol: "https",
        hostname: "**.autoscout24.de",
      },
      {
        protocol: "https",
        hostname: "**.autoscout24.net",
      },
    ],
  },
};

export default nextConfig;
