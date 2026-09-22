"""Exact empirical percentiles from raw request timings, without averaging percentiles."""
import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path


def percentile(values, p):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(p * len(ordered)) - 1)]


def analyze_run(folder):
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    with (folder / "requests.csv").open(encoding="utf-8", newline="") as f:
        all_rows = list(csv.DictReader(f))
    if not all_rows:
        return []
    origin = json.loads((folder / "requests.timing.json").read_text(encoding="utf-8"))["started_at"]
    start, end = origin + manifest["warmup"], origin + manifest["seconds"]
    active = json.loads((folder / "requests.users.json").read_text(encoding="utf-8"))
    active = [sample["users"] for sample in active if start <= sample["time"] < end]
    rows = [r for r in all_rows if start <= float(r["finished_at"]) - float(r["response_ms"])/1000
            and float(r["finished_at"]) < end]
    duration = end - start
    failures = [r for r in all_rows if r["name"].startswith("login/") and r["success"] != "1"]
    records = []
    for name in sorted({r["name"] for r in rows}):
        group = [r for r in rows if r["name"] == name]
        successful = [float(r["response_ms"]) for r in group if r["success"] == "1"]
        all_times = [float(r["response_ms"]) for r in group]
        record = dict(run=folder.name, label=manifest["label"], users=manifest["users"],
                      scenario=manifest["version"], repeat=manifest["repeat"], endpoint=name,
                      requests=len(group), successes=len(successful), failures=len(group)-len(successful),
                      rps=len(group)/duration, success_rps=len(successful)/duration,
                      error_pct=100*(len(group)-len(successful))/len(group),
                      max_ms=max(all_times), window_seconds=duration,
                      login_failures_full_run=len(failures),
                      min_active_users=min(active) if active else None,
                      full_concurrency=bool(active) and min(active) == manifest["users"],
                      observed_users=len({r["user_id"] for r in rows if r["name"].startswith("predict/")}),
                      sample_warning="P99 unstable: fewer than 1000 successes" if len(successful)<1000 else "",
                      status_counts=json.dumps(dict(Counter(r["status"] for r in group))),
                      reason_counts=json.dumps(dict(Counter(r["reason"] for r in group if r["reason"]))))
        for p in [50, 90, 95, 99]:
            record[f"p{p}_success_ms"] = percentile(successful, p/100)
            record[f"p{p}_all_ms"] = percentile(all_times, p/100)
        records.append(record)
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("batch", type=Path)
    args = parser.parse_args()
    records = [r for manifest in sorted(args.batch.glob("*/manifest.json")) for r in analyze_run(manifest.parent)]
    if not records:
        raise SystemExit("No measured requests. Inspect raw files and logs; no results were fabricated.")
    with (args.batch / "summary.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    predictions = [r for r in records if r["endpoint"].startswith("predict/")]
    for metric, ylabel in [("p95_success_ms", "P95 respostas válidas (ms)"),
                           ("p99_success_ms", "P99 respostas válidas (ms)"),
                           ("success_rps", "Predições válidas por segundo"),
                           ("error_pct", "Falhas (%)")]:
        fig, ax = plt.subplots(figsize=(9, 5))
        for scenario, endpoint in sorted({(r["scenario"], r["endpoint"]) for r in predictions}):
            points = [r for r in predictions if r["scenario"] == scenario and r["endpoint"] == endpoint
                      and r[metric] is not None]
            ax.scatter([r["users"] for r in points], [r[metric] for r in points],
                       label=f"{scenario}: {endpoint}", alpha=.8)
        ax.set(xlabel="Usuários configurados", ylabel=ylabel, title="Cada ponto representa uma execução independente")
        ax.grid(alpha=.2)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(args.batch / f"{metric}.png", dpi=180)
        plt.close(fig)
    print(f"Saved summary.csv and plots in {args.batch}")


if __name__ == "__main__":
    main()
