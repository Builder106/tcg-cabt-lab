"""Write the paper's numbers, tables and figure data from the three study reports.

Run from the repository root: python3 docs/paper/make_results.py
Uses only the standard library. Every number in the paper's results comes from here.
"""

import json
import statistics
from pathlib import Path

OUT = Path("docs/paper/generated")
STUDIES = {
    "A": "experiments/scaled/report.json",
    "B": "experiments/board/report.json",
    "C": "experiments/rl/report.json",
}
ARMS = ("fixed-opponent-pool", "diverse-opponent-pool")
AGENTS = ("board", "heuristic", "first", "random")
X_POSITION = {("A", 0): 1, ("A", 1): 2, ("B", 0): 4, ("B", 1): 5, ("C", 0): 7, ("C", 1): 8}


def pct(value: float, places: int = 2) -> str:
    return f"{100 * value:.{places}f}"


def signed(value: float, places: int = 2) -> str:
    """Percentage points with an explicit sign, using a math minus."""
    text = f"{100 * value:+.{places}f}"
    return "$-$" + text[1:] if text.startswith("-") else "$+$" + text[1:]


def interval(bounds: list[float], places: int = 2) -> str:
    return f"[{signed(bounds[0], places)}, {signed(bounds[1], places)}]"


def checkpoint_score(evaluation: dict) -> float:
    """Equally weighted mean of the held-out deck-family win rates (a draw counts half)."""
    return statistics.mean(
        f["wins"] / f["total_games"] for f in evaluation["family_breakdown"].values()
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    macros: list[str] = []
    rows: list[str] = []
    baseline_rows: list[str] = []
    csv = ["study,arm,seed,score,x"]
    means = ["study,arm,mean,x"]

    def macro(name: str, value: str) -> None:
        macros.append(f"\\newcommand{{\\{name}}}{{{value}}}")

    for key, path in STUDIES.items():
        report = json.loads(Path(path).read_text(encoding="utf-8"))
        sla = report["seed_level_analysis"]
        assert sla["n_seeds"] == [30, 30], (key, sla["n_seeds"])
        scores = {
            arm: [checkpoint_score(e) for e in report["checkpoint_evaluations"][arm]]
            for arm in ARMS
        }
        for i, arm in enumerate(ARMS):
            assert abs(statistics.mean(scores[arm]) - sla["means"][i]) < 1e-4, (key, arm)
            for j, score in enumerate(scores[arm]):
                jitter = (j / 29 - 0.5) * 0.5
                csv.append(f"{key},{arm},{j},{100 * score:.3f},{X_POSITION[(key, i)] + jitter:.3f}")
            means.append(f"{key},{arm},{100 * sla['means'][i]:.3f},{X_POSITION[(key, i)]}")
        macro(f"{key}FixedMean", pct(sla["means"][0]))
        macro(f"{key}DiverseMean", pct(sla["means"][1]))
        macro(f"{key}FixedSD", pct(sla["std"][0], 1))
        macro(f"{key}DiverseSD", pct(sla["std"][1], 1))
        macro(f"{key}Delta", signed(sla["delta"]))
        macro(f"{key}CIlow", signed(sla["ci_95"][0]))
        macro(f"{key}CIhigh", signed(sla["ci_95"][1]))
        macro(f"{key}NinetyLow", signed(sla["ci_90"][0]))
        macro(f"{key}NinetyHigh", signed(sla["ci_90"][1]))
        assert sla["equivalent"] and not sla["difference_detected"], key
        verdict = "equivalent"
        rows.append(
            f"{key} & {pct(sla['means'][0])} & {pct(sla['means'][1])} & {signed(sla['delta'])} "
            f"& {interval(sla['ci_95'])} & {interval(sla['ci_90'])} & {verdict} \\\\"
        )

        summary = report["ablation_results"]["summary_by_variant"]
        agreement = [a for arm in ARMS for a in summary[arm].get("teacher_agreement_by_seed", [])]
        if agreement:
            macro(f"{key}AgreeMin", pct(min(agreement), 1))
            macro(f"{key}AgreeMax", pct(max(agreement), 1))
            for i, arm in enumerate(("Fixed", "Diverse")):
                rates = summary[ARMS[i]]["teacher_agreement_by_seed"]
                macro(f"{key}Agree{arm}Mean", pct(statistics.mean(rates), 1))

        cells = []
        for agent in AGENTS:
            base = report["baseline_evaluations"].get(agent)
            cells.append(pct(base["overall_win_rate"], 1) if base else "n/a")
        baseline_rows.append(f"{key} & " + " & ".join(cells) + " \\\\")
        macro(f"{key}Games", str(report["baseline_evaluations"]["heuristic"]["total_games"]))

    # Seed-to-seed spread and the widest 95% bound across the three studies
    reports = [json.loads(Path(path).read_text(encoding="utf-8")) for path in STUDIES.values()]
    sds = [sd for r in reports for sd in r["seed_level_analysis"]["std"]]
    bounds = [abs(b) for r in reports for b in r["seed_level_analysis"]["ci_95"]]
    macro("SDMin", pct(min(sds), 1))
    macro("SDMax", pct(max(sds), 1))
    macro("MaxBound", pct(max(bounds)))

    # Study C: change from the starting checkpoint (the imitation checkpoints of study B)
    board = json.loads(Path(STUDIES["B"]).read_text(encoding="utf-8"))
    rl = json.loads(Path(STUDIES["C"]).read_text(encoding="utf-8"))
    start = {
        e["provenance"]["seed"]: checkpoint_score(e)
        for e in board["checkpoint_evaluations"][ARMS[0]]
    }
    for i, arm in enumerate(("Fixed", "Diverse")):
        evals = rl["checkpoint_evaluations"][ARMS[i]]
        change = [checkpoint_score(e) - start[e["provenance"]["seed"]] for e in evals]
        macro(f"CChange{arm}", signed(statistics.mean(change), 1))
        macro(f"CChange{arm}SD", pct(statistics.stdev(change), 1))
        macro(f"CUp{arm}", str(sum(c > 0 for c in change)))
        first = statistics.mean(e["provenance"]["training_score_first_quarter"] for e in evals)
        last = statistics.mean(e["provenance"]["training_score_last_quarter"] for e in evals)
        macro(f"CTrainFirst{arm}", pct(first, 1))
        macro(f"CTrainLast{arm}", pct(last, 1))
    macro("StartMean", pct(statistics.mean(start.values())))

    (OUT / "numbers.tex").write_text("\n".join(macros) + "\n", encoding="utf-8")
    # Write whole tabular environments: booktabs rules break when rows are input before the end
    results_head = (
        "\\begin{tabular}{@{}lrrrccl@{}}\n\\toprule\n"
        "Study & Fixed mean (\\%) & Diverse mean (\\%) & Difference & 95\\% interval "
        "& 90\\% interval & Result \\\\\n\\midrule\n"
    )
    baseline_head = (
        "\\begin{tabular}{@{}lrrrr@{}}\n\\toprule\n"
        "Study & Board & Heuristic & First & Random \\\\\n\\midrule\n"
    )
    tail = "\\bottomrule\n\\end{tabular}\n"
    (OUT / "results-table.tex").write_text(
        results_head + "\n".join(rows) + "\n" + tail, encoding="utf-8"
    )
    (OUT / "baseline-table.tex").write_text(
        baseline_head + "\n".join(baseline_rows) + "\n" + tail, encoding="utf-8"
    )
    (OUT / "seed-scores.csv").write_text("\n".join(csv) + "\n", encoding="utf-8")
    (OUT / "arm-means.csv").write_text("\n".join(means) + "\n", encoding="utf-8")
    # The figure reads one file per arm, so each arm gets its own marker and no table filter
    for arm in ARMS:
        lines = [csv[0]] + [row for row in csv[1:] if row.split(",")[1] == arm]
        name = "seed-scores-fixed.csv" if arm == ARMS[0] else "seed-scores-diverse.csv"
        (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {len(macros)} macros, {len(rows)} result rows, {len(csv) - 1} seed scores")


if __name__ == "__main__":
    main()
