"""
measure.py - reusable benchmarking helper (Data Structures and Management, Fall 2026)

Course rules implemented here:
- every measurement is repeated at least 3 times -> median + min-max
- cold and warm are separate rows
    cold = first run in a FRESH PROCESS (connect + query), repeated in >= 3 separate processes
    warm = runs after the first one, in the same process (the priming run is discarded)
- seed and n are carried into every output row
- output row: Method | n | Time (median, s) | Min-Max | Time/n (us) | Run | Growth factor | Result
"""

import argparse
import csv
import json
import sqlite3
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

DEFAULT_DB = "Data-Class.db"
SEED = 42


@dataclass
class MeasurementResult:
    method: str
    n: int
    times: List[float]
    run: str               # "cold" | "warm"
    seed: int
    result: Any = None      # what the query returned (e.g. number of customers found)
    growth_factor: Optional[float] = None

    @property
    def median(self) -> float:
        return statistics.median(self.times)

    @property
    def min_s(self) -> float:
        return min(self.times)

    @property
    def max_s(self) -> float:
        return max(self.times)

    @property
    def time_per_n_us(self) -> float:
        return self.median * 1e6 / self.n if self.n else 0.0

    def gf_str(self) -> str:
        return "—" if self.growth_factor is None else f"{self.growth_factor:.2f}x"

    def to_markdown_row(self) -> str:
        return (f"| {self.method} | {self.n:,} | {self.median:.6f} | {self.min_s:.6f}-{self.max_s:.6f} | "
                f"{self.time_per_n_us:.4f} | {self.run} | {self.gf_str()} | {self.result} |")

    def to_csv_dict(self) -> dict:
        return {
            "Method": self.method, "n": self.n,
            "Time (median, s)": f"{self.median:.6f}",
            "Min-Max": f"{self.min_s:.6f}-{self.max_s:.6f}",
            "Time/n (us)": f"{self.time_per_n_us:.4f}",
            "Run": self.run,
            "Growth factor": "" if self.growth_factor is None else f"{self.growth_factor:.4f}",
            "Result": self.result, "Seed": self.seed, "Repeats": len(self.times),
            "Min (s)": f"{self.min_s:.6f}", "Max (s)": f"{self.max_s:.6f}",
            "All times (s)": ";".join(f"{t:.6f}" for t in self.times),
        }


# ---------------------------------------------------------------- core helpers

def measure_warm(operation: Callable[[], Any], method: str, n: int, seed: int = SEED,
                 repeats: int = 5) -> MeasurementResult:
    """Warm runs: one priming run (discarded), then `repeats` timed runs in the same process."""
    if repeats < 3:
        raise ValueError("repeats must be >= 3 (ground rule 4)")
    operation()  # priming run = this process's cold run, not reported as warm
    times, result = [], None
    for _ in range(repeats):
        t0 = time.perf_counter()
        result = operation()
        times.append(time.perf_counter() - t0)
    return MeasurementResult(method, n, times, "warm", seed, result)


def measure_cold(sql: str, params: dict, method: str, n: int, db: str = DEFAULT_DB,
                 seed: int = SEED, repeats: int = 3, pragmas: Optional[List[str]] = None) -> MeasurementResult:
    """Cold runs: each one is a brand-new Python process that connects, runs the query once, and exits."""
    if repeats < 3:
        raise ValueError("repeats must be >= 3 (ground rule 4)")
    payload = json.dumps({"db": db, "sql": sql, "params": params, "pragmas": pragmas or []})
    times, result = [], None
    for _ in range(repeats):
        out = subprocess.run([sys.executable, __file__, "--child", payload],
                             capture_output=True, text=True, check=True)
        data = json.loads(out.stdout.strip().splitlines()[-1])
        times.append(data["elapsed"])
        result = data["result"]
    return MeasurementResult(method, n, times, "cold", seed, result)


def run_sql(conn: sqlite3.Connection, sql: str, params: dict, pragmas: List[str]):
    for p in pragmas:
        conn.execute(p)
    return conn.execute(sql, params).fetchone()[0]


def _child(payload: str):
    cfg = json.loads(payload)
    t0 = time.perf_counter()
    conn = sqlite3.connect(cfg["db"])          # reading the data is part of the measurement
    res = run_sql(conn, cfg["sql"], cfg["params"], cfg["pragmas"])
    elapsed = time.perf_counter() - t0
    conn.close()
    print(json.dumps({"elapsed": elapsed, "result": res}))


def add_growth_factors(results: List[MeasurementResult]) -> None:
    """Growth factor = this row's median / previous row's median (same method, same run type)."""
    last = {}
    for r in results:
        key = (r.method, r.run)
        if key in last:
            r.growth_factor = r.median / last[key].median
        last[key] = r


def format_table(results: List[MeasurementResult]) -> str:
    head = "| Method | n | Time (median, s) | Min-Max | Time/n (us) | Run | Growth factor | Result |"
    sep = "| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |"
    return "\n".join([head, sep] + [r.to_markdown_row() for r in results])


def export_to_csv(results: List[MeasurementResult], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].to_csv_dict().keys()))
        w.writeheader()
        for r in results:
            w.writerow(r.to_csv_dict())


def environment_line() -> str:
    import platform
    return (f"{platform.platform()} | {platform.processor()} | Python {platform.python_version()} | "
            f"sqlite3 C engine {sqlite3.sqlite_version}")


if __name__ == "__main__" and len(sys.argv) >= 3 and sys.argv[1] == "--child":
    _child(sys.argv[2])
