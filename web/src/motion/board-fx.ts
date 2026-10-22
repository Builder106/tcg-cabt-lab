// Board motion for the replay. A forward step is animated by comparing the board before and after
// it: cards still in view slide from where they were, new cards come from the deck, the hand or
// the Prize cards, and cards that left fly to their discard pile or onto the Pokémon they were
// attached to. An attack lunges, the hit card shakes and its damage floats up. Only what the
// current view shows is compared, so the AI's view never animates a card the AI could not see.
import { gsap } from 'gsap';

type Side = 'me' | 'them';
type Item = { el: HTMLElement; id: string; side: Side; zone: string; rect: DOMRect; hp: number; energy: number; energyCard: boolean };
export type Snapshot = { items: Item[]; zones: Map<string, DOMRect>; backs: Record<Side, number>; prizes: Record<Side, number> };

const SIDE: Record<Side, string> = { me: '.side--policy', them: '.side--opp' };
const sideOf = (el: Element): Side => (el.closest('.side')?.classList.contains('side--policy') ? 'me' : 'them');
const zoneOf = (el: Element) => /zone--(\w+)/.exec(el.closest('.zone')?.className ?? '')?.[1] ?? '';
const center = (r: DOMRect) => ({ x: r.left + r.width / 2, y: r.top + r.height / 2 });

export function snapshot(board: HTMLElement): Snapshot {
  const items = [...board.querySelectorAll<HTMLElement>('[data-card]')].map((el) => ({
    el, id: el.dataset.card!, side: sideOf(el), zone: zoneOf(el), rect: el.getBoundingClientRect(),
    hp: Number(el.dataset.hp ?? NaN), energy: el.querySelectorAll('.glyph--energy').length,
    energyCard: /face--energy/.test(el.className),
  }));
  const zones = new Map<string, DOMRect>();
  board.querySelectorAll<HTMLElement>('.zone').forEach((z) => zones.set(`${sideOf(z)}:${zoneOf(z)}`, z.getBoundingClientRect()));
  const count = (side: Side, sel: string) => board.querySelectorAll(`${SIDE[side]} ${sel}`).length;
  return {
    items, zones,
    backs: { me: count('me', '.zone--hand .card--back'), them: count('them', '.zone--hand .card--back') },
    prizes: { me: count('me', '.zone--prizes .card'), them: count('them', '.zone--prizes .card') },
  };
}

let running: gsap.core.Timeline | null = null;

/** Animate the step from `before` to the board as it is now. `speed` shortens everything while playing. */
export function animateStep(board: HTMLElement, before: Snapshot, attacker: Side | null, speed: number) {
  running?.progress(1).kill();
  const after = snapshot(board);
  const d = 0.5 / speed;
  const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
  running = tl;
  const b = board.getBoundingClientRect();
  // The board may be zoomed to fit the window: rects are on screen, offsets inside it are divided back
  const z = Number(board.dataset.zoom || 1);
  const local = (r: DOMRect) => ({ left: (r.left - b.left) / z - board.clientLeft, top: (r.top - b.top) / z - board.clientTop });
  // Offset that places something centred on `to` over the centre of `from`
  const fly = (from: DOMRect, to: DOMRect) => {
    const f = center(from), t = center(to);
    return { x: (f.x - t.x) / z, y: (f.y - t.y) / z };
  };

  // Pair each card now in view with the same card before: same zone first, then any zone
  const pool = [...before.items];
  const take = (pred: (o: Item) => boolean) => { const i = pool.findIndex(pred); return i < 0 ? null : pool.splice(i, 1)[0]!; };
  const pairs = after.items.map((n) => ({ n, o: take((o) => o.id === n.id && o.side === n.side && o.zone === n.zone) }));
  for (const p of pairs) if (!p.o) p.o = take((o) => o.id === p.n.id && o.side === p.n.side);
  const gone = pool;

  // The attack lands a beat after the lunge; damage and knockouts wait for it
  const hit = attacker ? 0.18 / speed : 0;
  if (attacker) {
    const att = board.querySelector<HTMLElement>(`${SIDE[attacker]} .zone--active [data-card]`);
    // Aim at the defender where it stood before the hit, even if the hit knocked it out
    const defender: Side = attacker === 'me' ? 'them' : 'me';
    const def = before.items.find((o) => o.side === defender && o.zone === 'active')?.rect
      ?? board.querySelector<HTMLElement>(`${SIDE[defender]} .zone--active [data-card]`)?.getBoundingClientRect();
    if (att && def) {
      const v = fly(def, att.getBoundingClientRect());
      tl.to(att, { x: v.x * 0.3, y: v.y * 0.3, rotation: attacker === 'me' ? -4 : 4, duration: hit, ease: 'power2.in' }, 0)
        .to(att, { x: 0, y: 0, rotation: 0, duration: 0.3 / speed, ease: 'power3.out', clearProps: 'transform' }, hit);
    }
  }

  for (const { n, o } of pairs) {
    if (o) {
      const dx = (o.rect.left - n.rect.left) / z, dy = (o.rect.top - n.rect.top) / z, s = o.rect.width / n.rect.width;
      if (Math.abs(dx) + Math.abs(dy) > 1 || Math.abs(s - 1) > 0.02) {
        tl.from(n.el, { x: dx, y: dy, scale: s, transformOrigin: '0 0', duration: d, clearProps: 'transform' }, 0);
      }
      if (n.hp < o.hp) damage(n.el, o.hp - n.hp, false);
      else if (n.hp > o.hp) damage(n.el, n.hp - o.hp, true);
      if (n.energy > o.energy) {
        const glyphs = [...n.el.querySelectorAll('.glyph--energy')].slice(o.energy);
        tl.from(glyphs, { scale: 0, duration: 0.35 / speed, ease: 'back.out(3)', stagger: 0.05 }, d * 0.8);
      }
      continue;
    }
    // A card that just appeared: drawn from the deck, taken from the Prize cards, or played from the hand
    if (n.zone === 'discard' || n.zone === 'prizes') continue;
    const evolvedFrom = (n.zone === 'active' || n.zone === 'bench')
      && gone.find((g) => g.side === n.side && g.zone === n.zone && Math.hypot(center(g.rect).x - center(n.rect).x, center(g.rect).y - center(n.rect).y) < 12);
    if (evolvedFrom) {
      gone.splice(gone.indexOf(evolvedFrom), 1);
      tl.fromTo(n.el, { scale: 1.12, filter: 'brightness(1.8)' }, { scale: 1, filter: 'brightness(1)', duration: d * 1.2, clearProps: 'transform,filter' }, 0);
      continue;
    }
    const src = n.zone === 'hand'
      ? before.zones.get(`${n.side}:${after.prizes[n.side] < before.prizes[n.side] ? 'prizes' : 'deck'}`)
      : before.zones.get(`${n.side}:hand`);
    if (src) tl.from(n.el, { ...fly(src, n.rect), scale: 0.55, autoAlpha: 0, duration: d, clearProps: 'transform,opacity,visibility' }, 0);
  }

  // Face-down cards (the opponent's hand in the AI's view) arrive from the deck or the Prize cards
  for (const side of ['me', 'them'] as Side[]) {
    const added = after.backs[side] - before.backs[side];
    if (added <= 0) continue;
    const src = before.zones.get(`${side}:${after.prizes[side] < before.prizes[side] ? 'prizes' : 'deck'}`);
    const backs = [...board.querySelectorAll<HTMLElement>(`${SIDE[side]} .zone--hand .card--back`)].slice(-added);
    if (src) backs.forEach((el) => tl.from(el, { ...fly(src, el.getBoundingClientRect()), autoAlpha: 0, duration: d, clearProps: 'transform,opacity,visibility' }, 0));
  }

  // Cards that left: Energy onto the Pokémon that gained it, everything else to its discard pile
  const gained = pairs.filter((p) => p.o && p.n.energy > p.o.energy).map((p) => p.n);
  for (const g of gone) {
    if (g.zone === 'discard') continue;
    const onto = g.energyCard ? gained.find((m) => m.side === g.side) : undefined;
    const to = onto?.rect ?? after.zones.get(`${g.side}:discard`);
    if (!to) continue;
    const ghost = g.el.cloneNode(true) as HTMLElement;
    const at = local(g.rect);
    Object.assign(ghost.style, { position: 'absolute', left: `${at.left}px`, top: `${at.top}px`, width: `${g.rect.width / z}px`, margin: '0', zIndex: '30', pointerEvents: 'none' });
    ghost.setAttribute('aria-hidden', 'true');
    board.append(ghost);
    const v = fly(to, g.rect);
    const knocked = g.zone === 'active' || g.zone === 'bench';
    tl.to(ghost, {
      x: v.x, y: v.y, scale: onto ? 0.3 : 0.6, rotation: knocked ? 14 : 0, autoAlpha: 0,
      duration: d * (knocked ? 1.4 : 1), ease: 'power2.in', onComplete: () => ghost.remove(),
    }, knocked ? hit + 0.15 / speed : 0);
  }

  function damage(el: HTMLElement, amount: number, heal: boolean) {
    tl.fromTo(el, { x: heal ? 0 : -7 }, { x: 0, duration: 0.45 / speed, ease: 'elastic.out(1.2, 0.3)', clearProps: 'transform' }, hit)
      .fromTo(el, { filter: heal ? 'brightness(1.4) saturate(1.4)' : 'brightness(1.7) saturate(0.5)' }, { filter: 'brightness(1) saturate(1)', duration: 0.4 / speed, clearProps: 'filter' }, hit);
    const r = el.getBoundingClientRect();
    const at = local(r);
    const num = document.createElement('span');
    num.className = `fx-num${heal ? ' is-heal' : ''}`;
    num.setAttribute('aria-hidden', 'true');
    num.textContent = `${heal ? '+' : '−'}${amount}`;
    Object.assign(num.style, { left: `${at.left + r.width / z / 2}px`, top: `${at.top + (r.height / z) * 0.35}px` });
    board.append(num);
    tl.fromTo(num, { xPercent: -50, yPercent: -50, y: 0, scale: 0.6, autoAlpha: 0 }, { y: -34, scale: 1, autoAlpha: 1, duration: 0.35 / speed, ease: 'back.out(2)' }, hit)
      .to(num, { y: -52, autoAlpha: 0, duration: 0.4 / speed, ease: 'power1.in', onComplete: () => num.remove() }, hit + 0.55 / speed);
  }
}
