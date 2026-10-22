import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// Production URL: canonical links, OG tags and the sitemap read it. Also in src/data/site.ts
// and public/robots.txt.
export default defineConfig({
  site: 'https://tcg-cabt-lab.vercel.app',
  trailingSlash: 'always',
  integrations: [sitemap()],
  prefetch: { prefetchAll: false, defaultStrategy: 'hover' },
  build: { inlineStylesheets: 'auto' },
});
