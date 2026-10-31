// The sort cards' art windows. Each drawing rests on its final frame, which states the finding;
// hovering or focusing a card in the hand replays how it got there, and the played card plays
// once as it lands. Reduced motion keeps the final frames.
import { gsap } from 'gsap';
import { ease, onPage, prefersReducedMotion } from '@/engine';
import type { SortKey } from '@/lib/sorts';

type Pick = { one: (id: string) => Element | null; all: (prefix: string) => Element[] };
type Build = (tl: gsap.core.Timeline, $: Pick) => void;

const pop = 'back.out(2.2)';

const ART: Record<SortKey, Build> = {
  // One deck dealt alternately into two piles that end level
  training: (tl, $) => {
    const dealt = [1, 2, 3, 4, 5].flatMap((i) => [$.one(`fixed${i}`), $.one(`diverse${i}`)]);
    tl.from(dealt, {
      x: (i: number) => (i % 2 ? -75 : 75), y: -24, rotation: (i: number) => (i % 2 ? 9 : -9),
      duration: 0.5, ease: ease.out, stagger: 0.08,
    }).from($.one('equal'), { scale: 0, transformOrigin: '50% 50%', duration: 0.45, ease: pop }, '-=0.2');
  },
  // The two decks meet
  deck: (tl, $) => {
    tl.from($.one('psychic'), { x: -150, duration: 0.6, ease: ease.out })
      .from($.one('colorless'), { x: 150, duration: 0.6, ease: ease.out }, 0)
      .from($.one('spark'), { scale: 0, rotation: -90, svgOrigin: '370 150', duration: 0.5, ease: pop }, 0.4);
  },
  // Four piles fill, and the taller one changes sides between the decks
  'training-and-deck': (tl, $) => {
    tl.from([$.one('psychic'), $.one('colorless')], { scale: 0, transformOrigin: '50% 50%', duration: 0.4, ease: pop, stagger: 0.1 });
    ['c1fixed', 'c1diverse', 'c2fixed', 'c2diverse'].forEach((p, i) => {
      tl.from($.all(p), { y: -40, autoAlpha: 0, duration: 0.35, ease: ease.out, stagger: 0.06 }, 0.2 + i * 0.18);
    });
  },
  // The heuristic's gear turns, the arrow taps the first option, the coin flips
  opponent: (tl, $) => {
    tl.from($.one('heuristic-gear'), { rotation: -180, svgOrigin: '255 128', duration: 1, ease: ease.out }, 0)
      .fromTo($.one('first-arrow'), { x: -16 }, { x: 0, duration: 0.3, ease: 'back.out(3)', repeat: 2 }, 0.1)
      .to($.one('coin'), { scaleX: 0, svgOrigin: '495 128', duration: 0.12, ease: 'sine.inOut', yoyo: true, repeat: 5 }, 0.15)
      .to($.one('coin'), { y: -24, duration: 0.36, ease: 'power2.out', yoyo: true, repeat: 1 }, 0.15);
  },
  // The two chairs trade places around the table
  seat: (tl, $) => {
    const left = $.one('chair-left'), right = $.one('chair-right');
    tl.set(left, { x: 224 }).set(right, { x: -224 })
      .to(left, { keyframes: { x: [112, 0], y: [-62, 0] }, duration: 0.8, ease: 'power2.inOut' }, 0)
      .to(right, { keyframes: { x: [-112, 0], y: [62, 0] }, duration: 0.8, ease: 'power2.inOut' }, 0)
      .from([...($.one('swap')?.children ?? [])], { autoAlpha: 0, duration: 0.3, stagger: 0.08 }, 0.5);
  },
  // Five Prize cards are taken; the last one stays put
  ending: (tl, $) => {
    const taken = $.all('taken');
    tl.set(taken, { opacity: 1, x: 0, y: 0, rotation: 0 })
      .from($.one('last-glow'), { opacity: 0, duration: 0.01 }, 0)
      .to(taken, { opacity: 0, x: -90, y: -24, rotation: -14, duration: 0.4, ease: 'power2.in', stagger: 0.14 }, 0.1)
      .from($.one('last-glow'), { opacity: 0, duration: 0.4 }, '>-0.05')
      .to($.one('last'), { rotation: 4, svgOrigin: '453 243', duration: 0.08, yoyo: true, repeat: 3 }, '<');
  },
  // Six checkpoints rise along the track, three for each pool
  checkpoint: (tl, $) => {
    tl.from($.all('flag'), {
      scaleY: 0, transformOrigin: '50% 100%', duration: 0.45, ease: pop,
      stagger: (i: number) => i * 0.12 + (i > 2 ? 0.2 : 0),
    });
  },
  // The grid fills in a diagonal wave
  matchup: (tl, $) => {
    tl.from($.all('row'), { scale: 0, transformOrigin: '50% 50%', duration: 0.3, ease: pop, stagger: 0.05 })
      .from($.all('cell'), {
        scale: 0, transformOrigin: '50% 50%', duration: 0.35, ease: pop,
        stagger: (i: number) => (Math.floor(i / 6) + (i % 6)) * 0.05,
      }, 0.1);
  },
};

function timeline(root: HTMLElement): gsap.core.Timeline | null {
  const key = root.dataset.art as SortKey;
  const build = ART[key];
  if (!build) return null;
  const tl = gsap.timeline({ paused: true });
  build(tl, {
    one: (id) => root.querySelector(`#${key}-${id}`),
    // Numbered parts (fixed1, cell2-3), not their inner pieces (fixed1-body)
    all: (prefix) => {
      const part = new RegExp(`^${key}-${prefix}\\d+(-\\d+)?$`);
      return [...root.querySelectorAll(`[id^="${key}-${prefix}"]`)].filter((e) => part.test(e.id));
    },
  });
  return tl.progress(1);
}

onPage(() => {
  if (prefersReducedMotion()) return;
  const offs: (() => void)[] = [];
  for (const root of document.querySelectorAll<HTMLElement>('.hand .sort-art')) {
    const tl = timeline(root);
    const slot = root.closest<HTMLElement>('.hand__slot');
    if (!tl || !slot) continue;
    const play = () => { if (!tl.isActive()) tl.restart(); };
    slot.addEventListener('pointerenter', play);
    slot.addEventListener('focusin', play);
    offs.push(() => { slot.removeEventListener('pointerenter', play); slot.removeEventListener('focusin', play); tl.kill(); });
  }
  const played = document.querySelector<HTMLElement>('.played .sort-art');
  const tl = played && timeline(played);
  if (tl) {
    // After the card lands (the deal on first load, the slide on a re-sort)
    const call = gsap.delayedCall(0.9, () => tl.restart());
    offs.push(() => { call.kill(); tl.kill(); });
  }
  return () => offs.forEach((f) => f());
});
