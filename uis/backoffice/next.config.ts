import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/inventory/:path*',
        destination: 'http://localhost:8012/inventory/:path*',
      },
      {
        source: '/api/auth/:path*',
        destination: 'http://localhost:8002/auth/:path*',
      },
    ];
  },
};

export default nextConfig;
