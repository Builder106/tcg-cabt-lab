import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Placeholder production URL: canonical links, OG tags and the sitemap read it. Set the real
// domain before deploying.
export default defineConfig({
  site: 'https://tcg-cabt-lab.example',
  trailingSlash: 'always',
  integrations: [sitemap()],
  prefetch: { prefetchAll: false, defaultStrategy: 'hover' },
  build: { inlineStylesheets: 'auto' },
});
