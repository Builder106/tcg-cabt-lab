// Astro adapter (ClientRouter). Call start(setup) once from the layout's <script>.
// Three kinds of navigation:
//   a re-sort (table to table): no curtain; the cards slide to their new piles (setSwap hooks)
//   back/forward: no curtain, no scroll reset
//   anything else: the curtain leaves while the next page loads, then enters
import { boot, cleanup, enter, leave, stopScroll, syncFlags } from './index';

type Swap = { capture: () => void; play: () => void };
let swap: Swap | null = null;
/** Hooks for navigations that animate the content itself instead of a curtain. */
export const setSwap = (s: Swap) => { swap = s; };

let mode: 'curtain' | 'quiet' | 'resort' | null = null;

export function start(setup?: () => void) {
  document.addEventListener('astro:before-preparation', (e) => {
    const resort = !!(e.sourceElement as Element | undefined)?.closest?.('[data-resort]')
      && !!document.querySelector('[data-table]');
    mode = e.navigationType === 'traverse' ? 'quiet' : resort ? 'resort' : 'curtain';
    if (mode !== 'curtain') { stopScroll(); return; }
    const load = e.loader;
    e.loader = async () => { await Promise.all([leave(), load()]); };
  });
  document.addEventListener('astro:before-swap', () => {
    if (mode === 'resort') swap?.capture();
    cleanup();
  });
  document.addEventListener('astro:after-swap', () => {
    syncFlags();
    document.getElementById('loader')?.remove();
  });
  document.addEventListener('astro:page-load', () => {
    if (!mode) return void boot(setup);
    const m = mode;
    mode = null;
    if (m === 'resort') {
      void enter({ transition: false, scrollTop: false });
      swap?.play();
    } else if (m === 'quiet') void enter({ transition: false, scrollTop: false });
    else void enter();
  });
  boot(setup);
}
