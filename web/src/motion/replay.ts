// The match viewer: steps through one stored game, decision by decision, from the policy's side
// (agent view) or as a spectator. The board and panel come from the same renderer the server
// used for the first paint.
import { gsap } from 'gsap';
import { ease, onPage, prefersReducedMotion } from '../engine';
import { boardHTML, decisionHTML, promptText, turnOwners, whereHTML } from '../lib/board';
import { animateStep, snapshot } from './board-fx';
import type { Replay, View } from '../lib/types';
import { nav } from './state';

const PLAY_STEP = 0.9; // seconds per decision while playing, at 1×

onPage(() => {
  const root = document.querySelector<HTMLElement>('[data-viewer]');
  const back = document.querySelector<HTMLAnchorElement>('[data-back]');
  if (back) back.href = nav.lastTable;
  if (!root) return;

  const id = root.dataset.id!;
  const seat = Number(root.dataset.seat);
  const total = Number(root.dataset.frames);
  const board = root.querySelector<HTMLElement>('[data-board]')!;
  // The decision panel and the announcer sit beside the viewer, in the same game article
  const game = root.closest<HTMLElement>('[data-game]') ?? document.body;
  const panel = game.querySelector<HTMLElement>('[data-decision]')!;
  const track = root.querySelector<HTMLInputElement>('[data-track]')!;
  const where = root.querySelector<HTMLElement>('[data-where]')!;
  const announce = game.querySelector<HTMLElement>('[data-announce]')!;
  const note = root.querySelector<HTMLElement>('[data-persp-note]')!;
  const playBtn = root.querySelector<HTMLButtonElement>('[data-play]')!;
  const viewBtns = [...root.querySelectorAll<HTMLButtonElement>('.persp__btn')];
  const speedBtns = [...root.querySelectorAll<HTMLButtonElement>('[data-speed]')];
  const rail = root.querySelector<HTMLElement>('[data-rail]')!;
  const segments = [...rail.querySelectorAll<HTMLElement>('[data-at]')];
  const stepBtns = [...root.querySelectorAll<HTMLButtonElement>('[data-step]')];

  const params = new URLSearchParams(location.search);
  const clamp = (i: number) => Math.max(0, Math.min(total - 1, i));
  const fromUrl = params.get('d');
  let k = fromUrl !== null && /^\d+$/.test(fromUrl) ? clamp(Number(fromUrl)) : Number(root.dataset.start);
  let view: View = params.get('view') === 'spectator' ? 'spectator' : 'agent';
  let replay: Replay | null = null;
  let playing: gsap.core.Tween | null = null;
  let speed = 1;
  let owners = new Map<number, number>();
  let dirty = fromUrl !== null || view !== 'agent';

  const notes: Record<View, string> = {
    agent: 'What the AI could see: its own hand, the board and card counts. Hidden cards stay face down.',
    spectator: 'The spectator view also shows the opponent’s hand, its choices and every Prize card. Those are marked Spectator only: the AI never saw them.',
  };

  // On desktop the board shrinks to fit the window, so the whole board and the controls are in view
  const controls = root.querySelector<HTMLElement>('[data-controls]')!;
  const desktop = matchMedia('(min-width: 48rem)');
  function fit() {
    if (!desktop.matches) { board.style.zoom = ''; delete board.dataset.zoom; return; }
    board.style.zoom = '1';
    const bar = document.querySelector('.bar')?.getBoundingClientRect().height ?? 56;
    const room = innerHeight - bar - controls.getBoundingClientRect().height - 56;
    const z = Math.max(0.7, Math.min(1, room / board.getBoundingClientRect().height));
    board.style.zoom = String(z);
    board.dataset.zoom = String(z);
  }

  function render(animate = true, step = false) {
    if (!replay) return;
    const ctx = { replay, view, seat };
    const f = replay.frames[k]!;
    // One step forward plays out on the board: cards move, attacks land
    const before = step && !prefersReducedMotion() ? snapshot(board) : null;
    board.innerHTML = boardHTML(ctx, f);
    fit();
    if (before) {
      const attack = f.events.find((e) => e.type === 'Attack' && e.player !== undefined);
      animateStep(board, before, attack ? (attack.player === seat ? 'me' : 'them') : null, playing ? speed : 1);
    }
    board.dataset.view = view;
    panel.innerHTML = decisionHTML(ctx, k);
    track.value = String(k);
    const turn = f.turn === 0 ? 'setup' : `turn ${f.turn}`;
    track.setAttribute('aria-valuetext', `Decision ${k + 1} of ${total}, ${turn}`);
    track.parentElement!.style.setProperty('--p', `${((k / Math.max(1, total - 1)) * 100).toFixed(2)}%`);
    segments.forEach((s, i) => s.classList.toggle('is-now', k >= Number(s.dataset.at) && k < Number(segments[i + 1]?.dataset.at ?? total)));
    where.innerHTML = whereHTML(replay, k, seat, owners);
    stepBtns.forEach((b) => { b.disabled = b.dataset.step!.endsWith('prev') ? k === 0 : k === total - 1; });
    viewBtns.forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.view === view)));
    note.textContent = notes[view];
    const url = new URL(location.href);
    url.searchParams.set('d', String(k));
    if (view === 'spectator') url.searchParams.set('view', 'spectator'); else url.searchParams.delete('view');
    history.replaceState(history.state, '', url);
    if (animate && !prefersReducedMotion()) {
      // The decision settles onto the table
      gsap.fromTo(panel, { y: 6, autoAlpha: 0.55 }, { y: 0, autoAlpha: 1, duration: 0.35, ease: ease.soft, overwrite: true });
    }
  }

  function say() {
    const f = replay?.frames[k];
    if (!f) return;
    const who = f.actor === seat ? 'The AI' : 'The opponent';
    announce.textContent = f.options.length
      ? `Decision ${k + 1} of ${total}, ${f.turn === 0 ? 'setup' : `turn ${f.turn}`}. ${who} ${promptText(f.prompt)}.`
      : `Decision ${k + 1} of ${total}. Game over.`;
  }

  function go(i: number) {
    const j = clamp(i);
    if (j === k || !replay) return;
    const step = j === k + 1;
    k = j;
    render(true, step);
    say();
  }

  function jumpTurn(dir: 1 | -1) {
    if (!replay) return;
    const turn = replay.frames[k]!.turn;
    if (dir > 0) {
      const j = replay.frames.findIndex((f, i) => i > k && f.turn !== turn);
      go(j < 0 ? total - 1 : j);
    } else {
      // Start of this turn, or the start of the previous one when already there
      let j = k;
      while (j > 0 && replay.frames[j - 1]!.turn === turn) j--;
      if (j === k && j > 0) {
        const prev = replay.frames[j - 1]!.turn;
        while (j > 0 && replay.frames[j - 1]!.turn === prev) j--;
      }
      go(j);
    }
  }

  function stop() {
    playing?.kill();
    playing = null;
    playBtn.setAttribute('aria-label', 'Play');
    playBtn.querySelector('use')?.setAttribute('href', '#i-play');
  }
  function play() {
    if (k >= total - 1) go(0);
    playBtn.setAttribute('aria-label', 'Pause');
    playBtn.querySelector('use')?.setAttribute('href', '#i-pause');
    const tick = () => {
      if (k >= total - 1) return stop();
      go(k + 1);
      playing = gsap.delayedCall(PLAY_STEP / speed, tick);
    };
    playing = gsap.delayedCall(PLAY_STEP / speed, tick);
  }

  const onStep = (e: Event) => {
    const s = (e.currentTarget as HTMLElement).dataset.step;
    stop();
    if (s === 'prev') go(k - 1);
    else if (s === 'next') go(k + 1);
    else if (s === 'turn-prev') jumpTurn(-1);
    else if (s === 'turn-next') jumpTurn(1);
  };
  const onPlay = () => (playing ? stop() : play());
  const onTrack = () => { stop(); go(Number(track.value)); };
  // The turn rail is a pointer shortcut; the slider and the turn buttons cover the same jumps
  const onRail = (e: MouseEvent) => {
    const at = (e.target as HTMLElement).dataset.at;
    if (at === undefined) return;
    stop();
    go(Number(at));
  };
  const onSpeed = (e: Event) => {
    speed = Number((e.currentTarget as HTMLElement).dataset.speed);
    speedBtns.forEach((b) => b.setAttribute('aria-pressed', String(Number(b.dataset.speed) === speed)));
  };
  const onView = (e: Event) => {
    view = (e.currentTarget as HTMLElement).dataset.view === 'spectator' ? 'spectator' : 'agent';
    render(false);
  };
  const onKey = (e: KeyboardEvent) => {
    const t = e.target instanceof HTMLElement ? e.target : document.body;
    if (t === track || t.closest('input, textarea, select, [contenteditable]') || e.metaKey || e.ctrlKey || e.altKey) return;
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault();
      stop();
      const dir = e.key === 'ArrowRight' ? 1 : -1;
      if (e.shiftKey) jumpTurn(dir); else go(k + dir);
    } else if (e.key === 'Home' && !t.closest('.pile__cards')) { e.preventDefault(); stop(); go(0); }
    else if (e.key === 'End' && !t.closest('.pile__cards')) { e.preventDefault(); stop(); go(total - 1); }
    else if (e.key === 'p' || e.key === 'P') { e.preventDefault(); onPlay(); }
  };
  // Links in the decision log step the viewer instead of reloading the page
  const onLog = (e: MouseEvent) => {
    const a = (e.target as Element).closest<HTMLAnchorElement>('a[href^="?d="]');
    if (!a) return;
    e.preventDefault();
    stop();
    go(Number(new URL(a.href).searchParams.get('d')));
    root.scrollIntoView({ block: 'start', behavior: prefersReducedMotion() ? 'auto' : 'smooth' });
  };

  fit();
  addEventListener('resize', fit);
  stepBtns.forEach((b) => b.addEventListener('click', onStep));
  playBtn.addEventListener('click', onPlay);
  track.addEventListener('input', onTrack);
  rail.addEventListener('click', onRail);
  speedBtns.forEach((b) => b.addEventListener('click', onSpeed));
  viewBtns.forEach((b) => b.addEventListener('click', onView));
  document.addEventListener('keydown', onKey);
  document.addEventListener('click', onLog);

  const controller = new AbortController();
  fetch(`/replays/${id}.json`, { signal: controller.signal })
    .then((r) => r.json() as Promise<Replay>)
    .then((data) => {
      replay = data;
      owners = turnOwners(data);
      root.dataset.ready = '';
      if (dirty) render(false);
      dirty = false;
    })
    .catch((err: unknown) => {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      console.error('replay failed to load', err);
    });

  return () => {
    controller.abort();
    stop();
    removeEventListener('resize', fit);
    stepBtns.forEach((b) => b.removeEventListener('click', onStep));
    playBtn.removeEventListener('click', onPlay);
    track.removeEventListener('input', onTrack);
    rail.removeEventListener('click', onRail);
    speedBtns.forEach((b) => b.removeEventListener('click', onSpeed));
    viewBtns.forEach((b) => b.removeEventListener('click', onView));
    document.removeEventListener('keydown', onKey);
    document.removeEventListener('click', onLog);
  };
});
