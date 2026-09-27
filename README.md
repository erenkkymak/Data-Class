# Meydan — Data Structures and Management (P0)

**Course:** Data Structures and Management (Fall 2026)  
**Instructor:** Assoc. Prof. Dr. Emre Akadal · Istanbul University, MIS  
**Student:** Mahmut Eren Akkaymak (`mahmuteren.akkaymak@ogr.iu.edu.tr`)  

---

## Overview

This repository contains the codebase, benchmarking helpers, prior estimates, and measurement reports for **P0 — Get to know Meydan (warm-up)**.

- [generate_db.py](generate_db.py): Generates 4 scales of orders data ($N = 10,000 / 100,000 / 1,000,000 / 10,000,000$) using seed `42`.
- [measure.py](measure.py): Generic benchmarking helper recording cold and warm runs (median, min-max, time/n) and exporting results to CSV.
- [measurements.csv](measurements.csv): CSV output containing all measurement results.
- [ESTIMATE.md](ESTIMATE.md): Prior estimates committed to git *before* measurements (Commit: `9df27a8`).
- [REPORT.md](REPORT.md): Complete assignment report ready for submission.

---

## How to Run

### 1. Generate the SQLite Database
```bash
python generate_db.py
```
*(Creates `Data-Class.db` with 11,110,000 total rows. Excluded from Git via `.gitignore`.)*

### 2. Run Benchmark & Export CSV
```bash
python measure.py --csv measurements.csv --repeats 5
```

---

## Results Summary

| Method | n | Time (median, s) | Min-Max | Time/n (us) | Run |
| --- | ---: | ---: | ---: | ---: | --- |
| Total Commission (SQL SUM) | 10,000 | 0.001994 | 0.001994-0.001994 | 0.1994 | cold |
| Total Commission (SQL SUM) | 10,000 | 0.000236 | 0.000231-0.001104 | 0.0236 | warm |
| Total Commission (SQL SUM) | 100,000 | 0.006978 | 0.006978-0.006978 | 0.0698 | cold |
| Total Commission (SQL SUM) | 100,000 | 0.005058 | 0.004972-0.006329 | 0.0506 | warm |
| Total Commission (SQL SUM) | 1,000,000 | 0.053356 | 0.053356-0.053356 | 0.0534 | cold |
| Total Commission (SQL SUM) | 1,000,000 | 0.052615 | 0.051841-0.053331 | 0.0526 | warm |
| Total Commission (SQL SUM) | 10,000,000 | 0.518187 | 0.518187-0.518187 | 0.0518 | cold |
| Total Commission (SQL SUM) | 10,000,000 | 0.511348 | 0.508229-0.544781 | 0.0511 | warm |

*Full details and analysis are available in [REPORT.md](REPORT.md).*
