import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://octocatsback.github.io',
  base: '/Gareth/',
  server: {
    host: true,
    port: 4321,
  },
});
