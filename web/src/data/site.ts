// Site-wide copy and the study facts that are not computed from the games table.

export const site = {
  name: 'CABT Lab',
  fullName: 'TCG CABT Lab',
  url: 'https://tcg-cabt-lab.vercel.app',
  repo: 'https://github.com/Builder106/tcg-cabt-lab',
  description:
    'A tiny AI learned the Pokémon card game by copying a bot, was trained two ways, then played 360 games with decks it had never seen. Sort the games yourself and replay any of them move by move.',
  question:
    'Does a game-playing AI do better with new decks when it learns from games against more kinds of opponents?',
};

export const facts = {
  recordDate: '14 November 2026',
  // The last run before the teacher-deck fix (see JOURNAL.md, 14 November 2026).
  earlier: {
    commit: 'e918838',
    date: '21 October 2026',
    fixed: 0.583,
    diverse: 0.578,
    delta: -0.6,
    ci: [-10.7, 9.6] as [number, number],
  },
  plannedSteps: 100_000,
  usedSteps: 400,
  copyAccuracy: 'Still, five AIs copied the bot on all 400 test decisions.',
  parameters: 2881,
  mewtwoAttacks: 378,
};
