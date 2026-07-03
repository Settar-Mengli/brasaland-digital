import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/incidents/:path*',
        destination: 'http://localhost:8011/api/incidents/:path*',
      },
    ];
  },
};

export default nextConfig;
