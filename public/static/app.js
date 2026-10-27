// Smart API routing & Universal Authentication Interceptor
(function() {
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        options = options || {};
        options.headers = options.headers || {};



        const token = localStorage.getItem("erp_token");
        if (token) {
            if (options.headers instanceof Headers) {
                options.headers.set("Authorization", "Bearer " + token);
            } else {
                options.headers["Authorization"] = "Bearer " + token;
            }
        }

        return originalFetch(url, options).then(response => {
            if (response.status === 401 && typeof url === "string" && !url.includes("/auth/login")) {
                handleLogout(false);
            }
            return response;
        });
    };
})();


// ----------------- WHATSAPP SHARING -----------------

async function shareInvoiceWhatsApp() {
    if (!currentViewingInvoiceId) {
        alert("يرجى حفظ الفاتورة أولاً قبل إرسالها للعميل!");
        return;
    }
    try {
        const res = await fetch(`/api/invoices/${currentViewingInvoiceId}/whatsapp-link`);
        const data = await res.json();
        window.open(data.url, "_blank");
    } catch (e) {
        alert("تعذر فتح واتساب: " + e.message);
    }
}

function exportCurrentInvoiceExcel() {
    if (!currentViewingInvoiceId) {
        alert("يرجى حفظ الفاتورة أولاً!");
        return;
    }
    window.location.href = `/api/invoices/${currentViewingInvoiceId}/export-excel`;
}

// ----------------- ATTACHMENTS & PHOTOS -----------------

function openAttachPhotosModal() {
    if (!currentViewingInvoiceId) {
        alert("يرجى حفظ الفاتورة أولاً لتتمكن من إرفاق الصور بها!");
        return;
    }
    document.getElementById("attach-inv-id-lbl").innerText = `فاتورة رقم: ${document.getElementById("meta-inv-no").value}`;
    document.getElementById("attach-modal").style.display = "flex";
}

async function uploadInvoicePhoto() {
    const fileInput = document.getElementById("attach-file-input");
    const captionInput = document.getElementById("attach-caption-input");

    if (!fileInput.files || fileInput.files.length === 0) {
        alert("يرجى اختيار صورة أولاً!");
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("caption", captionInput.value);

    try {
        const res = await fetch(`/api/invoices/${currentViewingInvoiceId}/attachments`, {
            method: "POST",
            body: formData
        });
        const data = await res.json();
        if (res.ok) {
            alert("✅ تم رفع الصورة بنجاح وربطها بالفاتورة!");
            fileInput.value = "";
            captionInput.value = "";
            closeModals();
            viewInvoiceDetail(currentViewingInvoiceId);
        } else {
            alert("فشل الرفع: " + data.detail);
        }
    } catch (e) {
        alert(e.message);
    }
}

// ----------------- SMART ORDER TEXT PARSER -----------------

function openSmartOrderModal() {
    document.getElementById("smart-order-modal").style.display = "flex";
}

async function processSmartOrderText() {
    const text = document.getElementById("smart-order-input").value.trim();
    if (!text) {
        alert("يرجى كتابة أو لصق نص الطلب!");
        return;
    }

    try {
        const res = await fetch("/api/orders/parse-text", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({text: text})
        });
        const data = await res.json();
        if (res.ok && data.parsed_items && data.parsed_items.length > 0) {
            const tbody = document.getElementById("invoice-items-tbody");
            tbody.innerHTML = "";
            data.parsed_items.forEach(it => {
                addRowToInvoice(it);
            });
            recalculateAll();
            closeModals();
            alert(`✅ تم تفكيك وإدراج ${data.parsed_items.length} بنود بنجاح في الفاتورة!`);
        } else {
            alert("لم يتم العثور على أرقام أو مقاسات صالحة في النص المدخل.");
        }
    } catch (e) {
        alert(e.message);
    }
}

// ----------------- SAMPLE PRE-FILL -----------------

function prefillSampleInvoice() {
    document.getElementById("meta-inv-no").value = "INV-2026-006";
    document.getElementById("meta-inv-date").value = "2026-04-14";
    document.getElementById("meta-client-name").value = "الحاج جعفر";
    document.getElementById("meta-driver-name").value = "أحمد / 01017828662";
    document.getElementById("meta-car-no").value = "جرار نقل ثقيل";
    document.getElementById("meta-loading-place").value = "المصنع / شق الثعبان";
    document.getElementById("meta-supervisor").value = "-";
    document.getElementById("meta-paid").value = "200000";

    const tbody = document.getElementById("invoice-items-tbody");
    tbody.innerHTML = "";

    const sampleData = [
        {package_no: "1", block_no: "B1", material_name: "جندولا 2 سم", qty: 45, length: 3.2, width: 0.8, price: 355, is_free: false},
        {package_no: "2", block_no: "B1", material_name: "جندولا 2 سم", qty: 23, length: 3.2, width: 0.75, price: 345, is_free: false},
        {package_no: "3", block_no: "B2", material_name: "جندولا 2 سم", qty: 45, length: 2.8, width: 0.8, price: 355, is_free: false},
        {package_no: "4", block_no: "B3", material_name: "حلايب 2 سم", qty: 53, length: 3.15, width: 0.7, price: 450, is_free: false},
        {package_no: "5", block_no: "B4", material_name: "نيو حلايب 2 سم", qty: 36, length: 3.85, width: 0.7, price: 325, is_free: false},
        {package_no: "6", block_no: "B4", material_name: "نيو حلايب 2 سم", qty: 25, length: 3.15, width: 0.8, price: 335, is_free: false},
        {package_no: "7", block_no: "B5", material_name: "نيو حلايب 3 سم", qty: 20, length: 2.95, width: 0.8, price: 380, is_free: false},
        {package_no: "8", block_no: "B5", material_name: "جندولا 2 سم", qty: 2, length: 2.45, width: 0.8, price: 0, is_free: true, notes: "طاولات عينة فري"}
    ];

    sampleData.forEach(it => {
        it.area = parseFloat((it.qty * it.length * it.width).toFixed(4));
        it.total = it.is_free ? 0 : parseFloat((it.area * it.price).toFixed(2));
        addRowToInvoice(it);
    });

    recalculateAll();
}

function clearInvoiceForm() {
    if (confirm("هل أنت متأكد من تفريغ الشاشة وتحرير فاتورة جديدة؟")) {
        setupInitialInvoiceRows(6);
    }
}

// ----------------- DASHBOARD & STATS -----------------

async function loadDashboardStats() {
    try {
        const res = await fetch("/api/dashboard/stats");
        const data = await res.json();

        document.getElementById("stat-sales").innerText = Number(data.total_sales).toLocaleString() + " ج.م";
        document.getElementById("stat-pieces").innerText = Number(data.total_pieces).toLocaleString() + " طاولات وترابيع";
        document.getElementById("stat-area").innerText = Number(data.total_area).toLocaleString() + " م٢";
        document.getElementById("stat-disk-files").innerText = `${data.disk_files_count || 0} ملف في المستودع`;

        const topTbody = document.getElementById("top-materials-tbody");
        topTbody.innerHTML = "";
        data.top_materials.forEach(m => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td style="font-weight:700;">${m.material_name}</td>
                <td>${m.total_qty} قطعة</td>
                <td>${Number(m.total_m2).toLocaleString()} م٢</td>
                <td style="font-weight:700; color:#15803d;">${Number(m.total_revenue).toLocaleString()} ج.م</td>
            `;
            topTbody.appendChild(tr);
        });

        const recTbody = document.getElementById("recent-invoices-tbody");
        recTbody.innerHTML = "";
        data.recent_invoices.forEach(inv => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><b>${inv.invoice_no}</b></td>
                <td>${inv.invoice_date}</td>
                <td><b>${inv.client_name}</b></td>
                <td>${inv.total_pieces} طاولات (${inv.total_area} م٢)</td>
                <td><b>${Number(inv.total_amount).toLocaleString()} ج.م</b></td>
                <td>
                    <button class="btn btn-outline" style="padding:4px 8px; font-size:0.8rem;" onclick="viewInvoiceDetail(${inv.id})">✏️ تعديل / عرض</button>
                    <a href="/api/invoices/${inv.id}/export-excel" class="btn btn-success" style="padding:4px 8px; font-size:0.8rem;">📥 إكسيل</a>
                </td>
            `;
            recTbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error loading stats:", e);
    }
}

// ----------------- INVOICES ARCHIVE -----------------

async function loadInvoicesArchive() {
    const searchVal = document.getElementById("archive-search") ? document.getElementById("archive-search").value : "";
    try {
        const res = await fetch(`/api/invoices?search=${encodeURIComponent(searchVal)}`);
        const list = await res.json();
        const tbody = document.getElementById("archive-tbody");
        tbody.innerHTML = "";

        list.forEach(inv => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><b>${inv.invoice_no}</b></td>
                <td>${inv.invoice_date}</td>
                <td><b>${inv.client_name}</b></td>
                <td>${inv.driver_name || '-'} / ${inv.car_no || '-'}</td>
                <td>${inv.total_pieces}</td>
                <td>${inv.total_area} م٢</td>
                <td><b>${Number(inv.total_amount).toLocaleString()} ج.م</b></td>
                <td>
                    <div style="display:flex; gap:0.3rem;">
                        <button class="btn btn-outline" style="padding:4px 8px; font-size:0.8rem;" onclick="viewInvoiceDetail(${inv.id})">✏️ تعديل / عرض</button>
                        <a href="/api/invoices/${inv.id}/export-excel" class="btn btn-success" style="padding:4px 8px; font-size:0.8rem;">📥 إكسيل</a>
                        <button class="btn btn-primary" style="padding:4px 8px; font-size:0.8rem; background:#25d366; border-color:#25d366;" onclick="directShareWhatsApp(${inv.id})">💬 واتساب</button>
                        <button class="btn btn-danger" style="padding:4px 8px; font-size:0.8rem;" onclick="deleteInvoiceItem(${inv.id})">✕</button>
                    </div>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (e) {
        console.error(e);
    }
}

async function directShareWhatsApp(id) {
    try {
        const res = await fetch(`/api/invoices/${id}/whatsapp-link`);
        const data = await res.json();
        window.open(data.url, "_blank");
    } catch (e) {
        alert(e.message);
    }
}

async function viewInvoiceDetail(id) {
    try {
        const res = await fetch(`/api/invoices/${id}`);
        const inv = await res.json();
        currentViewingInvoiceId = inv.id;

        document.getElementById("meta-inv-no").value = inv.invoice_no;
        document.getElementById("meta-inv-date").value = inv.invoice_date;
        document.getElementById("meta-client-name").value = inv.client_name;
        document.getElementById("meta-driver-name").value = inv.driver_name || "";
        document.getElementById("meta-car-no").value = inv.car_no || "";
        document.getElementById("meta-loading-place").value = inv.loading_place || "";
        document.getElementById("meta-supervisor").value = inv.supervisor || "";
        document.getElementById("meta-discount").value = inv.discount || 0;
        document.getElementById("meta-paid").value = inv.paid_amount || 0;
        document.getElementById("meta-notes").value = inv.notes || "";

        const tbody = document.getElementById("invoice-items-tbody");
        tbody.innerHTML = "";
        inv.items.forEach(it => {
            addRowToInvoice(it);
        });
        recalculateAll();

        const attGallery = document.getElementById("invoice-attachments-gallery");
        attGallery.innerHTML = "";
        if (inv.attachments && inv.attachments.length > 0) {
            document.getElementById("invoice-attachments-section").style.display = "block";
            inv.attachments.forEach(att => {
                const div = document.createElement("div");
                div.className = "gallery-item";
                div.innerHTML = `
                    <a href="/uploads/${att.file_path}" target="_blank">
                        <img src="/uploads/${att.file_path}">
                    </a>
                    <span style="font-size:0.75rem; font-weight:700;">${att.caption || att.file_name}</span>
                `;
                attGallery.appendChild(div);
            });
        } else {
            document.getElementById("invoice-attachments-section").style.display = "none";
        }

        const saveBtn = document.getElementById("btn-save-invoice");
        saveBtn.innerHTML = '<i class="fa-solid fa-check-double"></i> حفظ التعديلات على الفاتورة';
        saveBtn.className = "btn btn-primary";

        document.getElementById("btn-send-whatsapp").style.display = "inline-flex";
        document.getElementById("btn-attach-photos").style.display = "inline-flex";
        document.getElementById("btn-export-excel-current").style.display = "inline-flex";

        document.querySelectorAll(".nav-tab-btn").forEach(t => t.classList.remove("active"));
        document.querySelector("[data-tab='new-invoice-pane']").classList.add("active");
        document.querySelectorAll(".tab-pane").forEach(p => p.style.display = "none");
        document.getElementById("new-invoice-pane").style.display = "block";

        window.scrollTo({top: 0, behavior: "smooth"});
    } catch (e) {
        alert("فشل تحميل الفاتورة: " + e.message);
    }
}

async function deleteInvoiceItem(id) {
    if (confirm("هل أنت متأكد من حذف هذه الفاتورة؟")) {
        try {
            const res = await fetch(`/api/invoices/${id}`, {method: "DELETE"});
            if (res.ok) {
                alert("تم حذف الفاتورة");
                loadInvoicesArchive();
                loadDashboardStats();
            }
        } catch (e) {
            alert(e.message);
        }
    }
}

// ----------------- CLIENTS (PROFILES & STANDALONE RECORDS) -----------------

async function loadClients() {
    try {
        const res = await fetch("/api/clients");
        clientsList = await res.json();
        const dlist = document.getElementById("clients-datalist");
        if (dlist) {
            dlist.innerHTML = "";
            clientsList.forEach(c => {
                const opt = document.createElement("option");
                opt.value = c.name;
                dlist.appendChild(opt);
            });
        }
    } catch (e) {
        console.error(e);
    }
}

async function loadClientsList() {
    await loadClients();
    const tbody = document.getElementById("clients-tbody");
    tbody.innerHTML = "";
    const select = document.getElementById("client-statement-select");
    select.innerHTML = '<option value="">-- اختر عميل لعرض فواتيره وشغله --</option>';

    clientsList.forEach(c => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><b>${c.name}</b></td>
            <td>${c.phone || '-'}</td>
            <td>${c.address || '-'}</td>
            <td><span class="badge badge-blue">${c.invoices_count || 0} فواتير</span></td>
            <td><b>${Number(c.total_invoiced || 0).toLocaleString()} ج.م</b></td>
            <td>${c.total_pieces_count || 0} طاولات</td>
            <td>
                <button class="btn btn-primary" style="padding:4px 8px; font-size:0.8rem;" onclick="showClientStatement('${c.name}')">📜 عرض فواتير العميل</button>
            </td>
        `;
        tbody.appendChild(tr);

        const opt = document.createElement("option");
        opt.value = c.name;
        opt.innerText = `${c.name} (${c.invoices_count || 0} فواتير)`;
        select.appendChild(opt);
    });
}

async function showClientStatement(clientName) {
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
}

// ----------------- PRICES MANAGEMENT TAB -----------------

async function renderPricesTab() {
    await loadMaterials();
    const tbody = document.getElementById("prices-tbody");
    tbody.innerHTML = "";

    materialsList.forEach(m => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><b>${m.name}</b></td>
            <td><input type="text" class="form-control" style="width:100px;" id="price-thick-${m.id}" value="${m.default_thickness || ''}"></td>
            <td><input type="number" step="any" class="form-control" style="width:120px;" id="price-val-${m.id}" value="${m.default_price}"></td>
            <td>${m.unit || 'م٢'}</td>
            <td><input type="text" class="form-control" id="price-notes-${m.id}" value="${m.notes || ''}"></td>
            <td>
                <button class="btn btn-success" style="padding:4px 10px; font-size:0.85rem;" onclick="saveMaterialPrice(${m.id}, '${m.name}')">💾 حفظ السعر</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function saveMaterialPrice(id, name) {
    const thick = document.getElementById(`price-thick-${id}`).value;
    const price = parseFloat(document.getElementById(`price-val-${id}`).value) || 0;
    const notes = document.getElementById(`price-notes-${id}`).value;

    try {
        const res = await fetch("/api/materials", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                name: name,
                default_thickness: thick,
                default_price: price,
                notes: notes
            })
        });
        if (res.ok) {
            alert(`✅ تم تحديث سعر خامة (${name}) إلى ${price} ج.م`);
            loadMaterials();
        }
    } catch (e) {
        alert(e.message);
    }
}

async function addNewMaterial() {
    const name = document.getElementById("new-mat-name").value.trim();
    const thick = document.getElementById("new-mat-thick").value.trim();
    const price = parseFloat(document.getElementById("new-mat-price").value) || 0;
    if (!name || price <= 0) {
        alert("يرجى ملء اسم الخامة وسعر المتر!");
        return;
    }

    try {
        const res = await fetch("/api/materials", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                name: name,
                default_thickness: thick,
                default_price: price
            })
        });
        if (res.ok) {
            alert(`✅ تمت إضافة الخامة (${name}) بنجاح`);
            document.getElementById("new-mat-name").value = "";
            document.getElementById("new-mat-price").value = "";
            renderPricesTab();
        }
    } catch (e) {
        alert(e.message);
    }
}

// ----------------- REPOSITORY (مستودع الملفات والشغل) -----------------

async function loadRepository() {
    try {
        const res = await fetch("/api/repository/tree");
        const data = await res.json();
        repoTreeData = data.tree || [];

        document.getElementById("repo-total-files").innerText = `${data.total_files || 0} ملف`;
        document.getElementById("repo-total-folders").innerText = `${data.folders_count || 0} مجلد`;

        const folderContainer = document.getElementById("repo-folder-pills");
        folderContainer.innerHTML = "";

        repoTreeData.forEach((fld, idx) => {
            const btn = document.createElement("button");
            btn.className = `btn ${idx === 0 ? 'btn-primary' : 'btn-outline'}`;
            btn.style.cssText = "margin:3px; font-size:0.85rem; padding:5px 12px;";
            btn.innerHTML = `<i class="fa-solid fa-folder"></i> ${fld.folder_name} <span class="badge" style="background:rgba(0,0,0,0.15);">${fld.count}</span>`;
            btn.onclick = () => {
                document.querySelectorAll("#repo-folder-pills button").forEach(b => {
                    b.className = "btn btn-outline";
                });
                btn.className = "btn btn-primary";
                selectedRepoFolder = fld;
                renderRepoFiles(fld.files);
            };
            folderContainer.appendChild(btn);
        });

        if (repoTreeData.length > 0) {
            selectedRepoFolder = repoTreeData[0];
            renderRepoFiles(repoTreeData[0].files);
        }
    } catch (e) {
        console.error(e);
    }
}

function renderRepoFiles(files) {
    const tbody = document.getElementById("repo-files-tbody");
    tbody.innerHTML = "";

    const search = document.getElementById("repo-search-input").value.trim().toLowerCase();
    const filtered = files.filter(f => !search || f.name.toLowerCase().includes(search));

    filtered.forEach(f => {
        const tr = document.createElement("tr");
        const isExcel = f.ext === ".xlsx";
        const isPdf = f.ext === ".pdf";
        const isImg = [".jpg", ".jpeg", ".png", ".jfif"].includes(f.ext);

        let icon = '<i class="fa-solid fa-file"></i>';
        if (isExcel) icon = '<i class="fa-solid fa-file-excel" style="color:#16a34a;"></i>';
        if (isPdf) icon = '<i class="fa-solid fa-file-pdf" style="color:#dc2626;"></i>';
        if (isImg) icon = '<i class="fa-solid fa-file-image" style="color:#8b5cf6;"></i>';

        tr.innerHTML = `
            <td>${icon} <b style="margin-right:6px;">${f.name}</b></td>
            <td><span class="badge badge-blue">${f.ext.toUpperCase()}</span></td>
            <td>${f.size_kb} KB</td>
            <td>${f.mtime || '-'}</td>
            <td>
                <div style="display:flex; gap:0.4rem;">
                    <a href="/api/repository/download?path=${encodeURIComponent(f.rel_path)}" class="btn btn-outline" style="padding:3px 8px; font-size:0.8rem;" download>
                        <i class="fa-solid fa-download"></i> تحميل الأصلي
                    </a>
                    <button class="btn btn-primary" style="padding:3px 8px; font-size:0.8rem;" onclick="previewRepoFile(decodeURIComponent('${encodeURIComponent(f.rel_path)}'))">
                        <i class="fa-solid fa-eye"></i> معاينة سريعة
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterRepoFiles() {
    if (selectedRepoFolder) {
        renderRepoFiles(selectedRepoFolder.files);
    }
}

async function previewRepoFile(relPath) {
    const fallbackName = relPath ? relPath.split("/").pop().split("\\").pop() : "الملف";
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
}

// ----------------- PARTNERS (أحمد وحسين) -----------------

async function loadPartnersSummary() {
    try {
        const res = await fetch("/api/partners/summary");
        const data = await res.json();

        document.getElementById("partner-exp-total").innerText = Number(data.total_expenses).toLocaleString() + " ج.م";
        document.getElementById("partner-col-total").innerText = Number(data.total_collections_egp).toLocaleString() + " ج.م";

        const expTbody = document.getElementById("partner-exp-tbody");
        expTbody.innerHTML = "";
        data.expenses.forEach(e => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${e.expense_date}</td>
                <td><b>${e.partner_name}</b></td>
                <td><span class="badge badge-amber">${e.category}</span></td>
                <td>${e.description}</td>
                <td><b>${Number(e.amount).toLocaleString()} ج.م</b></td>
                <td>${e.recipient || '-'}</td>
                <td>${e.notes || '-'}</td>
            `;
            expTbody.appendChild(tr);
        });

        const colTbody = document.getElementById("partner-col-tbody");
        colTbody.innerHTML = "";
        data.collections.forEach(c => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${c.collection_date}</td>
                <td><b>${c.partner_name}</b></td>
                <td>${c.source_description}</td>
                <td>${Number(c.amount).toLocaleString()} ${c.currency}</td>
                <td><b>${Number(c.amount_egp).toLocaleString()} ج.م</b></td>
                <td>${c.notes || '-'}</td>
            `;
            colTbody.appendChild(tr);
        });
    } catch (e) {
        console.error(e);
    }
}

async function submitPartnerExpense() {
    const payload = {
        partner_name: document.getElementById("p-exp-partner").value,
        expense_date: document.getElementById("p-exp-date").value,
        category: document.getElementById("p-exp-cat").value,
        description: document.getElementById("p-exp-desc").value.trim(),
        amount: parseFloat(document.getElementById("p-exp-amount").value) || 0,
        recipient: document.getElementById("p-exp-recip").value.trim(),
        notes: document.getElementById("p-exp-notes").value.trim()
    };
    if (payload.amount <= 0 || !payload.description) {
        alert("يرجى ملء الوصف والمبلغ!");
        return;
    }
    try {
        const res = await fetch("/api/partners/expenses", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            alert("تم حفظ المصروف بنجاح");
            closeModals();
            loadPartnersSummary();
            loadDashboardStats();
        }
    } catch (e) {
        alert(e.message);
    }
}

async function submitPartnerCollection() {
    const payload = {
        partner_name: document.getElementById("p-col-partner").value,
        collection_date: document.getElementById("p-col-date").value,
        source_description: document.getElementById("p-col-src").value.trim(),
        amount: parseFloat(document.getElementById("p-col-amount").value) || 0,
        currency: document.getElementById("p-col-currency").value,
        exchange_rate: parseFloat(document.getElementById("p-col-rate").value) || 1,
        notes: document.getElementById("p-col-notes").value.trim()
    };
    if (payload.amount <= 0 || !payload.source_description) {
        alert("يرجى ملء البيان والمبلغ!");
        return;
    }
    try {
        const res = await fetch("/api/partners/collections", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            alert("تم حفظ المقبوض بنجاح");
            closeModals();
            loadPartnersSummary();
            loadDashboardStats();
        }
    } catch (e) {
        alert(e.message);
    }
}

// ----------------- FACTORIES -----------------

async function loadFactories() {
    try {
        const res = await fetch("/api/factories");
        const data = await res.json();

        const sTbody = document.getElementById("factories-summary-tbody");
        sTbody.innerHTML = "";
        data.summary.forEach(f => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td><b>${f.factory_name}</b></td>
                <td>${f.ops_count} عملية</td>
                <td>${Number(f.total_meters).toLocaleString()} م٢</td>
                <td>${Number(f.total_cost).toLocaleString()} ج.م</td>
                <td>${Number(f.total_paid).toLocaleString()} ج.م</td>
                <td style="color:${f.total_due > 0 ? '#b91c1c':'#15803d'}; font-weight:800;">
                    ${Number(f.total_due).toLocaleString()} ج.م
                </td>
            `;
            sTbody.appendChild(tr);
        });

        const opsTbody = document.getElementById("factories-ops-tbody");
        opsTbody.innerHTML = "";
        data.operations.forEach(op => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${op.op_date}</td>
                <td><b>${op.factory_name}</b></td>
                <td>${op.operation_type}</td>
                <td>${op.material_name || '-'}</td>
                <td>${op.meters} م٢</td>
                <td>${op.unit_price} ج.م</td>
                <td><b>${Number(op.total_amount).toLocaleString()} ج.م</b></td>
                <td>${Number(op.paid_amount).toLocaleString()} ج.م</td>
                <td style="color:${op.remaining_amount > 0 ? '#b91c1c':'#15803d'}; font-weight:700;">
                    ${Number(op.remaining_amount).toLocaleString()} ج.م
                </td>
                <td>${op.notes || '-'}</td>
            `;
            opsTbody.appendChild(tr);
        });
    } catch (e) {
        console.error(e);
    }
}

async function submitFactoryOp() {
    const payload = {
        factory_name: document.getElementById("f-name").value.trim(),
        op_date: document.getElementById("f-date").value,
        operation_type: document.getElementById("f-type").value,
        material_name: document.getElementById("f-mat").value.trim(),
        meters: parseFloat(document.getElementById("f-meters").value) || 0,
        unit_price: parseFloat(document.getElementById("f-price").value) || 0,
        paid_amount: parseFloat(document.getElementById("f-paid").value) || 0,
        notes: document.getElementById("f-notes").value.trim()
    };
    if (!payload.factory_name || payload.meters <= 0) {
        alert("يرجى ملء اسم المصنع وعدد الأمتار!");
        return;
    }
    try {
        const res = await fetch("/api/factories", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            alert("تم حفظ العملية بنجاح");
            closeModals();
            loadFactories();
        }
    } catch (e) {
        alert(e.message);
    }
}

// ----------------- MATERIALS -----------------

async function loadMaterials() {
    try {
        const res = await fetch("/api/materials");
        materialsList = await res.json();
        const dlist = document.getElementById("materials-datalist");
        if (dlist) {
            dlist.innerHTML = "";
            materialsList.forEach(m => {
                const opt = document.createElement("option");
                opt.value = m.name;
                dlist.appendChild(opt);
            });
        }
    } catch (e) {
        console.error(e);
    }
}

// ----------------- MODALS -----------------

function closeModals() {
    document.querySelectorAll(".modal-overlay").forEach(m => m.style.display = "none");
}

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


// ----------------- AUTHENTICATION MANAGER & CYBER SAFE-MODE -----------------

async function checkAuthAndInit() {
    const token = localStorage.getItem("erp_token");
    if (!token) {
        showLoginScreen();
        return;
    }

    try {
        const res = await fetch("/api/auth/me");
        if (res.ok) {
            const data = await res.json();
            unlockApp(data.username || "admin");
        } else {
            handleLogout(false);
        }
    } catch (e) {
        unlockApp("admin");
    }
}

function showLoginScreen() {
    const overlay = document.getElementById("login-overlay");
    const appWrapper = document.getElementById("app-wrapper");
    if (overlay) overlay.style.display = "flex";
    if (appWrapper) appWrapper.style.display = "none";
    const passInput = document.getElementById("login-password");
    if (passInput) passInput.value = "";
    const userErr = document.getElementById("login-error-msg");
    if (userErr) userErr.style.display = "none";
}

function unlockApp(username = "admin") {
    const overlay = document.getElementById("login-overlay");
    const appWrapper = document.getElementById("app-wrapper");
    if (overlay) overlay.style.display = "none";
    if (appWrapper) appWrapper.style.display = "block";
    const navUser = document.getElementById("nav-username");
    if (navUser) navUser.innerText = username;

    // Load initial ERP data now that user is verified!
    initTabs();
    loadDashboardStats();
    loadMaterials();
    loadClients();
    setupInitialInvoiceRows();
    loadInvoicesArchive();
    loadPartnersSummary();
    loadFactories();
    loadRepository();
}

async function handleLoginSubmit(event) {
    if (event) event.preventDefault();
    const usernameInput = document.getElementById("login-username");
    const passwordInput = document.getElementById("login-password");
    const errDiv = document.getElementById("login-error-msg");
    const submitBtn = document.getElementById("login-submit-btn");

    const username = usernameInput ? usernameInput.value.trim() : "";
    const password = passwordInput ? passwordInput.value.trim() : "";

    if (!username || !password) {
        if (errDiv) {
            errDiv.innerText = "يرجى إدخال اسم المستخدم وكلمة المرور";
            errDiv.style.display = "block";
        }
        return;
    }

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> جاري التحقق...`;
    }

    try {
        const res = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        if (res.ok) {
            const data = await res.json();
            localStorage.setItem("erp_token", data.token);
            document.cookie = `auth_token=${data.token}; path=/; max-age=2592000; SameSite=Lax`;
            unlockApp(data.username || username);
        } else {
            const errData = await res.json().catch(() => ({}));
            if (errDiv) {
                errDiv.innerText = errData.detail || "اسم المستخدم أو كلمة المرور غير صحيحة!";
                errDiv.style.display = "block";
            }
        }
    } catch (e) {
        if (errDiv) {
            errDiv.innerText = "فشل الاتصال بالخادم: " + e.message;
            errDiv.style.display = "block";
        }
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = `<i class="fa-solid fa-right-to-bracket"></i> دخول آمن إلى النظام`;
        }
    }
}

async function handleLogout(notify = true) {
    localStorage.removeItem("erp_token");
    sessionStorage.clear();
    document.cookie = "auth_token=; path=/; max-age=0; SameSite=Lax";
    try {
        await fetch("/api/auth/logout", { method: "POST" });
    } catch (e) {}

    showLoginScreen();
    if (notify) {
        alert("تم تسجيل الخروج بنجاح وإقفال المنظومة. يمكنك الآن ترك الجهاز بأمان.");
    }
}
