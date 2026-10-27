import sqlite3, openpyxl

conn = sqlite3.connect('data/marble_erp.db')
c = conn.cursor()
c.execute("SELECT SUM(net_amount) FROM invoices WHERE client_name = 'الحاج صلاح' AND status = 'جارية'")
tot_active = c.fetchone()[0]
c.execute("SELECT SUM(amount_egp) FROM client_payments WHERE client_name = 'الحاج صلاح'")
tot_paid = c.fetchone()[0]
rem = tot_active - tot_paid
print(f'DB Total Active Invoices: {tot_active:,.2f} | Paid: {tot_paid:,.2f} | Remaining: {rem:,.2f}')
conn.close()

wb = openpyxl.load_workbook(r'I:\خالي أحمد جلال\الحاج صلاح\حساب الحاج صلاح - النسخة المطورة 2026.xlsx', data_only=False)
ws = wb['الحاج صلاح جديد']
for r in range(1, ws.max_row+1):
    vals = [ws.cell(r, c).value for c in range(1, 6)]
    if any(vals):
        print(f'Excel Row {r}:', vals)
