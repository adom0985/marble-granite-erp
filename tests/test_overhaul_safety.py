import sqlite3
import tempfile
import unittest
from pathlib import Path


class LocalDbSafetyTests(unittest.TestCase):
    def test_backup_is_readable_and_has_expected_tables(self):
        db = Path(__file__).resolve().parents[1] / "data" / "marble_erp.pre-overhaul-20261028.db"
        self.assertTrue(db.exists())
        snapshot = Path(tempfile.gettempdir()) / "marble_erp_test_snapshot.db"
        snapshot.write_bytes(db.read_bytes())
        conn = sqlite3.connect(f"file:{snapshot.as_posix()}?mode=ro", uri=True)
        try:
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({"clients", "invoices", "invoice_items", "client_payments"}.issubset(tables))
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0], 51)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM client_payments").fetchone()[0], 8)
        finally:
            conn.close()

    def test_source_has_no_temp_database_silent_write_claim(self):
        src = Path(__file__).resolve().parents[1] / "database.py"
        text = src.read_text(encoding="utf-8")
        self.assertIn('DB_PATH = f"/tmp/data/marble_erp_{DB_VERSION}.db"', text)


if __name__ == "__main__":
    unittest.main()
