import requests
import os
import openpyxl
import time

BASE_URL = "http://127.0.0.1:8000"
WORK_DIR = r"I:\خالي أحمد جلال"

def test_full_flow():
    test_inv_no = f"TEST-{int(time.time())}"
    print("=== 1. Testing Repository Tree ===")
    r = requests.get(f"{BASE_URL}/api/repository/tree")
    assert r.status_code == 200, f"Failed repo tree: {r.text}"
    tree = r.json()
    print(f"Total folders found: {tree.get('folders_count')}, total files: {tree.get('total_files')}")
    assert tree.get("folders_count") > 0, "No folders found!"

    print("\n=== 2. Testing Repository Excel Preview ===")
    first_folder = tree["tree"][0]
    excel_file = None
    for f in first_folder["files"]:
        if f["name"].endswith(".xlsx") and not f["name"].startswith("~$"):
            excel_file = f["rel_path"]
            break
    if excel_file:
        r = requests.get(f"{BASE_URL}/api/repository/preview", params={"path": excel_file})
        assert r.status_code == 200, f"Preview failed: {r.text}"
        preview = r.json()
        sheet_rows = preview.get("sheets_data", {}).get("ورقة1", [])
        print(f"Previewed file: {excel_file}, rows count in sheet 1: {len(sheet_rows)}")
        assert len(sheet_rows) > 0

    print("\n=== 3. Testing Invoice Creation with Hard-Disk Auto-Save ===")
    payload = {
        "invoice_no": test_inv_no,
        "invoice_date": "2026-10-27",
        "client_name": "الحاج جعفر",
        "driver_name": "محمد السائق",
        "car_no": "ن ق ر 5555",
        "loading_place": "شق التعبان - مصنع الأدهم",
        "supervisor": "أحمد جلال",
        "discount": 0,
        "tax": 0,
        "notes": "فاتورة اختبارية للتأكد من الحفظ المباشر داخل فولدر العميل ع الجهاز",
        "items": [
            {
                "parcel_no": 1,
                "block_no": "105",
                "material_name": "جلالة فص ممتاز",
                "qty": 20,
                "length": 2.50,
                "width": 1.40,
                "price": 380.0,
                "is_free": False,
                "notes": "فرز أول"
            },
            {
                "parcel_no": 2,
                "block_no": "106",
                "material_name": "سيلفيا بيج",
                "qty": 10,
                "length": 2.20,
                "width": 1.10,
                "price": 290.0,
                "is_free": True,
                "notes": "شغل فري (عينة مجانية للعميل)"
            }
        ]
    }
    r = requests.post(f"{BASE_URL}/api/invoices", json=payload)
    assert r.status_code == 200, f"Invoice creation failed: {r.text}"
    inv_data = r.json()
    inv_id = inv_data["invoice_id"]
    print(f"Created invoice ID: {inv_id}, invoice_no: {inv_data['invoice_no']}")

    # Check physical file on disk
    expected_file = os.path.join(WORK_DIR, "الحاج جعفر", f"2026-10-27 - {test_inv_no}.xlsx")
    print(f"Checking disk file: {expected_file}")
    assert os.path.exists(expected_file), f"File was not created at {expected_file}!"
    print(f" File successfully exists on disk! Size: {os.path.getsize(expected_file)} bytes")

    # Verify openpyxl read of the generated excel file
    wb = openpyxl.load_workbook(expected_file, data_only=False)
    sheet = wb.active
    print(f"Sheet title: {sheet.title}, right_to_left: {sheet.views.sheetView[0].rightToLeft}")
    assert sheet.views.sheetView[0].rightToLeft is True
    # Verify header labels
    print(f"Cell B1: {sheet['B1'].value}, Cell C1: {sheet['C1'].value}, Cell D1: {sheet['D1'].value}, Cell E1: {sheet['E1'].value}")
    assert sheet["B1"].value == "التاريخ"
    assert sheet["E1"].value == "الحاج جعفر"
    wb.close()

    print("\n=== 4. Testing Invoice Editing (PUT) with Disk Refresh ===")
    edit_payload = payload.copy()
    edit_payload["notes"] = "تم تعديل الفاتورة وإضافة بند إضافي"
    edit_payload["items"][0]["price"] = 400.0  # Modified price
    r = requests.put(f"{BASE_URL}/api/invoices/{inv_id}", json=edit_payload)
    assert r.status_code == 200, f"Update failed: {r.text}"
    print(f"Invoice {inv_id} updated successfully!")

    # Verify disk file updated
    assert os.path.exists(expected_file)
    print(f"Disk file updated successfully after edit!")

    print("\n=== 5. Testing Client Invoices List (Decoupled / Independent) ===")
    r = requests.get(f"{BASE_URL}/api/clients/الحاج جعفر/statement")
    assert r.status_code == 200
    stmt = r.json()
    print(f"Client: {stmt['client_name']}, Total Invoices: {len(stmt.get('invoices', []))}")
    assert len(stmt.get("invoices", [])) > 0
    found_test = any(inv["invoice_no"] == test_inv_no for inv in stmt["invoices"])
    assert found_test, f"{test_inv_no} not found in client invoices!"

    print("\n=== 6. Testing Dashboard Stats ===")
    r = requests.get(f"{BASE_URL}/api/dashboard/stats")
    assert r.status_code == 200
    stats = r.json()
    print(f"Dashboard stats: Total Sales = {stats['total_sales']}, Invoices = {stats.get('inv_count', 0)}, Disk Files = {stats.get('disk_files_count', 0)}")

    print("\n ALL COMPREHENSIVE TESTS PASSED SUCCESSFULLY! ")

if __name__ == "__main__":
    test_full_flow()
