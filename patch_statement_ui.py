import shutil

path_js = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\static\app.js"
with open(path_js, "r", encoding="utf-8") as f:
    content = f.read()

old_func_start = "async function showClientStatement(clientName) {"
old_func_end = "document.getElementById(\"client-statement-modal\").style.display = \"flex\";\n    } catch (e) {\n        alert(\"فشل تحميل الفواتير: \" + e.message);\n    }\n}"

new_code = """async function showClientStatement(clientName) {
    if (!clientName) return;
    try {
        const res = await fetch(`/api/clients/${encodeURIComponent(clientName)}/statement`);
        const stmt = await res.json();

        document.getElementById("stmt-client-title").innerText = `كشف حساب وسجل فواتير: ${stmt.client_name}`;
        
        const specialBtn = document.getElementById("stmt-download-special-btn");
        if (specialBtn) {
            specialBtn.style.display = "inline-flex";
            specialBtn.href = `/api/special-files/${encodeURIComponent(stmt.client_name)}/download`;
        }

        const debitEl = document.getElementById("stmt-debit");
        const creditEl = document.getElementById("stmt-credit");
        const balanceEl = document.getElementById("stmt-balance");

        if (debitEl) debitEl.innerText = `${Number(stmt.total_active_invoices || 0).toLocaleString()} ج.م`;
        if (creditEl) creditEl.innerText = `${Number(stmt.total_payments || 0).toLocaleString()} ج.م`;
        if (balanceEl) balanceEl.innerText = `${Number(stmt.net_remaining || 0).toLocaleString()} ج.م`;

        const tbody = document.getElementById("stmt-tbody");
        tbody.innerHTML = "";

        // Combine active invoices and payments
        let transactions = [];
        (stmt.active_invoices || []).forEach(inv => {
            transactions.push({
                type: 'invoice',
                date: inv.invoice_date,
                no: inv.invoice_no,
                details: `${inv.total_pieces ? inv.total_pieces + ' قطعة - ' : ''}${inv.notes || ''}`,
                debit: inv.net_amount,
                credit: 0,
                id: inv.id
            });
        });

        (stmt.payments || []).forEach(p => {
            transactions.push({
                type: 'payment',
                date: p.payment_date,
                no: `<span style="color:#15803d; font-weight:800;">${p.notes || 'واصل منه'}</span>`,
                details: `طريقة الدفع: ${p.payment_method || 'نقداً'}`,
                debit: 0,
                credit: p.amount_egp,
                id: p.id
            });
        });

        if (transactions.length > 0) {
            transactions.forEach(t => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${t.date}</td>
                    <td>${t.type === 'invoice' ? '<span class="badge badge-blue">فاتورة بضاعة</span>' : '<span class="badge badge-green">دفعة واصلة</span>'}</td>
                    <td><b>${t.no}</b></td>
                    <td>${t.details || '-'}</td>
                    <td style="color:${t.debit > 0 ? '#b91c1c' : '#64748b'}; font-weight:700;">${t.debit > 0 ? Number(t.debit).toLocaleString() + ' ج.م' : '-'}</td>
                    <td style="color:${t.credit > 0 ? '#15803d' : '#64748b'}; font-weight:700;">${t.credit > 0 ? Number(t.credit).toLocaleString() + ' ج.م' : '-'}</td>
                    <td style="font-weight:800; color:#1e3a8a;">
                        ${t.type === 'invoice' ? `<button class="btn btn-outline" style="padding:2px 8px; font-size:0.75rem;" onclick="closeModals(); viewInvoiceDetail(${t.id})">✏️ تفاصيل</button>` : '-'}
                    </td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:15px; color:#64748b;">لا توجد معاملات جارية مسجلة لهذا العميل بعد.</td></tr>`;
        }

        // Show archived invoices button if any exist
        if (stmt.archived_invoices && stmt.archived_invoices.length > 0) {
            const archTr = document.createElement("tr");
            archTr.innerHTML = `
                <td colspan="7" style="background:#f8fafc; text-align:center; padding:10px;">
                    <button class="btn btn-outline" style="font-size:0.85rem;" onclick="toggleArchivedInvoicesSection()">
                        📁 عرض أرشيف الفواتير السابقة المقفلة (${stmt.archived_invoices.length} فاتورة مسددة)
                    </button>
                    <div id="archived-invoices-list" style="display:none; margin-top:10px; max-height:200px; overflow-y:auto;">
                        <table class="data-table" style="font-size:0.8rem; background:#fff;">
                            <thead>
                                <tr style="background:#f1f5f9;">
                                    <th>رقم الفاتورة</th>
                                    <th>التاريخ</th>
                                    <th>المبلغ</th>
                                    <th>الحالة</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${stmt.archived_invoices.map(a => `
                                    <tr>
                                        <td>${a.invoice_no}</td>
                                        <td>${a.invoice_date}</td>
                                        <td>${Number(a.net_amount).toLocaleString()} ج.م</td>
                                        <td><span class="badge" style="background:#e2e8f0; color:#475569;">خالص ومقفل</span></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </td>
            `;
            tbody.appendChild(archTr);
        }

        // Add action buttons at the bottom of the statement modal if not already present
        let actionsDiv = document.getElementById("stmt-quick-actions");
        if (!actionsDiv) {
            actionsDiv = document.createElement("div");
            actionsDiv.id = "stmt-quick-actions";
            actionsDiv.style = "display:flex; gap:0.75rem; margin-top:1rem; flex-wrap:wrap; justify-content:space-between; align-items:center;";
            const modalBox = document.querySelector("#client-statement-modal .modal-box");
            if (modalBox) {
                modalBox.appendChild(actionsDiv);
            }
        }
        actionsDiv.innerHTML = `
            <div style="display:flex; gap:0.5rem;">
                <button class="btn btn-primary" onclick="startNewInvoiceForClient('${stmt.client_name}')">➕ عمل فاتورة جديدة له</button>
                <button class="btn btn-success" onclick="openPaymentModal('${stmt.client_name}')">💵 تسجيل دفعة واصلة منه</button>
            </div>
            <div>
                <button class="btn btn-outline" onclick="closeModals()">إغلاق</button>
            </div>
        `;

        document.getElementById("client-statement-modal").style.display = "flex";
    } catch (e) {
        alert("فشل تحميل كشف الحساب: " + e.message);
    }
}

function toggleArchivedInvoicesSection() {
    const el = document.getElementById("archived-invoices-list");
    if (el) {
        el.style.display = (el.style.display === "none" || !el.style.display) ? "block" : "none";
    }
}

async function submitPayment() {
    const clientName = document.getElementById("pay-client-name").value.trim();
    const payDate = document.getElementById("pay-date").value || new Date().toISOString().split("T")[0];
    const amount = parseFloat(document.getElementById("pay-amount").value);
    const currency = document.getElementById("pay-currency").value || "EGP";
    const rate = parseFloat(document.getElementById("pay-rate").value) || 1;
    const method = document.getElementById("pay-method").value || "نقداً";
    const notes = document.getElementById("pay-notes").value.trim() || "واصل منه";

    if (!clientName || isNaN(amount) || amount <= 0) {
        alert("يرجى إدخال اسم العميل ومبلغ الدفعة بشكل صحيح");
        return;
    }

    try {
        const res = await fetch("/api/payments", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                client_name: clientName,
                payment_date: payDate,
                amount: amount,
                currency: currency,
                exchange_rate: rate,
                payment_method: method,
                notes: notes
            })
        });
        const data = await res.json();
        if (data.status === "success") {
            alert(`تم تسجيل دفعة بقيمة ${amount} ج.م للعميل ${clientName} بنجاح، وتحديث ملف الإكسيل التابع له على الجهاز!`);
            closeModals();
            showClientStatement(clientName);
        } else {
            alert("حدث خطأ أثناء حفظ الدفعة: " + (data.detail || ""));
        }
    } catch (e) {
        alert("فشل الاتصال بالخادم: " + e.message);
    }
}

function openPaymentModal(clientName = "") {
    closeModals();
    const clInput = document.getElementById("pay-client-name");
    if (clInput) clInput.value = clientName;
    const dateInput = document.getElementById("pay-date");
    if (dateInput) dateInput.value = new Date().toISOString().split("T")[0];
    const modal = document.getElementById("payment-modal");
    if (modal) modal.style.display = "flex";
}"""

# Normalize
content_norm = content.replace("\r\n", "\n")
start_idx = content_norm.find(old_func_start)
end_idx = content_norm.find("alert(\"فشل تحميل الفواتير: \" + e.message);\n    }\n}") + len("alert(\"فشل تحميل الفواتير: \" + e.message);\n    }\n}")

assert start_idx != -1 and end_idx != -1, "Target indices not found!"

updated_content = content_norm[:start_idx] + new_code + content_norm[end_idx:]

with open(path_js, "w", encoding="utf-8") as f:
    f.write(updated_content)

shutil.copy2(path_js, r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\public\static\app.js")
print("Updated showClientStatement & payment functions in static/app.js and public/static/app.js!")
