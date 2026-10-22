# Showcase site

The public showcase for TCG CABT Lab: the 360 held-out games laid out as cards on a table, and a replay of every game. It is a static [Astro](https://astro.build) site, live at <https://tcg-cabt-lab.vercel.app>.

## Build

The build reads the study report and the stored replays from `../experiments/`, so run it from a full checkout of the repository.

```sh
npm ci
npm run build
npm run preview
```

`npm run check` type-checks the site. The build writes one page and one replay file per game to `dist/`.

## Deploy

Vercel deploys the site from GitHub. The project uses `web/` as its root directory and may read files outside it, which the build needs for `experiments/`. Pushes to `main` deploy to production, and pull requests get a preview deployment.

Changes that touch neither `web/` nor `experiments/` skip the deploy. `vercel.json` adds trailing-slash redirects and long caching for hashed assets.

## Artwork

Every image is original. [`design/README.md`](design/README.md) lists the assets and how each was made, and [`DESIGN.md`](DESIGN.md) records the art direction.
