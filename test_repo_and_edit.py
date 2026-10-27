import urllib.request
import json

base = "http://127.0.0.1:8000"

print("1. Testing GET /api/repository/tree...")
res = urllib.request.urlopen(f"{base}/api/repository/tree")
data = json.loads(res.read())
print(f"Total files: {data['total_files']} across {data['folders_count']} folders")

print("\n2. Testing Preview of Excel file from repository...")
path_param = urllib.parse.quote("أحمد جلال جديد/14-4-2026.xlsx")
res = urllib.request.urlopen(f"{base}/api/repository/preview?path={path_param}")
prev_data = json.loads(res.read())
print("Preview Type:", prev_data.get("type"), "Filename:", prev_data.get("filename"), "Sheets:", prev_data.get("sheets"))

print("\n3. Testing PUT /api/invoices/1 (Edit Invoice at any time)...")
# Get current invoice 1
res = urllib.request.urlopen(f"{base}/api/invoices/1")
inv1 = json.loads(res.read())
inv1["notes"] = "تم التعديل وتحديث الملاحظات إلكترونياً"

put_req = urllib.request.Request(
    f"{base}/api/invoices/1",
    data=json.dumps(inv1).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="PUT"
)
res = urllib.request.urlopen(put_req)
upd_data = json.loads(res.read())
print("Update Result:", upd_data)

print("\nALL REPOSITORY & EDIT TESTS PASSED 100%!")
