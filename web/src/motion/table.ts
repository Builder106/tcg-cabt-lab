// The table: the first-load deal, the re-sort (cards slide to their new piles) and keyboard
// movement through a pile.
import { gsap } from 'gsap';
import { Flip } from 'gsap/Flip';
import { ease, isTouch, onPage, prefersReducedMotion } from '../engine';
import { setSwap } from '../engine/astro';
import { nav } from './state';

gsap.registerPlugin(Flip);

// Game cards in the piles, plus the sort cards: the one played moves from the hand to the table
const FLIP = '.pile__cards [data-flip-id], [data-flip-id^="sort-"]';
let flipState: Flip.FlipState | null = null;
let resorting = false;

setSwap({
  capture: () => {
    if (prefersReducedMotion()) return;
    flipState = Flip.getState(FLIP);
    resorting = true;
  },
  play: () => {
    const state = flipState;
    flipState = null;
    if (!state) return;
    const tiles = gsap.utils.toArray<HTMLElement>('.pile__cards [data-flip-id]');
    const sortCards = gsap.utils.toArray<HTMLElement>('[data-flip-id^="sort-"]');
    Flip.from(state, {
      targets: tiles,
      duration: 1.05,
      ease: ease.out,
      stagger: { amount: 0.4, from: 'random' },
      onComplete: () => { resorting = false; },
    });
    // The played card slides from the hand onto the table; the old one returns to the hand
    Flip.from(state, { targets: sortCards, duration: 0.85, ease: ease.inOut, scale: true, absolute: true, zIndex: 50 });
    gsap.from('.played__art, .played__rules', { autoAlpha: 0, duration: 0.5, delay: 0.55, ease: ease.soft });
    // Each card turns a little in flight and settles square to its resting angle
    gsap.fromTo(tiles.map((t) => t.firstElementChild), { rotation: () => gsap.utils.random(-7, 7) },
      { rotation: 0, duration: 1.1, ease: ease.out, stagger: { amount: 0.4, from: 'random' }, clearProps: 'transform' });
    gsap.from('.pile__label, .pile__rate, .pile__meta, .ci, .mgrid__score', { autoAlpha: 0, y: 10, duration: 0.7, ease: ease.out, stagger: 0.03, delay: 0.25 });
  },
});

/** Deal order: alternate between piles, as a dealer would. */
function dealOrder(): HTMLElement[] {
  const piles = gsap.utils.toArray<HTMLElement>('.pile__cards').map((p) => [...p.querySelectorAll<HTMLElement>('[data-flip-id]')]);
  const out: HTMLElement[] = [];
  const longest = Math.max(...piles.map((p) => p.length));
  for (let i = 0; i < longest; i++) for (const p of piles) if (p[i]) out.push(p[i]!);
  return out;
}

function deal(intro: gsap.core.Timeline) {
  const tiles = dealOrder();
  if (!tiles.length) return;
  const ox = innerWidth * 0.5;
  const oy = innerHeight + 80;
  // Animate a sample of the visible cards; the full table remains available immediately.
  const visible = tiles.slice(0, 24).filter((t) => t.getBoundingClientRect().top < innerHeight + 200);
  const from = visible.map((t) => { const r = t.getBoundingClientRect(); return { x: ox - (r.left + r.width / 2), y: oy - (r.top + r.height / 2) }; });
  const hand = gsap.utils.toArray<HTMLElement>('.hand__slot');
  if (hand.length) {
    intro.add(gsap.from(hand, { y: () => innerHeight * 0.6, rotation: () => gsap.utils.random(-30, 30), duration: 1.1, ease: ease.out, stagger: 0.08, clearProps: 'transform' }), 0);
  }
  intro.add(gsap.from(visible, {
    x: (i: number) => from[i]!.x,
    y: (i: number) => from[i]!.y,
    rotation: () => gsap.utils.random(-28, 28),
    duration: 0.85,
    ease: ease.out,
    stagger: Math.min(0.0028, 1 / visible.length),
    clearProps: 'transform',
  }), 0);
  // The piles' numbers count up as the cards land
  document.querySelectorAll<HTMLElement>('.pile__num').forEach((el) => {
    const end = parseFloat(el.textContent || '0');
    const o = { v: 0 };
    intro.add(gsap.to(o, { v: end, duration: 1.4, ease: 'power2.out', onUpdate: () => { el.textContent = o.v.toFixed(1); } }), 0.15);
  });
}

/** Roving focus inside a pile: one tab stop per pile, arrows move between cards. */
function roving(root: HTMLElement) {
  const tiles = [...root.querySelectorAll<HTMLElement>('a.tile')];
  if (!tiles.length) return () => {};
  tiles.forEach((t, i) => { t.tabIndex = i === 0 ? 0 : -1; });
  const cols = () => Math.max(1, Math.round(root.clientWidth / (tiles[0]!.offsetWidth + 4)));
  const onKey = (e: KeyboardEvent) => {
    const i = tiles.indexOf(e.target as HTMLElement);
    if (i < 0) return;
    const c = cols();
    // wrap-reverse: the first row sits at the bottom, so visual up is +cols
    const moves: Record<string, number> = { ArrowRight: 1, ArrowLeft: -1, ArrowUp: c, ArrowDown: -c };
    let j = i;
    if (e.key in moves) j = i + moves[e.key]!;
    else if (e.key === 'Home') j = 0;
    else if (e.key === 'End') j = tiles.length - 1;
    else return;
    e.preventDefault();
    j = Math.max(0, Math.min(tiles.length - 1, j));
    tiles[i]!.tabIndex = -1;
    tiles[j]!.tabIndex = 0;
    tiles[j]!.focus();
  };
  root.addEventListener('keydown', onKey);
  return () => root.removeEventListener('keydown', onKey);
}

/** The hand along the bottom edge breathes a little at rest and leans toward the pointer. */
function sway() {
  const hand = document.querySelector<HTMLElement>('.hand__fan');
  if (!hand || prefersReducedMotion() || isTouch()) return () => {};
  let visible = true;
  let lean = 0, target = 0;
  const seen = new IntersectionObserver(([e]) => { visible = !!e?.isIntersecting; });
  seen.observe(hand);
  const move = (e: PointerEvent) => { target = (e.clientX / innerWidth - 0.5) * 4; };
  addEventListener('pointermove', move, { passive: true });
  const rotate = gsap.quickSetter(hand, 'rotation', 'deg');
  const lift = gsap.quickSetter(hand, 'y', 'px');
  const tick = (time: number) => {
    if (!visible || document.hidden) return;
    lean += (target - lean) * 0.05;
    rotate(Math.sin(time * 0.6) * 0.8 + lean * 0.5);
    lift(Math.sin(time * 0.9) * 3);
  };
  gsap.ticker.add(tick);
  return () => { gsap.ticker.remove(tick); seen.disconnect(); removeEventListener('pointermove', move); };
}

onPage(({ intro, first }) => {
  if (!document.querySelector('[data-table]')) document.documentElement.classList.remove('deal-pending');
  const table = document.querySelector<HTMLElement>('[data-table]');
  if (!table) return;
  nav.lastTable = location.pathname;
  const offs = gsap.utils.toArray<HTMLElement>('.pile__cards').map(roving);
  if (first && !resorting && !prefersReducedMotion() && !isTouch()) deal(intro);
  document.documentElement.classList.remove('deal-pending');
  const offHand = sway();
  return () => { offs.forEach((f) => f()); offHand(); };
});
