import os
import openpyxl
import sqlite3
import re
from datetime import datetime
from database import init_db, get_connection

DATA_DIR = r"I:\خالي أحمد جلال"

def seed():
    init_db()
    conn = get_connection()
    c = conn.cursor()

    # Pre-populate materials
    base_materials = [
        ("نيو حلايب 2 سم", "2 سم", 325, "م٢"),
        ("نيو حلايب 3 سم", "3 سم", 380, "م٢"),
        ("نيو حلايب 1.8 سم", "1.8 سم", 270, "م٢"),
        ("نيو حلايب 2.8 سم", "2.8 سم", 320, "م٢"),
        ("حلايب 2 سم", "2 سم", 450, "م٢"),
        ("حلايب 3 سم", "3 سم", 520, "م٢"),
        ("جندولا 2 سم", "2 سم", 355, "م٢"),
        ("جندولا 3 سم", "3 سم", 420, "م٢"),
        ("صني 3 سم", "3 سم", 165, "م٢"),
        ("صني 2 سم", "2 سم", 145, "م٢"),
        ("صني غشيم 3 سم", "3 سم", 150, "م٢"),
        ("صني غشيم 2 سم", "2 سم", 117, "م٢"),
        ("سيلفيا 3 سم", "3 سم", 170, "م٢"),
        ("سيلفيا 2 سم", "2 سم", 155, "م٢"),
        ("سيلفيا غشيم", "3 سم", 150, "م٢"),
        ("ريشه 3 سم", "3 سم", 175, "م٢"),
        ("رمادي", "2 سم", 75, "م٢"),
        ("ترابيع نيو حلايب", "2 سم", 290, "م٢"),
        ("ترابيع صني", "2 سم", 135, "م٢"),
        ("أحمر أسواني", "3 سم", 650, "م٢"),
        ("روزا النصر", "2 سم", 340, "م٢")
    ]
    for name, thick, price, unit in base_materials:
        c.execute("""
        INSERT OR IGNORE INTO materials (name, default_thickness, default_price, unit)
        VALUES (?, ?, ?, ?)
        """, (name, thick, price, unit))

    # Pre-populate core clients
    clients = [
        ("الحاج صلاح", "01000000001", "القاهرة / شق الثعبان", 50000, "عميل رئيسي مستمر"),
        ("الحاج جعفر", "01000000002", "القاهرة", 0, "عميل جرارات ونيو حلايب وجندولا"),
        ("الحاج نور", "01000000003", "القاهرة", 15000, "عميل سيلفيا وصني"),
        ("الحاج عدنان", "01000000004", "القاهرة", 0, "عميل طاولات وترابيع"),
        ("الحاج راضي", "01000000005", "ليبيا / طرابلس", 62695, "عميل تصدير - تعامل بالدينار والجنيه"),
        ("أحمد رضا", "01000000006", "القاهرة", 87000, "عميل ترابيع وصني وسيلفيا"),
        ("مصطفي شيخون", "01000000007", "المنيا", 0, "عميل ريشة وسيلفيا"),
        ("صديق جعفر", "01000000008", "القاهرة", 0, "عميل صني وريشة"),
        ("اسماعيل غيث", "01000000009", "ليبيا", 144700, "عميل وتوريدات"),
        ("عيسي غيث", "01000000010", "ليبيا", 2000, "عميل تصدير رخام"),
        ("الحاج ابراهيم", "01000000011", "القاهرة", 0, "عميل فواتير"),
        ("أدهم", "01000000012", "القاهرة", 0, "عميل ومصنع"),
        ("سبهاوي", "01000000013", "ليبيا / سبها", 0, "عميل تصدير شركة الأهرامات"),
        ("الشيخ طه", "01000000014", "القاهرة", 22101, "شغل وتوريدات"),
        ("أحمد البكري", "01000000015", "القاهرة", 0, "عميل فواتير"),
        ("الهندي", "01000000016", "القاهرة", 52000, "مورد ومصنع")
    ]
    for name, phone, addr, op_bal, notes in clients:
        c.execute("""
        INSERT OR IGNORE INTO clients (name, phone, address, opening_balance, notes)
        VALUES (?, ?, ?, ?, ?)
        """, (name, phone, addr, op_bal, notes))

    # Pre-populate partner expenses & collections from حساب احمد وحسين.xlsx
    partner_expenses = [
        ("أحمد", "2026-05-15", "إكراميات", "اكراميه فاتورة 1", 1600, "سائقين وعمال", "فاتورة 1"),
        ("أحمد", "2026-05-18", "إكراميات", "اكراميه فاتورة 2", 2200, "عمال", "فاتورة 2"),
        ("أحمد", "2026-05-20", "ونش", "وناش وادري", 750, "ونش", "تحميل"),
        ("أحمد", "2026-05-22", "نقل", "تعديل جمل", 1200, "نقل", "شغل"),
        ("أحمد", "2026-05-25", "بياتة وضيافة", "واصل للسواق بياته وشاي", 500, "سائق", "مبيت"),
        ("أحمد", "2026-05-28", "إكراميات", "اكراميه فاتوره 4", 2100, "عمال", "فاتورة 4"),
        ("أحمد", "2026-06-01", "نقل", "نقل خامات", 600, "سائق", "مشوار")
    ]
    for p_name, p_date, cat, desc, amt, recip, nts in partner_expenses:
        c.execute("""
        INSERT INTO partner_expenses (partner_name, expense_date, category, description, amount, recipient, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (p_name, p_date, cat, desc, amt, recip, nts))

    partner_collections = [
        ("حسين", "2026-05-10", "واصل من حسين لاحمد ليد أحمد", 300000, "EGP", 1, 300000, "دفعة نقدية"),
        ("حسين", "2026-05-15", "واصل من حسين لاحمد ليد أحمد", 200000, "EGP", 1, 200000, "دفعة نقدية"),
        ("حسين", "2026-05-19", "واصل من الشغل دينار ليبي", 44345, "LYD", 5.43, 240793.35, "تحويل عملة"),
        ("أحمد", "2026-05-20", "واصل من الشغل كاش مصري", 300000, "EGP", 1, 300000, "دفعة من إيرادات الشغل")
    ]
    for p_name, c_date, src, amt, curr, rate, egp, nts in partner_collections:
        c.execute("""
        INSERT INTO partner_collections (partner_name, collection_date, source_description, amount, currency, exchange_rate, amount_egp, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (p_name, c_date, src, amt, curr, rate, egp, nts))

    # Pre-populate factory operations (نشر وتلميع)
    factories = [
        ("عرب مساعد", "2026-05-01", "نشر", "طاولات رخام غشيم", 23.39, 1050, 24559.5, 20000, 4559.5, "سمك 3 سم"),
        ("عرب مساعد", "2026-05-01", "تلميع", "طاولات تلميع لامع 75%", 678.695, 17, 11537.82, 10000, 1537.82, "تلميع"),
        ("عرب مساعد", "2026-05-05", "نشر", "طاولات رخام غشيم", 18.15, 1050, 19057.5, 19057.5, 0, "خالص"),
        ("مصنع البطل", "2026-05-12", "نشر وتلميع", "نيو حلايب وجندولا", 744.4, 280, 208432, 150000, 58432, "فاتورة رقم 4"),
        ("جبال زمزم (محمد اسماعيل)", "2026-05-08", "نشر", "رمادي ونيو جندولا", 126.27, 75, 20063.8, 13810, 6253.8, "واصل على 3 دفعات")
    ]
    for fac, f_date, op, mat, mtrs, pr, tot, pd, rem, nts in factories:
        c.execute("""
        INSERT INTO factory_accounts (factory_name, op_date, operation_type, material_name, meters, unit_price, total_amount, paid_amount, remaining_amount, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (fac, f_date, op, mat, mtrs, pr, tot, pd, rem, nts))

    # Now let's import the iconic real invoice: أحمد جلال جديد\14-4-2026.xlsx
    real_inv_path = os.path.join(DATA_DIR, "أحمد جلال جديد", "14-4-2026.xlsx")
    if os.path.exists(real_inv_path):
        try:
            wb = openpyxl.load_workbook(real_inv_path, data_only=True)
            ws = wb.active
            client_name = "الحاج جعفر"
            inv_date = "2026-04-14"
            driver_name = str(ws.cell(row=1, column=8).value or "أحمد / 01017828662")
            car_no = str(ws.cell(row=2, column=3).value or "جرار نقل ثقيل")
            loading_place = str(ws.cell(row=2, column=5).value or "المصنع / شق الثعبان")
            supervisor = str(ws.cell(row=2, column=8).value or "-")
            invoice_no = "INV-2026-001"

            # Insert invoice record
            c.execute("""
            INSERT OR REPLACE INTO invoices (invoice_no, invoice_date, client_name, driver_name, car_no, loading_place, supervisor, total_pieces, total_area, total_amount, net_amount, paid_amount, remaining_amount, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (invoice_no, inv_date, client_name, driver_name, car_no, loading_place, supervisor, 480, 1094.65, 384348.6, 384348.6, 200000, 184348.6, "فاتورة جرار حمولة جندولا ونيو حلايب وحلايب"))
            inv_id = c.lastrowid

            # Insert items
            for r in range(4, 30):
                mat = str(ws.cell(row=r, column=3).value or "").strip()
                if not mat or "الإجمالي" in mat:
                    continue
                qty = float(ws.cell(row=r, column=4).value or 0)
                length = float(ws.cell(row=r, column=5).value or 0)
                width = float(ws.cell(row=r, column=6).value or 0)
                area = float(ws.cell(row=r, column=7).value or 0)
                price = float(ws.cell(row=r, column=8).value or 0)
                total = float(ws.cell(row=r, column=9).value or 0)
                note = str(ws.cell(row=r, column=10).value or "").strip()
                pkg = str(ws.cell(row=r, column=1).value or "").strip()
                blk = str(ws.cell(row=r, column=2).value or "").strip()

                c.execute("""
                INSERT INTO invoice_items (invoice_id, row_index, package_no, block_no, material_name, qty, length, width, area, price, total, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (inv_id, r-3, pkg, blk, mat, qty, length, width, area, price, total, note))

            print("Successfully imported sample invoice 14-4-2026.xlsx")
        except Exception as e:
            print("Error importing real invoice:", e)

    # Also import one from الحاج صلاح
    salah_inv = os.path.join(DATA_DIR, "الحاج صلاح", "11-10-2026.xlsx")
    if os.path.exists(salah_inv):
        try:
            wb = openpyxl.load_workbook(salah_inv, data_only=True)
            ws = wb.active
            c.execute("""
            INSERT OR REPLACE INTO invoices (invoice_no, invoice_date, client_name, driver_name, car_no, loading_place, supervisor, total_pieces, total_area, total_amount, net_amount, paid_amount, remaining_amount, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("INV-2026-002", "2026-11-10", "الحاج صلاح", "عادل السائق", "ط ر ق 749", "المستودع", "-", 137, 744.41, 122828.21, 122828.21, 100000, 22828.21, "توريد صني 3 سم"))
            inv_id2 = c.lastrowid
            
            items_salah = [
                ("1", "صني 3 سم", 105, 2.87, 1.93, 581.61, 165, 95964.91),
                ("2", "صني 3 سم", 21, 2.80, 1.80, 105.84, 165, 17463.60),
                ("3", "صني 3 سم", 11, 2.83, 1.83, 56.97, 165, 9399.70),
            ]
            for idx, mat, q, l, w, ar, pr, tot in items_salah:
                c.execute("""
                INSERT INTO invoice_items (invoice_id, row_index, package_no, block_no, material_name, qty, length, width, area, price, total, notes)
                VALUES (?, ?, '', '', ?, ?, ?, ?, ?, ?, ?, '')
                """, (inv_id2, int(idx), mat, q, l, w, ar, pr, tot))
            print("Successfully imported sample invoice from الحاج صلاح")
        except Exception as e:
            print("Error importing salah invoice:", e)

    # Insert client payments
    payments = [
        ("الحاج جعفر", 1, "2026-04-15", 100000, "EGP", 1, 100000, "تحويل بنكي", "دفعة تحت الحساب"),
        ("الحاج جعفر", 1, "2026-04-20", 100000, "EGP", 1, 100000, "نقداً", "استلام كاش"),
        ("الحاج صلاح", 2, "2026-11-11", 100000, "EGP", 1, 100000, "شيك", "شيك مقبول الدفع رقم 49102"),
        ("الحاج راضي", None, "2026-04-18", 176280, "EGP", 1, 176280, "تحويل", "دفعة من حساب قديم"),
        ("الحاج راضي", None, "2026-04-25", 13000, "LYD", 5.43, 70590, "حوالة ليبية", "13 ألف دينار بسعر صرف 5.43")
    ]
    for cl, i_id, p_dt, amt, cur, rat, egp, mthd, nts in payments:
        c.execute("""
        INSERT INTO client_payments (client_name, invoice_id, payment_date, amount, currency, exchange_rate, amount_egp, payment_method, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cl, i_id, p_dt, amt, cur, rat, egp, mthd, nts))

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed()
