"""SQLite inventory for the synthetic Meridian Hall season archive."""
from pathlib import Path
from datetime import date, timedelta
import sqlite3
import tempfile

DB = Path(__file__).parent / '.data' / 'venue.sqlite3'
ROWS, WIDTH, SHOWS = 400, 28, 512
SHOW_NAMES = ('Neon Atlas', 'Velvet Current', 'The Static Hours')
SEAT_QUERY = 'SELECT row_num, seat_num, booked FROM seats WHERE show_id = ? ORDER BY rowid'


def prepare(path=DB, count=SHOWS):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        # Publish a completed seed atomically, so an interrupted first run can restart.
        with tempfile.TemporaryDirectory(dir=path.parent) as tmp:
            new = Path(tmp) / 'seed.sqlite3'
            db = sqlite3.connect(new)
            try:
                with db:
                    db.executescript('''
                        CREATE TABLE shows (id INTEGER PRIMARY KEY, title TEXT, night TEXT, on_sale INTEGER);
                        CREATE TABLE seats (show_id INTEGER, row_num INTEGER, seat_num INTEGER, booked INTEGER);
                    ''')
                    db.executemany('INSERT INTO shows VALUES (?, ?, ?, ?)', (
                        (i, SHOW_NAMES[(i - 1) % 3],
                         str(date(2027, 6, 3) + timedelta(days=(2 * (i-1) if i <= 3 else 3-i))), i <= 3)
                        for i in range(1, count+1)))
                    db.execute('''WITH RECURSIVE positions(pos) AS (
                        VALUES(0) UNION ALL SELECT pos + 1 FROM positions WHERE pos + 1 < ?
                    ) INSERT INTO seats
                    SELECT id, pos / ? + 1, pos % ? + 1,
                        CASE WHEN pos = ? THEN 0 ELSE
                        ((pos * 83 + id * 137 + pos * pos * 7) % 157) < 49 END
                    FROM shows CROSS JOIN positions''', (ROWS*WIDTH, WIDTH, WIDTH, WIDTH+11))
            finally:
                db.close()
            new.replace(path)


def shows(db):
    return [dict(id=i, title=t, night=n) for i, t, n in db.execute(
        'SELECT id, title, night FROM shows WHERE on_sale=1 ORDER BY id')]


def seats(db, show_id):
    return db.execute(SEAT_QUERY, (show_id,)).fetchall()
