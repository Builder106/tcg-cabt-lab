# TCG CABT Lab showcase: design record

Planning record for the public showcase (ROADMAP milestone 4). It follows the awwwards
workflow: brief, concept, art direction, structure, assets, build and QA. Keep it current.

## Phase 0: brief

- **Subject.** A controlled study. One small option-scoring policy (2,881 parameters) was
  trained two ways, against a fixed opponent pool or a diverse one, three seeds each. The six
  checkpoints played 360 held-out games on two deck families. The answer is a null result.
- **Audience.** Newcomers who have never seen the card game, and players or researchers who
  want to inspect choices, matchups and failures.
- **Job.** Let anyone check the claim against the games. Every number on the site must lead
  to the games that make it up.
- **Inputs.** `docs/showcase.md` (requirement), `ROADMAP.md` milestone 4, `RESEARCH.md`,
  `JOURNAL.md`, `experiments/ml-experiment-report.json` (360 game records) and
  `experiments/replays/*.json.gz` (one replay per game, schema 1, defined in
  `src/tcg_cabt_lab/showcase.py`).
- **Constraints.** No official card art, card backs, logos or trade dress. Card names appear
  as engine text only. Policy scores are scores, never chances. No move is called a mistake.
  The agent view never shows the opponent's hand, the opponent's options or any Prize card.
- **Assumptions.** No production domain yet: `site` in `astro.config.mjs` is a placeholder
  (`https://tcg-cabt-lab.example`). No deploy until the owner confirms.

## Phase 1: concepts

Anchor facts used below: the study is a fixed factorial design (2 variants, 3 seeds, 2 decks,
3 opponents, 5 labels, 2 seats = 360 games); both variants scored about 58%; the deck moved
the score far more than the variant; each deck holds only five distinct cards; most games end
without the Prize race finishing.

| | A. The Table | B. The Sorting Table | C. One-way glass |
|---|---|---|---|
| Territory | the game's material | the study's formal design | the research ethic (information boundary) |
| Idea | The site is a play mat; a game is dealt onto it | All 360 games lie on a table as cards; you sort them into piles by any study factor, and the pile heights are the result | Every view is shown through glass: the agent's side and the spectator's side, with a divider you drag |
| What the site is | one mat, its printed zones are the places (Active = the claim, Deck = the catalog) | one table holding 360 game cards | a viewing room with a one-way window |
| How you move | point at a zone; a game is dealt onto the mat | re-sort the table (the sort line replaces the navbar); pull a card to deal its game | pick a game, drag the glass |
| One unit | a game, dealt and stepped | a game card; opening it turns it over and deals the game onto the mat | a game seen from two sides |
| Signature | the deal | 360 cards fly from one arrangement to another; the claim's two piles stand level | the divider sliding across hidden cards |
| Anchor | a TCG mat | this study's 360-game design and its null result | the brief's spectator-only rule |
| Swap test | any card-game project | fails for another subject: needs a fixed, factorial set of real games | any hidden-information game |
| O / F / Fe / P / S | 3 / 5 / 3 / 3 / 4 | 4 / 5 / 4 / 2 / 5 | 4 / 4 / 4 / 3 / 3 |

**Pick B, The Sorting Table.** It turns the claim itself into the interface, so a visitor
checks the result by moving the real games, and The Table survives inside it as the place a
game is dealt. From C it takes the perspective switch in the match view, shown as a sleeve
that covers the cards the agent could not see.

### Concept card

```
Idea:        The 360 held-out games lie on a table as cards. Sort them and see what made a difference.
Metaphor:    A tournament organizer's table: game slips sorted into piles, one mat for replaying a game.
Signature:   The re-sort. Every card slides from its pile to its new pile (GSAP Flip across the route
             change); the pile heights, built from wins, are the chart. First load deals the 360 cards
             from one deck into the two training piles.
Emotion:     Calm and exact, like counting slips on a clean table. Then a small surprise: the piles match.
Motion verb: Slide and settle. Cards move flat across the rubber, turn a little in flight, and settle square.
Screenshot:  Two piles of 180 cards, win stacks nearly level, 58.3% and 57.8% set huge above them.
Structure:   The screen is the table. The sort in play lies face up as a Trainer card whose rules
             text is the finding; the 360 games lie in piles beside it; the other sorts wait as a
             hand of Trainer cards along the bottom edge. Playing a card (a real link, one URL per
             sort) slides it onto the table while the games re-sort and the old card returns to the
             hand. One unit is a game card; opening it deals the game onto the mat at /games/<id>/.
Escape hatch: /games/ lists all 360 games in a plain table with real links. Every page links to it.
```

## Phase 2: art direction

### Revision, 21 October 2026

The owner found the first build "sterile and corporate" and asked for more of the Pokémon TCG.
Research on licensing (Kaggle competition rules, pokemon.com legal pages, press asset terms)
found no permission to show official art, logos or card images on a public site, so the owner
chose original artwork plus text references and a non-affiliation note. Changes:

- The mat is a saturated Psychic violet (`#3D2E7E`), and game pages use the deck's mat: violet
  for Mewtwo games, blue (`#1E4A86`) for Snorlax games, which run Water Energy.
- Cards wear original type faces drawn in Glaxnimate and rendered in Blender: Psychic, Water,
  Colorless, Trainer and two Energy faces. Board cards show HP on the band, the attacks each
  Pokémon used in that game, damage counters and coin flips.
- The owner then pointed out that the build still had a conventional skeleton (top bar, hero,
  stacked sections, footer). That was true: the genericness test below had been run on the plan,
  not on the page. The structure was rebuilt as described in the concept card: no hero, no
  section stack, the hand of sort cards is the navigation and the played card holds the copy.
- The full-screen loader was removed. It hid the headline and pushed phone LCP to 6 s; the
  first-load deal of the cards remains as the table's opening move.

### Second revision, 22 October 2026

The owner asked for the look of the Pokémon TCG Live client, without its trade dress. The site
now uses a red app bar with italic uppercase tabs, dark hex battle boards with red and blue
zones, white panels under red ribbons, hexagonal controls and a gold primary button. The mark is
a hexagonal badge holding two played cards, one per training pool. Each sort card carries its own
animated Glaxnimate drawing of what the sort does, and Pokémon cards on the replay board carry one
of six original abstract motifs, coloured by type.

Copy was rewritten for readers with no machine learning background: "the AI" instead of "policy",
"likely range" instead of "95% interval", and every number says what it counts and out of how
many games. The replay page opens on the board, scaled to fit the window, with a player that
shows whose turn it is on a turn rail, and the board animates draws, plays, attacks and knockouts
between steps.

### Palette (superseded by the revisions above; kept for the record)

| Role | Token | Hex | Note |
|---|---|---|---|
| ground (the mat) | `--c-mat` | `#1B2545` | deep blue rubber |
| deep (zones, shadow) | `--c-mat-deep` | `#121A33` | printed zone fill |
| ink on mat | `--c-chalk` | `#F2F5FA` | neutral cool white, never cream |
| muted on mat | `--c-muted` | `#A9B3D1` | 7.2:1 on the mat |
| line | `--c-line` | `rgb(242 245 250 / 0.16)` | zone prints, rules |
| card face | `--c-card` | `#F4F6F9` | cool card stock |
| ink on card | `--c-ink` | `#10131A` | |
| card back | `--c-back` | `#0B1020` | with the 360-tick mark and a `#3D4F8F` rim, so a face-down card still reads against the mat (the fill alone is 1.26:1) |
| accent (the studied policy) | `--c-accent` | `#FFC83D` | only for the policy: its side, its choice, the current sort |

Energy glyph colors live inside the glyphs only: Psychic `#8E5CF0`, Water `#2E86E6`,
Colorless `#9AA3B5`. Win and loss are encoded by the card's face (face up = the policy won,
card back = it lost, half-turned = draw), with a legend and text, never by color alone.

### Type

- **Archivo** (Google, variable `wdth` 62 to 125, `wght` 100 to 900), one family, two voices.
  Display: width 125, weight 800, tracking -0.04em, leading 0.86, tabular figures, used for
  the big numbers and pile heights. Text and UI: width 100, weights 400 and 600.
- Hashes and game ids use the system monospace stack (no download).
- Scale (tokens): mega `clamp(4rem, 1rem + 11vw, 13rem)`, xl `clamp(2.25rem, 1.2rem + 4vw, 5rem)`,
  l `clamp(1.5rem, 1.15rem + 1.5vw, 2.5rem)`, m `clamp(1.125rem, 1rem + 0.5vw, 1.5rem)`,
  body `clamp(1rem, 0.95rem + 0.2vw, 1.125rem)`, s `0.875rem`, xs `0.8125rem`.

### Grid, rhythm, shape

- 12 columns, gutter `clamp(1rem, 0.6rem + 1.6vw, 2.5rem)`, outer margin = gutter. Hang
  everything from three lines: column 1 (labels, numbers), column 5 (piles start), column 9
  (notes). Phone: 4 columns.
- Rhythm moods: tight (pile internals), normal (between piles), airy (above the headline),
  full (the mat view fills the viewport).
- **Shape:** only cards are round, with radius `0.055 × card width` (a real card's corner).
  Everything else is square.

### Motion language

- Eases: the engine set (`expo.out` entrances, `expo.inOut` curtains, `power3.out` UI).
- Durations: hover 0.3 s, card slide 0.9 to 1.2 s, re-sort total under 1.6 s, curtain 0.8 s.
- The verb in practice: a card leaves with up to 6 degrees of turn and settles to its resting
  angle (each card rests at a fixed small angle from its id, -1.2 to +1.2 degrees, the way slips
  sit on a table). Stagger by pile position, 2 ms per card, capped so a sort never exceeds 1.6 s.
- Treatments (one per role):
  - game cards (primary): **lift** (rise 4 px, straighten to 0 degrees, shadow deepens; keyboard focus gets the same plus the accent ring).
  - sort line and corner links (nav): **marker slide**: a small card-shaped marker slides
    under the hovered option; the current sort keeps it.
  - replay controls (buttons): **press**: the glyph nudges in its direction 4 px; `:active`
    scales 0.96.
  - inline links: underline at rest that thickens on hover.
- Idle: **the lamp**. A soft pool of light over the mat follows a lagged pointer and drifts a
  few percent on the ticker when the pointer is still. It is the table's own light, pauses off
  screen and stays fixed under reduced motion.
- Page transition: **a card is dealt over the table**. The curtain is a card back (Blender
  render) sliding in flat with a small turn, then sliding off the far side. Opening a game:
  the clicked card flips and grows into the mat.

### Structure plan (the site as one table)

```
DESKTOP 1440                                                    PHONE 390
┌─────────────────────────────────────────────────────────────┐  ┌───────────────────────┐
│ CABT Lab                         Method   All 360 games      │  │ CABT Lab        Games │
│                                                              │  │ Sort the 360 games by │
│ Sort the 360 games by  [training] deck  training+deck        │  │ [training] deck  ...→ │ (snap row)
│                        opponent  seat  ending  checkpoint    │  │                       │
│                                                              │  │ 58.3%                 │
│   58.3%                         57.8%                        │  │ Fixed pool  pile ▤▤▤  │
│   Fixed opponent pool           Diverse opponent pool        │  │ 57.8%                 │
│   ▤▤▤▤▤▤▤▤▤▤▤▤▤▤▤               ▤▤▤▤▤▤▤▤▤▤▤▤▤▤▤             │  │ Diverse pool pile ▤▤▤ │
│   ▤▤▤ pile of 180 ▤▤▤           ▤▤▤ pile of 180 ▤▤▤          │  │                       │
│   (wins face up, losses back)                                │  │ notes (one column)    │
│                                                              │  │ dealt examples        │
│ notes on this sort (col 9)    dealt examples (4 games)       │  │                       │
└─────────────────────────────────────────────────────────────┘  └───────────────────────┘
   every sort is a URL: / (training)  /sort/deck/  /sort/training-and-deck/  /sort/opponent/
                        /sort/seat/  /sort/ending/  /sort/checkpoint/  /sort/matchup/ (36 piles)
   card click → /games/<id>/ (the mat)   "All 360 games" → /games/ (escape hatch)
   Method → /method/ (how the study ran)  unknown URL → 404 (a card that is not in the deck)
```

### Composition plan

```
THE MAT  /games/<id>/   desktop                                       phone
┌──────────────────────────────────────────────────────────────┐    ┌──────────────────────┐
│ ← Table   Game 117 of 360        [Agent view | Spectator]     │    │ ← Table   Agent|Spec │
│ The policy lost by deck-out on turn 55.  provenance line      │    │ Lost by deck-out, t55│
│ ┌────────────── mat (Blender surface) ───────────┐ ┌─────────┐│    │ opponent row (mini)  │
│ │ opp: hand ▮▮▮▮ prizes ▮▮▮▮▮▮ deck▤ discard     │ │Decision ││    │ opp active           │
│ │ opp bench  [ ][ ][ ][ ][ ]                     │ │42 of 250││    │ ───────────────────  │
│ │            opp active [card]                   │ │turn 6   ││    │ policy active        │
│ │ ───────────── center line ─────────────────────│ │prompt   ││    │ policy bench (scroll)│
│ │            policy active [card]                │ │options  ││    │ policy hand          │
│ │ policy bench [ ][ ][ ]                         │ │+ scores ││    │ decision panel       │
│ │ policy: prizes ▮▮▮▮▮▮ deck▤ discard hand [..]  │ │events   ││    │ events               │
│ └────────────────────────────────────────────────┘ └─────────┘│    │ ┌ sticky controls ─┐ │
│ turn track ───●──────────────────  ⏮ ◀ ▶ ⏭  play            │    │ │ ⏮ ◀ 42/250 ▶ ⏭ │ │
└──────────────────────────────────────────────────────────────┘    └──────────────────────┘

ESCAPE HATCH /games/: one table, 360 rows, grouped by checkpoint; columns: game, deck, opponent,
seat, result, ending, turns. Every row is a link.
METHOD /method/: the rules insert. One long column of short numbered facts set beside the
Blender table render; no cards.
404: a single face-down card on the empty mat: "This card is not in the deck."
```

### Genericness test

- Skeleton, first build: failed on screen. A top bar, a headline block, piles, notes, a featured
  row and a footer. Fixed in the revision above.
- Skeleton, revision: the screen is the table and the hand is the navigation. Two small corner
  links remain (How it was run, All 360 games) as utility, which the genre allows.
- Big numbers over piles: a generic stats page would use bar charts. Here every bar is a pile
  of real, clickable games. Kept.
- Dark navy with yellow: checked against the defaults list (not acid green, not cream).
  Yellow is reserved for the policy, so it carries meaning. Kept.
- Card hover lift: common in card UIs. Changed: the lift also straightens the card's resting
  angle, which only exists because the cards lie on a table.
- Corner links (Method, All 360 games): genre convention, carry real destinations. Kept.

## Assets

See the asset table in `web/design/README.md` (id, route, role, format, budget, acceptance).
Decisions:
- Blender ships **pre-rendered stills**, not a GLB. A real-time model does not earn its cost:
  the site's 3D objects are flat cards seen from above, and 360 live meshes would cost frame
  rate on phones. The stills keep real material and light.
- Glaxnimate draws three Energy glyphs, not nine: the held-out decks use only Psychic, Water
  and Colorless. It draws one status marker (asleep), the only status that occurs in the
  360 games.
- Pattern B (SMIL seeking) is not used. Every Glaxnimate mark is drawn in Glaxnimate and
  animated in GSAP (pattern A).
