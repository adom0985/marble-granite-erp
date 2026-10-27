import os
import pymupdf
from collections import defaultdict

def generate_invoice_pdf(invoice_dict, output_path):
    """
    Generates an official A4 PDF invoice matching the exact traditional marble workshop
    template requested by the user:
    - Strictly Right-to-Left (RTL) visual reading:
      * Top Meta Grid (yellow headers, crisp black borders, exact cell alignment).
      * Main Items Grid (Light blue headers, pink grand total bar).
      * Right-aligned Summary Card "ملخص الجرار" (yellow header, green sub-headers, green total).
    - Summary Table groups ONLY by material name / thickness (e.g. 'صني 3 سم', 'ترابيع سيلفيا').
      Never split by dimensions/lengths!
    - No corporate banner or footer signatures.
    """
    inv_no = invoice_dict.get("invoice_no", "INV-2026")
    inv_date = invoice_dict.get("invoice_date", "2026-10-27")
    client_name = invoice_dict.get("client_name", "الحاج صلاح")
    driver_name = invoice_dict.get("driver_name", "") or "-"
    car_no = invoice_dict.get("car_no", "") or "-"
    loading_place = invoice_dict.get("loading_place", "") or "-"
    supervisor = invoice_dict.get("supervisor", "") or "-"
    general_notes = invoice_dict.get("notes", "") or "-"
    items = invoice_dict.get("items", [])

    tot_qty = sum(float(it.get("qty") or 0) for it in items)
    tot_area = sum(float(it.get("area") or 0) for it in items)
    tot_amount = sum(float(it.get("total") or 0) for it in items)
    discount = float(invoice_dict.get("discount") or 0)
    net_amount = float(invoice_dict.get("net_amount") or (tot_amount - discount))

    # Main Items Table Rows (10 columns)
    # PyMuPDF lays out cells Left-to-Right in DOM order.
    # Therefore, DOM order:
    # 1. ملاحظات (Far Left) | 2. الإجمالي | 3. السعر | 4. المسطح | 5. عرض | 6. طول | 7. عدد | 8. نوع الخامه | 9. رقم البلوك | 10. رقم الطرد (Far Right)
    # In visual Arabic RTL, reading is:
    # رقم الطرد -> رقم البلوك -> نوع الخامه -> عدد -> طول -> عرض -> المسطح -> السعر -> الإجمالي -> ملاحظات
    rows_html = ""
    for idx, it in enumerate(items, 1):
        pkg = it.get("package_no") or "-"
        blk = it.get("block_no") or "-"
        mat = it.get("material_name", "")
        q = float(it.get("qty") or 0)
        l = float(it.get("length") or 0)
        w = float(it.get("width") or 0)
        ar = float(it.get("area") or 0)
        p = float(it.get("price") or 0)
        tot = float(it.get("total") or 0)
        note_str = it.get("notes") or "-"

        # Quantity formatting (integer if whole number)
        q_str = f"{q:,.0f}" if q.is_integer() else f"{q:,.2f}"

        rows_html += f"""
        <tr>
            <td style="border:1.5px solid #000; padding:5px 4px; text-align:center; font-size:11px;">{note_str}</td>
            <td style="border:1.5px solid #000; padding:5px 4px; text-align:center; font-weight:900; font-size:12.5px;">{tot:,.2f}</td>
            <td style="border:1.5px solid #000; padding:5px 4px; text-align:center;">{p:,.2f}</td>
            <td style="border:1.5px solid #000; padding:5px 4px; text-align:center; font-weight:bold;">{ar:,.2f}</td>
            <td style="border:1.5px solid #000; padding:5px 4px; text-align:center;">{w:.2f}</td>
            <td style="border:1.5px solid #000; padding:5px 4px; text-align:center;">{l:.2f}</td>
            <td style="border:1.5px solid #000; padding:5px 4px; text-align:center; font-weight:900;">{q_str}</td>
            <td style="border:1.5px solid #000; padding:5px 6px; text-align:center; font-weight:900; font-size:12.5px;">{mat}</td>
            <td style="border:1.5px solid #000; padding:5px 4px; text-align:center;">{blk}</td>
            <td style="border:1.5px solid #000; padding:5px 4px; text-align:center;">{pkg}</td>
        </tr>
        """

    # Group items for "ملخص الجرار"
    # STRICT RULE: Group ONLY by material_name / thickness! NEVER by length or width!
    summary_groups = defaultdict(lambda: {"qty": 0.0, "area": 0.0, "price": 0.0, "total": 0.0})
    for it in items:
        mat = (it.get("material_name") or "خامة").strip()
        summary_groups[mat]["qty"] += float(it.get("qty") or 0)
        summary_groups[mat]["area"] += float(it.get("area") or 0)
        summary_groups[mat]["price"] = float(it.get("price") or 0)
        summary_groups[mat]["total"] += float(it.get("total") or 0)

    summary_rows_html = ""
    for mat_name, g in summary_groups.items():
        g_q_str = f"{g['qty']:,.0f}" if g['qty'].is_integer() else f"{g['qty']:,.2f}"
        summary_rows_html += f"""
        <tr style="background:#ffffff;">
            <td style="border:1.5px solid #000; padding:6px 4px; text-align:center; font-weight:900; font-size:12.5px;">{g['total']:,.2f}</td>
            <td style="border:1.5px solid #000; padding:6px 4px; text-align:center;">{g['price']:,.2f}</td>
            <td style="border:1.5px solid #000; padding:6px 4px; text-align:center; font-weight:bold;">{g['area']:,.2f}</td>
            <td style="border:1.5px solid #000; padding:6px 4px; text-align:center; font-weight:bold;">{g_q_str}</td>
            <td style="border:1.5px solid #000; padding:6px 6px; text-align:center; font-weight:900; font-size:12.5px;">{mat_name}</td>
        </tr>
        """

    tot_q_str = f"{tot_qty:,.0f}" if tot_qty.is_integer() else f"{tot_qty:,.2f}"

    # General notes row (only if provided and informative)
    general_notes_row = ""
    if general_notes and general_notes != "-" and general_notes not in [it.get("notes") for it in items]:
        general_notes_row = f"""
        <tr>
            <td class="val" colspan="7" style="text-align:right; padding-right:12px; font-weight:bold; font-size:11.5px;">{general_notes}</td>
            <td class="lbl">ملاحظات عامة</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            margin: 0;
            padding: 12px;
            color: #000000;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        .meta-table td {{
            border: 1.5px solid #000000;
            padding: 5px 6px;
            text-align: center;
            font-size: 11.5px;
        }}
        .lbl {{
            background-color: #fef08a; /* Yellow */
            font-weight: 900;
            color: #000000;
        }}
        .val {{
            background-color: #ffffff;
            font-weight: bold;
            color: #000000;
        }}

        /* Main Items Table */
        .items-table th {{
            background-color: #dbeafe; /* Light Blue */
            color: #000000;
            font-weight: 900;
            border: 1.5px solid #000000;
            padding: 7px 3px;
            text-align: center;
            font-size: 12px;
        }}
        
        /* Characteristic Pink Grand Total Row */
        .pink-total-row td {{
            background-color: #fbcfe8 !important; /* Soft Pink */
            border: 1.5px solid #000000;
            padding: 7px 3px;
            font-weight: 900;
            font-size: 13px;
            text-align: center;
            color: #000000;
        }}

        /* "ملخص الجرار" Summary Table */
        .summary-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .sum-hdr {{
            background-color: #fef08a; /* Yellow */
            color: #000000;
            font-weight: 900;
            font-size: 13px;
            border: 1.5px solid #000000;
            padding: 6px;
            text-align: center;
        }}
        .sum-sub th {{
            background-color: #bbf7d0; /* Soft Green */
            color: #000000;
            font-weight: 900;
            border: 1.5px solid #000000;
            padding: 6px 3px;
            text-align: center;
            font-size: 11.5px;
        }}
        .sum-tot td {{
            background-color: #86efac !important; /* Bright Green */
            font-weight: 900;
            border: 1.5px solid #000000;
            padding: 7px 4px;
            text-align: center;
            color: #000000;
            font-size: 12.5px;
        }}
    </style>
    </head>
    <body>

        <!-- Exact Yellow Header Grid (8 columns aligned across rows) -->
        <table class="meta-table" style="margin-bottom: 12px;">
            <tr>
                <td class="val" style="width:17%;">{driver_name}</td>
                <td class="lbl" style="width:8%;">السائق</td>
                <td class="val" colspan="3" style="width:42%; font-size:14px; font-weight:900; color:#1e3a8a;">{client_name}</td>
                <td class="lbl" style="width:8%;">العميل</td>
                <td class="val" style="width:17%; font-weight:900;">{inv_date}</td>
                <td class="lbl" style="width:8%;">التاريخ</td>
            </tr>
            <tr>
                <td class="val" style="width:17%; font-weight:900; color:#b91c1c; font-size:13px;">{inv_no}</td>
                <td class="lbl" style="width:8%;">رقم الفاتوره</td>
                <td class="val" style="width:17%;">{supervisor}</td>
                <td class="lbl" style="width:8%;">المشرف</td>
                <td class="val" style="width:17%;">{loading_place}</td>
                <td class="lbl" style="width:8%;">مكان التحميل</td>
                <td class="val" style="width:17%;">{car_no}</td>
                <td class="lbl" style="width:8%;">رقم السيارة / الكونتر</td>
            </tr>
            {general_notes_row}
        </table>

        <!-- Main Items Table (10 columns, RTL Order) -->
        <table class="items-table">
            <thead>
                <tr>
                    <th style="width:12%;">ملاحظات</th>
                    <th style="width:13%;">الإجمالي</th>
                    <th style="width:8%;">السعر</th>
                    <th style="width:11%;">المسطح</th>
                    <th style="width:7%;">عرض</th>
                    <th style="width:7%;">طول</th>
                    <th style="width:8%;">عدد</th>
                    <th style="width:18%;">نوع الخامه</th>
                    <th style="width:8%;">رقم البلوك</th>
                    <th style="width:8%;">رقم الطرد</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
                <!-- Pink Grand Total Row -->
                <tr class="pink-total-row">
                    <td></td>
                    <td style="font-size:13.5px;">{net_amount:,.2f}</td>
                    <td></td>
                    <td>{tot_area:,.2f}</td>
                    <td></td>
                    <td></td>
                    <td>{tot_q_str}</td>
                    <td colspan="3" style="font-size:14px;">الإجمالي</td>
                </tr>
            </tbody>
        </table>

        <!-- "ملخص الجرار" Summary Card positioned at the right side -->
        <table style="width:100%; border:none; margin-top:14px;">
            <tr>
                <td style="width:38%; border:none; vertical-align:top;"></td>
                <td style="width:62%; border:none; padding:0; vertical-align:top;">
                    <table class="summary-table">
                        <thead>
                            <tr>
                                <th colspan="5" class="sum-hdr">ملخص الجرار</th>
                            </tr>
                            <tr class="sum-sub">
                                <th style="width:22%;">الإجمالي</th>
                                <th style="width:16%;">السعر</th>
                                <th style="width:18%;">كمية الأمتار</th>
                                <th style="width:16%;">عدد الترابيع</th>
                                <th style="width:28%;">الخامه و البيان</th>
                            </tr>
                        </thead>
                        <tbody>
                            {summary_rows_html}
                            <tr class="sum-tot">
                                <td>{net_amount:,.2f}</td>
                                <td>-</td>
                                <td>{tot_area:,.2f}</td>
                                <td>{tot_q_str}</td>
                                <td>الإجمالي</td>
                            </tr>
                        </tbody>
                    </table>
                </td>
            </tr>
        </table>

    </body>
    </html>
    """

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842) # A4 Standard
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
