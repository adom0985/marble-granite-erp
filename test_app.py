import os
import requests
import sys

# Test database and excel exporter directly
from database import get_connection
from excel_exporter import create_invoice_excel

print("1. Testing DB connection and count...")
conn = get_connection()
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM invoices")
inv_cnt = c.fetchone()[0]
print(f"Total invoices in DB: {inv_cnt}")

c.execute("SELECT COUNT(*) FROM clients")
cl_cnt = c.fetchone()[0]
print(f"Total clients in DB: {cl_cnt}")

c.execute("SELECT COUNT(*) FROM materials")
mat_cnt = c.fetchone()[0]
print(f"Total materials in DB: {mat_cnt}")

# Test Excel Exporter on Invoice #1
print("\n2. Testing Excel Exporter on Invoice #1...")
c.execute("SELECT * FROM invoices WHERE id = 1")
inv_row = dict(c.fetchone())
c.execute("SELECT * FROM invoice_items WHERE invoice_id = 1")
inv_row["items"] = [dict(r) for r in c.fetchall()]
conn.close()

test_xlsx_out = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\exports\test_invoice.xlsx"
create_invoice_excel(inv_row, test_xlsx_out)

print(f"Excel created successfully: {os.path.exists(test_xlsx_out)} ({os.path.getsize(test_xlsx_out)} bytes)")
print("ALL DIRECT TESTS PASSED SUCCESSFULLY!")
