# Pre-Measurement Estimates (P0 Section 5)

**Course:** Data Structures and Management · Fall 2026 · Istanbul University  
**Student:** Mahmut Eren Akkaymak  
**Commit Rule:** Must be committed to git BEFORE running measurements.

---

### Query to be Measured
```sql
SELECT SUM(amount * 0.09) FROM <table_name>;
```
*Total commission: Meydan takes 9% of every order. Single-pass aggregation across the full table.*

---

### Estimation Table (Prior Expectations)

| Scale (N) | Table Name | Expected Warm Time (s) | Expected Factor (vs prev) | Expected Cold Time (s) |
| :--- | :--- | :--- | :--- | :--- |
| **10,000** | `Orders_10k` | 0.0020 s (2.0 ms) | — | 0.0050 s |
| **100,000** | `Orders_100k` | 0.0200 s (20.0 ms) | **10.0x** | 0.0400 s |
| **1,000,000** | `ORDERS_1M` | 0.2000 s (200.0 ms) | **10.0x** | 0.4000 s |
| **10,000,000** | `ORDERS_10m` | **2.0000 s** (~2.0 s) | **10.0x** | **4.0000 s** |

---

### Rationale and Hypotheses

1. **Time at 10 Million Rows:**
   - We estimate that a full table scan and aggregation over 10,000,000 rows in SQLite will take approximately **2.00 seconds** for a warm run and **~4.00 seconds** for a cold run.
   - Database size is ~482 MB. With fast memory bandwidth and SQLite's optimized internal C aggregation loop, scanning 482 MB in memory should achieve roughly 5M rows/sec, yielding ~2 seconds.

2. **Growth Factor Across Scales:**
   - Because `SUM(amount * 0.09)` requires visiting each row exactly once without an index (linear complexity $O(N)$), the theoretical expectation is an exact **10.0x growth factor** between each 10x increase in row count ($10k \rightarrow 100k \rightarrow 1M \rightarrow 10M$).

3. **Cold vs. Warm Expectations:**
   - Cold runs are predicted to take 1.5x–2.0x longer at 10M rows due to cold OS page cache, initial page faulting, and disk reading from storage into memory.
