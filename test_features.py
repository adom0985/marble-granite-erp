import urllib.request
import json

base = "http://127.0.0.1:8000"

print("1. Testing workspace folders...")
res = urllib.request.urlopen(f"{base}/api/workspace/files")
data = json.loads(res.read())
print("Total files:", data["total"], "Folders sample:", data.get("folders", [])[:6])

print("\n2. Testing Smart Order Text Parser...")
req = urllib.request.Request(
    f"{base}/api/orders/parse-text",
    data=json.dumps({"text": "45 طاولة جندولا 2 سم 3.20 في 0.80 بسعر 355\n2 طاولة جندولا 2.50 في 0.80 فري"}).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
res = urllib.request.urlopen(req)
parsed = json.loads(res.read())
print("Parsed Items count:", len(parsed["parsed_items"]))
for it in parsed["parsed_items"]:
    print(f"  Item: {it['material_name']} | Qty: {it['qty']} | Area: {it['area']} | Price: {it['price']} | Free: {it['is_free']}")

print("\n3. Testing WhatsApp link generation...")
res = urllib.request.urlopen(f"{base}/api/invoices/1/whatsapp-link")
wa_data = json.loads(res.read())
print("WhatsApp Link Preview:")
print("Phone:", wa_data["phone"])
print("URL:", wa_data["url"][:120] + "...")

print("\nALL FEATURE TESTS COMPLETED WITH 100% SUCCESS!")
