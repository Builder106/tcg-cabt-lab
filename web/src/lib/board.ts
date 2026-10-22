// The mat: renders one decision frame of a replay as HTML. Shared by the server (first paint)
// and the client viewer, so both draw the same board. Every string from the replay is escaped.
//
// Information boundary. Agent view shows what the studied policy could know: its own hand, the
// public board and counts. The opponent's hand, the opponent's options and every Prize card stay
// face down. Spectator view adds them, and marks each one as spectator only.
import { opponentName } from './labels';
import type { CardInfo, Frame, GameEvent, Player, Pokemon, Replay, View } from './types';

const esc = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

const ENERGY: Record<string, { id: string; word: string }> = {
  P: { id: 'g-psychic', word: 'Psychic' },
  W: { id: 'g-water', word: 'Water' },
  C: { id: 'g-colorless', word: 'Colorless' },
};
const TYPE_LETTER: Record<number, string> = { 3: 'W', 5: 'P' };

const glyph = (letter: string, cls = 'glyph') => {
  const e = ENERGY[letter] ?? ENERGY.C!;
  return `<svg class="${cls}" viewBox="0 0 24 24" role="img" aria-label="${e.word}"><use href="#${e.id}"/></svg>`;
};

/** A card name from the engine catalog, with energy tokens such as {P} drawn as glyphs. */
export function nameHTML(name: string): string {
  return esc(name)
    // A soft hyphen mid-way through long words, so narrow cards break "Determi-nation", not "Determinat ion"
    .replace(/\p{L}{11,}/gu, (w) => `${w.slice(0, Math.ceil(w.length / 2))}&shy;${w.slice(Math.ceil(w.length / 2))}`)
    .replace(/\{([A-Z])\}/g, (_, l: string) => glyph(l, 'glyph glyph--inline'));
}

const SPEC = '<span class="spec-tag">Spectator only</span>';

export type Ctx = { replay: Replay; view: View; seat: number };

const card = (r: Replay, id: number): CardInfo =>
  r.cards[String(id)] ?? { name: 'Unknown card', hp: 0, card_type: -1, energy_type: 0, ex: false };

/** Attacks each card used in this game, from the replay's Attack events. */
const movesCache = new WeakMap<Replay, Map<number, number[]>>();
function movesOf(r: Replay, id: number): number[] {
  let m = movesCache.get(r);
  if (!m) {
    m = new Map();
    for (const f of r.frames) for (const e of f.events) {
      if (e.type !== 'Attack' || e.card === undefined || e.attack === undefined) continue;
      const list = m.get(e.card) ?? [];
      if (!list.includes(e.attack)) list.push(e.attack);
      m.set(e.card, list);
    }
    movesCache.set(r, m);
  }
  return m.get(id) ?? [];
}

/** One of six original art motifs per Pokémon name, so copies of a card share their art. */
function picHTML(c: CardInfo): string {
  if (c.card_type !== 0) return '';
  let h = 0;
  for (const ch of c.name) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return `<svg class="card__pic" viewBox="0 0 542 332" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false"><use href="#mon-art-${(h % 6) + 1}"/></svg>`;
}

/** Which original card face a card is printed on. */
function faceOf(c: CardInfo): string {
  if (c.card_type === 0) return c.energy_type === 5 ? 'psychic' : c.energy_type === 3 ? 'water' : 'colorless';
  if (c.card_type === 5) return c.energy_type === 5 ? 'energy-psychic' : c.energy_type === 3 ? 'energy-water' : 'colorless';
  return 'trainer';
}

function monHTML(ctx: Ctx, m: Pokemon, size: 'active' | 'bench', status: string[]): string {
  const c = card(ctx.replay, m.id);
  const damage = Math.max(0, m.max_hp - m.hp);
  const energy = m.energy.map((e) => glyph(TYPE_LETTER[card(ctx.replay, e).energy_type] ?? 'C', 'glyph glyph--energy')).join('');
  const tools = m.tools.map((t) => `<span class="card__tool">${nameHTML(card(ctx.replay, t).name)}</span>`).join('');
  const asleep = status.includes('asleep') && size === 'active'
    ? '<svg class="card__status" viewBox="0 0 24 24" role="img" aria-label="Asleep"><use href="#g-asleep"/></svg>' : '';
  const counter = damage
    ? `<span class="counter"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#t-counter"/></svg><b>${damage}</b><span class="sr-only"> damage</span></span>` : '';
  const moves = size === 'active'
    ? movesOf(ctx.replay, m.id).map((a) => {
        const at = ctx.replay.attacks[String(a)];
        return at ? `<span class="card__move">${esc(at.name)}${at.damage ? ` <b>${at.damage}</b>` : ''}</span>` : '';
      }).join('') : '';
  return `<div class="card card--${size} face--${faceOf(c)}" data-card="${m.id}" data-hp="${m.hp}">`
    + `<span class="card__hp"><b>${m.hp}</b><span class="sr-only"> of </span><span aria-hidden="true">/</span>${m.max_hp}<span class="card__hp-unit"> HP</span></span>`
    + picHTML(c) + `<span class="card__art">${counter}${asleep}</span>`
    + `<span class="card__name">${nameHTML(c.name)}</span>`
    + (moves ? `<span class="card__moves"><span class="sr-only">Attacks used this game: </span>${moves}</span>` : '')
    + `<span class="card__energy">${energy ? `<span class="sr-only">${m.energy.length} Energy attached: </span>${energy}` : ''}</span>`
    + tools + `</div>`;
}

function faceCard(ctx: Ctx, id: number, cls = 'card--mini', spec = false): string {
  const c = card(ctx.replay, id);
  const kind = c.card_type === 0 ? 'Pokémon' : c.card_type === 5 ? 'Energy' : c.card_type === 3 ? 'Supporter' : c.card_type === 1 ? 'Item' : 'Card';
  return `<div class="card ${cls} face--${faceOf(c)}${spec ? ' card--spec' : ''}" data-kind="${kind}" data-card="${id}">`
    + `<span class="card__kind">${kind}</span>${picHTML(c)}<span class="card__name">${nameHTML(c.name)}</span></div>`;
}

const backs = (n: number, cls: string, cap = 12) =>
  `<span class="backs ${cls}" aria-hidden="true">${'<i class="card card--back"></i>'.repeat(Math.min(n, cap))}${n > cap ? `<b>+${n - cap}</b>` : ''}</span>`;

function sideHTML(ctx: Ctx, p: Player, isPolicy: boolean): string {
  const who = isPolicy ? 'The AI' : opponentName[ctx.replay.game.opponent];
  const spectator = ctx.view === 'spectator';
  const active = p.active[0];
  const benchSlots = Array.from({ length: 5 }, (_, i) => p.bench[i]);

  // Hand: the policy always sees its own; the opponent's is face down unless spectating
  let hand: string;
  if (isPolicy) {
    hand = p.hand.length ? p.hand.map((id) => `<span class="slot">${faceCard(ctx, id)}</span>`).join('') : '<span class="zone__empty">No cards</span>';
  } else if (spectator) {
    hand = p.hand.length ? p.hand.map((id) => `<span class="slot">${faceCard(ctx, id, 'card--mini', true)}</span>`).join('') : '<span class="zone__empty">No cards</span>';
  } else {
    hand = backs(p.hand_count, 'backs--fan');
  }
  const handZone = `<div class="zone zone--hand${!isPolicy && spectator ? ' is-spec' : ''}">`
    + `<p class="zone__label">Hand <b>${p.hand_count}</b>${!isPolicy && spectator ? SPEC : ''}</p><div class="zone__cards">${hand}</div></div>`;

  // Prize cards: nobody sees them, so they are face down in agent view for both players
  const prizes = spectator
    ? `<div class="prizes prizes--open">${p.prizes.map((id) => faceCard(ctx, id, 'card--prize', true)).join('')}</div>`
    : `<div class="prizes">${'<i class="card card--back card--prize" aria-hidden="true"></i>'.repeat(p.prizes.length)}</div>`;
  const prizeZone = `<div class="zone zone--prizes${spectator ? ' is-spec' : ''}"><p class="zone__label">Prize cards <b>${p.prizes.length}</b>${spectator && p.prizes.length ? SPEC : ''}</p>${prizes}</div>`;

  const top = p.discard[p.discard.length - 1];
  const discardZone = `<div class="zone zone--discard"><p class="zone__label">Discard <b>${p.discard.length}</b></p>`
    + (top !== undefined ? faceCard(ctx, top, 'card--pile') : '<span class="zone__slot" aria-hidden="true"></span>') + `</div>`;
  const deckZone = `<div class="zone zone--deck"><p class="zone__label">Deck <b>${p.deck_count}</b></p>`
    + (p.deck_count ? `<img class="deck" src="/img/deck-150.webp" srcset="/img/deck-150.webp 150w, /img/deck-300.webp 300w" sizes="5rem" width="150" height="200" alt="" loading="lazy" decoding="async" style="--depth:${Math.min(1, p.deck_count / 60).toFixed(2)}">` : '<span class="zone__slot" aria-hidden="true"></span>')
    + `</div>`;

  const status = p.status.length ? `<p class="side__status">Active Pokémon is ${p.status.join(', ')}</p>` : '';
  const activeZone = `<div class="zone zone--active"><p class="zone__label">Active</p>${active ? monHTML(ctx, active, 'active', p.status) : '<span class="zone__slot zone__slot--active" aria-hidden="true"></span>'}${status}</div>`;
  const benchZone = `<div class="zone zone--bench"><p class="zone__label">Bench <b>${p.bench.length}</b></p><div class="bench">`
    + benchSlots.map((m) => (m ? monHTML(ctx, m, 'bench', []) : '<span class="zone__slot" aria-hidden="true"></span>')).join('') + `</div></div>`;

  return `<section class="side side--${isPolicy ? 'policy' : 'opp'}" aria-label="${esc(who)}">`
    + `<h2 class="side__name">${esc(who)}</h2>`
    + prizeZone + activeZone + benchZone + deckZone + discardZone + handZone + `</section>`;
}

export function boardHTML(ctx: Ctx, frame: Frame): string {
  const me = frame.players[ctx.seat]!;
  const them = frame.players[1 - ctx.seat]!;
  const stadium = frame.stadium.length
    ? `<p class="board__stadium">Stadium in play: ${nameHTML(card(ctx.replay, frame.stadium[0]!).name)}</p>` : '';
  return sideHTML(ctx, them, false) + `<div class="board__line" aria-hidden="true"></div>${stadium}` + sideHTML(ctx, me, true);
}

// ---------------------------------------------------------------------------------------------
// Events, in plain words

type Line = { text: string; spec: boolean; key: string };

function eventLines(ctx: Ctx, events: GameEvent[], turn: number): Line[] {
  const r = ctx.replay;
  const agent = ctx.view === 'agent';
  const isPolicy = (p?: number) => p === ctx.seat;
  const who = (p?: number) => (isPolicy(p) ? 'The AI' : 'The opponent');
  const nm = (id?: number) => (id === undefined ? 'a card' : nameHTML(card(r, id).name));
  const out: Line[] = [];
  const push = (text: string, key: string, spec = false) => out.push({ text, key, spec });

  // Opening-hand redraws repeat seven draws, seven cards shuffled back and a shuffle each time.
  // Fold them into one line per player and keep only the draws of the hand that stuck.
  const redraws = new Map<number, number>(), lastRedraw = new Map<number, number>();
  events.forEach((e, i) => {
    if (e.type !== 'HasBasicPokemon' || e.has_basic || e.player === undefined) return;
    redraws.set(e.player, (redraws.get(e.player) ?? 0) + 1);
    lastRedraw.set(e.player, i);
  });
  const folded = (e: GameEvent, i: number) => e.player !== undefined && redraws.has(e.player) && (
    (e.type === 'Draw' && i < lastRedraw.get(e.player)!) || e.type === 'Shuffle' || e.type === 'HasBasicPokemon'
    || (e.type === 'MoveCard' && e.from === 'hand' && e.to === 'deck'));

  for (const [i, e] of events.entries()) {
    const p = e.player;
    if (p !== undefined && redraws.has(p) && e.type === 'HasBasicPokemon' && i === events.findIndex((x) => x.type === 'HasBasicPokemon' && x.player === p && !x.has_basic)) {
      const n = redraws.get(p)!;
      push(`${who(p)} had no Basic Pokémon in its opening hand and redrew it${n > 1 ? ` (${n} times)` : ''}.`, `redraw-${p}`);
      continue;
    }
    if (folded(e, i)) continue;
    const hiddenForAgent = !isPolicy(p);
    switch (e.type) {
      case 'TurnStart': push(`Turn ${turn} begins for ${who(p).toLowerCase()}.`, 'turn'); break;
      case 'TurnEnd': push(`${who(p)} ended its turn.`, 'turnend'); break;
      case 'Draw':
        if (hiddenForAgent && agent) push(`${who(p)} drew a card.`, `draw-hidden-${p}`);
        else push(`${who(p)} drew ${nm(e.card)}.`, `draw-${p}`, hiddenForAgent);
        break;
      case 'Play': push(`${who(p)} played ${nm(e.card)}.`, 'play'); break;
      case 'Attach': push(`${who(p)} attached ${nm(e.card)} to ${nm(e.target)}.`, 'attach'); break;
      case 'Attack': {
        const a = r.attacks[String(e.attack)];
        push(`${who(p)}’s ${nm(e.card)} used ${a ? esc(a.name) : 'an attack'}.`, 'attack');
        break;
      }
      case 'HpChange': {
        const v = e.value ?? 0;
        push(v < 0 ? `${nm(e.card)} took ${-v} damage.` : `${nm(e.card)} healed ${v}.`, 'hp');
        break;
      }
      case 'Switch': push(`${who(p)} switched ${nm(e.bench)} into the Active Spot.`, 'switch'); break;
      case 'Coin': push(`<svg class="coin" viewBox="0 0 24 24" aria-hidden="true"><use href="#t-coin-${e.heads ? 'heads' : 'tails'}"/></svg>Coin flip: ${e.heads ? 'heads' : 'tails'}.`, 'coin'); break;
      case 'Shuffle': push(`${who(p)} shuffled its deck.`, 'shuffle'); break;
      case 'Asleep': push(e.recovered ? `${nm(e.card)} woke up.` : `${nm(e.card)} is still Asleep.`, 'asleep'); break;
      case 'HasBasicPokemon': if (!e.has_basic) push(`${who(p)} had no Basic Pokémon in its opening hand and drew again.`, 'mulligan'); break;
      case 'Result': break;
      case 'MoveCard': {
        const from = e.from, to = e.to;
        const c = e.card !== undefined ? card(r, e.card) : undefined;
        if (from === 'deck' && to === 'prize') { push(`${who(p)} set aside a Prize card.`, `prize-set-${p}`); break; }
        if (from === 'prize' && to === 'hand') {
          if (hiddenForAgent && agent) push(`${who(p)} took a Prize card.`, `prize-take-${p}`);
          else push(`${who(p)} took a Prize card: ${nm(e.card)}.`, `prize-take-${p}`, hiddenForAgent);
          break;
        }
        if (from === 'deck' && to === 'hand') {
          if (hiddenForAgent && agent) push(`${who(p)} put a card from its deck into its hand.`, `search-${p}`);
          else push(`${who(p)} put ${nm(e.card)} from its deck into its hand.`, `search-${p}`, hiddenForAgent);
          break;
        }
        if (from === 'hand' && to === 'deck') {
          if (hiddenForAgent && agent) push(`${who(p)} shuffled a card from its hand into its deck.`, `tuck-${p}`);
          else push(`${who(p)} shuffled ${nm(e.card)} from its hand into its deck.`, `tuck-${p}`, hiddenForAgent);
          break;
        }
        if (from === 'active' && to === 'discard' && c?.card_type === 0) { push(`${nm(e.card)} was Knocked Out.`, 'ko'); break; }
        if (from === 'attached' && to === 'discard') { push(`${who(p)} discarded ${nm(e.card)} from a Pokémon.`, 'energy-discard'); break; }
        if (to === 'active') { push(`${who(p)} put ${nm(e.card)} into the Active Spot.`, 'to-active'); break; }
        if (to === 'bench') { push(`${who(p)} put ${nm(e.card)} on the Bench.`, 'to-bench'); break; }
        if (to === 'discard') { push(`${who(p)} discarded ${nm(e.card)}.`, 'discard'); break; }
        push(`${who(p)} moved ${nm(e.card)} from ${esc(from ?? '?')} to ${esc(to ?? '?')}.`, 'move');
        break;
      }
      default: push(esc(e.type), 'other');
    }
  }
  return out;
}

/** Merge runs of the same hidden or repeated line ("drew a card" x7 becomes "drew 7 cards"). */
function merge(lines: Line[]): Line[] {
  const out: (Line & { n: number })[] = [];
  for (const l of lines) {
    const last = out[out.length - 1];
    if (last && last.text === l.text && last.spec === l.spec) last.n++;
    else out.push({ ...l, n: 1 });
  }
  return out.map((l) => (l.n > 1 ? { ...l, text: `${l.text.replace(/\.$/, '')} (${l.n} times).` } : l));
}

export function eventsHTML(ctx: Ctx, events: GameEvent[], turn: number): string {
  const lines = merge(eventLines(ctx, events, turn));
  if (!lines.length) return '<p class="events__none">Nothing happened on the table.</p>';
  const li = (l: Line) => `<li${l.spec ? ' class="is-spec"' : ''}>${l.text}${l.spec ? SPEC : ''}</li>`;
  // Long turns show the first lines and fold the rest
  if (lines.length <= 8) return `<ol class="events">${lines.map(li).join('')}</ol>`;
  return `<ol class="events">${lines.slice(0, 6).map(li).join('')}</ol>`
    + `<details class="events__more"><summary>Show ${lines.length - 6} more</summary><ol class="events" start="7">${lines.slice(6).map(li).join('')}</ol></details>`;
}

// ---------------------------------------------------------------------------------------------
// The decision panel

/** The engine's prompts, as what the player is doing. */
const PROMPTS: Record<string, string> = {
  'Choose an action': 'picks its next move',
  'Choose Energy to discard': 'picks Energy to discard',
  'Choose a Pokémon to switch in': 'picks a Pokémon to switch in',
  'Choose cards to put into the hand': 'picks cards to take into its hand',
  'Choose cards to discard': 'picks cards to discard',
  'Choose the Active Pokémon': 'picks its first Active Pokémon',
  'Choose a new Active Pokémon': 'picks a new Active Pokémon',
  'Choose Energy to attach': 'picks Energy to attach',
  'Go first?': 'decides whether to go first',
  'Choose Pokémon for the Bench': 'picks Pokémon for its Bench',
  'Choose how many cards to draw': 'picks how many cards to draw',
  'Discard energy card': 'picks an Energy card to discard',
};
export const promptText = (prompt: string) => PROMPTS[prompt] ?? prompt.charAt(0).toLowerCase() + prompt.slice(1);

export function decisionHTML(ctx: Ctx, k: number): string {
  const { replay, view, seat } = ctx;
  const f = replay.frames[k]!;
  const next = replay.frames[k + 1];
  const n = replay.frames.length;
  const mine = f.actor === seat;
  const when = f.turn === 0 ? 'setup' : `turn ${f.turn}`;
  const meta = `<p class="decision__count">Decision ${k + 1} of ${n} (both players), ${when}.</p>`;

  if (!f.options.length) {
    return `<h2 class="ribbon decision__prompt">Game over</h2><div class="panel__body">` + meta + eventsHTML(ctx, f.events.filter((e) => e.type !== 'Result'), f.turn) + `</div>`;
  }
  const need = f.min === f.max ? (f.max === 1 ? 'pick one' : `pick ${f.max}`) : `pick ${f.min} to ${f.max}`;
  const actor = mine ? 'The AI' : 'The opponent';
  let body: string;
  if (!mine && view === 'agent') {
    body = `<p class="decision__hidden">The opponent chose from cards the AI couldn’t see, so the AI’s view keeps them face down. Switch to the spectator view to see them.</p>`;
  } else {
    const scores = mine ? f.scores : null;
    const lo = scores ? Math.min(...scores) : 0, hi = scores ? Math.max(...scores) : 0;
    // The engine lists one option per copy of a card, so identical moves are grouped into one row
    const groups: number[][] = [];
    f.options.forEach((label, i) => {
      const g = groups.find((x) => f.options[x[0]!] === label);
      if (g) g.push(i); else groups.push([i]);
    });
    const items = groups.map((g) => {
      const picked = g.filter((i) => f.chosen.includes(i));
      // The row shows the chosen copy's score, or the best copy's when none was chosen
      const at = picked[0] ?? g.reduce((a, b) => ((scores?.[b] ?? 0) > (scores?.[a] ?? 0) ? b : a));
      const s = scores?.[at];
      const w = s === undefined ? 0 : hi > lo ? 0.08 + 0.92 * ((s - lo) / (hi - lo)) : 1;
      const others = scores && g.length > 1 ? g.filter((i) => i !== at).map((i) => scores[i]!) : [];
      const range = others.length
        ? `<span class="option__others">Other ${others.length > 1 ? 'copies' : 'copy'}: ${Math.min(...others).toFixed(2)}${others.length > 1 ? ` to ${Math.max(...others).toFixed(2)}` : ''}</span>` : '';
      const score = s === undefined ? ''
        : `<span class="option__score"><span class="option__bar" aria-hidden="true"><i style="transform:scaleX(${w.toFixed(3)})"></i></span><span class="option__num">score ${s.toFixed(2)}</span></span>${range}`;
      const times = g.length > 1 ? ` <span class="option__times">×${g.length}</span>` : '';
      const chosen = picked.length ? `<span class="option__chosen">Chosen${picked.length > 1 ? ` ×${picked.length}` : ''}</span>` : '';
      return `<li class="option${picked.length ? ' is-chosen' : ''}"><span class="option__label">${nameHTML(f.options[g[0]!]!)}${times}</span>${chosen}${score}</li>`;
    }).join('');
    const spec = !mine ? SPEC : '';
    const most = Math.max(...groups.map((g) => g.length));
    const copies = most > 1
      ? `<p class="decision__note">×${most} means ${most} copies of the same card could make that move. The game lists each copy as its own option and the AI scores each one separately, so identical moves can score slightly differently.</p>`
      : '';
    body = `<ol class="options${!mine ? ' is-spec' : ''}">${items}</ol>${spec}` + copies
      + (mine && f.scores ? `<p class="decision__note">Scores show how strongly the AI preferred each option; it plays the highest. They are not chances of winning.</p>` : '');
  }
  const result = next ? `<h3 class="decision__sub">What happened next</h3>${eventsHTML(ctx, next.events, next.turn)}` : '';
  return `<h2 class="ribbon decision__prompt">${actor} ${esc(promptText(f.prompt))}</h2><div class="panel__body">`
    + `<p class="decision__count">Decision ${k + 1} of ${n} (both players), ${when}. <span class="decision__need">${need[0]!.toUpperCase()}${need.slice(1)}.</span></p>` + body + result + `</div>`;
}

/** Who played each turn, from its TurnStart event. Turn 0 is the setup, played by both. */
export function turnOwners(r: Replay): Map<number, number> {
  const m = new Map<number, number>();
  for (const f of r.frames) for (const e of f.events) {
    if (e.type === 'TurnStart' && e.player !== undefined && !m.has(f.turn)) m.set(f.turn, e.player);
  }
  return m;
}

/** The player's readout: which turn, whose turn, and the decision count. */
export function whereHTML(r: Replay, k: number, seat: number, owners: Map<number, number>): string {
  const f = r.frames[k]!;
  const last = r.frames[r.frames.length - 1]!.turn;
  const owner = owners.get(f.turn);
  const who = owner === undefined ? '<span class="where__who">Both players</span>'
    : owner === seat ? '<span class="where__who is-ai">AI’s turn</span>' : '<span class="where__who is-opp">Opponent’s turn</span>';
  const turn = f.turn === 0 ? '<b>Setup</b>' : `<b>Turn ${f.turn}</b> of ${last}`;
  return `<span class="where__turn">${turn}</span>${who}<span class="where__dec">Decision ${k + 1} of ${r.frames.length}</span>`;
}

/** The decision index a deep link without ?d= opens on: the policy's first choice on turn 1 or later. */
export function startFrame(replay: Replay): number {
  const seat = replay.game.policy_seat;
  const i = replay.frames.findIndex((f) => f.turn >= 1 && f.actor === seat && f.options.length > 0);
  return i < 0 ? 0 : i;
}
