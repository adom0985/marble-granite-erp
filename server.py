import os
import sqlite3
import re
import urllib.parse
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import openpyxl
import fitz

from database import get_connection, init_db
from excel_exporter import create_invoice_excel
from auth import authenticate_user, create_auth_token, verify_auth_token, extract_token_from_request

app = FastAPI(title="نظام إدارة وفواتير ومستودع ملفات الرخام والجرانيت", version="6.0")

@app.middleware("http")
async def security_and_routing_middleware(request: Request, call_next):
    p = request.scope.get("path", "")
    
    # 1. API rewrite if needed
    if p != "/" and not p.startswith("/static") and not p.startswith("/uploads") and not p.startswith("/api/"):
        p = "/api" + p
        request.scope["path"] = p

    # 2. Public paths that do NOT require authentication
    public_exact = ["/", "/api/auth/login", "/auth/login", "/favicon.ico"]
    if p in public_exact or p.startswith("/static/"):
        return await call_next(request)

    # 3. Security guard: check token for EVERY other endpoint
    token = extract_token_from_request(request)
    user_payload = verify_auth_token(token)
    if not user_payload:
        return JSONResponse(
            status_code=401,
            content={"detail": "غير مصرح - يرجى تسجيل الدخول أولاً", "auth_required": True}
        )

    request.state.user = user_payload
    return await call_next(request)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
IS_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

if IS_VERCEL:
    EXPORTS_DIR = "/tmp/exports"
    UPLOADS_DIR = "/tmp/uploads"
    WORK_DIR = "/tmp/work_dir"
else:
    EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
    UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
    WORK_DIR = r"I:\خالي أحمد جلال"

os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
if IS_VERCEL:
    os.makedirs(WORK_DIR, exist_ok=True)

# Pydantic models
class InvoiceItemModel(BaseModel):
    package_no: Optional[str] = ""
    block_no: Optional[str] = ""
    material_name: str
    qty: float
    length: float
    width: float
    area: Optional[float] = 0
    price: float
    total: Optional[float] = 0
    is_free: Optional[bool] = False
    notes: Optional[str] = ""

class InvoiceCreateModel(BaseModel):
    invoice_no: str
    invoice_date: str
    client_name: str
    driver_name: Optional[str] = ""
    car_no: Optional[str] = ""
    loading_place: Optional[str] = ""
    supervisor: Optional[str] = ""
    discount: Optional[float] = 0
    paid_amount: Optional[float] = 0
    notes: Optional[str] = ""
    items: List[InvoiceItemModel]

class PaymentCreateModel(BaseModel):
    client_name: str
    invoice_id: Optional[int] = None
    payment_date: str
    amount: float
    currency: Optional[str] = "EGP"
    exchange_rate: Optional[float] = 1.0
    payment_method: Optional[str] = "نقداً"
    notes: Optional[str] = ""

class PartnerExpenseModel(BaseModel):
    partner_name: str
    expense_date: str
    category: str
    description: str
    amount: float
    recipient: Optional[str] = ""
    notes: Optional[str] = ""

class PartnerCollectionModel(BaseModel):
    partner_name: str
    collection_date: str
    source_description: str
    amount: float
    currency: Optional[str] = "EGP"
    exchange_rate: Optional[float] = 1.0
    notes: Optional[str] = ""

class FactoryOpModel(BaseModel):
    factory_name: str
    op_date: str
    operation_type: str
    material_name: Optional[str] = ""
    meters: float
    unit_price: float
    paid_amount: Optional[float] = 0
    notes: Optional[str] = ""

class ClientCreateModel(BaseModel):
    name: str
    phone: Optional[str] = ""
    address: Optional[str] = ""
    opening_balance: Optional[float] = 0
    notes: Optional[str] = ""

class MaterialUpdateModel(BaseModel):
    name: str
    default_thickness: Optional[str] = "2 سم"
    default_price: float
    unit: Optional[str] = "م٢"
    notes: Optional[str] = ""

class ParseOrderTextModel(BaseModel):
    text: str

def calculate_truck_summary(items):
    """Generates the ملخص الجرار table automatically grouped by material + dimensions, separating free items"""
    agg = {}
    for it in items:
        mat = it["material_name"]
        w = it.get("width", 0)
        is_free = bool(it.get("is_free", False))
        p = 0 if is_free else it.get("price", 0)
        suffix = " ( فري )" if is_free else (f" ( {w} )" if w > 0 else "")
        label = f"{mat}{suffix}"
        if label not in agg:
            agg[label] = {
                "material_label": label,
                "total_qty": 0,
                "total_area": 0,
                "price": p,
                "is_free": is_free,
                "total_amount": 0
            }
        agg[label]["total_qty"] += it.get("qty", 0)
        agg[label]["total_area"] += it.get("area", 0)
    
    summary_list = []
    for k, v in agg.items():
        v["total_area"] = round(v["total_area"], 3)
        v["total_amount"] = 0 if v["is_free"] else round(v["total_area"] * v["price"], 2)
        summary_list.append(v)
    return summary_list

def save_invoice_to_client_folder(invoice_dict):
    r"""
    Saves an exact .xlsx file directly into the client's physical folder on disk at:
    I:\خالي أحمد جلال\<client_name>\<inv_date> - <inv_no>.xlsx
    """
    client_name = (invoice_dict.get("client_name") or "فواتير عامة").strip()
    safe_client = re.sub(r'[\\/*?:"<>|]', "", client_name)
    
    target_folder = os.path.join(WORK_DIR, safe_client)
    os.makedirs(target_folder, exist_ok=True)

    inv_date = str(invoice_dict.get("invoice_date", datetime.now().strftime("%Y-%m-%d")))
    inv_no = str(invoice_dict.get("invoice_no", "INV"))
    safe_file_name = f"{inv_date} - {inv_no}.xlsx".replace(":", "-").replace("/", "-")
    target_path = os.path.join(target_folder, safe_file_name)

    try:
        create_invoice_excel(invoice_dict, target_path)
        return target_path
    except Exception as e:
        print(f"Error auto-saving invoice to client folder: {e}")
        return None

# ----------------- AUTHENTICATION ENDPOINTS (نظام الدخول الآمن والحماية) -----------------

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login")
@app.post("/auth/login")
def login_endpoint(data: LoginRequest):
    user = authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="اسم المستخدم أو كلمة المرور غير صحيحة")
    token = create_auth_token(user)
    resp = JSONResponse(content={"status": "success", "token": token, "username": user})
    resp.set_cookie(
        key="auth_token",
        value=token,
        max_age=2592000,
        httponly=False,
        samesite="lax",
        secure=IS_VERCEL
    )
    return resp

@app.get("/api/auth/me")
@app.get("/auth/me")
def check_auth(request: Request):
    token = extract_token_from_request(request)
    payload = verify_auth_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="غير مصرح")
    return {"status": "authenticated", "username": payload["sub"]}

@app.post("/api/auth/logout")
@app.post("/auth/logout")
def logout_endpoint():
    resp = JSONResponse(content={"status": "logged_out"})
    resp.delete_cookie(key="auth_token", path="/")
    return resp

# ----------------- REPOSITORY ENDPOINTS (مستودع الملفات والشغل) -----------------

@app.get("/api/repository/tree")
def get_repository_tree():
    if not os.path.exists(WORK_DIR):
        return {"error": "المستودع غير متاح على القرص", "tree": []}
    
    tree = []
    # Root files
    root_files = []
    for it in os.listdir(WORK_DIR):
        p = os.path.join(WORK_DIR, it)
        if os.path.isfile(p) and not it.startswith("~$"):
            root_files.append({
                "name": it,
                "rel_path": it.replace("\\", "/"),
                "size_kb": round(os.path.getsize(p) / 1024, 1),
                "ext": os.path.splitext(it)[1].lower(),
                "mtime": datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M")
            })
    if root_files:
        tree.append({
            "folder_name": "الملفات والفواتير العامة",
            "rel_dir": "",
            "count": len(root_files),
            "files": root_files
        })
    
    # Subdirectories
    for d in sorted(os.listdir(WORK_DIR)):
        p = os.path.join(WORK_DIR, d)
        if os.path.isdir(p):
            sub_files = []
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.startswith("~$"):
                        continue
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, WORK_DIR).replace("\\", "/")
                    sub_files.append({
                        "name": f,
                        "rel_path": rel,
                        "size_kb": round(os.path.getsize(fp) / 1024, 1),
                        "ext": os.path.splitext(f)[1].lower(),
                        "mtime": datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d %H:%M")
                    })
            tree.append({
                "folder_name": d,
                "rel_dir": d,
                "count": len(sub_files),
                "files": sub_files
            })
    
    total_files = sum(f["count"] for f in tree)
    return {"total_files": total_files, "folders_count": len(tree), "tree": tree}

@app.get("/api/repository/download")
def download_repository_file(path: str):
    clean_path = path.replace("/", os.sep).replace("\\", os.sep).lstrip(os.sep)
    full_path = os.path.abspath(os.path.join(WORK_DIR, clean_path))
    if not full_path.startswith(os.path.abspath(WORK_DIR)) or not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="الملف غير موجود في المستودع")
    
    filename = os.path.basename(full_path)
    return FileResponse(full_path, filename=filename)

@app.get("/api/repository/preview")
def preview_repository_file(path: str):
    clean_path = path.replace("/", os.sep).replace("\\", os.sep).lstrip(os.sep)
    full_path = os.path.abspath(os.path.join(WORK_DIR, clean_path))
    filename = os.path.basename(full_path) or os.path.basename(path)

    if not os.path.exists(full_path):
        return {
            "type": "error",
            "filename": filename,
            "error": "الملف غير موجود على هذا المسار في القرص الصلب أو تعذر الوصول إليه"
        }
    
    ext = os.path.splitext(full_path)[1].lower()

    if ext == ".xlsx":
        try:
            wb = openpyxl.load_workbook(full_path, data_only=True)
            sheets_data = {}
            for s in wb.sheetnames[:6]:
                ws = wb[s]
                rows = []
                for r in range(1, min(ws.max_row + 1, 60)):
                    row_vals = [str(ws.cell(row=r, column=c).value or "") for c in range(1, min(ws.max_column + 1, 16))]
                    if any(v.strip() for v in row_vals):
                        rows.append(row_vals)
                sheets_data[s] = rows
            return {
                "type": "excel",
                "filename": filename,
                "sheets": wb.sheetnames,
                "sheets_data": sheets_data
            }
        except Exception as e:
            return {"type": "error", "filename": filename, "error": f"تعذر قراءة ملف الإكسيل: {str(e)}"}

    elif ext == ".pdf":
        try:
            doc = fitz.open(full_path)
            pages_text = [page.get_text() for page in doc]
            return {
                "type": "pdf",
                "filename": filename,
                "pages_count": len(doc),
                "text": "\n--- فاصل صفحات ---\n".join(pages_text[:5])
            }
        except Exception as e:
            return {"type": "error", "filename": filename, "error": f"تعذر قراءة ملف الـ PDF: {str(e)}"}

    elif ext in [".jpg", ".jpeg", ".png", ".jfif"]:
        return {
            "type": "image",
            "filename": filename,
            "download_url": f"/api/repository/download?path={urllib.parse.quote(path)}"
        }

    return {"type": "unsupported", "filename": filename, "download_url": f"/api/repository/download?path={urllib.parse.quote(path)}"}

@app.post("/api/repository/upload")
async def upload_file_to_repository(folder: str = Form(""), file: UploadFile = File(...)):
    dest_folder = os.path.join(WORK_DIR, folder) if folder else WORK_DIR
    os.makedirs(dest_folder, exist_ok=True)
    
    save_path = os.path.join(dest_folder, file.filename)
    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    return {"status": "success", "message": f"تم حفظ الملف بنجاح داخل مجلد {folder or 'الرئيسي'}"}

# ----------------- INVOICES API (CRUD + DISK AUTO-SAVE) -----------------

@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*), COALESCE(SUM(total_amount), 0), COALESCE(SUM(total_pieces), 0), COALESCE(SUM(total_area), 0) FROM invoices")
    inv_count, total_sales, total_pieces, total_area = c.fetchone()

    # Get total repository files count
    c.execute("SELECT COUNT(*) FROM clients")
    clients_count = c.fetchone()[0]

    # Count actual files on disk
    disk_files_count = 0
    if os.path.exists(WORK_DIR):
        for root, dirs, files in os.walk(WORK_DIR):
            disk_files_count += sum(1 for f in files if not f.startswith("~$"))

    c.execute("""
    SELECT material_name, SUM(qty) as total_qty, ROUND(SUM(area), 2) as total_m2, ROUND(SUM(total), 2) as total_revenue
    FROM invoice_items
    GROUP BY material_name
    ORDER BY total_revenue DESC
    LIMIT 6
    """)
    top_materials = [dict(row) for row in c.fetchall()]

    c.execute("SELECT * FROM invoices ORDER BY invoice_date DESC, id DESC LIMIT 5")
    recent_invoices = [dict(row) for row in c.fetchall()]

    conn.close()
    return {
        "inv_count": inv_count,
        "total_sales": round(total_sales, 2),
        "total_pieces": int(total_pieces),
        "total_area": round(total_area, 2),
        "clients_count": clients_count,
        "disk_files_count": disk_files_count,
        "top_materials": top_materials,
        "recent_invoices": recent_invoices
    }

@app.get("/api/invoices")
def get_invoices(client: Optional[str] = None, search: Optional[str] = None):
    conn = get_connection()
    c = conn.cursor()
    query = "SELECT * FROM invoices WHERE 1=1"
    params = []
    if client:
        query += " AND client_name = ?"
        params.append(client)
    if search:
        query += " AND (invoice_no LIKE ? OR client_name LIKE ? OR driver_name LIKE ?)"
        wild = f"%{search}%"
        params.extend([wild, wild, wild])
    query += " ORDER BY invoice_date DESC, id DESC"
    c.execute(query, params)
    invoices = [dict(row) for row in c.fetchall()]
    conn.close()
    return invoices

@app.get("/api/invoices/{invoice_id}")
def get_invoice_detail(invoice_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    inv = c.fetchone()
    if not inv:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice = dict(inv)
    c.execute("SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY row_index ASC, id ASC", (invoice_id,))
    items = [dict(row) for row in c.fetchall()]
    
    c.execute("SELECT * FROM invoice_attachments WHERE invoice_id = ?", (invoice_id,))
    attachments = [dict(row) for row in c.fetchall()]

    c.execute("SELECT phone FROM clients WHERE name = ?", (invoice["client_name"],))
    cl = c.fetchone()
    client_phone = cl["phone"] if cl and cl["phone"] else ""

    conn.close()

    invoice["items"] = items
    invoice["attachments"] = attachments
    invoice["client_phone"] = client_phone
    invoice["truck_summary"] = calculate_truck_summary(items)
    return invoice

@app.post("/api/invoices")
def create_invoice(data: InvoiceCreateModel):
    conn = get_connection()
    c = conn.cursor()

    computed_items = []
    tot_qty = 0
    tot_area = 0
    tot_amount = 0

    for idx, it in enumerate(data.items, start=1):
        q = float(it.qty or 0)
        l = float(it.length or 0)
        w = float(it.width or 0)
        is_free = bool(it.is_free)
        p = 0.0 if is_free else float(it.price or 0)
        ar = round(q * l * w, 4) if (q > 0 and l > 0 and w > 0) else float(it.area or 0)
        line_tot = 0.0 if is_free else round(ar * p, 2)

        tot_qty += q
        tot_area += ar
        tot_amount += line_tot

        note = it.notes or ""
        if is_free and "فري" not in note:
            note = ("فري (مجاني) " + note).strip()

        computed_items.append({
            "package_no": it.package_no or "",
            "block_no": it.block_no or "",
            "material_name": it.material_name,
            "qty": q,
            "length": l,
            "width": w,
            "area": ar,
            "price": p,
            "total": line_tot,
            "is_free": 1 if is_free else 0,
            "notes": note,
            "row_index": idx
        })

    net_amt = round(tot_amount - (data.discount or 0), 2)
    rem_amt = round(net_amt - (data.paid_amount or 0), 2)

    try:
        c.execute("""
        INSERT INTO invoices (
            invoice_no, invoice_date, client_name, driver_name, car_no,
            loading_place, supervisor, total_pieces, total_area, total_amount,
            discount, net_amount, paid_amount, remaining_amount, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.invoice_no, data.invoice_date, data.client_name, data.driver_name, data.car_no,
            data.loading_place, data.supervisor, tot_qty, round(tot_area, 3), tot_amount,
            data.discount, net_amt, data.paid_amount, rem_amt, data.notes
        ))
        inv_id = c.lastrowid

        for it in computed_items:
            c.execute("""
            INSERT INTO invoice_items (
                invoice_id, row_index, package_no, block_no, material_name,
                qty, length, width, area, price, total, is_free, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                inv_id, it["row_index"], it["package_no"], it["block_no"], it["material_name"],
                it["qty"], it["length"], it["width"], it["area"], it["price"], it["total"], it["is_free"], it["notes"]
            ))

        c.execute("INSERT OR IGNORE INTO clients (name) VALUES (?)", (data.client_name,))

        if data.paid_amount and data.paid_amount > 0:
            c.execute("""
            INSERT INTO client_payments (client_name, invoice_id, payment_date, amount, amount_egp, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (data.client_name, inv_id, data.invoice_date, data.paid_amount, data.paid_amount, f"دفعة نقدية مع الفاتورة رقم {data.invoice_no}"))

        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"رقم الفاتورة موجود مسبقاً أو هناك خطأ في البيانات: {str(e)}")
    finally:
        conn.close()

    # AUTO-SAVE DIRECTLY INTO CLIENT FOLDER ON HARD DISK (I:\خالي أحمد جلال\<client_name>)
    full_inv_dict = {
        "invoice_no": data.invoice_no,
        "invoice_date": data.invoice_date,
        "client_name": data.client_name,
        "driver_name": data.driver_name,
        "car_no": data.car_no,
        "loading_place": data.loading_place,
        "supervisor": data.supervisor,
        "items": computed_items
    }
    saved_path = save_invoice_to_client_folder(full_inv_dict)

    # AUTO-SYNC CLIENT MASTER STATEMENT EXCEL ON DISK AND BUNDLED FILES
    try:
        from client_statement_sync import sync_client_statement_excel
        sync_client_statement_excel(data.client_name)
    except Exception as e:
        print(f"Error syncing client excel statement: {e}")

    return {
        "status": "success", 
        "invoice_id": inv_id, 
        "invoice_no": data.invoice_no,
        "saved_to_disk": saved_path
    }

# EDIT INVOICE AT ANY TIME (AND AUTO-UPDATE DISK FILE)
@app.put("/api/invoices/{invoice_id}")
def update_invoice(invoice_id: int, data: InvoiceCreateModel):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    existing = c.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="الفاتورة غير موجودة")

    computed_items = []
    tot_qty = 0
    tot_area = 0
    tot_amount = 0

    for idx, it in enumerate(data.items, start=1):
        q = float(it.qty or 0)
        l = float(it.length or 0)
        w = float(it.width or 0)
        is_free = bool(it.is_free)
        p = 0.0 if is_free else float(it.price or 0)
        ar = round(q * l * w, 4) if (q > 0 and l > 0 and w > 0) else float(it.area or 0)
        line_tot = 0.0 if is_free else round(ar * p, 2)

        tot_qty += q
        tot_area += ar
        tot_amount += line_tot

        note = it.notes or ""
        if is_free and "فري" not in note:
            note = ("فري (مجاني) " + note).strip()

        computed_items.append({
            "package_no": it.package_no or "",
            "block_no": it.block_no or "",
            "material_name": it.material_name,
            "qty": q,
            "length": l,
            "width": w,
            "area": ar,
            "price": p,
            "total": line_tot,
            "is_free": 1 if is_free else 0,
            "notes": note,
            "row_index": idx
        })

    net_amt = round(tot_amount - (data.discount or 0), 2)
    rem_amt = round(net_amt - (data.paid_amount or 0), 2)

    try:
        c.execute("""
        UPDATE invoices SET
            invoice_no = ?, invoice_date = ?, client_name = ?, driver_name = ?, car_no = ?,
            loading_place = ?, supervisor = ?, total_pieces = ?, total_area = ?, total_amount = ?,
            discount = ?, net_amount = ?, paid_amount = ?, remaining_amount = ?, notes = ?
        WHERE id = ?
        """, (
            data.invoice_no, data.invoice_date, data.client_name, data.driver_name, data.car_no,
            data.loading_place, data.supervisor, tot_qty, round(tot_area, 3), tot_amount,
            data.discount, net_amt, data.paid_amount, rem_amt, data.notes, invoice_id
        ))

        c.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        for it in computed_items:
            c.execute("""
            INSERT INTO invoice_items (
                invoice_id, row_index, package_no, block_no, material_name,
                qty, length, width, area, price, total, is_free, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id, it["row_index"], it["package_no"], it["block_no"], it["material_name"],
                it["qty"], it["length"], it["width"], it["area"], it["price"], it["total"], it["is_free"], it["notes"]
            ))

        c.execute("INSERT OR IGNORE INTO clients (name) VALUES (?)", (data.client_name,))

        c.execute("DELETE FROM client_payments WHERE invoice_id = ?", (invoice_id,))
        if data.paid_amount and data.paid_amount > 0:
            c.execute("""
            INSERT INTO client_payments (client_name, invoice_id, payment_date, amount, amount_egp, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (data.client_name, invoice_id, data.invoice_date, data.paid_amount, data.paid_amount, f"دفعة نقدية مع الفاتورة رقم {data.invoice_no}"))

        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        raise HTTPException(status_code=400, detail=f"خطأ أثناء تعديل الفاتورة: {str(e)}")
    finally:
        conn.close()

    # AUTO-UPDATE DIRECTLY IN CLIENT FOLDER ON HARD DISK
    full_inv_dict = {
        "invoice_no": data.invoice_no,
        "invoice_date": data.invoice_date,
        "client_name": data.client_name,
        "driver_name": data.driver_name,
        "car_no": data.car_no,
        "loading_place": data.loading_place,
        "supervisor": data.supervisor,
        "items": computed_items
    }
    saved_path = save_invoice_to_client_folder(full_inv_dict)

    # AUTO-SYNC CLIENT MASTER STATEMENT EXCEL ON DISK AND BUNDLED FILES
    try:
        from client_statement_sync import sync_client_statement_excel
        sync_client_statement_excel(data.client_name)
    except Exception as e:
        print(f"Error syncing client excel statement: {e}")

    return {
        "status": "success", 
        "invoice_id": invoice_id, 
        "invoice_no": data.invoice_no, 
        "saved_to_disk": saved_path,
        "message": "تم تعديل الفاتورة وتحديث ملف الإكسيل في مجلد العميل بنجاح"
    }

@app.delete("/api/invoices/{invoice_id}")
def delete_invoice(invoice_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT client_name FROM invoices WHERE id = ?", (invoice_id,))
    inv = c.fetchone()
    client_name = inv["client_name"] if inv else None

    c.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
    c.execute("DELETE FROM client_payments WHERE invoice_id = ?", (invoice_id,))
    c.execute("DELETE FROM invoice_attachments WHERE invoice_id = ?", (invoice_id,))
    c.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()

    if client_name:
        try:
            from client_statement_sync import sync_client_statement_excel
            sync_client_statement_excel(client_name)
        except Exception as e:
            print(f"Error syncing client excel statement on delete: {e}")

    return {"status": "success", "message": "تم حذف الفاتورة بنجاح"}

@app.get("/api/invoices/{invoice_id}/export-excel")
def export_invoice_excel(invoice_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    inv = c.fetchone()
    if not inv:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice_dict = dict(inv)

    c.execute("SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY row_index ASC", (invoice_id,))
    invoice_dict["items"] = [dict(row) for row in c.fetchall()]
    conn.close()

    filename = f"Invoice_{invoice_dict['invoice_no']}_{invoice_dict['invoice_date']}.xlsx"
    out_file = os.path.join(EXPORTS_DIR, filename)
    create_invoice_excel(invoice_dict, out_file)

    return FileResponse(out_file, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.get("/api/invoices/{invoice_id}/whatsapp-link")
def get_whatsapp_link(invoice_id: int, phone: Optional[str] = None):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    inv = c.fetchone()
    if not inv:
        conn.close()
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if not phone:
        c.execute("SELECT phone FROM clients WHERE name = ?", (inv["client_name"],))
        cl = c.fetchone()
        phone = cl["phone"] if cl and cl["phone"] else ""
    conn.close()

    clean_phone = re.sub(r"[^\d]", "", phone or "")
    if clean_phone.startswith("0"):
        clean_phone = "20" + clean_phone[1:]

    msg = (
        f"🏛️ *شركة خالي أحمد جلال للرخام والجرانيت*\n"
        f"السلام عليكم يا حاج {inv['client_name']}\n"
        f"مرفق تفاصيل الفاتورة رقم: *{inv['invoice_no']}*\n"
        f"📅 *التاريخ:* {inv['invoice_date']}\n"
        f"🚛 *السيارة:* {inv['car_no'] or '-'} | *السائق:* {inv['driver_name'] or '-'}\n"
        f"📦 *إجمالي عدد الطاولات:* {inv['total_pieces']} قطعة\n"
        f"📐 *إجمالي المسطح:* {inv['total_area']} م٢\n"
        f"💰 *إجمالي الفاتورة:* {inv['net_amount']:,.2f} ج.م\n"
        f"💵 *المسدد:* {inv['paid_amount']:,.2f} ج.م\n"
        f"⚖️ *المتبقي المستحق:* {inv['remaining_amount']:,.2f} ج.م\n"
        f"-------------------------------\n"
        f"تحياتنا لكم ونتشرف دائماً بالتعامل معكم."
    )

    encoded = urllib.parse.quote(msg)
    wa_url = f"https://api.whatsapp.com/send?phone={clean_phone}&text={encoded}"
    return {"url": wa_url, "message": msg, "phone": clean_phone}

# ----------------- ATTACHMENTS (PHOTOS / RECEIPTS) -----------------

@app.post("/api/invoices/{invoice_id}/attachments")
async def upload_attachment(invoice_id: int, file: UploadFile = File(...), caption: Optional[str] = Form("")):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT client_name FROM invoices WHERE id = ?", (invoice_id,))
    inv = c.fetchone()
    client_name = inv["client_name"] if inv else ""

    ext = os.path.splitext(file.filename)[1].lower()
    save_name = f"inv_{invoice_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
    save_path = os.path.join(UPLOADS_DIR, save_name)

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    c.execute("""
    INSERT INTO invoice_attachments (invoice_id, client_name, file_path, file_name, file_type, caption)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (invoice_id, client_name, save_name, file.filename, file.content_type, caption))
    att_id = c.lastrowid
    conn.commit()
    conn.close()

    return {"status": "success", "attachment_id": att_id, "file_name": file.filename, "url": f"/uploads/{save_name}"}

@app.get("/uploads/{filename}")
def serve_upload(filename: str):
    fpath = os.path.join(UPLOADS_DIR, filename)
    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(fpath)

# ----------------- SMART ORDER / TEXT PARSER -----------------

@app.post("/api/orders/parse-text")
def parse_order_text(order: ParseOrderTextModel):
    lines = order.text.strip().split("\n")
    items = []
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT name, default_price FROM materials")
    known_materials = {r["name"]: r["default_price"] for r in c.fetchall()}
    conn.close()

    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        
        is_free = bool(re.search(r"(فري|هدية|مجاني|عينات|بلاش)", line))
        nums = [float(n) for n in re.findall(r"\b\d+(?:\.\d+)?\b", line)]
        
        qty = 0
        length = 0
        width = 0
        price = 0

        if len(nums) >= 3:
            qty = nums[0]
            length = nums[1]
            width = nums[2]
            if len(nums) >= 4 and not is_free:
                price = nums[3]

        mat_name = "رخام / جرانيت"
        for km, default_p in known_materials.items():
            first_word = km.split()[0]
            if first_word in line or km in line:
                mat_name = km
                if price == 0 and not is_free:
                    price = default_p
                break

        if qty > 0:
            area = round(qty * length * width, 4) if (length > 0 and width > 0) else 0
            total = 0.0 if is_free else round(area * price, 2)
            items.append({
                "package_no": "",
                "block_no": "",
                "material_name": mat_name,
                "qty": qty,
                "length": length,
                "width": width,
                "area": area,
                "price": price,
                "total": total,
                "is_free": is_free,
                "notes": "تم التفكيك آلياً" + (" (فري)" if is_free else "")
            })

    return {"status": "success", "parsed_items": items}

# ----------------- CLIENTS (STANDALONE PROFILES) -----------------

@app.get("/api/clients")
def get_clients():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT 
        c.*,
        COUNT(i.id) as invoices_count,
        COALESCE(SUM(i.total_amount), 0) as total_invoiced,
        COALESCE(SUM(i.total_pieces), 0) as total_pieces_count
    FROM clients c
    LEFT JOIN invoices i ON c.name = i.client_name
    GROUP BY c.id
    ORDER BY c.name ASC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.post("/api/clients")
def create_client(client: ClientCreateModel):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
        INSERT INTO clients (name, phone, address, opening_balance, notes)
        VALUES (?, ?, ?, ?, ?)
        """, (client.name, client.phone, client.address, client.opening_balance, client.notes))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="العميل موجود بالفعل")
    conn.close()
    return {"status": "success", "message": "تمت إضافة العميل بنجاح"}

@app.get("/api/clients/{client_name}/statement")
@app.get("/clients/{client_name}/statement")
def get_client_statement(client_name: str):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM clients WHERE name = ?", (client_name,))
    cl = c.fetchone()

    # Get invoices for this client independently
    c.execute("SELECT id, invoice_no, invoice_date, total_pieces, total_area, net_amount, paid_amount, remaining_amount, notes, status FROM invoices WHERE client_name = ? ORDER BY id ASC", (client_name,))
    invoices = [dict(r) for r in c.fetchall()]

    # Separate active invoices from closed/archived invoices
    active_invoices = [inv for inv in invoices if "متقفلة" not in (inv.get("status") or "")]
    archived_invoices = [inv for inv in invoices if "متقفلة" in (inv.get("status") or "")]

    # Get payments for this client independently
    c.execute("SELECT id, invoice_id, payment_date, amount, currency, exchange_rate, amount_egp, payment_method, notes FROM client_payments WHERE client_name = ? ORDER BY id ASC", (client_name,))
    payments = [dict(r) for r in c.fetchall()]

    conn.close()

    total_active_invoices = sum(inv["net_amount"] for inv in active_invoices)
    total_payments = sum(p["amount_egp"] for p in payments)
    net_remaining = round(total_active_invoices - total_payments, 2)

    return {
        "client_name": client_name,
        "phone": cl["phone"] if cl else "",
        "notes": cl["notes"] if cl else "",
        "total_active_invoices": total_active_invoices,
        "total_payments": total_payments,
        "net_remaining": net_remaining,
        "invoices": invoices,
        "active_invoices": active_invoices,
        "archived_invoices": archived_invoices,
        "payments": payments
    }

@app.get("/api/special-files/{client_name}/download")
@app.get("/special-files/{client_name}/download")
def download_special_file(client_name: str):
    mapping = {
        "الحاج صلاح": ("الحاج صلاح", "حساب الحاج صلاح - النسخة المطورة 2026.xlsx"),
        "أحمد رضا": ("أحمد رضا", "حساب احمد رضا - النسخة المطورة 2026.xlsx"),
        "أدهم": ("أدهم", "ملف أدهم الشامل - النسخة المطورة 2026.xlsx"),
        "صديق جعفر": ("صديق جعفر", "حساب صديق جعفر - النسخة المطورة 2026.xlsx")
    }
    if client_name in mapping:
        folder, filename = mapping[client_name]
        filepath = os.path.join(WORK_DIR, folder, filename)
        if not os.path.exists(filepath):
            bundled = os.path.join(BASE_DIR, "bundled_files", folder, filename)
            if os.path.exists(bundled):
                filepath = bundled
        if os.path.exists(filepath):
            return FileResponse(filepath, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    raise HTTPException(status_code=404, detail="الملف غير موجود")

@app.post("/api/payments")
@app.post("/payments")
def add_payment(p: PaymentCreateModel):
    conn = get_connection()
    c = conn.cursor()
    amount_egp = round(p.amount * (p.exchange_rate or 1.0), 2)
    c.execute("""
    INSERT INTO client_payments (client_name, invoice_id, payment_date, amount, currency, exchange_rate, amount_egp, payment_method, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (p.client_name, p.invoice_id, p.payment_date, p.amount, p.currency, p.exchange_rate, amount_egp, p.payment_method, p.notes))
    conn.commit()
    conn.close()

    # AUTO-SYNC CLIENT MASTER STATEMENT EXCEL ON DISK AND BUNDLED FILES
    try:
        from client_statement_sync import sync_client_statement_excel
        sync_client_statement_excel(p.client_name)
    except Exception as e:
        print(f"Error syncing client excel statement on payment: {e}")

    return {"status": "success", "amount_egp": amount_egp}

# ----------------- MATERIALS & PRICE MANAGEMENT -----------------

@app.get("/api/materials")
def get_materials():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM materials ORDER BY name ASC")
    mats = [dict(r) for r in c.fetchall()]
    conn.close()
    return mats

@app.post("/api/materials")
def update_or_create_material(m: MaterialUpdateModel):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM materials WHERE name = ?", (m.name,))
    existing = c.fetchone()
    if existing:
        c.execute("""
        UPDATE materials 
        SET default_price = ?, default_thickness = ?, unit = ?, notes = ?
        WHERE id = ?
        """, (m.default_price, m.default_thickness, m.unit, m.notes, existing["id"]))
    else:
        c.execute("""
        INSERT INTO materials (name, default_thickness, default_price, unit, notes)
        VALUES (?, ?, ?, ?, ?)
        """, (m.name, m.default_thickness, m.default_price, m.unit, m.notes))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"تم تحديث سعر {m.name} إلى {m.default_price} ج.م"}

# ----------------- PARTNERS (أحمد وحسين) -----------------

@app.get("/api/partners/summary")
def get_partners_summary():
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT * FROM partner_expenses ORDER BY expense_date DESC, id DESC")
    expenses = [dict(r) for r in c.fetchall()]

    c.execute("SELECT * FROM partner_collections ORDER BY collection_date DESC, id DESC")
    collections = [dict(r) for r in c.fetchall()]

    total_expenses = sum(e["amount"] for e in expenses)
    total_collections_egp = sum(col["amount_egp"] for col in collections)

    c.execute("SELECT category, SUM(amount) as cat_total FROM partner_expenses GROUP BY category")
    cat_breakdown = [dict(r) for r in c.fetchall()]

    conn.close()
    return {
        "total_expenses": round(total_expenses, 2),
        "total_collections_egp": round(total_collections_egp, 2),
        "expenses": expenses,
        "collections": collections,
        "categories_breakdown": cat_breakdown
    }

@app.post("/api/partners/expenses")
def add_partner_expense(e: PartnerExpenseModel):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO partner_expenses (partner_name, expense_date, category, description, amount, recipient, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (e.partner_name, e.expense_date, e.category, e.description, e.amount, e.recipient, e.notes))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/partners/collections")
def add_partner_collection(col: PartnerCollectionModel):
    conn = get_connection()
    c = conn.cursor()
    amount_egp = round(col.amount * (col.exchange_rate or 1.0), 2)
    c.execute("""
    INSERT INTO partner_collections (partner_name, collection_date, source_description, amount, currency, exchange_rate, amount_egp, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (col.partner_name, col.collection_date, col.source_description, col.amount, col.currency, col.exchange_rate, amount_egp, col.notes))
    conn.commit()
    conn.close()
    return {"status": "success"}

# ----------------- FACTORIES & PROCESSING -----------------

@app.get("/api/factories")
def get_factories():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM factory_accounts ORDER BY op_date DESC, id DESC")
    ops = [dict(r) for r in c.fetchall()]

    c.execute("""
    SELECT 
        factory_name, 
        COUNT(*) as ops_count,
        SUM(meters) as total_meters,
        SUM(total_amount) as total_cost,
        SUM(paid_amount) as total_paid,
        SUM(remaining_amount) as total_due
    FROM factory_accounts
    GROUP BY factory_name
    """)
    summary = [dict(r) for r in c.fetchall()]
    conn.close()
    return {"operations": ops, "summary": summary}

@app.post("/api/factories")
def add_factory_op(op: FactoryOpModel):
    conn = get_connection()
    c = conn.cursor()
    tot = round(op.meters * op.unit_price, 2)
    rem = round(tot - (op.paid_amount or 0), 2)
    c.execute("""
    INSERT INTO factory_accounts (factory_name, op_date, operation_type, material_name, meters, unit_price, total_amount, paid_amount, remaining_amount, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (op.factory_name, op.op_date, op.operation_type, op.material_name, op.meters, op.unit_price, tot, op.paid_amount, rem, op.notes))
    conn.commit()
    conn.close()
    return {"status": "success"}

# Serve Frontend static assets
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

# Mirror all /api/... routes without /api prefix for Vercel Serverless compatibility
for route in list(app.routes):
    if hasattr(route, "path") and route.path.startswith("/api/"):
        non_api_path = route.path[4:]
        if hasattr(route, "endpoint") and hasattr(route, "methods"):
            app.add_api_route(
                non_api_path,
                route.endpoint,
                methods=route.methods,
                include_in_schema=False
            )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
