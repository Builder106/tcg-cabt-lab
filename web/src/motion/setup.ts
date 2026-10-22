// Global motion: runs once on the client, before the first page initializes.
import { gsap } from 'gsap';
import { ease, isTouch, prefersReducedMotion, setTransition } from '../engine';
import './table';
import './replay';
import './art';

/** The lamp over the table: its pool of light follows a lagged pointer and drifts at rest. */
function startLamp() {
  const pool = document.querySelector<HTMLElement>('.lamp__pool');
  if (!pool || prefersReducedMotion()) return;
  const target = { x: 0, y: 0 };
  const cur = { x: 0, y: 0 };
  if (!isTouch()) {
    addEventListener('pointermove', (e) => {
      target.x = (e.clientX / innerWidth - 0.5) * 0.35 * innerWidth;
      target.y = (e.clientY / innerHeight - 0.5) * 0.25 * innerHeight;
    }, { passive: true });
  }
  const setX = gsap.quickSetter(pool, 'x', 'px');
  const setY = gsap.quickSetter(pool, 'y', 'px');
  gsap.ticker.add((time) => {
    if (document.hidden) return;
    cur.x += (target.x - cur.x) * 0.035;
    cur.y += (target.y - cur.y) * 0.035;
    const driftX = Math.sin(time * 0.21) * innerWidth * 0.03;
    const driftY = Math.cos(time * 0.17) * innerHeight * 0.025;
    setX(cur.x + driftX);
    setY(cur.y + driftY);
  });
}

export function setupMotion() {
  // Page transition: a card back is dealt over the table, then slides off the far side
  setTransition({
    leave: (c) => gsap.timeline()
      .set(c, { autoAlpha: 1 })
      .fromTo(c.querySelector('.curtain__panel'),
        { xPercent: 105, yPercent: 6, rotation: 9 },
        { xPercent: 0, yPercent: 0, rotation: 0, duration: 0.75, ease: ease.inOut }),
    enter: (c) => gsap.timeline()
      .to(c.querySelector('.curtain__panel'), { xPercent: -105, yPercent: -5, rotation: -7, duration: 0.8, ease: ease.inOut })
      .set(c, { autoAlpha: 0 }),
  });
  startLamp();
}
