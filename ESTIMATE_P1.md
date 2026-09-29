# P1 — Pre-Measurement Estimates ("The dashboard is empty at 08:00")

**Student:** Mahmut Eren Akkaymak  
**Rule:** Committed to git BEFORE any P1 query is run. Nothing below has been measured yet.  
**Basis:** P0 results (Q1 at 10M = 0.51 s warm on this machine) + reasoning about how each algorithm visits the data.

Fill-in sentence: *when the data grows, the time grows ___ times as fast.*

| Query | Estimate |
| :--- | :--- |
| **Q1 — total commission** (`SUM(amount*0.09)`, full scan) | When the data grows, the time grows **1×** as fast (linear, ~10× per 10× step). **10M rows: ~0.55 s** (cold, fresh process), ~0.50 s warm. |
| **Q2 — naive** (every order compared with every other order, nested loop) | When the data grows, the time grows **N×** as fast — it is quadratic: **doubling the rows → ~4× the time**. Guess: ~2 s at 10,000 rows → ~0.12 s at 1,250. Extrapolated: 100,000 rows ≈ 200 s, 1,000,000 rows ≈ 20,000 s (~5.5 h). |
| **Q3 — grouping** (`GROUP BY customer_id, order_date`) | When the data grows, the time grows **~1.1–1.2×** as fast (sort-based grouping, n log n): ~11–12× per 10× step. **10M rows: ~8 s.** |

## Why
- Q1 visits each row once → O(n). P0 already showed ~10× per 10× above 100k rows.
- Q2 visits n rows for each of n rows → n² comparisons. At n = 10,000 that is 100 million row visits.
- Q3 visits each row once but has to sort/hash on (customer, day) → O(n log n), with an extra jump once the temp b-tree no longer fits in SQLite's cache.

## Expected answer consistency
Q2 and Q3 must return the **same number of distinct customers** at 10,000 rows. At 1,250 rows the answer may be 0 or 1.
