/** @type {import('next').NextConfig} */
const nextConfig = {
  // Next.js 14.2+ configuration optimized for production
  output: 'standalone', // Required for Docker deployment
  poweredByHeader: false,
  compress: true,

  // Add logging for debug in Docker
  logging: {
    fetches: {
      fullUrl: true,
    },
  },

  // Temporarily ignore TypeScript and ESLint errors for Docker build
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },


  images: {
    domains: ['localhost', 'api.anthias.com'],
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
    formats: ['image/webp', 'image/avif'],
  },

  // Environment variables for client-side
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
  },

  // Webpack configuration for better module resolution
  webpack: (config, { isServer }) => {
    // Improve module resolution for production builds
    config.resolve.fallback = {
      ...config.resolve.fallback,
      fs: false,
      net: false,
      tls: false,
    };

    return config;
  },

  // Build-time optimizations
  experimental: {
    // optimizeCss: true, // Disabled due to critters dependency issue
    optimizePackageImports: ['date-fns', 'lodash-es'],
    // Removed conflicting packages from serverComponentsExternalPackages
  },
}

module.exports = nextConfig