# Showcase artwork

Every image on the site is original and comes from one of two routes: Glaxnimate for flat
marks and card faces, Blender for anything that needs material and light. No official Pokémon
artwork, card backs, logos or symbols are used. Card names are printed as text from the engine
catalog.

## Glaxnimate (`glaxnimate/`)

Each SVG was drawn with the Glaxnimate MCP tools (`glaxnimate_create_svg`, `glaxnimate_edit_svg`)
and checked with a static render from the Glaxnimate fork CLI. The `.rawr` files are the fork's
project files for the same drawings.

| Id | Source | Used as | Format | Budget | Size |
|---|---|---|---|---|---|
| G1 card back | `card-back.svg` | page-transition card (`public/img/card-back.svg`); texture for the Blender card back | SVG | 15 KB | 10 KB |
| G2 mark | `mark.svg` | a hexagonal badge holding two played cards (blue and gold, one per training pool): bar mark (`src/components/Mark.astro`), `favicon.svg`, `favicon-32.png`, `apple-touch-icon.png` (badge on the bar red), OG image bar | SVG, PNG | 2 KB SVG | 0.8 KB |
| G3 Energy glyphs | `energy-psychic.svg`, `energy-water.svg`, `energy-colorless.svg` | type icons and attached Energy (`src/components/Sprite.astro`) | inline SVG symbols | 1 KB each | under 0.5 KB |
| G4 status | `status-asleep.svg` | Asleep marker on the Active card | inline symbol | 1 KB | 0.4 KB |
| G5 controls | `icons.svg` | replay buttons and back arrow | inline symbols | 3 KB | 1.7 KB |
| G6 tokens | `tokens.svg` | coin heads and tails in the event log, damage counters, bar stat icons | inline symbols | 2 KB | 1.3 KB |
| G7 card faces | `faces.py` writes `face-*.svg` | textures for the Blender card faces (Psychic, Water, Colorless, Trainer, Psychic Energy, Water Energy) | SVG | none (source only) | |
| G8 hex tiles | `hex-dark.svg`, `hex-light.svg` | board and app-chrome backgrounds | SVG tile | 1 KB | 0.3 KB |
| G10 Pokémon art | `faces.py` writes `mon-art-1.svg` to `mon-art-6.svg` | the art window of Pokémon cards on the replay board, one of six abstract motifs per card name (orb, ringed planet, peaks, spiral, zigzags, bubbles); the sprite drops the placeholder ground and draws in currentColor, and CSS colours the window by type. Original motifs, no likenesses | inline SVG symbols | 2 KB each | 0.8 to 1.6 KB |
| G9 sort art | `faces.py` writes `sort-*.svg` | the art window of each sort card, in the hand and on the played card (`src/components/SortArt.astro`, inlined so `src/motion/art.ts` can animate it) | inline SVG | 8 KB each | 2 to 8 KB |

`faces.py` holds the element lists passed to `glaxnimate_create_svg` and writes the faces and
sort art in the tool's own serialization (checked byte for byte against the tool output for
the Psychic face and the Training art); every sort art file was rendered with the fork CLI. `hex-light.svg` is `hex-dark.svg` with a lighter stroke.

Glaxnimate's importer does not support `<symbol>`, `<use>`, `clip-path` or `stroke-dasharray`,
so the sources draw ticks, icons and art windows as plain geometry. The site's sprite wraps the
same path data in symbols.

Each sort card's art (G9) draws what that sort does to the 360 games: two level piles for
Training, the two decks' type discs for Deck, four piles that swap leaders for Training and
deck, three opponent tokens, two chairs trading seats, the last Prize card left, six checkpoint
flags, and the matchup grid. The subject sits in a `<sort>-motif` group in the upper right, so
the card name can sit bottom left and the played card can scale it clear of the headline. Ids
carry the sort key so all eight can share a page.

Reduced motion: the sort art rests on its final frame, which is also what the SVG file draws;
hovering a hand card replays how it got there only when motion is allowed. The sprite, faces
and tiles are static by design.

## Blender (`blender/table.blend`)

Blender 5.2 through the Blender MCP. The card is a 63 x 88 mm mesh, 0.32 mm thick, with a
3.5 mm corner radius; faces and back use the Glaxnimate textures in `blender/textures/`.
Renders were converted to WebP with sharp.

| Id | Render | Used as | Budget | Size |
|---|---|---|---|---|
| B1 card faces | `face-*-{64,160,320}.webp`, `face-trainer-plain-800.webp` | game tiles (64), board cards (160), featured and hand cards (320), the played card (800, a Trainer face with no printed rule lines so the finding's text runs clean) | 30 KB per file | 0.9 to 12 KB |
| B2 card back | `card-back-{64,160,320}.webp` | losses in the piles, face-down hands, Prize cards | 10 KB | 1 to 7.5 KB |
| B3 deck stack | `deck-{150,300}.webp` | Deck zone on the board | 10 KB | 3.4 and 7.1 KB |
| B4 piles | `hero-{960,1600}.webp`, `og.png` base | method page figure, OG image | 150 KB | 15 and 28 KB |
| B5 lone card | `lone-{960,1600}.webp` | 404 page | 100 KB | 4.6 and 12 KB |

Pre-rendered stills, not a GLB: the site's objects are flat cards seen from above, and 360 live
meshes would cost frame rate on phones. Reduced motion uses the same stills.

Retired renders: Psychic violet and Water blue play mats (`mat-*`), used before the board moved
to the hex style. The `.blend` file still holds both mat objects.
