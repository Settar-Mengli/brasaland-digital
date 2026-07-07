import type { NextConfig } from 'next';

function rewriteOrigin(envVar: string, fallback: string): string {
  return (process.env[envVar] ?? fallback).replace(/\/$/, '');
}

const nextConfig: NextConfig = {
  async rewrites() {
    const incidentsOrigin = rewriteOrigin('INCIDENTS_API_ORIGIN', 'http://localhost:8011');

    return [
      {
        source: '/api/incidents/:path*',
        destination: `${incidentsOrigin}/api/incidents/:path*`,
      },
    ];
  },
};

export default nextConfig;
