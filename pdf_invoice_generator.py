import os
import pymupdf

def generate_invoice_pdf(invoice_dict, output_path):
    """
    Generates a beautifully formatted official A4 PDF invoice without signatures.
    """
    inv_no = invoice_dict.get("invoice_no", "INV-2026")
    inv_date = invoice_dict.get("invoice_date", "2026-10-27")
    client_name = invoice_dict.get("client_name", "الحاج صلاح")
    driver_name = invoice_dict.get("driver_name", "")
    car_no = invoice_dict.get("car_no", "")
    notes = invoice_dict.get("notes", "")
    items = invoice_dict.get("items", [])
    
    tot_qty = sum(float(it.get("qty") or 0) for it in items)
    tot_area = sum(float(it.get("area") or 0) for it in items)
    tot_amount = sum(float(it.get("total") or 0) for it in items)
    discount = float(invoice_dict.get("discount") or 0)
    net_amount = float(invoice_dict.get("net_amount") or (tot_amount - discount))
    paid_amount = float(invoice_dict.get("paid_amount") or 0)
    rem_amount = net_amount - paid_amount

    # Build HTML table rows
    rows_html = ""
    for idx, it in enumerate(items, 1):
        q = float(it.get("qty") or 0)
        l = float(it.get("length") or 0)
        w = float(it.get("width") or 0)
        ar = float(it.get("area") or 0)
        p = float(it.get("price") or 0)
        tot = float(it.get("total") or 0)
        dim_str = f"{l:.2f} × {w:.2f}" if (l > 0 and w > 0) else "-"
        note_str = it.get("notes") or ""
        pkg = it.get("package_no") or ""
        if pkg and pkg not in note_str:
            note_str = f"{pkg} - {note_str}".strip(" -")
            
        bg = "#ffffff" if idx % 2 == 1 else "#f8fafc"
        rows_html += f"""
        <tr style="background:{bg};">
            <td style="padding:6px; border:1px solid #cbd5e1; text-align:center;">{idx}</td>
            <td style="padding:6px; border:1px solid #cbd5e1; text-align:right; font-weight:bold;">{it.get('material_name', '')}</td>
            <td style="padding:6px; border:1px solid #cbd5e1; text-align:center;">{q:,.0f}</td>
            <td style="padding:6px; border:1px solid #cbd5e1; text-align:center; direction:ltr;">{dim_str}</td>
            <td style="padding:6px; border:1px solid #cbd5e1; text-align:center; font-weight:bold;">{ar:,.2f}</td>
            <td style="padding:6px; border:1px solid #cbd5e1; text-align:center;">{p:,.2f}</td>
            <td style="padding:6px; border:1px solid #cbd5e1; text-align:center; font-weight:bold; color:#1e3a8a;">{tot:,.2f}</td>
            <td style="padding:6px; border:1px solid #cbd5e1; text-align:right;">{note_str}</td>
        </tr>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: sans-serif;
            margin: 0;
            padding: 24px;
            color: #0f172a;
            direction: rtl;
        }}
        .header-box {{
            border-bottom: 3px double #1e3a8a;
            padding-bottom: 12px;
            margin-bottom: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .title {{
            font-size: 22px;
            font-weight: bold;
            color: #1e3a8a;
            margin: 0;
            text-align: center;
        }}
        .subtitle {{
            font-size: 13px;
            color: #64748b;
            text-align: center;
            margin-top: 4px;
        }}
        .info-grid {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 16px;
            background: #f1f5f9;
            border-radius: 8px;
        }}
        .info-grid td {{
            padding: 8px 12px;
            font-size: 13px;
            border: 1px solid #e2e8f0;
        }}
        .table-data {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-bottom: 16px;
        }}
        .table-data th {{
            background: #1e3a8a;
            color: #ffffff;
            padding: 8px 6px;
            border: 1px solid #1e3a8a;
            font-size: 12px;
            text-align: center;
        }}
        .tot-card {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        .tot-card td {{
            padding: 10px;
            font-size: 14px;
            border: 1px solid #cbd5e1;
        }}
    </style>
    </head>
    <body>
        <div class="header-box">
            <div class="title">فاتورة توريد رخام وجرانيت</div>
            <div class="subtitle">الاسطنبة الرسمية - محاجر ومصانع الرخام والجرانيت</div>
        </div>

        <table class="info-grid">
            <tr>
                <td style="width:33%;"><b>اسم العميل:</b> <span style="font-size:15px; color:#1e3a8a; font-weight:bold;">{client_name}</span></td>
                <td style="width:33%;"><b>رقم الفاتورة:</b> <span style="font-weight:bold;">{inv_no}</span></td>
                <td style="width:34%;"><b>تاريخ التوريد:</b> <span style="font-weight:bold;">{inv_date}</span></td>
            </tr>
            <tr>
                <td><b>سائق السيارة:</b> {driver_name or '-'}</td>
                <td><b>رقم السيارة:</b> {car_no or '-'}</td>
                <td><b>ملاحظات الفاتورة:</b> {notes or '-'}</td>
            </tr>
        </table>

        <table class="table-data">
            <thead>
                <tr>
                    <th style="width:5%;">م</th>
                    <th style="width:28%;">البيان والخامة</th>
                    <th style="width:10%;">العدد</th>
                    <th style="width:14%;">المقاس (طول × عرض)</th>
                    <th style="width:11%;">المسطح (م٢)</th>
                    <th style="width:10%;">سعر المتر</th>
                    <th style="width:12%;">الإجمالي (ج.م)</th>
                    <th style="width:10%;">ملاحظات</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>

        <table class="tot-card">
            <tr style="background:#fef08a; font-weight:bold;">
                <td style="width:35%; text-align:right;">إجمالي الكميات والمسطح:</td>
                <td style="width:30%; text-align:center;">{tot_qty:,.0f} قطعة ({tot_area:,.2f} م٢)</td>
                <td style="width:35%; text-align:center; font-size:16px; color:#1e3a8a; font-weight:900;">
                    صافي الفاتورة: {net_amount:,.2f} ج.م
                </td>
            </tr>
        </table>

        <!-- Note: Signatures block completely omitted as requested -->
    </body>
    </html>
    """

    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842) # A4
    rect = pymupdf.Rect(20, 20, 575, 822)
    page.insert_htmlbox(rect, html_content)

    if os.path.dirname(output_path): os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    doc.close()
    return output_path

if __name__ == "__main__":
    test_dict = {
        "invoice_no": "فاتورة 27 / 10",
        "invoice_date": "2026-10-27",
        "client_name": "الحاج صلاح",
        "items": [
            {
                "material_name": "ترابيع سيلفيا",
                "qty": 220,
                "length": 0.60,
                "width": 0.30,
                "area": 39.60,
                "price": 185.0,
                "total": 7326.0,
                "package_no": "28 صندوق",
                "notes": "منها 28 صندوق"
            }
        ]
    }
    out = generate_invoice_pdf(test_dict, "test_out_invoice.pdf")
    print(f"Generated test invoice PDF: {out}, size: {os.path.getsize(out)} bytes")
