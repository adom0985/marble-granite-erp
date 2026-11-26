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
        inv = c.execute("SELECT COUNT(*) cnt, ROUND(SUM(net_amount), 2) tot FROM invoices WHERE client_name = 'الحاج صلاح' AND status NOT IN ('متقفلة (أرشيف قديم)', 'خارج الحساب')").fetchone()
        pay = c.execute("SELECT COUNT(*) cnt, ROUND(SUM(amount_egp), 2) tot FROM client_payments WHERE client_name = 'الحاج صلاح'").fetchone()

        self.assertEqual(inv['cnt'], 10)
        self.assertEqual(inv['tot'], 1595602.46)

        self.assertEqual(pay['cnt'], 4)
        self.assertEqual(pay['tot'], 553700.00)

        remaining = round(inv['tot'] - pay['tot'], 2)
        self.assertEqual(remaining, 1041902.46)

        # Check outside-account invoice 96 exists under Haj Salah but excluded from balance
        inv_outside = c.execute("SELECT invoice_no, net_amount, status FROM invoices WHERE id = 96").fetchone()
        self.assertEqual(inv_outside['invoice_no'], 'فاتورة 24 / 11')
        self.assertEqual(inv_outside['status'], 'خارج الحساب')
        self.assertEqual(inv_outside['net_amount'], 368020.50)

        # Check new invoice 98 (فاتورة 22 / 11)
        inv_new = c.execute("SELECT invoice_no, net_amount, status FROM invoices WHERE id = 98").fetchone()
        self.assertEqual(inv_new['invoice_no'], 'فاتورة 22 / 11')
        self.assertEqual(inv_new['net_amount'], 110223.40)

        # Check the 4 payments in chronological order
        rows = c.execute("SELECT payment_date, amount_egp FROM client_payments WHERE client_name = 'الحاج صلاح' ORDER BY payment_date ASC, id ASC").fetchall()
        self.assertEqual(rows[0]['payment_date'], '2026-10-15')
        self.assertEqual(rows[0]['amount_egp'], 156000.0)

        self.assertEqual(rows[1]['payment_date'], '2026-10-17')
        self.assertEqual(rows[1]['amount_egp'], 5200.0)

        self.assertEqual(rows[2]['payment_date'], '2026-10-20')
        self.assertEqual(rows[2]['amount_egp'], 132500.0)

        self.assertEqual(rows[3]['payment_date'], '2026-11-09')
        self.assertEqual(rows[3]['amount_egp'], 260000.0)

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

        self.assertEqual(inv['cnt'], 2)
        self.assertEqual(inv['tot'], 221088.25)

        self.assertEqual(pay['cnt'], 1)
        self.assertEqual(pay['tot'], 40000.00)

        remaining = round(inv['tot'] - pay['tot'], 2)
        self.assertEqual(remaining, 181088.25)

    def test_haj_salah_pdf_statement_generation(self):
        import fitz
        from statement_pdf_generator import generate_client_statement_pdf

        pdf_bytes = generate_client_statement_pdf("الحاج صلاح", conn=self.conn)
        self.assertGreater(len(pdf_bytes), 5000)

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        self.assertEqual(len(doc), 1)
        text = doc[0].get_text()
        self.assertIn("1,595,602.46", text)
        self.assertIn("553,700.00", text)
        self.assertIn("1,041,902.46", text)
        doc.close()

    def test_eissa_pdf_statement_generation(self):
        import fitz
        from statement_pdf_generator import generate_client_statement_pdf

        pdf_bytes = generate_client_statement_pdf("عيسى", conn=self.conn)
        self.assertGreater(len(pdf_bytes), 5000)

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        self.assertEqual(len(doc), 1)
        text = doc[0].get_text()
        self.assertIn("221,088.25", text)
        self.assertIn("40,000.00", text)
        self.assertIn("181,088.25", text)
        doc.close()

if __name__ == "__main__":
    unittest.main()
