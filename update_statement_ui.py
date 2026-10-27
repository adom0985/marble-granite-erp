# 1. Update index.html
path_html = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\static\index.html"
with open(path_html, "r", encoding="utf-8") as f:
    html = f.read()

target_html = """            <div class="modal-header">
                <h3 id="stmt-client-title" style="font-weight:800; color:#1e3a8a;">كشف حساب العميل</h3>
                <button class="btn btn-outline" onclick="closeModals()">✕</button>
            </div>"""

replacement_html = """            <div class="modal-header">
                <div style="display:flex; align-items:center; gap:1rem;">
                    <h3 id="stmt-client-title" style="font-weight:800; color:#1e3a8a; margin:0;">كشف حساب العميل</h3>
                    <a id="stmt-download-special-btn" href="#" class="btn btn-success" style="display:none; font-weight:700; padding:4px 12px; font-size:0.85rem;"><i class="fa-solid fa-file-excel"></i> 📥 تحميل النسخة المطورة 2026 (.xlsx)</a>
                </div>
                <button class="btn btn-outline" onclick="closeModals()">✕</button>
            </div>"""

html_norm = html.replace("\r\n", "\n")
target_html_norm = target_html.replace("\r\n", "\n")
assert target_html_norm in html_norm, "Target HTML not found!"
new_html = html_norm.replace(target_html_norm, replacement_html, 1)
with open(path_html, "w", encoding="utf-8") as f:
    f.write(new_html)
print("Updated index.html!")

# 2. Update app.js
path_js = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\static\app.js"
with open(path_js, "r", encoding="utf-8") as f:
    js = f.read()

target_js = """        document.getElementById("stmt-client-title").innerText = `سجل فواتير وشغل: ${stmt.client_name}`;
        const tbody = document.getElementById("stmt-tbody");"""

replacement_js = """        document.getElementById("stmt-client-title").innerText = `سجل فواتير وشغل: ${stmt.client_name}`;
        
        const specialBtn = document.getElementById("stmt-download-special-btn");
        if (specialBtn) {
            if (["الحاج صلاح", "أحمد رضا", "أدهم"].includes(stmt.client_name)) {
                specialBtn.style.display = "inline-flex";
                specialBtn.href = `/api/special-files/${encodeURIComponent(stmt.client_name)}/download`;
            } else {
                specialBtn.style.display = "none";
            }
        }

        const tbody = document.getElementById("stmt-tbody");"""

js_norm = js.replace("\r\n", "\n")
target_js_norm = target_js.replace("\r\n", "\n")
assert target_js_norm in js_norm, "Target JS not found!"
new_js = js_norm.replace(target_js_norm, replacement_js, 1)
with open(path_js, "w", encoding="utf-8") as f:
    f.write(new_js)
print("Updated app.js!")
