import os
import pymupdf
from collections import defaultdict

def generate_invoice_pdf(invoice_dict, output_path):
    """
    Generates an official A4 Landscape (بالعرض) PDF invoice matching the exact traditional
    marble workshop template requested by the user:
    - Orientation: A4 Landscape (842 x 595 pt) for generous width and perfect readability.
    - Strictly Right-to-Left (RTL) visual reading:
      * Top Meta Grid (yellow labels, bold values, crisp black borders).
      * Main Items Grid (light blue headers, bold numbers, pink grand total bar).
      * Right-aligned Summary Card "ملخص الجرار" (yellow header, green sub-headers, green total).
    - Summary Table groups ONLY by material name / thickness (e.g. 'صني 3 سم', 'ترابيع سيلفيا').
      Never split by dimensions/lengths!
    - Automatic pagination for multi-row invoices without any content clipping.
    - Strictly NO corporate banners or signatures.
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

    # Summary table data: group ONLY by material name / thickness! NEVER by length or width!
    summary_groups = defaultdict(lambda: {"qty": 0.0, "area": 0.0, "price": 0.0, "total": 0.0})
    for it in items:
        mat = (it.get("material_name") or "خامة").strip()
        is_free = bool(it.get("is_free", False)) or (float(it.get("price") or 0) == 0 and "فري" in (it.get("notes") or ""))
        if is_free and "فري" not in mat:
            mat_key = f"{mat} (فري)"
        else:
            mat_key = mat
        summary_groups[mat_key]["qty"] += float(it.get("qty") or 0)
        summary_groups[mat_key]["area"] += float(it.get("area") or 0)
        p = float(it.get("price") or 0)
        if p > 0:
            summary_groups[mat_key]["price"] = p
        summary_groups[mat_key]["total"] += float(it.get("total") or 0)

    summary_rows_html = ""
    for mat_name, g in summary_groups.items():
        g_q_str = f"{g['qty']:,.0f}" if float(g['qty']).is_integer() else f"{g['qty']:,.2f}"
        p_val = g['price']
        p_str = f"{p_val:,.2f}" if p_val > 0 else "0.00"
        summary_rows_html += f"""
        <tr style="background:#ffffff;">
            <td style="border:1.5px solid #000; padding:5px 4px; text-align:center; font-weight:900; font-size:12px;">{g['total']:,.2f}</td>
            <td style="border:1.5px solid #000; padding:5px 4px; text-align:center; font-size:11px;">{p_str}</td>
            <td style="border:1.5px solid #000; padding:5px 4px; text-align:center; font-weight:bold; font-size:11.5px;">{g['area']:,.3f}</td>
            <td style="border:1.5px solid #000; padding:5px 4px; text-align:center; font-weight:bold; font-size:11.5px;">{g_q_str}</td>
            <td style="border:1.5px solid #000; padding:5px 6px; text-align:center; font-weight:900; font-size:12px;">{mat_name}</td>
        </tr>
        """

    tot_q_str = f"{tot_qty:,.0f}" if float(tot_qty).is_integer() else f"{tot_qty:,.2f}"

    css_head = """
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
            margin: 0;
            padding: 0;
            color: #000000;
        }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        .meta-table td {
            border: 1.5px solid #000000;
            padding: 4px 6px;
            text-align: center;
            font-size: 11px;
        }
        .lbl {
            background-color: #fef08a; /* Yellow */
            font-weight: 900;
            color: #000000;
        }
        .val {
            background-color: #ffffff;
            font-weight: bold;
            color: #000000;
        }
        .items-table th {
            background-color: #dbeafe; /* Light Blue */
            color: #000000;
            font-weight: 900;
            border: 1.5px solid #000000;
            padding: 5px 3px;
            text-align: center;
            font-size: 11px;
        }
        .items-table td {
            border: 1.5px solid #000000;
            padding: 4px 3px;
            text-align: center;
            font-size: 11px;
        }
        .pink-total-row td {
            background-color: #fbcfe8 !important; /* Pink */
            border: 1.5px solid #000000;
            padding: 5px 3px;
            font-weight: 900;
            font-size: 12px;
            text-align: center;
            color: #000000;
        }
        .summary-table {
            width: 100%;
            border-collapse: collapse;
        }
        .sum-hdr {
            background-color: #fef08a; /* Yellow */
            color: #000000;
            font-weight: 900;
            font-size: 12px;
            border: 1.5px solid #000000;
            padding: 5px;
            text-align: center;
        }
        .sum-sub th {
            background-color: #bbf7d0; /* Soft Green */
            color: #000000;
            font-weight: 900;
            border: 1.5px solid #000000;
            padding: 4px 3px;
            text-align: center;
            font-size: 10.5px;
        }
        .sum-tot td {
            background-color: #86efac !important; /* Bright Green */
            font-weight: 900;
            border: 1.5px solid #000000;
            padding: 5px 4px;
            text-align: center;
            color: #000000;
            font-size: 11.5px;
        }
    </style>
    """

    meta_html = f"""
    <table class="meta-table" style="margin-bottom: 6px;">
        <tr>
            <td class="val" style="width:17%;">{driver_name}</td>
            <td class="lbl" style="width:8%;">السائق</td>
            <td class="val" colspan="3" style="width:42%; font-size:13.5px; font-weight:900; color:#1e3a8a;">{client_name}</td>
            <td class="lbl" style="width:8%;">العميل</td>
            <td class="val" style="width:17%; font-weight:900;">{inv_date}</td>
            <td class="lbl" style="width:8%;">التاريخ</td>
        </tr>
        <tr>
            <td class="val" style="width:17%; font-weight:900; color:#b91c1c; font-size:12.5px;">{inv_no}</td>
            <td class="lbl" style="width:8%;">رقم الفاتوره</td>
            <td class="val" style="width:17%;">{supervisor}</td>
            <td class="lbl" style="width:8%;">المشرف</td>
            <td class="val" style="width:17%;">{loading_place}</td>
            <td class="lbl" style="width:8%;">مكان التحميل</td>
            <td class="val" style="width:17%;">{car_no}</td>
            <td class="lbl" style="width:8%;">رقم السيارة / الكونتر</td>
        </tr>
    </table>
    """

    table_header = """
    <thead>
        <tr>
            <th style="width:14%;">ملاحظات</th>
            <th style="width:12%;">الإجمالي</th>
            <th style="width:8%;">السعر</th>
            <th style="width:10%;">المسطح</th>
            <th style="width:7%;">عرض</th>
            <th style="width:7%;">طول</th>
            <th style="width:7%;">عدد</th>
            <th style="width:17%;">نوع الخامه</th>
            <th style="width:9%;">كود الصنف</th>
            <th style="width:9%;">رقم الطرد</th>
        </tr>
    </thead>
    """

    def render_row(it):
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
        q_str = f"{q:,.0f}" if q.is_integer() else f"{q:,.2f}"

        return f"""
        <tr>
            <td style="font-size:10px;">{note_str}</td>
            <td style="font-weight:900; font-size:11.5px;">{tot:,.2f}</td>
            <td>{p:,.2f}</td>
            <td style="font-weight:bold;">{ar:,.3f}</td>
            <td>{w:.2f}</td>
            <td>{l:.2f}</td>
            <td style="font-weight:900;">{q_str}</td>
            <td style="font-weight:900; font-size:11.5px;">{mat}</td>
            <td>{blk}</td>
            <td>{pkg}</td>
        </tr>
        """

    summary_card_html = f"""
    <table style="width:100%; border:none; margin-top:10px;">
        <tr>
            <td style="width:35%; border:none; vertical-align:top;"></td>
            <td style="width:65%; border:none; padding:0; vertical-align:top;">
                <table class="summary-table">
                    <thead>
                        <tr>
                            <th colspan="5" class="sum-hdr">ملخص الجرار</th>
                        </tr>
                        <tr class="sum-sub">
                            <th style="width:22%;">الإجمالي</th>
                            <th style="width:16%;">السعر</th>
                            <th style="width:18%;">كمية الأمتار</th>
                            <th style="width:16%;">عدد الطاولات</th>
                            <th style="width:28%;">الخامه و البيان</th>
                        </tr>
                    </thead>
                    <tbody>
                        {summary_rows_html}
                        <tr class="sum-tot">
                            <td>{net_amount:,.2f}</td>
                            <td>-</td>
                            <td>{tot_area:,.3f}</td>
                            <td>{tot_q_str}</td>
                            <td>الإجمالي</td>
                        </tr>
                    </tbody>
                </table>
            </td>
        </tr>
    </table>
    """

    doc = pymupdf.open()
    rect = pymupdf.Rect(20, 16, 822, 579) # A4 Landscape printable rectangle

    # Pagination logic in Landscape:
    # If <= 13 items, fit entirely on 1 landscape page
    if len(items) <= 13:
        rows_str = "".join(render_row(it) for it in items)
        page_html = f"""
        <!DOCTYPE html><html><head><meta charset="utf-8">{css_head}</head><body>
        {meta_html}
        <table class="items-table">
            {table_header}
            <tbody>
                {rows_str}
                <tr class="pink-total-row">
                    <td></td>
                    <td style="font-size:12.5px;">{net_amount:,.2f}</td>
                    <td></td>
                    <td>{tot_area:,.3f}</td>
                    <td></td>
                    <td></td>
                    <td>{tot_q_str}</td>
                    <td colspan="3" style="font-size:13px;">الإجمالي</td>
                </tr>
            </tbody>
        </table>
        {summary_card_html}
        </body></html>
        """
        page = doc.new_page(width=842, height=595)
        page.insert_htmlbox(rect, page_html)
    else:
        # Multi-page Landscape layout
        if len(items) <= 40:
            chunks = [items[:20], items[20:]]
        else:
            chunks = [items[:20]]
            rem = items[20:]
            while rem:
                chunks.append(rem[:22])
                rem = rem[22:]

        total_pages = len(chunks)
        for p_idx, chunk in enumerate(chunks, 1):
            is_first = (p_idx == 1)
            is_last = (p_idx == total_pages)

            rows_str = "".join(render_row(it) for it in chunk)

            if is_first:
                header_part = meta_html
            else:
                header_part = f"""
                <div style="display:flex; justify-content:space-between; margin-bottom:6px; border-bottom:1.5px solid #000; padding-bottom:3px;">
                    <span style="font-size:12px; font-weight:900; color:#1e3a8a;">{inv_no} - العميل: {client_name} (استكمال البنود)</span>
                    <span style="font-size:11px; font-weight:bold; color:#64748b;">صفحة ( {p_idx} من {total_pages} )</span>
                </div>
                """

            if is_last:
                bottom_part = f"""
                <tr class="pink-total-row">
                    <td></td>
                    <td style="font-size:12.5px;">{net_amount:,.2f}</td>
                    <td></td>
                    <td>{tot_area:,.3f}</td>
                    <td></td>
                    <td></td>
                    <td>{tot_q_str}</td>
                    <td colspan="3" style="font-size:13px;">الإجمالي</td>
                </tr>
                </tbody></table>
                {summary_card_html}
                """
            else:
                bottom_part = f"""
                </tbody></table>
                <div style="text-align:center; font-size:10.5px; font-weight:bold; color:#475569; margin-top:5px;">--- يتبع تفاصيل البنود في الصفحة التالية ---</div>
                """

            page_html = f"""
            <!DOCTYPE html><html><head><meta charset="utf-8">{css_head}</head><body>
            {header_part}
            <table class="items-table">
                {table_header}
                <tbody>
                    {rows_str}
                    {bottom_part}
            </body></html>
            """
            page = doc.new_page(width=842, height=595)
            page.insert_htmlbox(rect, page_html)

    if os.path.dirname(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    doc.close()
    return output_path
