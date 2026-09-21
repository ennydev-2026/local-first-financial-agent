"""Ledger export/import, tags, and summary breakdown."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from lffa import ledger


class LedgerTests(unittest.TestCase):
    def test_export_import_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.db"
            ledger.add_transaction(db, "Test", -100, category="food", tags="a,b")
            raw = ledger.export_ledger_json(db)
            db2 = Path(tmp) / "ledger2.db"
            count = ledger.import_ledger_json(db2, raw)
            self.assertEqual(count, 1)
            txs = ledger.list_transactions(db2)
            self.assertEqual(txs[0].category, "food")
            self.assertEqual(txs[0].tags, "a,b")

    def test_summary_by_tag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "ledger.db"
            ledger.add_transaction(db, "A", -500, tags="coffee")
            ledger.add_transaction(db, "B", -300, tags="coffee,work")
            s = ledger.summarize(db)
            self.assertEqual(s.by_tag["coffee"], -800)
            self.assertEqual(s.by_tag["work"], -300)

    def test_routing_decision_dict(self) -> None:
        from lffa import nosana_overflow

        d = nosana_overflow.decide_route("hi", local_max_chars=100)
        self.assertIn("route", d.to_dict())
        self.assertTrue(d.to_dict()["within_local_budget"])


if __name__ == "__main__":
    unittest.main()
