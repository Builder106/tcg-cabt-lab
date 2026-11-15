"""A rule-based teacher whose choices depend on the board, not only on the option offered."""

from collections import Counter
from collections.abc import Mapping, Sequence
from enum import IntEnum
from typing import Any

from tcg_cabt_lab.agent import sanitize_observation
from tcg_cabt_lab.catalog import get_attack_by_id, get_catalog_by_id
from tcg_cabt_lab.deck import REFERENCE_DECK, validate_deck


class OptionType(IntEnum):
    """CABT `OptionType` values (https://matsuoinstitute.github.io/cabt/api.html#enums)."""

    NUMBER = 0
    YES = 1
    NO = 2
    CARD = 3
    TOOL_CARD = 4
    ENERGY_CARD = 5
    ENERGY = 6
    PLAY = 7
    ATTACH = 8
    EVOLVE = 9
    ABILITY = 10
    DISCARD = 11
    RETREAT = 12
    ATTACK = 13
    END = 14
    SKILL = 15
    SPECIAL_CONDITION = 16


class Area(IntEnum):
    """CABT `AreaType` values."""

    DECK = 1
    HAND = 2
    DISCARD = 3
    ACTIVE = 4
    BENCH = 5
    PRIZE = 6
    LOOKING = 12


class CardType(IntEnum):
    """CABT `CardType` values."""

    POKEMON = 0
    ITEM = 1
    TOOL = 2
    SUPPORTER = 3
    STADIUM = 4
    BASIC_ENERGY = 5
    SPECIAL_ENERGY = 6


COLORLESS = 0
RAINBOW = 10

# SelectContext values where choosing more of one's own cards costs resources
COSTLY_CONTEXTS = frozenset({8, 9, 10, 11, 20, 23, 26, 27, 29, 30, 32})
CONTEXT_MAIN = 0
SETUP_CONTEXTS = frozenset({1, 2})  # SETUP_ACTIVE_POKEMON, SETUP_BENCH_POKEMON
CONTEXT_ATTACH_TO = 22

# Worth of keeping or fetching a Trainer card, by CardType
KEEP_VALUES: dict[int, float] = {
    CardType.SUPPORTER: 40.0,
    CardType.ITEM: 30.0,
    CardType.TOOL: 20.0,
}

Card = Mapping[str, Any]


def missing_energy(attached: Sequence[int], cost: Sequence[int]) -> int:
    """Count the energy units still needed to pay `cost` from `attached` energy types."""
    pool = Counter(attached)
    wild = pool.pop(RAINBOW, 0)
    missing = 0
    for energy in cost:
        if energy == COLORLESS:
            continue
        if pool[energy] > 0:
            pool[energy] -= 1
        elif wild > 0:
            wild -= 1
        else:
            missing += 1
    colorless = sum(1 for energy in cost if energy == COLORLESS)
    spare = sum(pool.values()) + wild
    return missing + max(0, colorless - spare)


class BoardAgent:
    """Rule-based CABT agent that reads HP, energy, bench size and knockout chances.

    On its turn it takes a knockout when one is on offer, then evolves, keeps two Pokémon
    on the bench, attaches energy where it brings an attack closest, retreats an active
    that cannot attack or is about to be knocked out, and attacks for the most damage.
    It uses only its own observation and the public card catalog.
    """

    def __init__(self, deck: Sequence[int] | None = None) -> None:
        self.deck = validate_deck(deck) if deck is not None else list(REFERENCE_DECK)
        self.cards: Mapping[int, Card] = get_catalog_by_id()
        self.attacks: Mapping[int, Card] = get_attack_by_id()

    # Board reading

    def _card(self, card_id: object) -> Card:
        return self.cards.get(int(card_id), {}) if isinstance(card_id, int) else {}

    def _attacks_of(self, mon: Card) -> list[Card]:
        ids = self._card(mon.get("id")).get("attacks") or []
        return [self.attacks[a] for a in ids if a in self.attacks]

    def _missing(self, mon: Card, extra: Sequence[int] = ()) -> int:
        """Fewest energy units this Pokémon still needs for any of its attacks."""
        energies = [*list(mon.get("energies") or []), *extra]
        costs = [list(a.get("energies") or []) for a in self._attacks_of(mon)]
        return min((missing_energy(energies, c) for c in costs), default=99)

    def _damage(self, attack: Card, attacker: Card, defender: Card | None) -> int:
        damage = int(attack.get("damage") or 0)
        if defender is None or damage <= 0:
            return damage
        attacker_type = self._card(attacker.get("id")).get("energyType")
        defender_card = self._card(defender.get("id"))
        if attacker_type is not None and defender_card.get("weakness") == attacker_type:
            damage *= 2
        if attacker_type is not None and defender_card.get("resistance") == attacker_type:
            damage = max(0, damage - 30)
        return damage

    def _threat(self, attacker: Card | None, defender: Card | None) -> int:
        """Most damage `attacker` can deal to `defender` next turn (one energy attach allowed)."""
        if attacker is None:
            return 0
        energies = list(attacker.get("energies") or [])
        return max(
            (
                self._damage(a, attacker, defender)
                for a in self._attacks_of(attacker)
                if missing_energy(energies, list(a.get("energies") or [])) <= 1
            ),
            default=0,
        )

    def _can_attack(self, mon: Card) -> bool:
        return self._missing(mon) == 0

    @staticmethod
    def _active(player: Card) -> Card | None:
        active = player.get("active")
        if isinstance(active, list) and active and isinstance(active[0], Mapping):
            return active[0]
        return None

    @staticmethod
    def _bench(player: Card) -> list[Card]:
        bench = player.get("bench")
        return [m for m in bench if isinstance(m, Mapping)] if isinstance(bench, list) else []

    def _in_play(self, player: Card, area: object, index: object) -> Card | None:
        if area == Area.ACTIVE:
            return self._active(player)
        bench = self._bench(player)
        if area == Area.BENCH and isinstance(index, int) and 0 <= index < len(bench):
            return bench[index]
        return None

    def _card_at(self, obs: Card, players: list[Card], option: Card, me: int) -> Card | None:
        owner = option.get("playerIndex", me)
        player = players[owner] if isinstance(owner, int) and 0 <= owner < 2 else players[me]
        area, index = option.get("area"), option.get("index")
        if area in (Area.ACTIVE, Area.BENCH):
            return self._in_play(player, area, index)
        zones: dict[int, Any] = {
            Area.HAND: player.get("hand"),
            Area.DISCARD: player.get("discard"),
            Area.PRIZE: player.get("prize"),
            Area.DECK: (obs.get("select") or {}).get("deck"),
            Area.LOOKING: (obs.get("current") or {}).get("looking"),
        }
        zone = zones.get(area) if isinstance(area, int) else None
        if isinstance(zone, list) and isinstance(index, int) and 0 <= index < len(zone):
            card = zone[index]
            return card if isinstance(card, Mapping) else None
        return None

    # Scoring

    def _card_value(self, card: Card | None, me_state: Card) -> float:
        """How much this card is worth keeping or fetching, given the board."""
        if card is None:
            return 0.0
        data = self._card(card.get("id"))
        kind = data.get("cardType")
        in_play = [m for m in [self._active(me_state), *self._bench(me_state)] if m]
        if kind == CardType.POKEMON:
            if data.get("basic"):
                return 60.0 if len(in_play) < 3 else 35.0
            names = {self._card(m.get("id")).get("name") for m in in_play}
            return 70.0 if data.get("evolvesFrom") in names else 30.0
        if kind in (CardType.BASIC_ENERGY, CardType.SPECIAL_ENERGY):
            return 45.0 if any(self._missing(m) > 0 for m in in_play) else 15.0
        return KEEP_VALUES.get(kind, 10.0) if isinstance(kind, int) else 10.0

    def _pokemon_value(self, mon: Card | None, opp_active: Card | None) -> float:
        """How good this Pokémon is as the next Active."""
        if mon is None:
            return 0.0
        hp = float(mon.get("hp") or self._card(mon.get("id")).get("hp") or 0)
        best = max((self._damage(a, mon, opp_active) for a in self._attacks_of(mon)), default=0)
        ready = 100.0 if self._can_attack(mon) else -10.0 * self._missing(mon)
        return ready + best / 5.0 + hp / 10.0

    def _score_main(self, option: Card, me_state: Card, opp_state: Card) -> float:
        kind = option.get("type")
        active = self._active(me_state)
        opp_active = self._active(opp_state)
        hand = me_state.get("hand") or []

        if kind == OptionType.ATTACK:
            attack = self.attacks.get(int(option.get("attackId", -1)), {})
            damage = self._damage(attack, active or {}, opp_active)
            opp_hp = int(opp_active.get("hp") or 0) if opp_active else 0
            if opp_active is not None and damage >= opp_hp > 0:
                return 10_000.0 + damage
            return 1_000.0 + damage
        if kind == OptionType.EVOLVE:
            return 6_000.0 + (200.0 if option.get("inPlayArea") == Area.ACTIVE else 0.0)
        if kind == OptionType.PLAY:
            index = option.get("index")
            card = hand[index] if isinstance(index, int) and 0 <= index < len(hand) else None
            data = self._card(card.get("id")) if isinstance(card, Mapping) else {}
            kind_of_card = data.get("cardType")
            if kind_of_card == CardType.POKEMON:
                return 5_500.0 if len(self._bench(me_state)) < 2 else 2_500.0
            if kind_of_card == CardType.SUPPORTER:
                return 4_000.0 if len(hand) <= 4 else 2_200.0
            if kind_of_card == CardType.ITEM:
                return 3_000.0
            if kind_of_card == CardType.TOOL:
                return 2_000.0
            return 1_500.0
        if kind == OptionType.ATTACH:
            index = option.get("index")
            card = hand[index] if isinstance(index, int) and 0 <= index < len(hand) else None
            data = self._card(card.get("id")) if isinstance(card, Mapping) else {}
            target = self._in_play(me_state, option.get("inPlayArea"), option.get("inPlayIndex"))
            on_active = 300.0 if option.get("inPlayArea") == Area.ACTIVE else 0.0
            if target is None:
                return 1_000.0
            if data.get("cardType") not in (CardType.BASIC_ENERGY, CardType.SPECIAL_ENERGY):
                return 1_800.0 + on_active
            before = self._missing(target)
            after = self._missing(target, extra=[int(data.get("energyType") or 0)])
            if after < before:
                return 5_000.0 - 100.0 * after + on_active
            return 1_200.0 + on_active
        if kind == OptionType.RETREAT:
            return 4_800.0 if self._should_retreat(me_state, opp_state) else 0.0
        if kind == OptionType.ABILITY:
            return 2_500.0
        if kind == OptionType.END:
            return 500.0
        return 400.0

    def _should_retreat(self, me_state: Card, opp_state: Card) -> bool:
        active = self._active(me_state)
        bench = self._bench(me_state)
        if active is None or not bench:
            return False
        opp_active = self._active(opp_state)
        if not self._can_attack(active) and any(self._can_attack(m) for m in bench):
            return True
        threat = self._threat(opp_active, active)
        hp = int(active.get("hp") or 0)
        knocks_out = any(
            self._damage(a, active, opp_active) >= int((opp_active or {}).get("hp") or 0) > 0
            for a in self._attacks_of(active)
            if self._can_attack(active)
        )
        if threat >= hp and not knocks_out:
            return any(int(m.get("hp") or 0) > self._threat(opp_active, m) for m in bench)
        return False

    def _score_option(
        self, obs: Card, option: Card, context: int | None, me: int, players: list[Card]
    ) -> float:
        me_state, opp_state = players[me], players[1 - me]
        kind = option.get("type")
        if context == CONTEXT_MAIN:
            return self._score_main(option, me_state, opp_state)
        if kind == OptionType.YES:
            return 1.0
        if kind == OptionType.NO:
            return 0.0
        if kind == OptionType.NUMBER:
            return float(option.get("number") or 0)
        if kind == OptionType.CARD:
            card = self._card_at(obs, players, option, me)
            if option.get("area") in (Area.ACTIVE, Area.BENCH):
                if context == CONTEXT_ATTACH_TO and card is not None:
                    on_active = 5.0 if option.get("area") == Area.ACTIVE else 0.0
                    return 50.0 - 10.0 * self._missing(card) + on_active
                return self._pokemon_value(card, self._active(opp_state))
            if context in SETUP_CONTEXTS and card is not None:
                return float(self._card(card.get("id")).get("hp") or 0)
            return self._card_value(card, me_state)
        return 0.0

    def __call__(
        self,
        observation: Mapping[str, Any],
        configuration: Mapping[str, Any] | None = None,
    ) -> list[int]:
        obs = sanitize_observation(observation)
        sel = obs.get("select")
        if sel is None:
            return list(self.deck)
        options = sel.get("option") or []
        max_count = int(sel.get("maxCount") or 0)
        min_count = int(sel.get("minCount") or 0)
        if not options or max_count <= 0:
            return []

        current = obs.get("current") or {}
        players = current.get("players")
        me = int(current.get("yourIndex") or 0)
        if not isinstance(players, list) or len(players) < 2:
            return list(range(min(max_count, len(options))))
        context = sel.get("context")

        scores = [
            self._score_option(obs, o, context, me, players) if isinstance(o, Mapping) else 0.0
            for o in options
        ]
        ranked = sorted(range(len(options)), key=lambda i: (-scores[i], i))

        own = all(not isinstance(o, Mapping) or o.get("playerIndex", me) == me for o in options)
        if context in COSTLY_CONTEXTS and own:
            # Give up as little as possible: the lowest-valued cards, and only as many as required
            return sorted(ranked[::-1][:min_count])
        count = 1 if context == CONTEXT_MAIN else max_count
        return ranked[: min(count, len(options))]
