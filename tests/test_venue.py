from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

import venue


class InventoryTest(unittest.TestCase):
    def test_shows_and_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'venue.db'
            venue.prepare(path, count=4)
            venue.prepare(path, count=4)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual([s['id'] for s in venue.shows(db)], [1, 2, 3])
                rows = venue.seats(db, 1)
                self.assertEqual([(r,n) for r,n,_ in rows], [
                    (r,n) for r in range(1, venue.ROWS+1) for n in range(1, venue.WIDTH+1)])
                self.assertIn((2,12,0), rows)
                self.assertEqual({booked for _,_,booked in rows}, {0,1})
                self.assertNotEqual(rows, venue.seats(db, 2))
                self.assertEqual(venue.seats(db, 10), [])


if __name__ == '__main__':
    unittest.main()
