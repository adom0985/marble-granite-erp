# -*- coding: utf-8 -*-
import os
import sqlite3
import pymupdf
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "marble_erp.db")

def generate_client_statement_pdf(client_name: str, output_path: str = None, conn = None) -> bytes:
    """
    Generates a professional, organized A4 PDF statement for any client (e.g. Haj Salah)
    dynamically from the SQLite database.
    - Fits on a single A4 Landscape or paginates cleanly if many rows.
    - Features Invoices table, Payments table, and Summary Balance Card.
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        close_conn = True

    c = conn.cursor()

    # Get client metadata
    cl = c.execute("SELECT * FROM clients WHERE name = ?", (client_name,)).fetchone()
    client_phone = cl["phone"] if cl and "phone" in cl.keys() else ""

    # Get active invoices
    inv_rows = c.execute("""
        SELECT id, invoice_no, invoice_date, total_pieces, total_area, net_amount, notes, status
        FROM invoices
        WHERE client_name = ? AND status != 'متقفلة (أرشيف قديم)'
        ORDER BY invoice_date ASC, id ASC
    """, (client_name,)).fetchall()

    # Get payments
    pay_rows = c.execute("""
        SELECT id, payment_date, amount_egp, payment_method, notes
        FROM client_payments
        WHERE client_name = ?
        ORDER BY payment_date ASC, id ASC
    """, (client_name,)).fetchall()

    if close_conn:
        conn.close()

    total_invoices_amt = sum(r["net_amount"] for r in inv_rows)
    total_area = sum(r["total_area"] or 0 for r in inv_rows)
    total_pcs = sum(r["total_pieces"] or 0 for r in inv_rows)
    total_paid_amt = sum(r["amount_egp"] for r in pay_rows)
    net_remaining = round(total_invoices_amt - total_paid_amt, 2)

    today_str = datetime.now().strftime("%Y/%m/%d")

    # Build invoices HTML rows
    inv_tr_list = []
    for idx, inv in enumerate(inv_rows, 1):
        inv_no = inv["invoice_no"] or "-"
        inv_dt = str(inv["invoice_date"] or "-")
        ar = float(inv["total_area"] or 0)
        amt = float(inv["net_amount"] or 0)
        note = inv["notes"] or "-"
        # Clean note if it's too long or noisy
        if note == "حساب الحاج صلاح جديد":
            note = "فاتورة معتمدة"

        inv_tr_list.append(f"""
        <tr>
            <td style="width:5%; font-weight:bold;">{idx}</td>
            <td style="width:13%; font-weight:bold;">{inv_dt}</td>
            <td style="width:20%; font-weight:900; color:#1e3a8a;">{inv_no}</td>
            <td style="width:12%; font-weight:bold;">{ar:,.3f}</td>
            <td style="width:16%; font-weight:900; font-size:11px;">{amt:,.2f}</td>
            <td style="width:34%; text-align:right; padding-right:8px; font-size:9.5px;">{note}</td>
        </tr>
        """)
    inv_rows_html = "".join(inv_tr_list)

    # Build payments HTML rows
    pay_tr_list = []
    for idx, pay in enumerate(pay_rows, 1):
        p_dt = str(pay["payment_date"] or "-")
        p_amt = float(pay["amount_egp"] or 0)
        p_meth = pay["payment_method"] or "نقداً"
        p_note = pay["notes"] or "واصل (دفعة مسددة)"

        pay_tr_list.append(f"""
        <tr style="background-color:#fef9c3;">
            <td style="width:6%; font-weight:bold;">{idx}</td>
            <td style="width:16%; font-weight:bold;">{p_dt}</td>
            <td style="width:24%; font-weight:900; color:#15803d; font-size:11.5px;">{p_amt:,.2f} ج</td>
            <td style="width:20%; font-weight:bold;">{p_meth}</td>
            <td style="width:34%; text-align:right; padding-right:8px; font-weight:bold; color:#15803d; font-size:10px;">{p_note}</td>
        </tr>
        """)
    pay_rows_html = "".join(pay_tr_list)

    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            margin: 0;
            padding: 8px 16px;
            color: #000000;
        }}
        .header-title {{
            text-align: center;
            background-color: #fef08a; /* Yellow */
            border: 1.5px solid #000;
            padding: 5px;
            font-size: 17px;
            font-weight: 900;
            color: #1e3a8a;
            margin-bottom: 6px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .meta-table td {{
            border: 1.2px solid #000000;
            padding: 3px 6px;
            text-align: center;
            font-size: 11px;
        }}
        .lbl {{
            background-color: #fef08a;
            font-weight: 900;
        }}
        .val {{
            background-color: #ffffff;
            font-weight: bold;
        }}
        .section-header {{
            background-color: #e2e8f0;
            font-weight: 900;
            font-size: 11.5px;
            border: 1.2px solid #000;
            padding: 3px 6px;
            margin-top: 6px;
            margin-bottom: 3px;
            color: #0f172a;
        }}
        .data-table th {{
            background-color: #dbeafe; /* Light Blue */
            font-weight: 900;
            border: 1.2px solid #000;
            padding: 3.5px 3px;
            text-align: center;
            font-size: 10px;
        }}
        .data-table td {{
            border: 1.2px solid #000;
            padding: 2.5px 3px;
            text-align: center;
            font-size: 10px;
        }}
        .tot-row td {{
            background-color: #86efac !important; /* Green total */
            font-weight: 900;
            font-size: 11px;
            border: 1.2px solid #000;
        }}
        .summary-card {{
            border-collapse: collapse;
            width: 100%;
            margin-top: 4px;
        }}
        .sum-hdr {{
            background-color: #fef08a;
            font-weight: 900;
            font-size: 11.5px;
            border: 1.2px solid #000;
            padding: 3.5px;
            text-align: center;
        }}
        .sum-lbl {{
            background-color: #f8fafc;
            font-weight: bold;
            border: 1.2px solid #000;
            padding: 3.5px 8px;
            text-align: right;
            font-size: 11px;
            width: 60%;
        }}
        .sum-val {{
            background-color: #ffffff;
            font-weight: 900;
            border: 1.2px solid #000;
            padding: 3.5px 8px;
            text-align: center;
            font-size: 12px;
            width: 40%;
        }}
    </style>
    </head>
    <body>
        <div class="header-title">كشف حساب وسجل حركات: {client_name}</div>

        <table class="meta-table" style="margin-bottom: 6px;">
            <tr>
                <td class="lbl" style="width:10%;">التاريخ</td>
                <td class="val" style="width:18%;">{today_str}</td>
                <td class="lbl" style="width:10%;">المسؤول</td>
                <td class="val" style="width:18%;">أحمد جلال</td>
                <td class="lbl" style="width:10%;">العميل</td>
                <td class="val" style="width:20%; font-size:12.5px; font-weight:900; color:#1e3a8a;">{client_name}</td>
                <td class="lbl" style="width:6%;">الحالة</td>
                <td class="val" style="width:8%; color:#15803d; font-weight:900;">نشط</td>
            </tr>
        </table>

        <!-- Invoices Section -->
        <table class="data-table">
            <thead>
                <tr>
                    <th colspan="6" style="background-color:#93c5fd; color:#0f172a; font-size:11px; text-align:right; padding-right:10px;">
                        📋 سجل الفواتير المعتمدة الصادرة ({len(inv_rows)} فواتير)
                    </th>
                </tr>
                <tr>
                    <th>م</th>
                    <th>التاريخ</th>
                    <th>رقم وبيان الفاتورة</th>
                    <th>المسطح (م²)</th>
                    <th>المبلغ المستحق (ج)</th>
                    <th>ملاحظات وبيان الصنف</th>
                </tr>
            </thead>
            <tbody>
                {inv_rows_html}
                <tr class="tot-row">
                    <td colspan="3" style="text-align:center;">إجمالي الفواتير المعتمدة</td>
                    <td>{total_area:,.3f}</td>
                    <td style="font-size:11.5px;">{total_invoices_amt:,.2f}</td>
                    <td style="font-size:9.5px;">إجمالي المسطح {total_area:,.3f} م² ({total_pcs:,.0f} قطعة/طاولة)</td>
                </tr>
            </tbody>
        </table>

        <!-- Layout grid: Payments table on Left, Summary Card on Right -->
        <table style="width:100%; border:none; margin-top:6px;">
            <tr style="border:none;">
                <!-- Payments Table (Left/Right) -->
                <td style="width:58%; vertical-align:top; border:none; padding-left:8px;">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th colspan="5" style="background-color:#bbf7d0; color:#14532d; font-size:11px; text-align:right; padding-right:10px;">
                                    💵 سجل الدفعات النقدية المسددة (واصل منه) - ({len(pay_rows)} دفعات)
                                </th>
                            </tr>
                            <tr>
                                <th>م</th>
                                <th>التاريخ</th>
                                <th>المبلغ (ج)</th>
                                <th>طريقة السداد</th>
                                <th>ملاحظات الدفعة</th>
                            </tr>
                        </thead>
                        <tbody>
                            {pay_rows_html}
                            <tr class="tot-row" style="background-color:#bbf7d0 !important;">
                                <td colspan="2" style="text-align:center;">إجمالي الواصل</td>
                                <td colspan="3" style="color:#15803d; font-size:12px; text-align:right; padding-right:15px;">{total_paid_amt:,.2f} جنيه</td>
                            </tr>
                        </tbody>
                    </table>
                </td>

                <!-- Summary Card -->
                <td style="width:42%; vertical-align:top; border:none; padding-right:8px;">
                    <table class="summary-card">
                        <tr>
                            <th colspan="2" class="sum-hdr">خلاصة الحساب المالي المعتمد</th>
                        </tr>
                        <tr>
                            <td class="sum-lbl">إجمالي قيمة الفواتير ({len(inv_rows)} فواتير):</td>
                            <td class="sum-val">{total_invoices_amt:,.2f} ج</td>
                        </tr>
                        <tr>
                            <td class="sum-lbl">إجمالي المبالغ المسددة (واصل):</td>
                            <td class="sum-val" style="color:#15803d;">{total_paid_amt:,.2f} ج</td>
                        </tr>
                        <tr style="background-color:#fef08a;">
                            <td class="sum-lbl" style="background-color:#fef08a; font-weight:900; font-size:12px;">صافي المبلغ المتبقي المستحق:</td>
                            <td class="sum-val" style="background-color:#fef08a; color:#b91c1c; font-size:14px;">{net_remaining:,.2f} ج</td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    doc = pymupdf.open()
    page = doc.new_page(width=842, height=595) # A4 Landscape
    rect = pymupdf.Rect(15, 15, 827, 580)
    page.insert_htmlbox(rect, html_content)

    pdf_bytes = doc.tobytes()

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)
        print(f"Saved statement PDF to {output_path}")

    doc.close()
    return pdf_bytes

if __name__ == "__main__":
    test_out = os.path.join(r"I:\خالي أحمد جلال\الحاج صلاح", "كشف حساب الحاج صلاح.pdf")
    generate_client_statement_pdf("الحاج صلاح", test_out)
    bundled_out = os.path.join(BASE_DIR, "bundled_files", "الحاج صلاح", "كشف حساب الحاج صلاح.pdf")
    generate_client_statement_pdf("الحاج صلاح", bundled_out)
