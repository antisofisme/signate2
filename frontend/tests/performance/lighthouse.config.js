// Custom Lighthouse configuration for performance testing

module.exports = {
  extends: 'lighthouse:default',
  settings: {
    maxWaitForFcp: 15 * 1000,
    maxWaitForLoad: 35 * 1000,
    formFactor: 'desktop',
    throttling: {
      rttMs: 40,
      throughputKbps: 10240,
      cpuSlowdownMultiplier: 1,
      requestLatencyMs: 0,
      downloadThroughputKbps: 0,
      uploadThroughputKbps: 0,
    },
    screenEmulation: {
      mobile: false,
      width: 1920,
      height: 1080,
      deviceScaleFactor: 1,
      disabled: false,
    },
    emulatedUserAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
  },
  audits: [
    // Core Web Vitals
    'first-contentful-paint',
    'largest-contentful-paint',
    'cumulative-layout-shift',
    'total-blocking-time',

    // Performance audits
    'speed-index',
    'interactive',
    'first-meaningful-paint',
    'max-potential-fid',

    // Resource optimization
    'unused-javascript',
    'unused-css-rules',
    'unminified-javascript',
    'unminified-css',
    'modern-image-formats',
    'efficient-animated-content',
    'optimized-images',
    'properly-size-images',

    // Critical resource hints
    'uses-rel-preload',
    'uses-rel-preconnect',
    'uses-responsive-images',

    // Network optimization
    'render-blocking-resources',
    'critical-request-chains',
    'uses-long-cache-ttl',
    'total-byte-weight',

    // JavaScript optimization
    'bootup-time',
    'mainthread-work-breakdown',
    'third-party-summary',
    'legacy-javascript',

    // Accessibility audits
    'color-contrast',
    'image-alt',
    'label',
    'aria-allowed-attr',
    'aria-hidden-body',
    'aria-required-children',
    'aria-required-parent',
    'aria-roles',
    'aria-valid-attr',
    'aria-valid-attr-value',
    'button-name',
    'bypass',
    'document-title',
    'duplicate-id-aria',
    'html-has-lang',
    'html-lang-valid',
    'link-name',
    'meta-viewport',
    'tabindex',

    // SEO audits
    'meta-description',
    'http-status-code',
    'link-text',
    'is-crawlable',
    'robots-txt',
    'hreflang',
    'canonical',

    // Best practices
    'uses-https',
    'is-on-https',
    'errors-in-console',
    'no-vulnerable-libraries',
    'charset',
    'doctype',
  ],
  categories: {
    performance: {
      title: 'Performance',
      auditRefs: [
        { id: 'first-contentful-paint', weight: 10 },
        { id: 'speed-index', weight: 10 },
        { id: 'largest-contentful-paint', weight: 25 },
        { id: 'interactive', weight: 10 },
        { id: 'total-blocking-time', weight: 30 },
        { id: 'cumulative-layout-shift', weight: 15 },
      ],
    },
    accessibility: {
      title: 'Accessibility',
      auditRefs: [
        { id: 'color-contrast', weight: 3 },
        { id: 'image-alt', weight: 10 },
        { id: 'label', weight: 10 },
        { id: 'aria-allowed-attr', weight: 10 },
        { id: 'aria-hidden-body', weight: 10 },
        { id: 'aria-required-children', weight: 10 },
        { id: 'aria-required-parent', weight: 10 },
        { id: 'aria-roles', weight: 10 },
        { id: 'aria-valid-attr', weight: 10 },
        { id: 'aria-valid-attr-value', weight: 10 },
        { id: 'button-name', weight: 10 },
        { id: 'bypass', weight: 3 },
        { id: 'document-title', weight: 3 },
        { id: 'duplicate-id-aria', weight: 3 },
        { id: 'html-has-lang', weight: 3 },
        { id: 'html-lang-valid', weight: 3 },
        { id: 'link-name', weight: 3 },
        { id: 'meta-viewport', weight: 10 },
        { id: 'tabindex', weight: 3 },
      ],
    },
    'best-practices': {
      title: 'Best Practices',
      auditRefs: [
        { id: 'uses-https', weight: 5 },
        { id: 'is-on-https', weight: 5 },
        { id: 'errors-in-console', weight: 1 },
        { id: 'no-vulnerable-libraries', weight: 5 },
        { id: 'charset', weight: 1 },
        { id: 'doctype', weight: 1 },
      ],
    },
    seo: {
      title: 'SEO',
      auditRefs: [
        { id: 'meta-description', weight: 1 },
        { id: 'http-status-code', weight: 1 },
        { id: 'link-text', weight: 1 },
        { id: 'is-crawlable', weight: 1 },
        { id: 'robots-txt', weight: 1 },
        { id: 'hreflang', weight: 1 },
        { id: 'canonical', weight: 1 },
      ],
    },
  },
}