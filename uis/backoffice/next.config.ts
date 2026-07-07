import type { NextConfig } from 'next';

function rewriteOrigin(envVar: string, fallback: string): string {
  return (process.env[envVar] ?? fallback).replace(/\/$/, '');
}

const nextConfig: NextConfig = {
  async rewrites() {
    const inventoryOrigin = rewriteOrigin('INVENTORY_API_ORIGIN', 'http://localhost:8012');
    const authOrigin = rewriteOrigin('AUTH_API_ORIGIN', 'http://localhost:8002');

    return [
      {
        source: '/api/inventory/:path*',
        destination: `${inventoryOrigin}/inventory/:path*`,
      },
      {
        source: '/api/auth/:path*',
        destination: `${authOrigin}/auth/:path*`,
      },
    ];
  },
};

export default nextConfig;
