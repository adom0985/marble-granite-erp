path = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\static\app.js"
with open(path, "r", encoding="utf-8") as f:
    code = f.read()

# Replace previewRepoFile and renderRepoFiles button
old_button = """                    <button class="btn btn-primary" style="padding:3px 8px; font-size:0.8rem;" onclick="previewRepoFile('${f.rel_path}')">
                        <i class="fa-solid fa-eye"></i> معاينة سريعة
                    </button>"""

new_button = """                    <button class="btn btn-primary" style="padding:3px 8px; font-size:0.8rem;" onclick="previewRepoFile(decodeURIComponent('${encodeURIComponent(f.rel_path)}'))">
                        <i class="fa-solid fa-eye"></i> معاينة سريعة
                    </button>"""

old_preview = """async function previewRepoFile(relPath) {
    try {
        const res = await fetch(`/api/repository/preview?path=${encodeURIComponent(relPath)}`);
        const data = await res.json();

        document.getElementById("preview-modal-title").innerText = `معاينة: ${data.filename}`;
        const contentBox = document.getElementById("preview-modal-content");
        contentBox.innerHTML = "";

        if (data.type === "excel") {
            let html = `<div style="margin-bottom:10px; font-weight:700;">الشيتات المتاحة: ${data.sheets.join(" | ")}</div>`;
            const firstSheet = data.sheets[0];
            const rows = data.sheets_data[firstSheet] || [];

            html += `<div style="max-height:450px; overflow:auto; border:1px solid #cbd5e1; border-radius:6px;">`;
            html += `<table class="invoice-grid-table" style="font-size:0.85rem;">`;
            rows.forEach((r, idx) => {
                html += `<tr style="${idx === 0 ? 'background:#d9e1f2; font-weight:800;' : ''}">`;
                r.forEach(c => {
                    html += `<td>${c}</td>`;
                });
                html += `</tr>`;
            });
            html += `</table></div>`;
            contentBox.innerHTML = html;
        } else if (data.type === "pdf") {
            contentBox.innerHTML = `
                <div style="padding:10px; background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; max-height:450px; overflow-y:auto; white-space:pre-wrap; font-family:monospace; direction:rtl;">
                    ${data.text || 'لا يوجد نص قابل للقراءة المباشرة.'}
                </div>
            `;
        } else if (data.type === "image") {
            contentBox.innerHTML = `
                <div style="text-align:center;">
                    <img src="${data.download_url}" style="max-width:100%; max-height:450px; border-radius:8px;">
                </div>
            `;
        } else {
            contentBox.innerHTML = `<div style="text-align:center; padding:20px;">هذا النوع من الملفات يمكن تنزيله مباشرة: <a href="${data.download_url}" class="btn btn-success">تحميل الملف</a></div>`;
        }

        document.getElementById("repo-preview-modal").style.display = "flex";
    } catch (e) {
        alert("فشل المعاينة: " + e.message);
    }
}"""

new_preview = """async function previewRepoFile(relPath) {
    const fallbackName = relPath ? relPath.split("/").pop().split("\\\\").pop() : "الملف";
    try {
        const res = await fetch(`/api/repository/preview?path=${encodeURIComponent(relPath)}`);
        const data = await res.json();
        const displayName = data.filename || fallbackName;

        document.getElementById("preview-modal-title").innerText = `معاينة: ${displayName}`;
        const contentBox = document.getElementById("preview-modal-content");
        contentBox.innerHTML = "";

        if (data.type === "excel") {
            let html = `<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; background:#f1f5f9; padding:8px 12px; border-radius:6px;">`;
            html += `<span style="font-weight:700; color:#1e3a8a;"><i class="fa-solid fa-table"></i> الشيتات: ${(data.sheets || []).join(" | ")}</span>`;
            html += `<a href="/api/repository/download?path=${encodeURIComponent(relPath)}" class="btn btn-success" style="padding:3px 10px; font-size:0.8rem;" download><i class="fa-solid fa-download"></i> تحميل الإكسيل الأصلي</a>`;
            html += `</div>`;

            const firstSheet = (data.sheets && data.sheets[0]) || Object.keys(data.sheets_data || {})[0];
            const rows = (data.sheets_data && data.sheets_data[firstSheet]) || [];

            html += `<div style="max-height:480px; overflow:auto; border:1px solid #cbd5e1; border-radius:6px; box-shadow:inset 0 1px 3px rgba(0,0,0,0.05);">`;
            html += `<table class="invoice-grid-table" style="font-size:0.85rem; width:100%; border-collapse:collapse;">`;
            rows.forEach((r, idx) => {
                const isHdr = idx === 0;
                html += `<tr style="${isHdr ? 'background:#d9e1f2; font-weight:800; position:sticky; top:0;' : (idx % 2 === 0 ? 'background:#f8fafc;' : '')}">`;
                r.forEach(c => {
                    html += `<td style="padding:6px 8px; border:1px solid #cbd5e1; text-align:center;">${c}</td>`;
                });
                html += `</tr>`;
            });
            html += `</table></div>`;
            contentBox.innerHTML = html;
        } else if (data.type === "pdf") {
            contentBox.innerHTML = `
                <div style="display:flex; justify-content:flex-end; margin-bottom:8px;">
                    <a href="/api/repository/download?path=${encodeURIComponent(relPath)}" class="btn btn-success" style="padding:3px 10px; font-size:0.8rem;" download><i class="fa-solid fa-download"></i> تحميل الـ PDF</a>
                </div>
                <div style="padding:15px; background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; max-height:450px; overflow-y:auto; white-space:pre-wrap; font-family:monospace; direction:rtl; line-height:1.6;">
                    ${data.text || 'لا يوجد نص قابل للقراءة المباشرة.'}
                </div>
            `;
        } else if (data.type === "image") {
            contentBox.innerHTML = `
                <div style="text-align:center;">
                    <img src="${data.download_url}" style="max-width:100%; max-height:450px; border-radius:8px; box-shadow:0 4px 6px rgba(0,0,0,0.1);">
                    <div style="margin-top:10px;">
                        <a href="${data.download_url}" class="btn btn-primary" download><i class="fa-solid fa-download"></i> تحميل الصورة</a>
                    </div>
                </div>
            `;
        } else if (data.type === "error") {
            contentBox.innerHTML = `
                <div style="text-align:center; padding:30px; color:#b91c1c;">
                    <i class="fa-solid fa-triangle-exclamation" style="font-size:2.5rem; margin-bottom:10px;"></i>
                    <div style="font-weight:700; font-size:1.1rem; margin-bottom:15px;">${data.error || 'تعذر استعراض هذا الملف'}</div>
                    <a href="/api/repository/download?path=${encodeURIComponent(relPath)}" class="btn btn-primary" download>
                        <i class="fa-solid fa-download"></i> اضغط هنا لتحميل الملف وفتحه على جهازك
                    </a>
                </div>
            `;
        } else {
            contentBox.innerHTML = `
                <div style="text-align:center; padding:30px;">
                    <div style="font-size:1rem; margin-bottom:15px; color:#475569;">هذا الملف جاهز للتنزيل المباشر:</div>
                    <a href="${data.download_url || `/api/repository/download?path=${encodeURIComponent(relPath)}`}" class="btn btn-success" download>
                        <i class="fa-solid fa-download"></i> تحميل الملف
                    </a>
                </div>
            `;
        }

        document.getElementById("repo-preview-modal").style.display = "flex";
    } catch (e) {
        document.getElementById("preview-modal-title").innerText = `معاينة: ${fallbackName}`;
        document.getElementById("preview-modal-content").innerHTML = `
            <div style="text-align:center; padding:30px; color:#b91c1c;">
                <i class="fa-solid fa-triangle-exclamation" style="font-size:2.5rem; margin-bottom:10px;"></i>
                <div style="font-weight:700; font-size:1.1rem; margin-bottom:15px;">فشل الاتصال بالمعاينة: ${e.message}</div>
                <a href="/api/repository/download?path=${encodeURIComponent(relPath)}" class="btn btn-primary" download>
                    <i class="fa-solid fa-download"></i> اضغط هنا لتحميل الملف مباشرة
                </a>
            </div>
        `;
        document.getElementById("repo-preview-modal").style.display = "flex";
    }
}"""

code_norm = code.replace("\r\n", "\n")
old_btn_norm = old_button.replace("\r\n", "\n")
old_prev_norm = old_preview.replace("\r\n", "\n")

assert old_btn_norm in code_norm, "Button not found"
assert old_prev_norm in code_norm, "Preview not found"

code_norm = code_norm.replace(old_btn_norm, new_button, 1)
code_norm = code_norm.replace(old_prev_norm, new_preview, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(code_norm)
print("Updated static/app.js successfully!")
