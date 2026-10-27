import shutil

path_html = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\static\index.html"
with open(path_html, "r", encoding="utf-8") as f:
    html = f.read()

# Section to insert in Dashboard
dashboard_target = """            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">"""

big_four_section = """            <!-- ==================== THE BIG FOUR MASTER ACCOUNTS ==================== -->
            <div class="card-box" style="margin-bottom: 1.5rem; background:#f8fafc; border: 2px solid #3b82f6; border-radius:12px; padding:1.25rem;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">
                    <div>
                        <h3 style="font-weight:900; color:#1e3a8a; font-size:1.3rem; margin:0 0 4px 0;">
                            <i class="fa-solid fa-crown" style="color:#eab308;"></i> بوابة الحسابات وملفات الشغل الرئيسية (الأربعة الكبار)
                        </h3>
                        <span style="font-size:0.88rem; color:#64748b; font-weight:600;">الحسابات الأساسية التي طلبتها في الواجهة الرئيسية - وباقي العملاء متاحون بالقوائم في أي وقت</span>
                    </div>
                    <span class="badge badge-blue" style="font-size:0.85rem; padding:6px 12px; font-weight:800;">النسخة المطورة 2026</span>
                </div>

                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap:1rem;">
                    <!-- 1. الحاج صلاح -->
                    <div style="background: linear-gradient(135deg, #1e3a8a, #2563eb); color:#fff; border-radius:10px; padding:1.2rem; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="background:#fef08a; color:#854d0e; font-size:0.75rem; font-weight:800; padding:2px 8px; border-radius:12px;">عميل رئيسي</span>
                            <i class="fa-solid fa-crown" style="color:#fde047;"></i>
                        </div>
                        <h4 style="margin:10px 0 4px 0; font-size:1.2rem; font-weight:900;">ملف الحاج صلاح</h4>
                        <p style="font-size:0.82rem; opacity:0.9; margin-bottom:12px;">38 فاتورة مسجلة بجميع المسميات وسجل واصل والدينار</p>
                        <div style="display:flex; flex-direction:column; gap:6px;">
                            <div style="display:flex; gap:6px;">
                                <button class="btn btn-warning" style="flex:1; padding:6px; font-size:0.82rem; font-weight:800;" onclick="showClientStatement('الحاج صلاح')">👁️ فتح الحساب</button>
                                <a href="/api/special-files/الحاج صلاح/download" class="btn btn-outline" style="background:#fff; color:#1e3a8a; padding:6px 8px; font-size:0.82rem; font-weight:800;" download>📥 إكسيل مطور</a>
                            </div>
                            <button class="btn btn-outline" style="background:rgba(255,255,255,0.15); color:#fff; border:1px solid rgba(255,255,255,0.4); padding:4px; font-size:0.8rem;" onclick="startNewInvoiceForClient('الحاج صلاح')">➕ عمل فاتورة جديدة له</button>
                        </div>
                    </div>

                    <!-- 2. أحمد رضا -->
                    <div style="background: linear-gradient(135deg, #0f766e, #0d9488); color:#fff; border-radius:10px; padding:1.2rem; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="background:#ccfbf1; color:#0f766e; font-size:0.75rem; font-weight:800; padding:2px 8px; border-radius:12px;">عميل رئيسي</span>
                            <i class="fa-solid fa-gem" style="color:#a7f3d0;"></i>
                        </div>
                        <h4 style="margin:10px 0 4px 0; font-size:1.2rem; font-weight:900;">ملف أحمد رضا</h4>
                        <p style="font-size:0.82rem; opacity:0.9; margin-bottom:12px;">26 فاتورة مسجلة وصافي القديم ودفعات علي السيوفي</p>
                        <div style="display:flex; flex-direction:column; gap:6px;">
                            <div style="display:flex; gap:6px;">
                                <button class="btn btn-warning" style="flex:1; padding:6px; font-size:0.82rem; font-weight:800;" onclick="showClientStatement('أحمد رضا')">👁️ فتح الحساب</button>
                                <a href="/api/special-files/أحمد رضا/download" class="btn btn-outline" style="background:#fff; color:#0f766e; padding:6px 8px; font-size:0.82rem; font-weight:800;" download>📥 إكسيل مطور</a>
                            </div>
                            <button class="btn btn-outline" style="background:rgba(255,255,255,0.15); color:#fff; border:1px solid rgba(255,255,255,0.4); padding:4px; font-size:0.8rem;" onclick="startNewInvoiceForClient('أحمد رضا')">➕ عمل فاتورة جديدة له</button>
                        </div>
                    </div>

                    <!-- 3. أدهم -->
                    <div style="background: linear-gradient(135deg, #7c2d12, #c2410c); color:#fff; border-radius:10px; padding:1.2rem; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="background:#ffedd5; color:#9a3412; font-size:0.75rem; font-weight:800; padding:2px 8px; border-radius:12px;">توريد وشحنات</span>
                            <i class="fa-solid fa-truck-fast" style="color:#fed7aa;"></i>
                        </div>
                        <h4 style="margin:10px 0 4px 0; font-size:1.2rem; font-weight:900;">ملف أدهم الشامل</h4>
                        <p style="font-size:0.82rem; opacity:0.9; margin-bottom:12px;">شحنات 1-9 وإجمالي أمتار الخامات وورشة عرب مساعد</p>
                        <div style="display:flex; flex-direction:column; gap:6px;">
                            <div style="display:flex; gap:6px;">
                                <button class="btn btn-warning" style="flex:1; padding:6px; font-size:0.82rem; font-weight:800;" onclick="showClientStatement('أدهم')">👁️ فتح الحساب</button>
                                <a href="/api/special-files/أدهم/download" class="btn btn-outline" style="background:#fff; color:#7c2d12; padding:6px 8px; font-size:0.82rem; font-weight:800;" download>📥 إكسيل مطور</a>
                            </div>
                            <button class="btn btn-outline" style="background:rgba(255,255,255,0.15); color:#fff; border:1px solid rgba(255,255,255,0.4); padding:4px; font-size:0.8rem;" onclick="startNewInvoiceForClient('أدهم')">➕ عمل فاتورة جديدة له</button>
                        </div>
                    </div>

                    <!-- 4. صديق جعفر -->
                    <div style="background: linear-gradient(135deg, #4c1d95, #6d28d9); color:#fff; border-radius:10px; padding:1.2rem; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="background:#f3e8ff; color:#6b21a8; font-size:0.75rem; font-weight:800; padding:2px 8px; border-radius:12px;">عميل رئيسي</span>
                            <i class="fa-solid fa-scale-balanced" style="color:#d8b4fe;"></i>
                        </div>
                        <h4 style="margin:10px 0 4px 0; font-size:1.2rem; font-weight:900;">ملف صديق جعفر</h4>
                        <p style="font-size:0.82rem; opacity:0.9; margin-bottom:12px;">فواتير 1-5 وحساب قديم وإجمالي الدفعات الواصلة</p>
                        <div style="display:flex; flex-direction:column; gap:6px;">
                            <div style="display:flex; gap:6px;">
                                <button class="btn btn-warning" style="flex:1; padding:6px; font-size:0.82rem; font-weight:800;" onclick="showClientStatement('صديق جعفر')">👁️ فتح الحساب</button>
                                <a href="/api/special-files/صديق جعفر/download" class="btn btn-outline" style="background:#fff; color:#4c1d95; padding:6px 8px; font-size:0.82rem; font-weight:800;" download>📥 إكسيل مطور</a>
                            </div>
                            <button class="btn btn-outline" style="background:rgba(255,255,255,0.15); color:#fff; border:1px solid rgba(255,255,255,0.4); padding:4px; font-size:0.8rem;" onclick="startNewInvoiceForClient('صديق جعفر')">➕ عمل فاتورة جديدة له</button>
                        </div>
                    </div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">"""

html_norm = html.replace("\r\n", "\n")
target_norm = dashboard_target.replace("\r\n", "\n")
assert target_norm in html_norm, "Dashboard target not found!"
new_html = html_norm.replace(target_norm, big_four_section, 1)

with open(path_html, "w", encoding="utf-8") as f:
    f.write(new_html)

# Also copy to public/index.html
shutil.copy2(path_html, r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\public\index.html")
print("Updated Dashboard with Big Four in static and public index.html!")

# Add startNewInvoiceForClient to static/app.js and public/static/app.js
path_js = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\static\app.js"
with open(path_js, "r", encoding="utf-8") as f:
    js_content = f.read()

helper_code = """
function startNewInvoiceForClient(clientName) {
    clearInvoiceForm();
    const clientInput = document.getElementById("inv-client-name");
    if (clientInput) {
        clientInput.value = clientName;
    }
    const newInvBtn = document.querySelector('[data-tab="new-invoice-pane"]');
    if (newInvBtn) {
        newInvBtn.click();
    }
}
"""

if "function startNewInvoiceForClient" not in js_content:
    js_content += helper_code
    with open(path_js, "w", encoding="utf-8") as f:
        f.write(js_content)
    shutil.copy2(path_js, r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\public\static\app.js")
    print("Added startNewInvoiceForClient to app.js and public/static/app.js!")
