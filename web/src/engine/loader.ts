// First-load sequence. Progress follows real work (fonts + critical images), with a floor so it
// reads as intentional and a ceiling so it never becomes a usability problem.
import { gsap } from 'gsap';
import { ease, prefersReducedMotion } from './env';

let format = (p: number) => String(Math.round(p)).padStart(3, '0');
let progress: ((p: number) => void) | null = null;
/** Counter text; p goes 0 → 100. */
export const setLoaderFormat = (fn: (p: number) => string) => { format = fn; };
/** Called every frame with p (0 → 100), for art that follows the count. */
export const setLoaderProgress = (fn: (p: number) => void) => { progress = fn; };
let exit: ((root: HTMLElement) => gsap.core.Timeline) | null = null;
/** The loader → page handoff. Return a timeline. */
export const setLoaderExit = (fn: (root: HTMLElement) => gsap.core.Timeline) => { exit = fn; };

const MIN = 1.0;
const MAX = 2.0;

function criticalAssets(): Promise<unknown>[] {
  const imgs = [...document.querySelectorAll<HTMLImageElement>('img[data-critical]')];
  return [document.fonts.ready, ...imgs.map((i) => (i.complete ? Promise.resolve() : i.decode().catch(() => {})))];
}

export async function runLoader(): Promise<void> {
  const root = document.getElementById('loader');
  if (!root || root.hidden) return;
  if (prefersReducedMotion()) {
    await Promise.race([Promise.all(criticalAssets()), wait(MAX)]);
    progress?.(100);
    await gsap.to(root, { autoAlpha: 0, duration: 0.3 });
    return finish(root);
  }
  const count = root.querySelector<HTMLElement>('[data-loader-count]');
  const tasks = criticalAssets();
  let done = 0;
  const shown = { v: 0 };
  const target = { v: 0 };
  tasks.forEach((t) => t.then(() => { done++; target.v = (done / tasks.length) * 100; }));
  const start = performance.now();

  await new Promise<void>((resolve) => {
    const tick = () => {
      // Time-based, so a slow phone does not stretch the loader: the count follows real
      // loading, never runs ahead of an eased MIN-second clock, and is forced home at MAX.
      const elapsed = (performance.now() - start) / 1000;
      const t = Math.min(1, elapsed / MIN);
      const clock = 100 * (1 - Math.pow(1 - t, 3));
      shown.v = elapsed > MAX ? 100 : Math.min(target.v, clock);
      if (count) count.textContent = format(shown.v);
      progress?.(shown.v);
      if (shown.v === 100) { gsap.ticker.remove(tick); resolve(); }
    };
    gsap.ticker.add(tick);
  });

  if (exit) { await exit(root); return finish(root); }
  await gsap.to(root, { yPercent: -100, duration: 0.8, ease: ease.inOut });
  finish(root);
}

function finish(root: HTMLElement) {
  root.hidden = true;
  document.documentElement.classList.add('is-loaded');
}

const wait = (s: number) => new Promise((r) => setTimeout(r, s * 1000));
