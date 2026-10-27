import sqlite3
import os
import shutil

IS_VERCEL = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGINAL_DB_PATH = os.path.join(BASE_DIR, "data", "marble_erp.db")

DB_VERSION = "2026_10_28_v6"
if IS_VERCEL:
    os.makedirs("/tmp/data", exist_ok=True)
    DB_PATH = f"/tmp/data/marble_erp_{DB_VERSION}.db"
    if os.path.exists(ORIGINAL_DB_PATH):
        if not os.path.exists(DB_PATH):
            try:
                shutil.copy2(ORIGINAL_DB_PATH, DB_PATH)
            except Exception as e:
                print(f"Error copying DB to /tmp: {e}")
else:
    DB_PATH = ORIGINAL_DB_PATH
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Clients table
    c.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        phone TEXT,
        address TEXT,
        opening_balance REAL DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Materials table
    c.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        default_thickness TEXT,
        default_price REAL DEFAULT 0,
        unit TEXT DEFAULT 'م٢',
        notes TEXT
    )
    """)
    
    # Invoices table
    c.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT UNIQUE NOT NULL,
        invoice_date TEXT NOT NULL,
        client_name TEXT NOT NULL,
        driver_name TEXT,
        car_no TEXT,
        loading_place TEXT,
        supervisor TEXT,
        total_pieces REAL DEFAULT 0,
        total_area REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        discount REAL DEFAULT 0,
        net_amount REAL DEFAULT 0,
        paid_amount REAL DEFAULT 0,
        remaining_amount REAL DEFAULT 0,
        notes TEXT,
        status TEXT DEFAULT 'معتمدة',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Invoice items table
    c.execute("""
    CREATE TABLE IF NOT EXISTS invoice_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        row_index INTEGER,
        package_no TEXT,
        block_no TEXT,
        material_name TEXT NOT NULL,
        qty REAL DEFAULT 0,
        length REAL DEFAULT 0,
        width REAL DEFAULT 0,
        area REAL DEFAULT 0,
        price REAL DEFAULT 0,
        total REAL DEFAULT 0,
        is_free INTEGER DEFAULT 0,
        notes TEXT,
        FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE
    )
    """)
    
    # Check if is_free column exists in invoice_items, if not add it
    c.execute("PRAGMA table_info(invoice_items)")
    columns = [col["name"] for col in c.fetchall()]
    if "is_free" not in columns:
        c.execute("ALTER TABLE invoice_items ADD COLUMN is_free INTEGER DEFAULT 0")

    # Invoice attachments (photos, receipts, checks, slabs photos)
    c.execute("""
    CREATE TABLE IF NOT EXISTS invoice_attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        client_name TEXT,
        file_path TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_type TEXT,
        caption TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Client payments / collections
    c.execute("""
    CREATE TABLE IF NOT EXISTS client_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT NOT NULL,
        invoice_id INTEGER,
        payment_date TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'EGP',
        exchange_rate REAL DEFAULT 1,
        amount_egp REAL NOT NULL,
        payment_method TEXT DEFAULT 'نقداً',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Partner operational expenses (أحمد وحسين)
    c.execute("""
    CREATE TABLE IF NOT EXISTS partner_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partner_name TEXT NOT NULL,
        expense_date TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        recipient TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Partner collections / distributions
    c.execute("""
    CREATE TABLE IF NOT EXISTS partner_collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        partner_name TEXT NOT NULL,
        collection_date TEXT NOT NULL,
        source_description TEXT NOT NULL,
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'EGP',
        exchange_rate REAL DEFAULT 1,
        amount_egp REAL NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Factories accounts (نشر وتلميع ومسحات)
    c.execute("""
    CREATE TABLE IF NOT EXISTS factory_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        factory_name TEXT NOT NULL,
        op_date TEXT NOT NULL,
        operation_type TEXT NOT NULL,
        material_name TEXT,
        meters REAL DEFAULT 0,
        unit_price REAL DEFAULT 0,
        total_amount REAL DEFAULT 0,
        paid_amount REAL DEFAULT 0,
        remaining_amount REAL DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database schema upgraded successfully at:", DB_PATH)
