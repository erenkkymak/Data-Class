"""
measure.py - Generic and Reusable Benchmarking Helper
Course: Data Structures and Management · Assoc. Prof. Dr. Emre Akadal · Istanbul University, MIS
Assignment: P0 - Get to know Meydan

Requirements:
- Run operation at least 3 times and report median, min, max
- Record cold and warm runs as separate rows
- Take fixed seed and row count (n) as parameters and carry into output
- Emit rows formatted exactly as:
  Method | n | Time (median, s) | Min-Max | Time/n (µs) | Run
- Export results to CSV
"""

import sys
import time
import sqlite3
import csv
import argparse
import statistics
from dataclasses import dataclass, asdict
from typing import Callable, Any, List, Optional, Tuple


@dataclass
class MeasurementResult:
    method: str
    n: int
    time_median_s: float
    min_max: str
    time_per_n_us: float
    run: str
    seed: int
    min_s: float
    max_s: float
    repeats: int

    def to_table_row(self) -> str:
        """Returns a pipe-delimited row matching the course requirement."""
        return f"{self.method} | {self.n:,} | {self.time_median_s:.6f} | {self.min_max} | {self.time_per_n_us:.4f} | {self.run}"

    def to_markdown_row(self) -> str:
        return f"| {self.method} | {self.n:,} | {self.time_median_s:.6f} | {self.min_max} | {self.time_per_n_us:.4f} | {self.run} |"

    def to_csv_dict(self) -> dict:
        return {
            "Method": self.method,
            "n": self.n,
            "Time (median, s)": f"{self.time_median_s:.6f}",
            "Min-Max": self.min_max,
            "Time/n (us)": f"{self.time_per_n_us:.4f}",
            "Run": self.run,
            "Seed": self.seed,
            "Min (s)": f"{self.min_s:.6f}",
            "Max (s)": f"{self.max_s:.6f}",
            "Repeats": self.repeats,
        }


def measure(
    operation: Callable[[], Any],
    method: str,
    n: int,
    seed: int = 42,
    warm_repeats: int = 5,
    cold_operation: Optional[Callable[[], Any]] = None,
    time_func: Callable[[], float] = time.perf_counter,
) -> Tuple[MeasurementResult, MeasurementResult]:
    """
    Executes a cold run and at least 3 warm runs, returning two MeasurementResult objects:
    (cold_result, warm_result)
    
    Parameters:
    - operation: Callable to run for measurements
    - method: Description / method name (e.g. 'Total Commission (SUM)')
    - n: Row count / scale
    - seed: Fixed generator seed
    - warm_repeats: Number of warm runs (must be >= 3 per assignment spec)
    - cold_operation: Optional separate callable for cold run (e.g. fresh connection)
    - time_func: High resolution timer function (default: time.perf_counter)
    """
    if warm_repeats < 3:
        raise ValueError("warm_repeats must be at least 3 as per specification.")

    # 1. Cold Run: First run on untouched state
    run_cold_fn = cold_operation if cold_operation is not None else operation
    t_start = time_func()
    _ = run_cold_fn()
    cold_elapsed = time_func() - t_start

    cold_time_per_n = (cold_elapsed * 1_000_000.0) / n if n > 0 else 0.0
    cold_result = MeasurementResult(
        method=method,
        n=n,
        time_median_s=cold_elapsed,
        min_max=f"{cold_elapsed:.6f}-{cold_elapsed:.6f}",
        time_per_n_us=cold_time_per_n,
        run="cold",
        seed=seed,
        min_s=cold_elapsed,
        max_s=cold_elapsed,
        repeats=1,
    )

    # 2. Warm Runs: At least 3 executions on warmed cache
    warm_times: List[float] = []
    for _ in range(warm_repeats):
        t_start = time_func()
        _ = operation()
        warm_times.append(time_func() - t_start)

    warm_median = statistics.median(warm_times)
    warm_min = min(warm_times)
    warm_max = max(warm_times)
    warm_time_per_n = (warm_median * 1_000_000.0) / n if n > 0 else 0.0

    warm_result = MeasurementResult(
        method=method,
        n=n,
        time_median_s=warm_median,
        min_max=f"{warm_min:.6f}-{warm_max:.6f}",
        time_per_n_us=warm_time_per_n,
        run="warm",
        seed=seed,
        min_s=warm_min,
        max_s=warm_max,
        repeats=warm_repeats,
    )

    return cold_result, warm_result


def export_to_csv(results: List[MeasurementResult], filepath: str = "measurements.csv"):
    """Exports measurement results to a CSV file."""
    if not results:
        return
    fieldnames = list(results[0].to_csv_dict().keys())
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for res in results:
            writer.writerow(res.to_csv_dict())


def format_table(results: List[MeasurementResult]) -> str:
    """Formats results into the standard course markdown table."""
    headers = ["Method", "n", "Time (median, s)", "Min-Max", "Time/n (us)", "Run"]
    separator = ["---", "---:", "---:", "---:", "---:", "---"]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for r in results:
        lines.append(r.to_markdown_row())
    return "\n".join(lines)


def benchmark_p0_query(db_path: str = "Data-Class.db", seed: int = 42, warm_repeats: int = 5) -> List[MeasurementResult]:
    """
    Executes the P0 assignment query:
    Total commission: Meydan takes 9% of every order.
    Query: SELECT SUM(amount * 0.09) FROM <table>
    Across all 4 scales: 10,000 / 100,000 / 1,000,000 / 10,000,000 rows.
    """
    tables = [
        ("Orders_10k", 10_000),
        ("Orders_100k", 100_000),
        ("ORDERS_1M", 1_000_000),
        ("ORDERS_10m", 10_000_000),
    ]

    all_results: List[MeasurementResult] = []

    for table_name, n in tables:
        query = f"SELECT SUM(amount * 0.09) FROM {table_name};"

        # Cold operation: Open fresh connection and execute query once
        def cold_op(t_name=table_name, q=query):
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            res = cur.execute(q).fetchone()
            conn.close()
            return res

        # Warm operation: Reuse connection across warm repetitions
        warm_conn = sqlite3.connect(db_path)
        warm_cur = warm_conn.cursor()

        def warm_op(cur=warm_cur, q=query):
            return cur.execute(q).fetchone()

        method_label = "Total Commission (SQL SUM)"
        cold_res, warm_res = measure(
            operation=warm_op,
            method=method_label,
            n=n,
            seed=seed,
            warm_repeats=warm_repeats,
            cold_operation=cold_op,
        )
        warm_conn.close()

        all_results.append(cold_res)
        all_results.append(warm_res)

    return all_results


def main():
    parser = argparse.ArgumentParser(description="Meydan P0 Measurement Helper")
    parser.add_argument("--db", default="Data-Class.db", help="Path to SQLite database")
    parser.add_argument("--seed", type=int, default=42, help="Random seed used in generator")
    parser.add_argument("--repeats", type=int, default=5, help="Number of warm runs (min 3)")
    parser.add_argument("--csv", default="measurements.csv", help="Path to output CSV file")
    args = parser.parse_args()

    print(f"Running P0 Commission benchmark on '{args.db}' (Seed={args.seed}, Warm repeats={args.repeats})...\n")
    results = benchmark_p0_query(db_path=args.db, seed=args.seed, warm_repeats=args.repeats)

    table_md = format_table(results)
    print("### Measurement Results Table (Course Standard Format):\n")
    print(table_md)
    print("\n")

    export_to_csv(results, args.csv)
    print(f"-> Results successfully exported to CSV: {args.csv}")


if __name__ == "__main__":
    main()
