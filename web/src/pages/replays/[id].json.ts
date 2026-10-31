// One replay per game, served as static JSON for the match viewer.
import type { APIRoute } from 'astro';
import { getGames, getReplay } from '@/lib/study';

export function getStaticPaths() {
  return getGames().map((g) => ({ params: { id: g.game_id } }));
}

export const GET: APIRoute = ({ params }) =>
  new Response(JSON.stringify(getReplay(String(params.id))), { headers: { 'Content-Type': 'application/json' } });
