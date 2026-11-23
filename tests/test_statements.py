# -*- coding: utf-8 -*-
import unittest
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "marble_erp.db")

class StatementVerificationTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def tearDown(self):
        self.conn.close()

    def test_haj_salah_statement(self):
        c = self.conn.cursor()
        inv = c.execute("SELECT COUNT(*) cnt, ROUND(SUM(net_amount), 2) tot FROM invoices WHERE client_name = 'الحاج صلاح'").fetchone()
        pay = c.execute("SELECT COUNT(*) cnt, ROUND(SUM(amount_egp), 2) tot FROM client_payments WHERE client_name = 'الحاج صلاح'").fetchone()

        self.assertEqual(inv['cnt'], 10)
        self.assertEqual(inv['tot'], 1853399.56)

        self.assertEqual(pay['cnt'], 3)
        self.assertEqual(pay['tot'], 548500.00)

        remaining = round(inv['tot'] - pay['tot'], 2)
        self.assertEqual(remaining, 1304899.56)

        # Check the 3 payments
        rows = c.execute("SELECT payment_date, amount_egp FROM client_payments WHERE client_name = 'الحاج صلاح' ORDER BY payment_date").fetchall()
        self.assertEqual(rows[0]['payment_date'], '2026-10-15')
        self.assertEqual(rows[0]['amount_egp'], 156000.0)

        self.assertEqual(rows[1]['payment_date'], '2026-10-20')
        self.assertEqual(rows[1]['amount_egp'], 132500.0)

        self.assertEqual(rows[2]['payment_date'], '2026-11-09')
        self.assertEqual(rows[2]['amount_egp'], 260000.0)

    def test_sadeeq_gaafar_statement(self):
        c = self.conn.cursor()
        inv = c.execute("SELECT COUNT(*) cnt, ROUND(SUM(net_amount), 2) tot FROM invoices WHERE client_name = 'صديق جعفر'").fetchone()
        pay = c.execute("SELECT COUNT(*) cnt, ROUND(SUM(amount_egp), 2) tot FROM client_payments WHERE client_name = 'صديق جعفر'").fetchone()

        self.assertEqual(inv['cnt'], 6)
        self.assertEqual(inv['tot'], 640781.00)

        self.assertEqual(pay['cnt'], 7)
        self.assertEqual(pay['tot'], 590000.00)

        remaining = round(inv['tot'] - pay['tot'], 2)
        self.assertEqual(remaining, 50781.00)

        # Check last payment is 100,000
        last_pay = c.execute("SELECT payment_date, amount_egp FROM client_payments WHERE client_name = 'صديق جعفر' ORDER BY id DESC LIMIT 1").fetchone()
        self.assertEqual(last_pay['amount_egp'], 100000.0)

    def test_eissa_statement(self):
        c = self.conn.cursor()
        inv = c.execute("SELECT COUNT(*) cnt, ROUND(SUM(net_amount), 2) tot FROM invoices WHERE client_name = 'عيسى'").fetchone()
        pay = c.execute("SELECT COUNT(*) cnt, ROUND(SUM(amount_egp), 2) tot FROM client_payments WHERE client_name = 'عيسى'").fetchone()

        self.assertEqual(inv['cnt'], 1)
        self.assertEqual(inv['tot'], 119950.85)

        self.assertEqual(pay['cnt'], 1)
        self.assertEqual(pay['tot'], 40000.00)

        remaining = round(inv['tot'] - pay['tot'], 2)
        self.assertEqual(remaining, 79950.85)

if __name__ == "__main__":
    unittest.main()
