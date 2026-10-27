import sqlite3
import os
from datetime import datetime
from pdf_invoice_generator import generate_invoice_pdf
from excel_exporter import create_invoice_excel
from client_statement_sync import sync_client_statement_excel

DB_PATH = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\data\marble_erp.db"
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Check if invoice already exists
c.execute("SELECT id FROM invoices WHERE invoice_no = 'فاتورة 27 / 10' AND client_name = 'الحاج صلاح'")
row = c.fetchone()

qty = 220.0
length = 0.60
width = 0.30
area = round(qty * length * width, 2) # 39.60 m2
price = 185.0
total = round(area * price, 2) # 7326.0 EGP

if row:
    inv_id = row[0]
    c.execute("""
    UPDATE invoices 
    SET invoice_date = '2026-10-27', total_pieces = ?, total_area = ?, total_amount = ?, 
        net_amount = ?, remaining_amount = ?, status = 'جارية', notes = 'ترابيع سيلفيا منها 28 صندوق'
    WHERE id = ?
    """, (qty, area, total, total, total, inv_id))
    c.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (inv_id,))
else:
    c.execute("""
    INSERT INTO invoices (
        invoice_no, invoice_date, client_name, driver_name, car_no, 
        total_pieces, total_area, total_amount, discount, net_amount, 
        paid_amount, remaining_amount, notes, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        'فاتورة 27 / 10', '2026-10-27', 'الحاج صلاح', '-', '-',
        qty, area, total, 0.0, total, 0.0, total, 'ترابيع سيلفيا منها 28 صندوق', 'جارية'
    ))
    inv_id = c.lastrowid

c.execute("""
INSERT INTO invoice_items (
    invoice_id, row_index, package_no, block_no, material_name, 
    qty, length, width, area, price, total, is_free, notes
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    inv_id, 1, '28 صندوق', '', 'ترابيع سيلفيا',
    qty, length, width, area, price, total, 0, 'منها 28 صندوق'
))

conn.commit()
conn.close()

# Prepare dictionary for file exports
inv_dict = {
    "id": inv_id,
    "invoice_no": "فاتورة 27 / 10",
    "invoice_date": "2026-10-27",
    "client_name": "الحاج صلاح",
    "driver_name": "-",
    "car_no": "-",
    "total_pieces": qty,
    "total_area": area,
    "total_amount": total,
    "net_amount": total,
    "notes": "ترابيع سيلفيا منها 28 صندوق",
    "items": [
        {
            "package_no": "28 صندوق",
            "material_name": "ترابيع سيلفيا",
            "qty": qty,
            "length": length,
            "width": width,
            "area": area,
            "price": price,
            "total": total,
            "notes": "منها 28 صندوق"
        }
    ]
}

# Save Individual Excel File in Haj Salah folder
client_folder = r"I:\خالي أحمد جلال\الحاج صلاح"
os.makedirs(client_folder, exist_ok=True)
excel_path = os.path.join(client_folder, "2026-10-27 - فاتورة 27-10.xlsx")
create_invoice_excel(inv_dict, excel_path)
print(f"Saved Excel Invoice: {excel_path}")

# Save Individual PDF File (NO SIGNATURES) in Haj Salah folder
pdf_path = os.path.join(client_folder, "2026-10-27 - فاتورة 27-10.pdf")
generate_invoice_pdf(inv_dict, pdf_path)
print(f"Saved PDF Invoice: {pdf_path}")

# Also copy to static/exports so it can be downloaded directly
static_exports = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\static\exports"
os.makedirs(static_exports, exist_ok=True)
generate_invoice_pdf(inv_dict, os.path.join(static_exports, f"invoice_{inv_id}.pdf"))

# Auto-sync Haj Salah master statement Excel file on computer and in bundled_files
sync_client_statement_excel("الحاج صلاح")
print("Haj Salah statement successfully synchronized on disk and in cloud bundle!")
