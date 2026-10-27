path = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\static\index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

target = """                <div class="box-header">
                    <div class="box-title"><i class="fa-solid fa-users"></i> دليل وحسابات العملاء (كشوف الحساب والديون)</div>
                    <div style="display:flex; gap:0.5rem; align-items:center;">
                        <select id="client-statement-select" class="form-control" style="width:320px;" onchange="showClientStatement(this.value)">
                            <option value="">-- اختر عميل لعرض كشف الحساب --</option>
                        </select>
                        <button class="btn btn-success" onclick="openAddPaymentModal()"><i class="fa-solid fa-hand-holding-dollar"></i> تسجيل دفعة جديدة</button>
                    </div>
                </div>"""

vip_html = """

                <!-- VIP Master Cards for Salah, Reda, and Adham -->
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:1rem; margin-bottom:1.5rem;">
                    <div style="background: linear-gradient(135deg, #1e3a8a, #3b82f6); color:#fff; border-radius:12px; padding:1.25rem; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="background:#fef08a; color:#854d0e; font-size:0.75rem; font-weight:800; padding:3px 8px; border-radius:20px;">نسخة مطورة 2026</span>
                            <i class="fa-solid fa-crown" style="color:#fde047; font-size:1.2rem;"></i>
                        </div>
                        <h3 style="margin:8px 0 4px 0; font-size:1.25rem;">ملف الحاج صلاح الشامل</h3>
                        <p style="font-size:0.85rem; opacity:0.9; margin-bottom:12px;">38 فاتورة مسجلة بجميع المسميات الأصلية والدفعات</p>
                        <div style="display:flex; gap:6px;">
                            <button class="btn btn-warning" style="flex:1; padding:6px; font-size:0.85rem; font-weight:700;" onclick="showClientStatement('الحاج صلاح')">👁️ عرض السجل</button>
                            <a href="/api/special-files/الحاج صلاح/download" class="btn btn-outline" style="background:#fff; color:#1e3a8a; padding:6px 10px; font-size:0.85rem; font-weight:700;">📥 إكسيل مطور</a>
                        </div>
                    </div>

                    <div style="background: linear-gradient(135deg, #0f766e, #14b8a6); color:#fff; border-radius:12px; padding:1.25rem; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="background:#ccfbf1; color:#0f766e; font-size:0.75rem; font-weight:800; padding:3px 8px; border-radius:20px;">نسخة مطورة 2026</span>
                            <i class="fa-solid fa-gem" style="color:#a7f3d0; font-size:1.2rem;"></i>
                        </div>
                        <h3 style="margin:8px 0 4px 0; font-size:1.25rem;">ملف أحمد رضا الشامل</h3>
                        <p style="font-size:0.85rem; opacity:0.9; margin-bottom:12px;">26 فاتورة مسجلة بالأسماء الأصلية ودفعات واصل</p>
                        <div style="display:flex; gap:6px;">
                            <button class="btn btn-warning" style="flex:1; padding:6px; font-size:0.85rem; font-weight:700;" onclick="showClientStatement('أحمد رضا')">👁️ عرض السجل</button>
                            <a href="/api/special-files/أحمد رضا/download" class="btn btn-outline" style="background:#fff; color:#0f766e; padding:6px 10px; font-size:0.85rem; font-weight:700;">📥 إكسيل مطور</a>
                        </div>
                    </div>

                    <div style="background: linear-gradient(135deg, #7c2d12, #ea580c); color:#fff; border-radius:12px; padding:1.25rem; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="background:#ffedd5; color:#9a3412; font-size:0.75rem; font-weight:800; padding:3px 8px; border-radius:20px;">نسخة مطورة 2026</span>
                            <i class="fa-solid fa-truck-fast" style="color:#fed7aa; font-size:1.2rem;"></i>
                        </div>
                        <h3 style="margin:8px 0 4px 0; font-size:1.25rem;">ملف أدهم الشامل</h3>
                        <p style="font-size:0.85rem; opacity:0.9; margin-bottom:12px;">شحنات 1-9 ومستودع أمتار الخامات وورشة عرب مساعد</p>
                        <div style="display:flex; gap:6px;">
                            <button class="btn btn-warning" style="flex:1; padding:6px; font-size:0.85rem; font-weight:700;" onclick="showClientStatement('أدهم')">👁️ عرض السجل</button>
                            <a href="/api/special-files/أدهم/download" class="btn btn-outline" style="background:#fff; color:#7c2d12; padding:6px 10px; font-size:0.85rem; font-weight:700;">📥 إكسيل مطور</a>
                        </div>
                    </div>
                </div>"""

content_norm = content.replace("\r\n", "\n")
target_norm = target.replace("\r\n", "\n")
assert target_norm in content_norm, "Target not found!"
new_content = content_norm.replace(target_norm, target_norm + vip_html, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(new_content)
print("Successfully inserted VIP cards!")
