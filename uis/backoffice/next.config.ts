import type { NextConfig } from 'next';

function rewriteOrigin(envVar: string, fallback: string): string {
  return (process.env[envVar] ?? fallback).replace(/\/$/, '');
}

const nextConfig: NextConfig = {
  async rewrites() {
    const inventoryOrigin = rewriteOrigin('INVENTORY_API_ORIGIN', 'http://localhost:8012');
    const authOrigin = rewriteOrigin('AUTH_API_ORIGIN', 'http://localhost:8002');
    const telemetryOrigin = rewriteOrigin('TELEMETRY_API_ORIGIN', 'http://localhost:8013');

    return [
      {
        source: '/api/inventory/:path*',
        destination: `${inventoryOrigin}/inventory/:path*`,
      },
      {
        source: '/api/auth/:path*',
        destination: `${authOrigin}/auth/:path*`,
      },
      {
        source: '/api/telemetry/:path*',
        destination: `${telemetryOrigin}/telemetry/:path*`,
      },
    ];
  },
};

export default nextConfig;
