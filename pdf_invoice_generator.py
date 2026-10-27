import os
import pymupdf
from collections import defaultdict

def generate_invoice_pdf(invoice_dict, output_path):
    """
    Generates a beautifully formatted official A4 PDF invoice matching the exact
    traditional marble workshop template (yellow meta grid, pink grand totals,
    green "ملخص الجرار" summary), styled in a crisp, modern electronic layout.
    """
    inv_no = invoice_dict.get("invoice_no", "INV-2026")
    inv_date = invoice_dict.get("invoice_date", "2026-10-27")
    client_name = invoice_dict.get("client_name", "الحاج صلاح")
    driver_name = invoice_dict.get("driver_name", "") or "-"
    car_no = invoice_dict.get("car_no", "") or "-"
    loading_place = invoice_dict.get("loading_place", "") or "-"
    supervisor = invoice_dict.get("supervisor", "") or "-"
    notes = invoice_dict.get("notes", "") or "-"
    items = invoice_dict.get("items", [])

    tot_qty = sum(float(it.get("qty") or 0) for it in items)
    tot_area = sum(float(it.get("area") or 0) for it in items)
    tot_amount = sum(float(it.get("total") or 0) for it in items)
    discount = float(invoice_dict.get("discount") or 0)
    net_amount = float(invoice_dict.get("net_amount") or (tot_amount - discount))
    paid_amount = float(invoice_dict.get("paid_amount") or 0)
    rem_amount = net_amount - paid_amount

    # Build Main Items Table Rows (10 columns, RTL)
    # Order: رقم الطرد | رقم البلوك | نوع الخامه | عدد | طول | عرض | المسطح | السعر | الإجمالي | ملاحظات
    rows_html = ""
    for idx, it in enumerate(items, 1):
        pkg = it.get("package_no") or (f"صندوق {idx}" if "صندوق" in (it.get("notes") or "") else "-")
        blk = it.get("block_no") or "-"
        mat = it.get("material_name", "")
        q = float(it.get("qty") or 0)
        l = float(it.get("length") or 0)
        w = float(it.get("width") or 0)
        ar = float(it.get("area") or 0)
        p = float(it.get("price") or 0)
        tot = float(it.get("total") or 0)
        note_str = it.get("notes") or "-"

        rows_html += f"""
        <tr>
            <td style="border:1px solid #1e293b; padding:6px 4px; text-align:center; font-weight:bold;">{pkg}</td>
            <td style="border:1px solid #1e293b; padding:6px 4px; text-align:center;">{blk}</td>
            <td style="border:1px solid #1e293b; padding:6px 6px; text-align:center; font-weight:bold; font-size:13px;">{mat}</td>
            <td style="border:1px solid #1e293b; padding:6px 4px; text-align:center; font-weight:bold;">{q:,.2f}</td>
            <td style="border:1px solid #1e293b; padding:6px 4px; text-align:center;">{l:.2f}</td>
            <td style="border:1px solid #1e293b; padding:6px 4px; text-align:center;">{w:.2f}</td>
            <td style="border:1px solid #1e293b; padding:6px 4px; text-align:center; font-weight:bold;">{ar:,.2f}</td>
            <td style="border:1px solid #1e293b; padding:6px 4px; text-align:center;">{p:,.2f}</td>
            <td style="border:1px solid #1e293b; padding:6px 4px; text-align:center; font-weight:bold; font-size:13px;">{tot:,.2f}</td>
            <td style="border:1px solid #1e293b; padding:6px 6px; text-align:center; font-size:11px;">{note_str}</td>
        </tr>
        """

    # Group items for "ملخص الجرار"
    summary_groups = defaultdict(lambda: {"qty": 0.0, "area": 0.0, "price": 0.0, "total": 0.0, "dim": ""})
    for it in items:
        mat = it.get("material_name", "خامة")
        w = float(it.get("width") or 0)
        l = float(it.get("length") or 0)
        dim_str = f"{w:.1f}" if w > 0 else (f"{l:.1f}" if l > 0 else "")
        key = f"{mat} ( {dim_str} )" if dim_str else mat
        summary_groups[key]["qty"] += float(it.get("qty") or 0)
        summary_groups[key]["area"] += float(it.get("area") or 0)
        summary_groups[key]["price"] = float(it.get("price") or 0)
        summary_groups[key]["total"] += float(it.get("total") or 0)

    summary_rows_html = ""
    for mat_label, g in summary_groups.items():
        summary_rows_html += f"""
        <tr style="background:#ffffff;">
            <td style="border:1px solid #1e293b; padding:6px 8px; text-align:center; font-weight:bold;">{mat_label}</td>
            <td style="border:1px solid #1e293b; padding:6px 6px; text-align:center; font-weight:bold;">{g['qty']:,.2f}</td>
            <td style="border:1px solid #1e293b; padding:6px 6px; text-align:center; font-weight:bold;">{g['area']:,.2f}</td>
            <td style="border:1px solid #1e293b; padding:6px 6px; text-align:center;">{g['price']:,.2f}</td>
            <td style="border:1px solid #1e293b; padding:6px 6px; text-align:center; font-weight:bold;">{g['total']:,.2f}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Cairo', sans-serif;
            margin: 0;
            padding: 16px;
            color: #0f172a;
            direction: rtl;
        }}
        .brand-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #0f172a;
            padding-bottom: 8px;
            margin-bottom: 12px;
        }}
        .brand-title {{
            font-size: 18px;
            font-weight: 900;
            color: #0f172a;
            margin: 0;
        }}
        .brand-sub {{
            font-size: 11px;
            color: #475569;
            margin-top: 2px;
        }}
        .badge-electronic {{
            background: #dbeafe;
            color: #1e40af;
            border: 1px solid #93c5fd;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: bold;
            text-align: center;
        }}
        
        /* Exact Yellow Top Meta Grid */
        .meta-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 12px;
            font-size: 12px;
        }}
        .meta-table td {{
            border: 1px solid #1e293b;
            padding: 5px 8px;
            text-align: center;
        }}
        .meta-lbl {{
            background-color: #fffa65;
            font-weight: bold;
            color: #000000;
            font-size: 12px;
        }}
        .meta-val {{
            background-color: #ffffff;
            font-weight: bold;
            color: #0f172a;
        }}

        /* Main Items Grid */
        .items-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 11.5px;
            margin-bottom: 16px;
        }}
        .items-table th {{
            background-color: #dbeafe;
            color: #000000;
            font-weight: 900;
            border: 1px solid #1e293b;
            padding: 7px 4px;
            text-align: center;
            font-size: 12px;
        }}
        
        /* Characteristic Pink Total Row */
        .pink-total-row td {{
            background-color: #fbcfe8 !important;
            border: 1px solid #1e293b;
            padding: 8px 4px;
            font-weight: 900;
            font-size: 13.5px;
            text-align: center;
            color: #000000;
        }}

        /* Bottom Summary "ملخص الجرار" Table */
        .summary-table {{
            width: 60%;
            margin-right: auto;
            border-collapse: collapse;
            font-size: 11.5px;
            margin-top: 10px;
        }}
        .summary-header {{
            background-color: #fffa65;
            color: #000000;
            font-weight: 900;
            font-size: 13px;
            text-align: center;
            border: 1px solid #1e293b;
            padding: 6px;
        }}
        .summary-sub-header th {{
            background-color: #86efac;
            color: #000000;
            font-weight: bold;
            border: 1px solid #1e293b;
            padding: 6px 4px;
            text-align: center;
            font-size: 11.5px;
        }}
        .summary-total td {{
            background-color: #4ade80 !important;
            font-weight: 900;
            border: 1px solid #1e293b;
            padding: 7px 6px;
            text-align: center;
            color: #000000;
            font-size: 12.5px;
        }}

        .footer-note {{
            margin-top: 24px;
            font-size: 10.5px;
            color: #64748b;
            text-align: center;
            border-top: 1px dashed #cbd5e1;
            padding-top: 8px;
        }}
    </style>
    </head>
    <body>

        <!-- Brand Top Bar -->
        <div class="brand-header">
            <div>
                <div class="brand-title">🏛️ شركة ومصانع خالي أحمد جلال للرخام والجرانيت</div>
                <div class="brand-sub">إدارة المبيعات والمستودع المركزي - فاتورة توريد إلكترونية رسمية</div>
            </div>
            <div class="badge-electronic">
                ✓ معتمدة إلكترونياً
            </div>
        </div>

        <!-- Exact Yellow Header Grid (4 columns x 2 rows) -->
        <table class="meta-table">
            <tr>
                <td class="meta-lbl" style="width:13%;">التاريخ</td>
                <td class="meta-val" style="width:20%;">{inv_date}</td>
                <td class="meta-lbl" style="width:13%;">العميل</td>
                <td class="meta-val" style="width:20%; font-size:13px; color:#1e3a8a;">{client_name}</td>
                <td class="meta-lbl" style="width:13%;">السائق</td>
                <td class="meta-val" style="width:21%;">{driver_name}</td>
            </tr>
            <tr>
                <td class="meta-lbl">رقم السيارة / الكونتر</td>
                <td class="meta-val">{car_no}</td>
                <td class="meta-lbl">مكان التحميل</td>
                <td class="meta-val">{loading_place}</td>
                <td class="meta-lbl">المشرف</td>
                <td class="meta-val">{supervisor}</td>
            </tr>
            <tr>
                <td class="meta-lbl">رقم الفاتوره</td>
                <td class="meta-val" style="font-size:13px; color:#b91c1c;">{inv_no}</td>
                <td class="meta-lbl">ملاحظات عامة</td>
                <td class="meta-val" colspan="3" style="text-align:right; font-size:11px;">{notes}</td>
            </tr>
        </table>

        <!-- Main Items Table (10 columns) -->
        <table class="items-table">
            <thead>
                <tr>
                    <th style="width:10%;">رقم الطرد</th>
                    <th style="width:8%;">رقم البلوك</th>
                    <th style="width:20%;">نوع الخامه</th>
                    <th style="width:9%;">عدد</th>
                    <th style="width:7%;">طول</th>
                    <th style="width:7%;">عرض</th>
                    <th style="width:10%;">المسطح</th>
                    <th style="width:8%;">السعر</th>
                    <th style="width:11%;">الإجمالي</th>
                    <th style="width:10%;">ملاحظات</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
                <!-- Pink Grand Total Row -->
                <tr class="pink-total-row">
                    <td colspan="3" style="text-align:center; font-size:14px;">الإجمالي</td>
                    <td>{tot_qty:,.0f}</td>
                    <td>-</td>
                    <td>-</td>
                    <td>{tot_area:,.2f}</td>
                    <td>-</td>
                    <td>{net_amount:,.2f}</td>
                    <td>-</td>
                </tr>
            </tbody>
        </table>

        <!-- "ملخص الجرار" Summary Card at Bottom -->
        <table class="summary-table">
            <thead>
                <tr>
                    <th colspan="5" class="summary-header">ملخص الجرار</th>
                </tr>
                <tr class="summary-sub-header">
                    <th style="width:36%;">الخامه و البيان</th>
                    <th style="width:16%;">عدد الترابيع</th>
                    <th style="width:16%;">كمية الأمتار</th>
                    <th style="width:14%;">السعر</th>
                    <th style="width:18%;">الإجمالي</th>
                </tr>
            </thead>
            <tbody>
                {summary_rows_html}
                <tr class="summary-total">
                    <td>الإجمالي</td>
                    <td>{tot_qty:,.2f}</td>
                    <td>{tot_area:,.2f}</td>
                    <td>-</td>
                    <td>{net_amount:,.2f}</td>
                </tr>
            </tbody>
        </table>

        <!-- Electronic Verification Footer (No Signatures) -->
        <div class="footer-note">
            تم استخراج هذه الفاتورة إلكترونياً من نظام Antigravity Marble ERP - موثقة ومعتمدة محاسبياً بدون حاجة لتوقيع يدوي
        </div>

    </body>
    </html>
    """

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842) # A4
    rect = pymupdf.Rect(18, 18, 577, 824)
    page.insert_htmlbox(rect, html_content)

    if os.path.dirname(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    doc.close()
    return output_path

if __name__ == "__main__":
    test_dict = {
        "invoice_no": "فاتورة 27 / 10",
        "invoice_date": "2026-10-27",
        "client_name": "الحاج صلاح",
        "driver_name": "-",
        "car_no": "-",
        "loading_place": "-",
        "supervisor": "-",
        "notes": "28 صندوق × 220 تربيعة",
        "items": [
            {
                "package_no": "صندوق 28",
                "block_no": "-",
                "material_name": "ترابيع سيلفيا",
                "qty": 6160.0,
                "length": 0.60,
                "width": 0.30,
                "area": 1108.80,
                "price": 185.0,
                "total": 205128.0,
                "notes": "28 صندوق × 220 تربيعة"
            }
        ]
    }
    out = generate_invoice_pdf(test_dict, "test_out_matching_photo.pdf")
    print(f"Generated matching photo PDF: {out}, size: {os.path.getsize(out)} bytes")
