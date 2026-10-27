import sqlite3
import os
import re
from pdf_invoice_generator import generate_invoice_pdf

DB_PATH = "data/marble_erp.db"
HAJ_SALAH_DIR = r"I:\خالي أحمد جلال\الحاج صلاح"
STATIC_EXPORTS = "static/exports"
EXPORTS = "exports"

os.makedirs(STATIC_EXPORTS, exist_ok=True)
os.makedirs(EXPORTS, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT * FROM invoices WHERE client_name LIKE ? ORDER BY invoice_date ASC, id ASC", ('%صلاح%',))
invoices = c.fetchall()

print(f"Generating updated PDFs for {len(invoices)} Haj Salah invoices...")

for inv in invoices:
    inv_dict = dict(inv)
    inv_id = inv_dict['id']
    c.execute("SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY row_index ASC", (inv_id,))
    inv_dict['items'] = [dict(r) for r in c.fetchall()]

    clean_no = re.sub(r'[\s/\\:*?"<>|]+', '-', inv_dict['invoice_no']).strip('-')
    file_base = f"{inv_dict['invoice_date']} - {clean_no}"

    # 1. Save to Haj Salah folder on I: drive
    if os.path.exists(r"I:\خالي أحمد جلال"):
        os.makedirs(HAJ_SALAH_DIR, exist_ok=True)
        drive_path = os.path.join(HAJ_SALAH_DIR, f"{file_base}.pdf")
        generate_invoice_pdf(inv_dict, drive_path)
        print(f" -> Saved to Drive: {drive_path}")

    # 2. Save to static/exports
    static_path = os.path.join(STATIC_EXPORTS, f"invoice_{inv_id}.pdf")
    generate_invoice_pdf(inv_dict, static_path)

    # 3. Save to exports
    exp_filename = f"Invoice_{clean_no}_{inv_dict['invoice_date']}.pdf"
    exp_path = os.path.join(EXPORTS, exp_filename)
    generate_invoice_pdf(inv_dict, exp_path)

conn.close()
print("All Haj Salah PDFs regenerated successfully with the new RTL layout and unified summary!")
