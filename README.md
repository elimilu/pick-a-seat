# Pick a Seat

Choose a summer concert at the fictional Meridian Hall, explore its seating chart and select B12. This is a rehearsal app: no accounts, reservations, payments, CDNs or external APIs. A seat click updates only the browser. Refreshing or changing shows clears the selection.

## Run it

With Python 3.10+ and its standard SQLite module, run this from the repository root:

```sh
python3 server.py
```

Open <http://127.0.0.1:8000>. The first start generates `.data/venue.sqlite3` (about 89 MiB); later starts reuse it. The seed is deterministic: 512 performances × 8 venue sections × 50 rows × 28 seats = **5,734,400 inventory rows**. Three shows are on sale; the rest provide historical inventory. The generated database is not in Git. Use `--port`, `--host` or `--db` to change the defaults; `--host 0.0.0.0` is for a sandbox preview, not a production deployment.

## Rehearse the two waits

1. Choose **Velvet Current**, then **Neon Atlas**. Each change makes one local seat-inventory request. The map contains 11,200 seats once loaded.
2. In **Front floor**, find row **B** and click **12**. The seat turns amber and the ticket shows **1** and **B12**. Click again to deselect. The gray seats are booked.
3. Repeat on the performance PR. Compare **changing shows** separately from **clicking an already-loaded seat**. Keep `main` as the slow version; don't merge the demo PR.

The baseline has two independent bottlenecks. In `venue.py`, a lookup by show scans every performance's seats. In `web/app.js`, toggling one seat replaces the entire map. The API, CSS, controls and generated inventory are shared between demonstrations. There are no injected delays or CPU throttles.

## Verify and measure

```sh
python3 -m unittest discover -s tests -v
python3 bench/database.py  # after the first server start
```

The database benchmark reports the actual production query plan, matching rows, and warm execution + fetch time, **not HTTP or full map-load latency**. It warms up three times, then reports the median, nearest-rank p90 and all 21 timed samples, using one connection. Use `--db` to select a different file.

The optional browser benchmark needs Playwright and Chromium. In a second terminal:

```sh
python3 -m venv .venv
.venv/bin/pip install -r bench/requirements.txt
# Skip this if chromium is on PATH, or set CHROMIUM to a compatible browser executable.
.venv/bin/playwright install chromium
.venv/bin/python bench/click.py http://127.0.0.1:8000
```

Playwright drives real mouse clicks in headless Chromium at 1440 × 900 with no CPU/network throttle. The timer starts at the trusted click's browser timestamp and ends in the second `requestAnimationFrame` callback. This is **click to a frame after a paint opportunity**, a bounded-method proxy for a visible update, not a physical display timestamp, INP score, or handler-only time. It checks B12's color, pressed state and counter for each toggle, counts all browser requests during the click loop, and reports whether unrelated seat A1 survived. It also checks switching shows, multi-selecting by keyboard and clearing the selection. Three warm-ups and 21 timed clicks. Compare branches on the same machine and browser; timings will vary elsewhere.

For a side-by-side rehearsal, use separate checkouts or worktrees, separate ports and separate databases so adding an index to the optimized version cannot change the baseline. Both checkouts generate the same inventory. Run each benchmark sequentially, on an otherwise idle machine.
