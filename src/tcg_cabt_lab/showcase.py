"""Compact match replays and per-game records for the public showcase."""

import re
from collections.abc import Mapping, Sequence
from typing import Any

REPLAY_SCHEMA_VERSION = 1

# Engine zone codes used by selection options and card-movement logs
AREA_NAMES = {
    1: "deck",
    2: "hand",
    3: "discard",
    4: "active",
    5: "bench",
    6: "prize",
    8: "attached",
}

# Engine Result reasons, inferred from the final board of each game
END_REASONS = {1: "prizes", 2: "deck-out", 3: "no-pokemon"}

CONTEXT_PROMPTS = {
    "Main": "Choose an action",
    "IsFirst": "Go first?",
    "SetupActivePokemon": "Choose the Active Pokémon",
    "SetupBenchPokemon": "Choose Pokémon for the Bench",
    "Switch": "Choose a Pokémon to switch in",
    "ToActive": "Choose a new Active Pokémon",
    "DiscardEnergy": "Choose Energy to discard",
    "Discard": "Choose cards to discard",
    "ToHand": "Choose cards to put into the hand",
    "AttachTo": "Choose Energy to attach",
    "DrawCount": "Choose how many cards to draw",
}

STATUS_FLAGS = ("poisoned", "burned", "asleep", "paralyzed", "confused")

# Engine log keys renamed for the replay; serial numbers are dropped
EVENT_KEYS = {
    "type": "type",
    "playerIndex": "player",
    "cardId": "card",
    "cardIdTarget": "target",
    "cardIdActive": "active",
    "cardIdBench": "bench",
    "attackId": "attack",
    "value": "value",
    "head": "heads",
    "isRecover": "recovered",
    "hasBasicPokemon": "has_basic",
    "result": "result",
    "reason": "reason",
}


def _prompt(context: str | None) -> str:
    if context is None:
        return ""
    if context in CONTEXT_PROMPTS:
        return CONTEXT_PROMPTS[context]
    return re.sub(r"(?<!^)(?=[A-Z])", " ", context).capitalize()


def _zone(player: Mapping[str, Any], area: int | None) -> list[Any]:
    name = AREA_NAMES.get(area or 0)
    cards = player.get(name) if name else None
    return cards if isinstance(cards, list) else []


def _at(cards: Sequence[Any], index: Any) -> Mapping[str, Any] | None:
    if not isinstance(index, int) or not 0 <= index < len(cards):
        return None
    card = cards[index]
    return card if isinstance(card, Mapping) else None


def _name(card: Mapping[str, Any] | None, catalog: Mapping[int, Mapping[str, Any]]) -> str:
    if card is None:
        return "a card"
    return str(catalog.get(int(card.get("id", -1)), {}).get("name") or card.get("name") or "a card")


def option_label(
    option: Mapping[str, Any],
    frame: Mapping[str, Any],
    catalog: Mapping[int, Mapping[str, Any]],
    attacks: Mapping[int, Mapping[str, Any]],
) -> str:
    """Describe one selection option in plain words using the spectator frame."""
    current = frame.get("current") or {}
    players = current.get("players") or [{}, {}]
    actor = int(current.get("yourIndex", 0))
    me = players[actor]
    kind = option.get("type")
    context = (frame.get("select") or {}).get("context")

    if kind == "End":
        return "End turn"
    if kind == "Retreat":
        return f"Retreat {_name(_at(_zone(me, 4), 0), catalog)}"
    if kind == "Attack":
        attack = attacks.get(int(option.get("attackId", -1)), {})
        damage = int(attack.get("damage") or 0)
        suffix = f" for {damage}" if damage else ""
        return f"Attack: {attack.get('name', 'unknown attack')}{suffix}"
    if kind == "Play":
        return f"Play {_name(_at(_zone(me, 2), option.get('index')), catalog)}"
    if kind == "Attach":
        energy = _name(_at(_zone(me, 2), option.get("index")), catalog)
        target = _at(_zone(me, option.get("inPlayArea")), option.get("inPlayIndex"))
        return f"Attach {energy} to {_name(target, catalog)}"
    if kind == "Card":
        owner = int(option.get("playerIndex", actor))
        area = option.get("area")
        card = _at(_zone(players[owner], area), option.get("index"))
        whose = "" if owner == actor else "opponent's "
        return f"{_name(card, catalog)} ({whose}{AREA_NAMES.get(area or 0, 'zone')})"
    if kind == "Energy":
        holder = _at(
            _zone(players[int(option.get("playerIndex", actor))], option.get("area")),
            option.get("index"),
        )
        energy_cards = holder.get("energyCards") if holder else None
        energy_card = _at(
            energy_cards if isinstance(energy_cards, list) else [], option.get("energyIndex")
        )
        return f"{_name(energy_card, catalog)} on {_name(holder, catalog)}"
    if kind in ("Yes", "No"):
        if context == "IsFirst":
            return "Go first" if kind == "Yes" else "Go second"
        return str(kind)
    if kind == "Number":
        return str(option.get("number"))
    if kind == "EnergyCard":
        return "Energy card"
    return str(kind)


def _pokemon(mon: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": mon.get("id"),
        "hp": mon.get("hp"),
        "max_hp": mon.get("maxHp"),
        "energy": [c.get("id") for c in mon.get("energyCards") or []],
        "tools": [c.get("id") for c in mon.get("tools") or [] if isinstance(c, Mapping)],
        "evolved_from": [
            c.get("id") for c in mon.get("preEvolution") or [] if isinstance(c, Mapping)
        ],
    }


def _ids(cards: Any) -> list[Any]:
    return [c.get("id") for c in cards or [] if isinstance(c, Mapping)]


def _player(state: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "active": [_pokemon(m) for m in state.get("active") or []],
        "bench": [_pokemon(m) for m in state.get("bench") or []],
        "hand": _ids(state.get("hand")),
        "hand_count": state.get("handCount", 0),
        "deck_count": state.get("deckCount", 0),
        "discard": _ids(state.get("discard")),
        "prizes": _ids(state.get("prize")),
        "status": [flag for flag in STATUS_FLAGS if state.get(flag)],
    }


def _event(log: Mapping[str, Any]) -> dict[str, Any]:
    event = {EVENT_KEYS[k]: v for k, v in log.items() if k in EVENT_KEYS}
    for key, out in (("fromArea", "from"), ("toArea", "to")):
        if key in log:
            event[out] = AREA_NAMES.get(log[key], f"area {log[key]}")
    return event


def end_reason(frames: Sequence[Mapping[str, Any]], statuses: Sequence[str]) -> tuple[str, Any]:
    """Classify how a game ended from its Result log and final player statuses."""
    if any(s in ("INVALID", "ERROR", "TIMEOUT") for s in statuses):
        return "invalid", None
    for frame in reversed(frames):
        for log in frame.get("logs") or []:
            if log.get("type") == "Result":
                code = log.get("reason")
                return END_REASONS.get(code, "unknown"), code
    return "unknown", None


def compact_replay(
    log: Mapping[str, Any],
    game: Mapping[str, Any],
    catalog: Mapping[int, Mapping[str, Any]],
    attacks: Mapping[int, Mapping[str, Any]],
) -> dict[str, Any]:
    """Convert a battle log recorded with record_replay=True into a compact replay.

    Each frame pairs the engine's spectator state with the decision made from it.
    The decision list comes from the agent wrapper, because the engine's own
    frame actions trail the frames by one step.
    """
    replay = log["replay"]
    frames: list[Mapping[str, Any]] = replay["frames"]
    decisions: list[Mapping[str, Any]] = replay["decisions"]

    out_frames: list[dict[str, Any]] = []
    seen_cards: set[int] = set()
    seen_attacks: set[int] = set()

    for k, frame in enumerate(frames):
        current = frame.get("current") or {}
        select = frame.get("select") or {}
        options = select.get("option") or []
        decision = decisions[k] if k < len(decisions) else None
        if decision is not None and (
            decision["seat"] != current.get("yourIndex")
            or decision["turn"] != current.get("turn")
            or decision["option_count"] != len(options)
        ):
            raise ValueError(f"Decision {k} does not match engine frame {k}")

        players = [_player(p) for p in current.get("players") or []]
        for p in players:
            for zone in ("hand", "discard", "prizes"):
                seen_cards.update(p[zone])
            for mon in p["active"] + p["bench"]:
                seen_cards.update([mon["id"], *mon["energy"], *mon["tools"], *mon["evolved_from"]])
        events = [_event(entry) for entry in frame.get("logs") or []]
        for event in events:
            seen_cards.update(
                event[k2]
                for k2 in ("card", "target", "active", "bench")
                if isinstance(event.get(k2), int)
            )
            if isinstance(event.get("attack"), int):
                seen_attacks.add(event["attack"])
        for option in options:
            if option.get("type") == "Attack":
                seen_attacks.add(int(option.get("attackId", -1)))

        out_frames.append(
            {
                "turn": current.get("turn"),
                "actor": current.get("yourIndex"),
                "prompt": _prompt(select.get("context")) if options else "",
                "min": select.get("minCount", 0),
                "max": select.get("maxCount", 0),
                "options": [option_label(o, frame, catalog, attacks) for o in options],
                "chosen": decision["action"] if decision else [],
                "scores": decision["scores"] if decision else None,
                "events": events,
                "stadium": _ids(current.get("stadium")),
                "players": players,
            }
        )

    cards = {
        cid: {
            "name": catalog[cid].get("name"),
            "hp": catalog[cid].get("hp"),
            "card_type": catalog[cid].get("cardType"),
            "energy_type": catalog[cid].get("energyType"),
            "ex": bool(catalog[cid].get("ex")),
        }
        for cid in sorted(c for c in seen_cards if isinstance(c, int) and c in catalog)
    }
    attack_table = {
        aid: {
            "name": attacks[aid].get("name"),
            "damage": attacks[aid].get("damage"),
            "text": attacks[aid].get("text"),
        }
        for aid in sorted(seen_attacks)
        if aid in attacks
    }
    return {
        "schema_version": REPLAY_SCHEMA_VERSION,
        "game": dict(game),
        "cards": cards,
        "attacks": attack_table,
        "frames": out_frames,
    }


def summarize_game(log: Mapping[str, Any], policy_seat: int) -> dict[str, Any]:
    """Summarize one recorded game from the studied policy's point of view."""
    frames = log["replay"]["frames"]
    statuses = log["outcome"]["statuses"]
    reason, code = end_reason(frames, statuses)
    winner = log["outcome"]["winner"]
    final_players = ((frames[-1].get("current") or {}).get("players") or []) if frames else []
    prizes_left = [len(p.get("prize") or []) for p in final_players]
    # Prizes are only laid out after setup, so empty lists before then mean "none taken yet"
    prizes_dealt = len(prizes_left) == 2 and (any(prizes_left) or reason == "prizes")
    taken = [6 - n for n in prizes_left] if prizes_dealt else [0, 0]
    return {
        "policy_seat": policy_seat,
        "result": "draw" if winner == "draw" else ("win" if winner == policy_seat else "loss"),
        "end_reason": reason,
        "engine_reason_code": code,
        "statuses": list(statuses),
        "turns": (frames[-1].get("current") or {}).get("turn") if frames else None,
        "decisions": len(log["replay"]["decisions"]),
        "prizes_taken": {"policy": taken[policy_seat], "opponent": taken[1 - policy_seat]},
    }
