"""Benchmark the production row lookup, including fetchall, excluding HTTP and JSON."""
import argparse
import json
from math import ceil
from pathlib import Path
import sqlite3
import statistics
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import venue

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--db', type=Path, default=venue.DB)
parser.add_argument('--show', type=int, default=1)
parser.add_argument('--samples', type=int, default=21)
args = parser.parse_args()
if args.samples < 1:
    parser.error('samples must be positive')
with sqlite3.connect(args.db.resolve().as_uri() + '?mode=ro', uri=True) as db:
    plan = [r[3] for r in db.execute('EXPLAIN QUERY PLAN ' + venue.SEAT_QUERY, (args.show,))]
    rows = db.execute('SELECT COUNT(*) FROM seats').fetchone()[0]
    for _ in range(3):
        expected = venue.seats(db, args.show)
    assert expected, 'Selected show must have seats'
    times = []
    for _ in range(args.samples):
        t0 = time.perf_counter_ns()
        result = venue.seats(db, args.show)
        times.append(round((time.perf_counter_ns() - t0) / 1e6, 2))
        assert result == expected
    print(json.dumps(dict(sqlite=sqlite3.sqlite_version, show=args.show, inventory=rows,
                          matches=len(expected), plan=plan, median_ms=statistics.median(times),
                          p90_ms=sorted(times)[ceil(.9*len(times))-1], samples_ms=times), indent=2))
