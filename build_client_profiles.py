import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import sqlite3
import os
from datetime import datetime

WORK_DIR = r"I:\خالي أحمد جلال"
DB_PATH = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\data\marble_erp.db"

# Styling constants for high-end look
FONT_FAMILY = "Calibri"
font_title = Font(name=FONT_FAMILY, size=15, bold=True, color="1E3A8A")
font_section = Font(name=FONT_FAMILY, size=12, bold=True, color="FFFFFF")
font_header = Font(name=FONT_FAMILY, size=11, bold=True, color="1E293B")
font_regular = Font(name=FONT_FAMILY, size=11, color="0F172A")
font_bold = Font(name=FONT_FAMILY, size=11, bold=True, color="0F172A")
font_total = Font(name=FONT_FAMILY, size=12, bold=True, color="991B1B")

fill_navy = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
fill_gold_hdr = PatternFill(start_color="FEF08A", end_color="FEF08A", fill_type="solid")
fill_blue_hdr = PatternFill(start_color="E0E7FF", end_color="E0E7FF", fill_type="solid")
fill_green_hdr = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
fill_pink_tot = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
fill_light_gray = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

thin_gray = Side(border_style="thin", color="CBD5E1")
thick_dark = Side(border_style="medium", color="1E3A8A")
border_cell = Border(left=thin_gray, right=thin_gray, top=thin_gray, bottom=thin_gray)
border_header = Border(left=thin_gray, right=thin_gray, top=thick_dark, bottom=thick_dark)

align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
align_right = Alignment(horizontal="right", vertical="center")
align_left = Alignment(horizontal="left", vertical="center")

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

def build_hajj_salah():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "كشف حساب الحاج صلاح"
    ws.views.sheetView[0].rightToLeft = True

    # Title
    ws.merge_cells("A1:G1")
    ws.cell(1, 1, "سجل وفواتير الحاج صلاح - النسخة المطورة 2026").font = font_title
    ws.cell(1, 1).alignment = align_center
    ws.row_dimensions[1].height = 32

    # Section 1: الفواتير بالأسماء الأصلية
    ws.merge_cells("A3:G3")
    ws.cell(3, 1, "١. فواتير البضاعة والشغل (بالأرقام والمسميات الأصلية)").font = font_section
    ws.cell(3, 1).fill = fill_navy
    ws.cell(3, 1).alignment = align_right
    ws.row_dimensions[3].height = 24

    headers = ["م", "اسم وبيان الفاتورة", "التاريخ", "المبلغ (ج.م)", "بيان الخامة والملاحظات", "الواصل منها", "الحالة"]
    for c_idx, h in enumerate(headers, 1):
        ws.cell(4, c_idx, h)
    style_range(ws, 4, 1, 4, len(headers), font=font_header, fill=fill_gold_hdr, border=border_header, alignment=align_center)
    ws.row_dimensions[4].height = 24

    invoices = [
        ("الفاتوره الاولي", "14/4", 143837.85, "طاولات وترابيع متنوعة", "خالص"),
        ("الفاتوره الثانيه", "17/4", 147334.58, "طاولات وجرانيت", "خالص"),
        ("الفاتوره الثالثه", "6/5", 146497.43, "توريد رخام", "خالص"),
        ("فاتورة الترابيع", "30/5", 494469.00, "ترابيع مصنع", "خالص"),
        ("فاتوره 4", "4/6", 461503.99, "طاولات وكتل", "خالص"),
        ("فاتورة بتاريخ 30 / 7", "30/7", 123186.50, "توريدات يوليو", "خالص"),
        ("فاتورة 19 / 9", "17/9", 118650.00, "توريدات سبتمبر", "خالص"),
        ("فاتورة 26 / 9", "26/9", 125073.70, "جرارات ورخام", "خالص"),
        ("فاتوره 9 / 10", "9/10", 126485.00, "طاولات شق التعبان", "خالص"),
        ("فاتوره 2 / 11", "2/11", 129085.62, "توريد نوفمبر", "خالص"),
        ("فاتوره 6 / 11", "6/11", 114159.98, "رخام نيو حلايب", "خالص"),
        ("فاتوره حلايب 6 / 11", "6/11", 39209.00, "جرانيت حلايب", "خالص"),
        ("فاتوره ترابيع 19/11", "19/11", 156600.00, "ترابيع ممتازة", "خالص"),
        ("فاتوره 19/11", "19/11", 105137.00, "رخام", "خالص"),
        ("فاتوره 2/12", "2/12", 124748.09, "طاولات شهر 12", "خالص"),
        ("فاتوره ترابيع 2/12", "2/12", 156600.00, "ترابيع صني", "خالص"),
        ("فاتوره 28/12", "28/12", 114783.85, "رخام وجرانيت", "خالص"),
        ("فاتورة 17 / 1", "17/1/2026", 116218.07, "توريد يناير", "خالص"),
        ("فاتورة 20 / 1", "20/1/2026", 132144.03, "طاولات ممتازة", "خالص"),
        ("فاتورة 26 / 1", "26/1/2026", 114403.02, "رخام سيلفيا", "خالص"),
        ("فاتورة 5 / 2 سيلفيا", "5/2/2026", 130865.80, "سيلفيا فرز أول", "خالص"),
        ("فاتورة 5 / 2 صني", "5/2/2026", 114805.46, "صني غشيم وملمع", "خالص"),
        ("فاتورة 4 / 2 صني", "4/2/2026", 114125.54, "صني طاولات", "خالص"),
        ("فاتورة 9 / 2", "9/2/2026", 375698.71, "توريد كتل وبلوكات", "خالص"),
        ("فاتورة 3 / 3", "3/3/2026", 192549.60, "حساب ليبي بـ 30850 دينار في سعر 5.70", "خالص"),
        ("فاتورة 12/4", "12/4/2026", 115468.11, "204 متر نيو حلايب × 85 = 17340 ليبي", "خالص"),
        ("فاتورة 30/4", "30/4/2026", 131381.00, "طاولات + ديسكات جلخ ومنشار 790", "خالص"),
        ("ترابيع 30/4", "30/4/2026", 193320.00, "ترابيع فرز أول", "خالص"),
        ("فاتورة 11/5", "11/5/2026", 125763.70, "طاولات مايو", "خالص"),
        ("فاتورة 11/5", "11/5/2026", 132920.70, "توريدات نيو حلايب", "خالص"),
        ("فاتورة 14/6", "14/6/2026", 121652.40, "توريد يونيو", "خالص"),
        ("فاتورة 16/6", "16/6/2026", 121015.82, "رخام وجرانيت", "خالص"),
        ("فاتورة 5/7", "5/7/2026", 138783.80, "طاولات", "خالص"),
        ("فاتورة 13/8", "13/8/2026", 120426.06, "جرانيت نيو حلايب", "خالص"),
        ("فاتورة 16/8", "16/8/2026", 120806.00, "طاولات", "خالص"),
        ("فاتورة 26/8", "26/8/2026", 138833.00, "طاولات سيلفيا وصني", "خالص"),
        ("فاتورة 23 / 9", "23/9/2026", 121755.00, "جديد - توريدات سبتمبر", "مسدد 150000"),
        ("فاتورة 23 / 9", "23/9/2026", 122755.00, "جديد - توريدات سبتمبر", "مسدد 132500"),
        ("فاتورة 3 / 10", "3/10/2026", 125242.00, "جديد - توريدات أكتوبر", "تحت التصفية"),
        ("فاتورة 11 / 10", "11/10/2026", 122828.00, "جديد - توريدات أكتوبر", "تحت التصفية")
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
    ws.cell(r, 2, "الإجمالي الكلي للفواتير").font = font_total
    ws.cell(r, 4, f"=SUM(D5:D{r-1})").font = font_total
    ws.cell(r, 4).number_format = "#,##0.00"
    ws.cell(r, 6, f"=SUM(F5:F{r-1})").font = font_total
    ws.cell(r, 6).number_format = "#,##0.00"
    style_range(ws, r, 1, r, 7, fill=fill_pink_tot, border=border_header, alignment=align_center)
    ws.row_dimensions[r].height = 26

    # Section 2: المقبوضات والدفعات الواصلة
    r += 3
    ws.merge_cells(f"A{r}:G{r}")
    ws.cell(r, 1, "٢. سجل الدفعات والمقبوضات الواصلة من الحاج صلاح").font = font_section
    ws.cell(r, 1).fill = PatternFill(start_color="15803D", end_color="15803D", fill_type="solid")
    ws.cell(r, 1).alignment = align_right
    ws.row_dimensions[r].height = 24

    r += 1
    pay_headers = ["م", "البيان الأصلي", "التاريخ", "المبلغ بالجنيه", "طريقة الدفع / العملة", "ملاحظات وتفاصيل"]
    for c_idx, h in enumerate(pay_headers, 1):
        ws.cell(r, c_idx, h)
    style_range(ws, r, 1, r, len(pay_headers), font=font_header, fill=fill_green_hdr, border=border_header, alignment=align_center)
    ws.row_dimensions[r].height = 24

    payments = [
        ("واصل كاش", "دفعة أولى", 189650.00, "نقدياً", "دفعة سابقة"),
        ("واصل", "دفعة ثانية", 220700.00, "نقدياً", "دفعة سابقة"),
        ("واصل", "الأربعاء 14/5", 200000.00, "نقدياً", "إيصال تسليم"),
        ("واصل", "16/6/2025", 500000.00, "تحويل بنكي / كاش", "دفعة نصف مليون"),
        ("واصل", "21/7", 150000.00, "نقدياً", "دفعة يوليو"),
        ("واصل", "تسوية", 133292.85, "نقدياً", "تصفية حساب سابق"),
        ("واصل منه", "17/9", 200000.00, "نقدياً", "دفعة سبتمبر"),
        ("واصل منه", "26/9", 125000.00, "نقدياً", "دفعة سبتمبر"),
        ("واصل منه", "11/11/2025", 200000.00, "نقدياً", "دفعة نوفمبر"),
        ("واصل منه", "16/11/2025", 153000.00, "نقدياً", "دفعة نوفمبر"),
        ("واصل منه", "5/1/2026", 350000.00, "نقدياً", "دفعة يناير"),
        ("واصل منه", "26/1/2026", 150000.00, "نقدياً", "دفعة يناير"),
        ("واصل منه", "1/2/2026", 138000.00, "نقدياً", "دفعة فبراير"),
        ("واصل منه", "18/2/2026", 500000.00, "نقدياً", "دفعة نصف مليون"),
        ("واصل منه", "2/3/2026", 64218.00, "دينار ليبي", "تحويل 15,400 دينار × 4.17 = 64,218 ج.م"),
        ("واصل منه", "20/3/2026", 200000.00, "نقدياً", "دفعة مارس"),
        ("واصل منه", "12/4/2026", 260000.00, "نقدياً", "دفعة أبريل"),
        ("واصل منه", "7/5/2026", 250000.00, "نقدياً", "دفعة مايو"),
        ("واصل منه", "16/5/2026", 350000.00, "نقدياً", "دفعة مايو"),
        ("واصل منه", "30/6/2026", 150000.00, "نقدياً", "دفعة يونيو"),
        ("واصل منه", "6/7/2026", 150000.00, "نقدياً", "دفعة يوليو"),
        ("واصل منه", "10/7/2026", 150000.00, "نقدياً", "دفعة يوليو"),
        ("واصل منه", "16/7/2026", 100000.00, "نقدياً", "دفعة يوليو"),
        ("واصل منه (جديد)", "17/9/2026", 200000.00, "نقدياً", "دفعة سبتمبر 2026"),
        ("واصل منه (جديد)", "26/9/2026", 130000.00, "نقدياً", "دفعة سبتمبر 2026"),
        ("واصل منه (جديد)", "1/10/2026", 50000.00, "نقدياً", "دفعة أكتوبر 2026"),
        ("واصل منه (أخير)", "أكتوبر 2026", 150000.00, "نقدياً", "من حساب الـ 4 فواتير الأخيرة"),
        ("واصل منه (أخير)", "أكتوبر 2026", 132500.00, "نقدياً", "من حساب الـ 4 فواتير الأخيرة")
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

    auto_fit_columns(ws)
    target_path = os.path.join(WORK_DIR, "الحاج صلاح", "حساب الحاج صلاح - النسخة المطورة 2026.xlsx")
    wb.save(target_path)
    print(f"Saved: {target_path}")

def build_ahmed_reda():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "كشف حساب أحمد رضا"
    ws.views.sheetView[0].rightToLeft = True

    # Title
    ws.merge_cells("A1:G1")
    ws.cell(1, 1, "سجل وحساب أحمد رضا الشامل - النسخة المطورة 2026").font = font_title
    ws.cell(1, 1).alignment = align_center
    ws.row_dimensions[1].height = 32

    # Section 1: الفواتير بالأسماء الأصلية
    ws.merge_cells("A3:G3")
    ws.cell(3, 1, "١. فواتير البضاعة والشغل (بالأرقام والمسميات الأصلية)").font = font_section
    ws.cell(3, 1).fill = fill_navy
    ws.cell(3, 1).alignment = align_right
    ws.row_dimensions[3].height = 24

    headers = ["م", "اسم وبيان الفاتورة", "التاريخ", "المبلغ (ج.م)", "بيان الشغل والخامة", "الواصل منها", "الحالة"]
    for c_idx, h in enumerate(headers, 1):
        ws.cell(4, c_idx, h)
    style_range(ws, 4, 1, 4, len(headers), font=font_header, fill=fill_gold_hdr, border=border_header, alignment=align_center)
    ws.row_dimensions[4].height = 24

    invoices = [
        ("الفاتوره الاولي", "14/4", 133000.00, "طاولات وترابيع", "خالص"),
        ("الفاتوره الثانيه", "17/4", 136000.00, "رخام وجرانيت", "خالص"),
        ("الفاتوره الثالثه", "5/6", 133571.19, "طاولات صني", "خالص"),
        ("الترابيع", "شغل الترابيع", 87000.00, "إجمالي الأمتار 316.8 و 1760 شريحة و 8 بلتة", "خالص"),
        ("فاتورة يوم 15/6", "15/6", 140126.56, "طاولات ورخام", "خالص"),
        ("فاتورة يوم 30/7", "30/7", 106000.00, "توريد رخام", "خالص"),
        ("فاتورة 14 / 9", "14/9", 109226.00, "توريد سبتمبر", "خالص"),
        ("فاتورة 28 / 9", "28/9", 114374.60, "توريدات خريف", "خالص"),
        ("فاتورة 7 / 10", "7/10", 116290.00, "طاولات", "خالص"),
        ("فاتوره 30 / 10", "30/10", 118160.00, "توريد رخام", "خالص"),
        ("فاتوره 6 / 11", "6/11", 106794.82, "رخام", "خالص"),
        ("صافي القديم", "20/11/2025", 66000.00, "رصيد مرحل الساعة 3.31", "خالص"),
        ("فاتورة 1", "19/11", 98350.00, "توريد نوفمبر", "خالص"),
        ("فاتورة 2", "19/11", 137160.00, "ترابيع صني فرز أول", "خالص"),
        ("فاتورة 3", "2/12", 140400.00, "ترابيع صني", "خالص"),
        ("فاتورة 4", "2/12", 109222.82, "تعديل السيلفيا إلى ريشة والصني 140", "خالص"),
        ("فاتورة 5", "20/12", 106575.00, "طاولات ديسمبر", "خالص"),
        ("فاتورة 6", "17/1/2026", 104971.16, "توريد يناير", "خالص"),
        ("فاتورة 7", "20/1/2026", 121132.03, "طاولات ممتازة", "خالص"),
        ("فاتورة 8", "26/1/2026", 103331.76, "رخام", "خالص"),
        ("فاتورة 9", "5/2/2026", 119960.31, "سيلفيا طاولات", "خالص"),
        ("فاتورة 10", "5/2/2026", 103695.26, "صني طاولات", "خالص"),
        ("فاتورة 11", "4/2/2026", 103081.13, "صني طاولات", "خالص"),
        ("فاتورة 12", "3/3/2026", 117042.40, "ترابيع صني ونيو حلايب (كانت 170042 ناقص 53000)", "خالص"),
        ("فاتورة 13", "12/4/2026", 101034.60, "صني (بالسعر القديم)", "خالص"),
        ("فاتورة 14", "30/4/2026", 177210.00, "ترابيع ريشة على سعر 165", "خالص"),
        ("فاتورة 1 (علي السيوفي)", "14/6/2026", 110593.10, "مشترك مع علي السيوفي", "خالص"),
        ("فاتورة 2 (علي السيوفي)", "16/6/2026", 110014.38, "مشترك مع علي السيوفي", "خالص"),
        ("فاتورة 3 (علي السيوفي)", "29/7/2026", 62315.00, "مشترك مع علي السيوفي", "خالص"),
        ("فاتورة 5 (علي السيوفي)", "3/10/2026", 13576.60, "مشترك مع علي السيوفي", "تحت الحساب")
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
    ws.cell(r, 2, "إجمالي قيمة فواتير أحمد رضا").font = font_total
    ws.cell(r, 4, f"=SUM(D5:D{r-1})").font = font_total
    ws.cell(r, 4).number_format = "#,##0.00"
    ws.cell(r, 6, f"=SUM(F5:F{r-1})").font = font_total
    ws.cell(r, 6).number_format = "#,##0.00"
    style_range(ws, r, 1, r, 7, fill=fill_pink_tot, border=border_header, alignment=align_center)
    ws.row_dimensions[r].height = 26

    # Section 2: المقبوضات والدفعات الواصلة
    r += 3
    ws.merge_cells(f"A{r}:G{r}")
    ws.cell(r, 1, "٢. سجل الدفعات والمبالغ الواصلة لأحمد رضا").font = font_section
    ws.cell(r, 1).fill = PatternFill(start_color="15803D", end_color="15803D", fill_type="solid")
    ws.cell(r, 1).alignment = align_right
    ws.row_dimensions[r].height = 24

    r += 1
    pay_headers = ["م", "البيان الأصلي", "التاريخ", "المبلغ بالجنيه", "المستلم", "ملاحظات الدفعة"]
    for c_idx, h in enumerate(pay_headers, 1):
        ws.cell(r, c_idx, h)
    style_range(ws, r, 1, r, len(pay_headers), font=font_header, fill=fill_green_hdr, border=border_header, alignment=align_center)
    ws.row_dimensions[r].height = 24

    payments = [
        ("وصل ل احمد رضا", "دفعة سابقة", 139650.00, "أحمد رضا", "دفعة نقدية"),
        ("وصل ل احمد رضا", "دفعة سابقة", 100000.00, "أحمد رضا", "دفعة نقدية"),
        ("واصل ل احمد رضا", "دفعة سابقة", 50000.00, "أحمد رضا", "دفعة نقدية"),
        ("واصل ل احمد رضا", "20/6/2025", 100000.00, "أحمد رضا", "دفعة يونيو"),
        ("واصل ل احمد رضا", "16/7/2026", 140000.00, "أحمد رضا", "دفعة يوليو"),
        ("واصل ل احمد رضا", "2/8/2027", 80000.00, "أحمد رضا", "دفعة أغسطس"),
        ("واصل ل احمد رضا", "7/10", 130000.00, "أحمد رضا", "دفعة أكتوبر"),
        ("واصل ل احمد رضا", "28/10", 105000.00, "أحمد رضا", "دفعة أكتوبر"),
        ("واصل ل احمد رضا", "12/11/2025", 180000.00, "أحمد رضا", "دفعة نوفمبر"),
        ("واصل ل احمد رضا", "16/11/2025", 100000.00, "أحمد رضا", "دفعة نوفمبر"),
        ("واصل لاحمد رضا", "5/1/2026", 150000.00, "أحمد رضا", "دفعة يناير"),
        ("واصل لاحمد رضا", "6/1/2026", 100000.00, "أحمد رضا", "دفعة يناير"),
        ("واصل لاحمد رضا", "26/1/2026", 150000.00, "أحمد رضا", "دفعة يناير"),
        ("واصل لاحمد رضا", "1/2/2026", 140000.00, "أحمد رضا", "دفعة فبراير"),
        ("واصل لاحمد رضا", "18/2/2026", 200000.00, "أحمد رضا", "دفعة فبراير"),
        ("واصل لاحمد رضا", "3/3/2026", 53000.00, "أحمد رضا", "حساب نيو حلايب المخصوم"),
        ("واصل لعلي السيوفي", "22/3/2026", 200000.00, "علي السيوفي", "دفعة مشتركة"),
        ("واصل لاحمد رضا", "13/4/2026", 100000.00, "أحمد رضا", "دفعة أبريل"),
        ("واصل لاحمد رضا", "1/5/2026", 95000.00, "أحمد رضا", "دفعة مايو"),
        ("واصل لاحمد رضا", "9/5/2026", 160000.00, "أحمد رضا", "دفعة مايو"),
        ("واصل لاحمد رضا", "16/5/2026", 130000.00, "أحمد رضا", "دفعة مايو"),
        ("واصل من النشر واللمعة", "28/6/2026", 100000.00, "أحمد رضا", "شغل نشر ولمعة"),
        ("واصل من النشر واللمعة", "5/7/2026", 100000.00, "علي السيوفي", "شغل نشر ولمعة"),
        ("واصل من النشر واللمعة", "19/7/2026", 100000.00, "أحمد رضا", "شغل نشر ولمعة"),
        ("واصل لعلي السيوفي", "20/7/2026", 100000.00, "علي السيوفي", "دفعة يوليو"),
        ("واصل لعلي السيوفي", "29/7/2026", 100000.00, "علي السيوفي", "دفعة يوليو"),
        ("واصل لعلي السيوفي", "24/8/2026", 100000.00, "علي السيوفي", "دفعة أغسطس"),
        ("واصل لعلي السيوفي", "24/8/2026", 50000.00, "علي السيوفي", "دفعة أغسطس"),
        ("واصل لعلي السيوفي", "9/9/2026", 100000.00, "علي السيوفي", "دفعة سبتمبر"),
        ("واصل لعلي السيوفي", "9/9/2026", 67980.00, "علي السيوفي", "تصفية نشر"),
        ("واصل لاحمد رضا", "30/9/2026", 80000.00, "أحمد رضا", "دفعة سبتمبر")
    ]

    p_start = r + 1
    r = p_start
    for idx, (b, dt, amt, rec, nts) in enumerate(payments, 1):
        ws.cell(r, 1, idx)
        ws.cell(r, 2, b)
        ws.cell(r, 3, dt)
        ws.cell(r, 4, amt)
        ws.cell(r, 5, rec)
        ws.cell(r, 6, nts)
        style_range(ws, r, 1, r, 6, font=font_regular, border=border_cell, alignment=align_center)
        ws.cell(r, 2).alignment = align_right
        ws.cell(r, 4).number_format = "#,##0.00"
        if r % 2 == 0:
            style_range(ws, r, 1, r, 6, fill=fill_light_gray)
        r += 1

    # Total Payments
    ws.cell(r, 2, "إجمالي الواصل والمسدد لأحمد رضا").font = Font(name=FONT_FAMILY, size=12, bold=True, color="15803D")
    ws.cell(r, 4, f"=SUM(D{p_start}:D{r-1})").font = Font(name=FONT_FAMILY, size=12, bold=True, color="15803D")
    ws.cell(r, 4).number_format = "#,##0.00"
    style_range(ws, r, 1, r, 6, fill=fill_green_hdr, border=border_header, alignment=align_center)
    ws.row_dimensions[r].height = 26

    auto_fit_columns(ws)
    target_path = os.path.join(WORK_DIR, "أحمد رضا", "حساب احمد رضا - النسخة المطورة 2026.xlsx")
    wb.save(target_path)
    print(f"Saved: {target_path}")

def build_adham():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ملف أدهم الشامل"
    ws.views.sheetView[0].rightToLeft = True

    # Title
    ws.merge_cells("A1:H1")
    ws.cell(1, 1, "سجل وتوريدات ومستودع أدهم الشامل - النسخة المطورة 2026").font = font_title
    ws.cell(1, 1).alignment = align_center
    ws.row_dimensions[1].height = 32

    # Section 1: فواتير وتوريدات أدهم (1 إلى 9)
    ws.merge_cells("A3:H3")
    ws.cell(3, 1, "١. فواتير التوريد والتحميل والنقل (من 1 إلى 9)").font = font_section
    ws.cell(3, 1).fill = fill_navy
    ws.cell(3, 1).alignment = align_right
    ws.row_dimensions[3].height = 24

    headers = ["رقم الشحنة", "اسم الملف الأصلي", "التاريخ", "العميل المستلم", "السائق", "إجمالي القطع", "المسطح (م٢)", "القيمة الإجمالية (ج.م)"]
    for c_idx, h in enumerate(headers, 1):
        ws.cell(4, c_idx, h)
    style_range(ws, 4, 1, 4, len(headers), font=font_header, fill=fill_gold_hdr, border=border_header, alignment=align_center)
    ws.row_dimensions[4].height = 24

    shipments = [
        ("شحنة 1", "1.xlsx", "22/06/2026", "الحاج نور", "اللمعة", 137, 732.51, 115896.00),
        ("شحنة 2", "2.xlsx", "07/05/2026", "الحاج صلاح", "-", 142, 744.10, 138783.80),
        ("شحنة 3", "3.xlsx", "11/07/2026", "صديق جعفر", "-", 135, 715.40, 135000.00),
        ("شحنة 4", "4.xlsx", "22/07/2026", "صديق جعفر", "-", 128, 690.20, 128500.00),
        ("شحنة 5", "5.xlsx", "01/08/2026", "صديق جعفر", "-", 139, 730.00, 142000.00),
        ("شحنة 6", "6.xlsx", "13/08/2026", "الحاج صلاح", "-", 130, 712.50, 120426.06),
        ("شحنة 7", "7.xlsx", "16/08/2026", "الحاج صلاح", "-", 133, 720.80, 120806.00),
        ("شحنة 8", "8.xlsx", "22/08/2026", "مصطفي شيخون", "-", 145, 755.30, 138000.00),
        ("شحنة 9", "9.xlsx", "27/08/2026", "مصطفي شيخون", "-", 140, 738.90, 132000.00)
    ]

    r = 5
    for idx, (sh_no, f_name, dt, client, drv, pcs, area, amt) in enumerate(shipments, 1):
        ws.cell(r, 1, sh_no)
        ws.cell(r, 2, f_name)
        ws.cell(r, 3, dt)
        ws.cell(r, 4, client)
        ws.cell(r, 5, drv)
        ws.cell(r, 6, pcs)
        ws.cell(r, 7, area)
        ws.cell(r, 8, amt)
        style_range(ws, r, 1, r, 8, font=font_regular, border=border_cell, alignment=align_center)
        ws.cell(r, 4).alignment = align_right
        ws.cell(r, 7).number_format = "#,##0.00"
        ws.cell(r, 8).number_format = "#,##0.00"
        if r % 2 == 0:
            style_range(ws, r, 1, r, 8, fill=fill_light_gray)
        r += 1

    # Total Shipments
    ws.cell(r, 4, "إجمالي شحنات أدهم").font = font_total
    ws.cell(r, 6, f"=SUM(F5:F{r-1})").font = font_total
    ws.cell(r, 7, f"=SUM(G5:G{r-1})").font = font_total
    ws.cell(r, 7).number_format = "#,##0.00"
    ws.cell(r, 8, f"=SUM(H5:H{r-1})").font = font_total
    ws.cell(r, 8).number_format = "#,##0.00"
    style_range(ws, r, 1, r, 8, fill=fill_pink_tot, border=border_header, alignment=align_center)
    ws.row_dimensions[r].height = 26

    # Section 2: إجمالي أمتار الخامات (ملف اجمالي امتار.xlsx)
    r += 3
    ws.merge_cells(f"A{r}:H{r}")
    ws.cell(r, 1, "٢. ملخص إجمالي أمتار الخامات والأسعار (من ملف اجمالي امتار.xlsx)").font = font_section
    ws.cell(r, 1).fill = PatternFill(start_color="0369A1", end_color="0369A1", fill_type="solid")
    ws.cell(r, 1).alignment = align_right
    ws.row_dimensions[r].height = 24

    r += 1
    m_headers = ["م", "نوع الخامة والبيان", "السمك", "إجمالي الأمتار (م٢)", "سعر المتر (ج.م)", "القيمة الإجمالية (ج.م)", "الملاحظات", "الحالة"]
    for c_idx, h in enumerate(m_headers, 1):
        ws.cell(r, c_idx, h)
    style_range(ws, r, 1, r, len(m_headers), font=font_header, fill=fill_blue_hdr, border=border_header, alignment=align_center)
    ws.row_dimensions[r].height = 24

    materials_summary = [
        ("سيلفيا طاولات", "3 سم", 824.48, 175.00, 144284.00, "طاولات فرز أول", "معتمد"),
        ("صني طاولات", "3 سم", 2363.67, 155.00, 366368.85, "طاولات صني متنوعة", "معتمد"),
        ("ريشة طاولات", "3 سم", 1537.38, 165.00, 253667.70, "ريشة ممتازة", "معتمد"),
        ("صني غشيم", "2 سم / 3 سم", 503.95, 135.00, 68033.25, "ألواح صني غشيم", "معتمد")
    ]

    m_start = r + 1
    r = m_start
    for idx, (m_name, thk, mtrs, prc, tot, nts, st) in enumerate(materials_summary, 1):
        ws.cell(r, 1, idx)
        ws.cell(r, 2, m_name)
        ws.cell(r, 3, thk)
        ws.cell(r, 4, mtrs)
        ws.cell(r, 5, prc)
        ws.cell(r, 6, tot)
        ws.cell(r, 7, nts)
        ws.cell(r, 8, st)
        style_range(ws, r, 1, r, 8, font=font_regular, border=border_cell, alignment=align_center)
        ws.cell(r, 2).alignment = align_right
        ws.cell(r, 4).number_format = "#,##0.00"
        ws.cell(r, 5).number_format = "#,##0.00"
        ws.cell(r, 6).number_format = "#,##0.00"
        if r % 2 == 0:
            style_range(ws, r, 1, r, 8, fill=fill_light_gray)
        r += 1

    # Total Materials
    ws.cell(r, 2, "إجمالي خامات أدهم").font = font_total
    ws.cell(r, 4, f"=SUM(D{m_start}:D{r-1})").font = font_total
    ws.cell(r, 4).number_format = "#,##0.00"
    ws.cell(r, 6, f"=SUM(F{m_start}:F{r-1})").font = font_total
    ws.cell(r, 6).number_format = "#,##0.00"
    style_range(ws, r, 1, r, 8, fill=fill_pink_tot, border=border_header, alignment=align_center)
    ws.row_dimensions[r].height = 26

    # Section 3: حساب وتفاصيل عرب مساعد (1تفاصيل عرب مساعد.xlsx)
    r += 3
    ws.merge_cells(f"A{r}:H{r}")
    ws.cell(r, 1, "٣. حساب ورشة عرب مساعد (حق الحجر والنوالين - رجب علي)").font = font_section
    ws.cell(r, 1).fill = PatternFill(start_color="15803D", end_color="15803D", fill_type="solid")
    ws.cell(r, 1).alignment = align_right
    ws.row_dimensions[r].height = 24

    r += 1
    arab_headers = ["م", "البيان الأصلي", "المبلغ الإجمالي (ج.م)", "الواصل من رجب علي", "المتبقي المستحق", "الملاحظات", "الحالة", ""]
    for c_idx, h in enumerate(arab_headers, 1):
        if h: ws.cell(r, c_idx, h)
    style_range(ws, r, 1, r, 7, font=font_header, fill=fill_green_hdr, border=border_header, alignment=align_center)
    ws.row_dimensions[r].height = 24

    r += 1
    ws.cell(r, 1, 1)
    ws.cell(r, 2, "حق الحجر والنوالين (عرب مساعد)")
    ws.cell(r, 3, 427000.00)
    ws.cell(r, 4, 180000.00)
    ws.cell(r, 5, 247000.00)
    ws.cell(r, 6, "واصل 180,000 ج.م من رجب علي")
    ws.cell(r, 7, "جاري المتابعة")
    style_range(ws, r, 1, r, 7, font=font_bold, border=border_cell, alignment=align_center)
    ws.cell(r, 3).number_format = "#,##0.00"
    ws.cell(r, 4).number_format = "#,##0.00"
    ws.cell(r, 5).number_format = "#,##0.00"

    auto_fit_columns(ws)
    target_path = os.path.join(WORK_DIR, "أدهم", "ملف أدهم الشامل - النسخة المطورة 2026.xlsx")
    wb.save(target_path)
    print(f"Saved: {target_path}")

def sync_db_records():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Ensure clients exist
    c.execute("INSERT OR IGNORE INTO clients (name, phone, address, notes) VALUES (?, ?, ?, ?)",
              ("الحاج صلاح", "01000000001", "القاهرة / شق الثعبان", "عميل رئيسي مستمر"))
    c.execute("INSERT OR IGNORE INTO clients (name, phone, address, notes) VALUES (?, ?, ?, ?)",
              ("أحمد رضا", "01000000006", "القاهرة", "عميل ترابيع وصني وسيلفيا"))
    c.execute("INSERT OR IGNORE INTO clients (name, phone, address, notes) VALUES (?, ?, ?, ?)",
              ("أدهم", "01000000012", "شق التعبان", "توريدات وشحنات أدهم وعرب مساعد"))

    # Populate Ahmed Reda Invoices
    ahmed_reda_invoices = [
        ("الفاتوره الاولي", "2026-04-14", 133000.00, "طاولات وترابيع"),
        ("الفاتوره الثانيه", "2026-04-17", 136000.00, "رخام وجرانيت"),
        ("الفاتوره الثالثه", "2025-06-05", 133571.19, "طاولات صني"),
        ("الترابيع", "2025-06-10", 87000.00, "إجمالي الأمتار 316.8 و 1760 شريحة و 8 بلتة"),
        ("فاتورة يوم 15/6", "2025-06-15", 140126.56, "طاولات ورخام"),
        ("فاتورة يوم 30/7", "2025-07-30", 106000.00, "توريد رخام"),
        ("فاتورة 14 / 9", "2025-09-14", 109226.00, "توريد سبتمبر"),
        ("فاتورة 28 / 9", "2025-09-28", 114374.60, "توريدات خريف"),
        ("فاتورة 7 / 10", "2025-10-07", 116290.00, "طاولات"),
        ("فاتوره 30 / 10", "2025-10-30", 118160.00, "توريد رخام"),
        ("فاتوره 6 / 11", "2025-11-06", 106794.82, "رخام"),
        ("صافي القديم", "2025-11-20", 66000.00, "رصيد مرحل الساعة 3.31"),
        ("فاتورة 1", "2025-11-19", 98350.00, "توريد نوفمبر"),
        ("فاتورة 2", "2025-11-19", 137160.00, "ترابيع صني فرز أول"),
        ("فاتورة 3", "2025-12-02", 140400.00, "ترابيع صني"),
        ("فاتورة 4", "2025-12-02", 109222.82, "تعديل السيلفيا إلى ريشة والصني 140"),
        ("فاتورة 5", "2025-12-20", 106575.00, "طاولات ديسمبر"),
        ("فاتورة 6", "2026-01-17", 104971.16, "توريد يناير"),
        ("فاتورة 7", "2026-01-20", 121132.03, "طاولات ممتازة"),
        ("فاتورة 8", "2026-01-26", 103331.76, "رخام"),
        ("فاتورة 9", "2026-02-05", 119960.31, "سيلفيا طاولات"),
        ("فاتورة 10", "2026-02-05", 103695.26, "صني طاولات"),
        ("فاتورة 11", "2026-02-04", 103081.13, "صني طاولات"),
        ("فاتورة 12", "2026-03-03", 117042.40, "ترابيع صني ونيو حلايب (كانت 170042 ناقص 53000)"),
        ("فاتورة 13", "2026-04-12", 101034.60, "صني (بالسعر القديم)"),
        ("فاتورة 14", "2026-04-30", 177210.00, "ترابيع ريشة على سعر 165")
    ]
    for inv_name, dt, amt, nts in ahmed_reda_invoices:
        c.execute("""
        INSERT OR IGNORE INTO invoices (invoice_no, invoice_date, client_name, driver_name, car_no, total_pieces, total_area, total_amount, net_amount, paid_amount, remaining_amount, notes, status)
        VALUES (?, ?, 'أحمد رضا', '-', '-', 100, 500, ?, ?, ?, 0, ?, 'معتمدة')
        """, (inv_name, dt, amt, amt, amt, nts))

    # Populate Adham Invoices / Shipments
    adham_shipments = [
        ("شحنة 1 (1.xlsx)", "2026-06-22", "الحاج نور", "اللمعة", 137, 732.51, 115896.00, "سيلفيا 3 سم وصني 3 سم"),
        ("شحنة 2 (2.xlsx)", "2026-05-07", "الحاج صلاح", "-", 142, 744.10, 138783.80, "جندولة وصني"),
        ("شحنة 3 (3.xlsx)", "2026-07-11", "صديق جعفر", "-", 135, 715.40, 135000.00, "صني 3 سم وريشة 3 سم"),
        ("شحنة 4 (4.xlsx)", "2026-07-22", "صديق جعفر", "-", 128, 690.20, 128500.00, "صني غشيم وترابيع"),
        ("شحنة 5 (5.xlsx)", "2026-08-01", "صديق جعفر", "-", 139, 730.00, 142000.00, "صني 2 سم"),
        ("شحنة 6 (6.xlsx)", "2026-08-13", "الحاج صلاح", "-", 130, 712.50, 120426.06, "نيو حلايب وجندولة"),
        ("شحنة 7 (7.xlsx)", "2026-08-16", "الحاج صلاح", "-", 133, 720.80, 120806.00, "حلايب وسيلفيا"),
        ("شحنة 8 (8.xlsx)", "2026-08-22", "مصطفي شيخون", "-", 145, 755.30, 138000.00, "ريشة 3 سم وسيلفيا 3 سم"),
        ("شحنة 9 (9.xlsx)", "2026-08-27", "مصطفي شيخون", "-", 140, 738.90, 132000.00, "ريشة غشيم"),
        ("ورشة عرب مساعد (حق الحجر والنوالين)", "2026-05-01", "عرب مساعد / رجب علي", "-", 0, 0, 427000.00, "واصل 180000 والباقي 247000 ج.م"),
        ("إجمالي أمتار الخامات (سيلفيا، صني، ريشة)", "2026-06-01", "مستودع أدهم", "-", 0, 5229.48, 832353.80, "سيلفيا 824.48 م٢، صني 2363.67 م٢، ريشة 1537.38 م٢، صني غشيم 503.95 م٢")
    ]
    for sh_name, dt, cl, drv, pcs, area, amt, nts in adham_shipments:
        c.execute("""
        INSERT OR IGNORE INTO invoices (invoice_no, invoice_date, client_name, driver_name, car_no, total_pieces, total_area, total_amount, net_amount, paid_amount, remaining_amount, notes, status)
        VALUES (?, ?, 'أدهم', ?, '-', ?, ?, ?, ?, ?, 0, ?, 'معتمدة')
        """, (sh_name, dt, drv, pcs, area, amt, amt, amt, f"{cl} - {nts}"))

    conn.commit()
    conn.close()
    print("Database sync complete!")

if __name__ == "__main__":
    print("Building Hajj Salah upgraded file...")
    build_hajj_salah()
    print("\nBuilding Ahmed Reda upgraded file...")
    build_ahmed_reda()
    print("\nBuilding Adham upgraded file...")
    build_adham()
    print("\nSyncing records into Database...")
    sync_db_records()
    print("\n ALL FILES AND DATABASE RECORDS CREATED SUCCESSFULLY! ")
