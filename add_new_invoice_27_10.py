import sqlite3
import os
import re
from pdf_invoice_generator import generate_invoice_pdf
from excel_exporter import create_invoice_excel
from calc_new_invoice import invoice_rows, grand_pieces, grand_area, grand_amount

DB_PATH = "data/marble_erp.db"
HAJ_SALAH_DIR = r"I:\خالي أحمد جلال\الحاج صلاح"
STATIC_EXPORTS = "static/exports"
EXPORTS = "exports"

os.makedirs(STATIC_EXPORTS, exist_ok=True)
os.makedirs(EXPORTS, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# 1. Insert or update the new 27/10 invoice in database
inv_no = "فاتورة 27 / 10 (2)"
inv_date = "2026-10-27"
client_name = "الحاج صلاح"

c.execute("SELECT id FROM invoices WHERE invoice_no = ? AND client_name = ?", (inv_no, client_name))
existing = c.fetchone()

if existing:
    inv_id = existing['id']
    c.execute("""
    UPDATE invoices SET
        invoice_date = ?,
        total_pieces = ?,
        total_area = ?,
        total_amount = ?,
        net_amount = ?,
        remaining_amount = ?,
        notes = ?
    WHERE id = ?
    """, (inv_date, grand_pieces, grand_area, grand_amount, grand_amount, grand_amount, 
          "جرانيت (رويال 470 + جندولة 480 + نيوحلايب 355) + 3 شرائح رويال فري + سيلفيا 3 سم (40 طاولة @ 190)", inv_id))
    c.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (inv_id,))
    print(f"Updated existing invoice ID: {inv_id}")
else:
    c.execute("""
    INSERT INTO invoices (
        invoice_no, invoice_date, client_name, driver_name, car_no, loading_place, supervisor,
        total_pieces, total_area, total_amount, discount, net_amount, paid_amount, remaining_amount,
        status, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inv_no, inv_date, client_name, "-", "-", "-", "-",
        grand_pieces, grand_area, grand_amount, 0.0, grand_amount, 0.0, grand_amount,
        "مفتوحة (نشطة)", "جرانيت (رويال 470 + جندولة 480 + نيوحلايب 355) + 3 شرائح رويال فري + سيلفيا 3 سم (40 طاولة @ 190)"
    ))
    inv_id = c.lastrowid
    print(f"Inserted new invoice with ID: {inv_id}")

for r in invoice_rows:
    c.execute("""
    INSERT INTO invoice_items (
        invoice_id, row_index, package_no, block_no, material_name,
        qty, length, width, area, price, total, notes, is_free
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inv_id, r['row_index'], r['package_no'], r['block_no'], r['material_name'],
        r['qty'], r['length'], r['width'], r['area'], r['price'], r['total'],
        r['notes'], 1 if 'فري' in r['material_name'] else 0
    ))

conn.commit()

# 2. Build invoice dict for generator
c.execute("SELECT * FROM invoices WHERE id = ?", (inv_id,))
inv_dict = dict(c.fetchone())
c.execute("SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY row_index ASC", (inv_id,))
inv_dict['items'] = [dict(r) for r in c.fetchall()]

# 3. Export PDF (Landscape) & Excel (Unified Summary) to Haj Salah Drive folder
file_base = "2026-10-27 - فاتورة 27-10 (2)"
pdf_drive = os.path.join(HAJ_SALAH_DIR, f"{file_base}.pdf")
excel_drive = os.path.join(HAJ_SALAH_DIR, f"{file_base}.xlsx")

generate_invoice_pdf(inv_dict, pdf_drive)
create_invoice_excel(inv_dict, excel_drive)
print(f"Saved to Drive: {pdf_drive}")
print(f"Saved to Drive: {excel_drive}")

# Also save to static/exports and exports
clean_inv_no = re.sub(r'[\s/\\:*?"<>|]+', '-', inv_no).strip('-')
generate_invoice_pdf(inv_dict, os.path.join(STATIC_EXPORTS, f"invoice_{inv_id}.pdf"))
generate_invoice_pdf(inv_dict, os.path.join(EXPORTS, f"Invoice_{clean_inv_no}_{inv_date}.pdf"))
create_invoice_excel(inv_dict, os.path.join(EXPORTS, f"Invoice_{clean_inv_no}_{inv_date}.xlsx"))

# 4. Now regenerate ALL Haj Salah PDFs to Landscape with Unified Summary
c.execute("SELECT * FROM invoices WHERE client_name = ? ORDER BY invoice_date ASC, id ASC", (client_name,))
all_invoices = c.fetchall()

print(f"\nRegenerating all {len(all_invoices)} invoices for Haj Salah in Landscape...")
for inv_row in all_invoices:
    i_dict = dict(inv_row)
    i_id = i_dict['id']
    c.execute("SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY row_index ASC", (i_id,))
    i_dict['items'] = [dict(r) for r in c.fetchall()]

    clean_no = re.sub(r'[\s/\\:*?"<>|]+', '-', i_dict['invoice_no']).strip('-')
    name_clean = f"{i_dict['invoice_date']} - {clean_no}"
    
    # Save Landscape PDF to Drive
    p_drive = os.path.join(HAJ_SALAH_DIR, f"{name_clean}.pdf")
    generate_invoice_pdf(i_dict, p_drive)
    
    # Save Excel to Drive
    x_drive = os.path.join(HAJ_SALAH_DIR, f"{name_clean}.xlsx")
    create_invoice_excel(i_dict, x_drive)

    # Static exports for web
    generate_invoice_pdf(i_dict, os.path.join(STATIC_EXPORTS, f"invoice_{i_id}.pdf"))

conn.close()
print("All invoices successfully processed and saved to Drive!")
