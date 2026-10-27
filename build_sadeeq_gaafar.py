import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import sqlite3
import os

WORK_DIR = r"I:\خالي أحمد جلال"
DB_PATH = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\data\marble_erp.db"

FONT_FAMILY = "Calibri"
font_title = Font(name=FONT_FAMILY, size=15, bold=True, color="1E3A8A")
font_section = Font(name=FONT_FAMILY, size=12, bold=True, color="FFFFFF")
font_header = Font(name=FONT_FAMILY, size=11, bold=True, color="1E293B")
font_regular = Font(name=FONT_FAMILY, size=11, color="0F172A")
font_bold = Font(name=FONT_FAMILY, size=11, bold=True, color="0F172A")
font_total = Font(name=FONT_FAMILY, size=12, bold=True, color="991B1B")

fill_navy = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
fill_gold_hdr = PatternFill(start_color="FEF08A", end_color="FEF08A", fill_type="solid")
fill_green_hdr = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
fill_pink_tot = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
fill_light_gray = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

thin_gray = Side(border_style="thin", color="CBD5E1")
thick_dark = Side(border_style="medium", color="1E3A8A")
border_cell = Border(left=thin_gray, right=thin_gray, top=thin_gray, bottom=thin_gray)
border_header = Border(left=thin_gray, right=thin_gray, top=thick_dark, bottom=thick_dark)

align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
align_right = Alignment(horizontal="right", vertical="center")

def style_range(ws, start_row, start_col, end_row, end_col, font=None, fill=None, border=None, alignment=None, num_format=None):
    for r in range(start_row, end_row + 1):
        for c in range(start_col, end_col + 1):
            cell = ws.cell(row=r, column=c)
            if font: cell.font = font
            if fill: cell.fill = fill
            if border: cell.border = border
            if alignment: cell.alignment = alignment
            if num_format: cell.number_format = num_format

def auto_fit_columns(ws):
    ws.views.sheetView[0].rightToLeft = True
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val = str(cell.value or "")
            if "\n" in val:
                val = max(val.split("\n"), key=len)
            max_len = max(max_len, len(val))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

def build_sadeeq():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "كشف حساب صديق جعفر"
    ws.views.sheetView[0].rightToLeft = True

    # Title
    ws.merge_cells("A1:G1")
    ws.cell(1, 1, "سجل وحساب صديق جعفر الشامل - النسخة المطورة 2026").font = font_title
    ws.cell(1, 1).alignment = align_center
    ws.row_dimensions[1].height = 32

    # Section 1: الفواتير بالأسماء الأصلية
    ws.merge_cells("A3:G3")
    ws.cell(3, 1, "١. فواتير البضاعة والتوريد (بالمسميات الأصلية من الدفاتر)").font = font_section
    ws.cell(3, 1).fill = fill_navy
    ws.cell(3, 1).alignment = align_right
    ws.row_dimensions[3].height = 24

    headers = ["م", "اسم الفاتورة والبيان", "التاريخ", "المبلغ (ج.م)", "بيان الشغل / الجهة", "الواصل منها", "الحالة"]
    for c_idx, h in enumerate(headers, 1):
        ws.cell(4, c_idx, h)
    style_range(ws, 4, 1, 4, len(headers), font=font_header, fill=fill_gold_hdr, border=border_header, alignment=align_center)
    ws.row_dimensions[4].height = 24

    invoices = [
        ("جعفر - حساب قديم", "رصيد سابق", 8000.00, "باقي قديم مرحل", "خالص"),
        ("فاتورة 1", "07/11/2026", 129066.00, "أحمد وحسين (صني وسيلفيا 138 طاولة 774 م٢)", "خالص"),
        ("فاتورة 2", "07/11/2026", 127981.00, "شغل أدهم (طاولات ممتازة)", "خالص"),
        ("فاتورة 3", "22/07/2026", 120194.00, "شغل أدهم (توريد صني)", "خالص"),
        ("فاتورة 4", "01/08/2026", 125971.00, "شغل أدهم وعلي", "خالص"),
        ("فاتوره 5", "13/09/2026", 129569.00, "الشيخ طه", "تحت الحساب")
    ]

    r = 5
    for idx, (name, dt, amt, notes, status) in enumerate(invoices, 1):
        ws.cell(r, 1, idx)
        ws.cell(r, 2, name)
        ws.cell(r, 3, dt)
        ws.cell(r, 4, amt)
        ws.cell(r, 5, notes)
        ws.cell(r, 6, amt if status == "خالص" else 0)
        ws.cell(r, 7, status)
        style_range(ws, r, 1, r, 7, font=font_regular, border=border_cell, alignment=align_center)
        ws.cell(r, 2).alignment = align_right
        ws.cell(r, 4).number_format = "#,##0.00"
        ws.cell(r, 6).number_format = "#,##0.00"
        if r % 2 == 0:
            style_range(ws, r, 1, r, 7, fill=fill_light_gray)
        r += 1

    # Total row
    ws.cell(r, 2, "إجمالي فواتير صديق جعفر").font = font_total
    ws.cell(r, 4, f"=SUM(D5:D{r-1})").font = font_total
    ws.cell(r, 4).number_format = "#,##0.00"
    ws.cell(r, 6, f"=SUM(F5:F{r-1})").font = font_total
    ws.cell(r, 6).number_format = "#,##0.00"
    style_range(ws, r, 1, r, 7, fill=fill_pink_tot, border=border_header, alignment=align_center)
    ws.row_dimensions[r].height = 26

    # Section 2: المقبوضات والدفعات الواصلة
    r += 3
    ws.merge_cells(f"A{r}:G{r}")
    ws.cell(r, 1, "٢. سجل الدفعات والمقبوضات الواصلة من صديق جعفر").font = font_section
    ws.cell(r, 1).fill = PatternFill(start_color="15803D", end_color="15803D", fill_type="solid")
    ws.cell(r, 1).alignment = align_right
    ws.row_dimensions[r].height = 24

    r += 1
    pay_headers = ["م", "البيان الأصلي", "التاريخ", "المبلغ بالجنيه", "طريقة السداد", "ملاحظات الدفعة"]
    for c_idx, h in enumerate(pay_headers, 1):
        ws.cell(r, c_idx, h)
    style_range(ws, r, 1, r, len(pay_headers), font=font_header, fill=fill_green_hdr, border=border_header, alignment=align_center)
    ws.row_dimensions[r].height = 24

    payments = [
        ("واصل منه", "19/07/2026", 100000.00, "نقدياً", "دفعة يوليو الأولى"),
        ("واصل منه", "28/07/2026", 40000.00, "نقدياً", "دفعة يوليو الثانية"),
        ("واصل منه", "17/08/2026", 50000.00, "نقدياً", "دفعة أغسطس الأولى"),
        ("واصل منه", "09/08/2026", 50000.00, "نقدياً", "دفعة أغسطس الثانية"),
        ("واصل منه", "23/09/2026", 150000.00, "نقدياً", "دفعة سبتمبر الكبرى"),
        ("واصل منه", "13/10/2026", 100000.00, "نقدياً", "دفعة أكتوبر")
    ]

    p_start = r + 1
    r = p_start
    for idx, (b, dt, amt, meth, nts) in enumerate(payments, 1):
        ws.cell(r, 1, idx)
        ws.cell(r, 2, b)
        ws.cell(r, 3, dt)
        ws.cell(r, 4, amt)
        ws.cell(r, 5, meth)
        ws.cell(r, 6, nts)
        style_range(ws, r, 1, r, 6, font=font_regular, border=border_cell, alignment=align_center)
        ws.cell(r, 2).alignment = align_right
        ws.cell(r, 4).number_format = "#,##0.00"
        if r % 2 == 0:
            style_range(ws, r, 1, r, 6, fill=fill_light_gray)
        r += 1

    # Total Payments
    ws.cell(r, 2, "إجمالي الواصل والمسدد").font = Font(name=FONT_FAMILY, size=12, bold=True, color="15803D")
    ws.cell(r, 4, f"=SUM(D{p_start}:D{r-1})").font = Font(name=FONT_FAMILY, size=12, bold=True, color="15803D")
    ws.cell(r, 4).number_format = "#,##0.00"
    style_range(ws, r, 1, r, 6, fill=fill_green_hdr, border=border_header, alignment=align_center)
    ws.row_dimensions[r].height = 26

    # Summary Row: المتبقي
    r += 1
    ws.cell(r, 2, "الرصيد المتبقي عليه").font = font_total
    ws.cell(r, 4, f"=D11-D{r-1}").font = font_total
    ws.cell(r, 4).number_format = "#,##0.00"
    style_range(ws, r, 1, r, 6, fill=fill_pink_tot, border=border_header, alignment=align_center)
    ws.row_dimensions[r].height = 28

    auto_fit_columns(ws)
    target_path = os.path.join(WORK_DIR, "صديق جعفر", "حساب صديق جعفر - النسخة المطورة 2026.xlsx")
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    wb.save(target_path)
    print(f"Saved: {target_path}")

def sync_sadeeq_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Ensure client exists
    c.execute("INSERT OR IGNORE INTO clients (name, phone, address, notes) VALUES (?, ?, ?, ?)",
              ("صديق جعفر", "01000000008", "القاهرة", "عميل رئيسي - طاولات صني وسيلفيا"))

    sadeeq_invoices = [
        ("جعفر - حساب قديم", "2026-05-01", 8000.00, "باقي قديم مرحل من الدفاتر"),
        ("فاتورة 1 (احمد وحسين)", "2026-11-07", 129066.00, "138 طاولة صني وسيلفيا مسطح 774 م٢"),
        ("فاتورة 2 (ادهم)", "2026-11-07", 127981.00, "طاولات توريد شغل أدهم"),
        ("فاتورة 3 (ادهم)", "2026-07-22", 120194.00, "طاولات توريد شغل أدهم"),
        ("فاتورة 4 (ادهم وعلي)", "2026-08-01", 125971.00, "طاولات توريد أدهم وعلي"),
        ("فاتوره 5 (الشيخ طه)", "2026-09-13", 129569.00, "توريدات رخام الشيخ طه")
    ]
    for inv_name, dt, amt, nts in sadeeq_invoices:
        c.execute("""
        INSERT OR IGNORE INTO invoices (invoice_no, invoice_date, client_name, driver_name, car_no, total_pieces, total_area, total_amount, net_amount, paid_amount, remaining_amount, notes, status)
        VALUES (?, ?, 'صديق جعفر', '-', '-', 138, 774, ?, ?, ?, 0, ?, 'معتمدة')
        """, (inv_name, dt, amt, amt, amt, nts))

    sadeeq_payments = [
        ("2026-07-19", 100000.00, "دفعة نقدية واصل 1"),
        ("2026-07-28", 40000.00, "دفعة نقدية واصل 2"),
        ("2026-08-17", 50000.00, "دفعة نقدية واصل 3"),
        ("2026-08-09", 50000.00, "دفعة نقدية واصل 4"),
        ("2026-09-23", 150000.00, "دفعة نقدية واصل 5"),
        ("2026-10-13", 100000.00, "دفعة نقدية واصل 6")
    ]
    for p_dt, amt, nts in sadeeq_payments:
        c.execute("""
        INSERT INTO client_payments (client_name, payment_date, amount, currency, exchange_rate, amount_egp, payment_method, notes)
        VALUES ('صديق جعفر', ?, ?, 'EGP', 1, ?, 'نقداً', ?)
        """, (p_dt, amt, amt, nts))

    conn.commit()
    conn.close()
    print("Sadeeq Gaafar synced to DB successfully!")

if __name__ == "__main__":
    build_sadeeq()
    sync_sadeeq_db()
