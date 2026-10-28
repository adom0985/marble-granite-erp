// Universal Authentication Interceptor (Attaches Token, Preserves /api/ Routing)
(function() {
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        options = options || {};
        options.headers = options.headers || {};

        const token = localStorage.getItem("erp_token");
        if (token) {
            if (options.headers instanceof Headers) {
                if (!options.headers.has("Authorization")) {
                    options.headers.set("Authorization", "Bearer " + token);
                }
            } else if (Array.isArray(options.headers)) {
                options.headers.push(["Authorization", "Bearer " + token]);
            } else {
                if (!options.headers["Authorization"]) {
                    options.headers["Authorization"] = "Bearer " + token;
                }
            }
        }
        return originalFetch(url, options);
    };
})();

// Global state
let materialsList = [];
let clientsList = [];
let currentViewingInvoiceId = null;
let repoTreeData = [];
let selectedRepoFolder = null;

document.addEventListener("DOMContentLoaded", () => {
    checkAuthAndInit();
});

// Tab Navigation
function initTabs() {
    const tabs = document.querySelectorAll(".nav-tab-btn");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            const targetId = tab.getAttribute("data-tab");
            document.querySelectorAll(".tab-pane").forEach(pane => {
                pane.style.display = pane.id === targetId ? "block" : "none";
            });

            if (targetId === "dashboard-pane") loadDashboardStats();
            if (targetId === "archive-pane") loadInvoicesArchive();
            if (targetId === "clients-pane") loadClientsList();
            if (targetId === "repository-pane") loadRepository();
        });
    });
}

// ----------------- INVOICE BUILDER & EDITING -----------------

function setupInitialInvoiceRows(count = 7) {
    const tbody = document.getElementById("invoice-items-tbody");
    tbody.innerHTML = "";
    currentViewingInvoiceId = null;
    
    const saveBtn = document.getElementById("btn-save-invoice");
    if (saveBtn) {
        saveBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> حفظ الفاتورة في النظام والفولدر';
        saveBtn.className = "btn btn-success";
    }

    const dateInput = document.getElementById("meta-inv-date");
    if (!dateInput.value) {
        dateInput.value = new Date().toISOString().split("T")[0];
    }
    const invNoInput = document.getElementById("meta-inv-no");
    if (!invNoInput.value) {
        const rnd = Math.floor(100 + Math.random() * 900);
        invNoInput.value = `INV-${new Date().getFullYear()}-${rnd}`;
    }

    document.getElementById("btn-send-whatsapp").style.display = "none";
    document.getElementById("btn-attach-photos").style.display = "none";
    document.getElementById("btn-export-excel-current").style.display = "none";
    const pdfBtn = document.getElementById("btn-export-pdf-current");
    if (pdfBtn) pdfBtn.style.display = "none";

    for (let i = 0; i < count; i++) {
        addRowToInvoice();
    }
    recalculateAll();
}

function addRowToInvoice(itemData = null) {
    const tbody = document.getElementById("invoice-items-tbody");
    const tr = document.createElement("tr");

    const pkg = itemData ? (itemData.package_no || "") : "";
    const blk = itemData ? (itemData.block_no || "") : "";
    const mat = itemData ? (itemData.material_name || "") : "";
    const qty = itemData ? (itemData.qty || "") : "";
    const len = itemData ? (itemData.length || "") : "";
    const wid = itemData ? (itemData.width || "") : "";
    const area = itemData ? (itemData.area || 0) : 0;
    const isFree = itemData ? Boolean(itemData.is_free) : false;
    const prc = isFree ? 0 : (itemData ? (itemData.price || "") : "");
    const tot = isFree ? 0 : (itemData ? (itemData.total || 0) : 0);
    const nts = itemData ? (itemData.notes || "") : "";

    tr.className = isFree ? "free-row" : "";
    tr.innerHTML = `
        <td><input type="text" class="grid-input col-pkg" value="${pkg}"></td>
        <td><input type="text" class="grid-input col-blk" value="${blk}"></td>
        <td>
            <input type="text" list="materials-datalist" class="grid-input col-mat" value="${mat}" placeholder="اختر الخامة...">
        </td>
        <td><input type="number" step="any" class="grid-input col-qty" value="${qty}" oninput="onCellChange(this)"></td>
        <td><input type="number" step="any" class="grid-input col-len" value="${len}" oninput="onCellChange(this)"></td>
        <td><input type="number" step="any" class="grid-input col-wid" value="${wid}" oninput="onCellChange(this)"></td>
        <td><input type="number" step="any" class="grid-input col-area readonly-val" value="${area}" readonly></td>
        <td><input type="number" step="any" class="grid-input col-prc" value="${prc}" ${isFree ? 'readonly style="background:#fef08a;"' : ''} oninput="onCellChange(this)"></td>
        <td><input type="number" step="any" class="grid-input col-tot readonly-val" value="${tot}" readonly></td>
        <td style="text-align:center;">
            <label style="font-size:0.75rem; font-weight:800; cursor:pointer; color:#b45309; display:inline-flex; align-items:center; gap:2px;">
                <input type="checkbox" class="col-free" ${isFree ? "checked" : ""} onchange="onToggleFree(this)"> فري
            </label>
        </td>
        <td><input type="text" class="grid-input col-notes" value="${nts}"></td>
        <td class="no-print"><button type="button" class="btn btn-danger" style="padding:2px 8px; font-size:0.8rem;" onclick="removeInvoiceRow(this)">✕</button></td>
    `;

    tbody.appendChild(tr);

    const matInput = tr.querySelector(".col-mat");
    matInput.addEventListener("change", () => {
        const selected = materialsList.find(m => m.name === matInput.value);
        if (selected && selected.default_price) {
            const prcInput = tr.querySelector(".col-prc");
            const freeBox = tr.querySelector(".col-free");
            if (!freeBox.checked && !prcInput.value) {
                prcInput.value = selected.default_price;
                onCellChange(prcInput);
            }
        }
    });
}

function onToggleFree(chk) {
    const tr = chk.closest("tr");
    const prcInput = tr.querySelector(".col-prc");
    const notesInput = tr.querySelector(".col-notes");

    if (chk.checked) {
        tr.classList.add("free-row");
        prcInput.value = 0;
        prcInput.readOnly = true;
        prcInput.style.backgroundColor = "#fef08a";
        if (!notesInput.value.includes("فري")) {
            notesInput.value = ("فري (مجاني) " + notesInput.value).trim();
        }
    } else {
        tr.classList.remove("free-row");
        prcInput.readOnly = false;
        prcInput.style.backgroundColor = "transparent";
        notesInput.value = notesInput.value.replace("فري (مجاني)", "").replace("فري", "").trim();
        const mat = tr.querySelector(".col-mat").value.trim();
        const selected = materialsList.find(m => m.name === mat);
        if (selected) prcInput.value = selected.default_price;
    }
    onCellChange(prcInput);
}

function removeInvoiceRow(btn) {
    const tr = btn.closest("tr");
    tr.remove();
    recalculateAll();
}

function onCellChange(input) {
    const tr = input.closest("tr");
    const qty = parseFloat(tr.querySelector(".col-qty").value) || 0;
    const len = parseFloat(tr.querySelector(".col-len").value) || 0;
    const wid = parseFloat(tr.querySelector(".col-wid").value) || 0;
    const isFree = tr.querySelector(".col-free").checked;
    const prc = isFree ? 0 : (parseFloat(tr.querySelector(".col-prc").value) || 0);

    let area = 0;
    if (qty > 0 && len > 0 && wid > 0) {
        area = parseFloat((qty * len * wid).toFixed(4));
    }
    tr.querySelector(".col-area").value = area > 0 ? area : "";

    let total = 0;
    if (area > 0 && prc > 0 && !isFree) {
        total = parseFloat((area * prc).toFixed(2));
    }
    tr.querySelector(".col-tot").value = total > 0 ? total : 0;

    recalculateAll();
}

function recalculateAll() {
    const rows = document.querySelectorAll("#invoice-items-tbody tr");
    let totalPieces = 0;
    let totalArea = 0;
    let totalAmount = 0;
    let totalFreePieces = 0;

    const truckMap = {};

    rows.forEach(tr => {
        const mat = tr.querySelector(".col-mat").value.trim();
        const qty = parseFloat(tr.querySelector(".col-qty").value) || 0;
        const wid = parseFloat(tr.querySelector(".col-wid").value) || 0;
        const area = parseFloat(tr.querySelector(".col-area").value) || 0;
        const isFree = tr.querySelector(".col-free") ? tr.querySelector(".col-free").checked : false;
        const prc = isFree ? 0 : (parseFloat(tr.querySelector(".col-prc").value) || 0);
        const tot = isFree ? 0 : (parseFloat(tr.querySelector(".col-tot").value) || 0);

        if (qty > 0) totalPieces += qty;
        if (area > 0) totalArea += area;
        if (tot > 0) totalAmount += tot;
        if (isFree && qty > 0) totalFreePieces += qty;

        if (mat && qty > 0) {
            const suffix = isFree ? " ( فري )" : "";
            const label = `${mat}${suffix}`;
            if (!truckMap[label]) {
                truckMap[label] = {
                    label: label,
                    qty: 0,
                    area: 0,
                    price: prc,
                    is_free: isFree
                };
            }
            truckMap[label].qty += qty;
            truckMap[label].area += area;
        }
    });

    document.getElementById("lbl-total-pieces").innerText = totalPieces + (totalFreePieces > 0 ? ` (${totalFreePieces} فري)` : '');
    document.getElementById("lbl-total-area").innerText = totalArea.toFixed(3);
    document.getElementById("lbl-total-amount").innerText = totalAmount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});

    // Render truck summary table
    const truckTbody = document.getElementById("truck-summary-tbody");
    truckTbody.innerHTML = "";

    let sTotQty = 0;
    let sTotArea = 0;
    let sTotAmount = 0;

    Object.values(truckMap).forEach(item => {
        const itemTot = item.is_free ? 0 : parseFloat((item.area * item.price).toFixed(2));
        sTotQty += item.qty;
        sTotArea += item.area;
        sTotAmount += itemTot;

        const tr = document.createElement("tr");
        if (item.is_free) tr.style.backgroundColor = "#fef08a";
        tr.innerHTML = `
            <td>${item.label}</td>
            <td>${item.qty}</td>
            <td>${item.area.toFixed(3)}</td>
            <td>${item.is_free ? '<span style="color:#b45309; font-weight:800;">فري (0)</span>' : item.price}</td>
            <td>${item.is_free ? '0.00' : itemTot.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
        `;
        truckTbody.appendChild(tr);
    });

    document.getElementById("sum-tot-qty").innerText = sTotQty;
    document.getElementById("sum-tot-area").innerText = sTotArea.toFixed(3);
    document.getElementById("sum-tot-amount").innerText = sTotAmount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});

    const discountVal = parseFloat(document.getElementById("meta-discount") ? document.getElementById("meta-discount").value : 0) || 0;
    const paidVal = parseFloat(document.getElementById("meta-paid") ? document.getElementById("meta-paid").value : 0) || 0;
    const netAmount = Math.max(0, totalAmount - discountVal);
    const remainingAmount = netAmount - paidVal;

    const netEl = document.getElementById("lbl-net-amount");
    if (netEl) netEl.innerText = netAmount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});

    const remEl = document.getElementById("lbl-remaining-amount");
    if (remEl) remEl.innerText = remainingAmount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
}

// ----------------- SAVE OR UPDATE INVOICE (تعديل وحفظ مباشر في فولدر العميل) -----------------

async function saveCurrentInvoice(silent = false) {
    const invNo = document.getElementById("meta-inv-no").value.trim();
    const invDate = document.getElementById("meta-inv-date").value.trim();
    const client = document.getElementById("meta-client-name").value.trim();

    if (!invNo || !invDate || !client) {
        alert("يرجى ملء البيانات الأساسية: رقم الفاتورة، التاريخ، واسم العميل!");
        return;
    }

    const rows = document.querySelectorAll("#invoice-items-tbody tr");
    const items = [];

    rows.forEach(tr => {
        const mat = tr.querySelector(".col-mat").value.trim();
        const qty = parseFloat(tr.querySelector(".col-qty").value) || 0;
        const len = parseFloat(tr.querySelector(".col-len").value) || 0;
        const wid = parseFloat(tr.querySelector(".col-wid").value) || 0;
        const area = parseFloat(tr.querySelector(".col-area").value) || 0;
        const isFree = tr.querySelector(".col-free").checked;
        const prc = isFree ? 0 : (parseFloat(tr.querySelector(".col-prc").value) || 0);
        const tot = isFree ? 0 : (parseFloat(tr.querySelector(".col-tot").value) || 0);
        const pkg = tr.querySelector(".col-pkg").value.trim();
        const blk = tr.querySelector(".col-blk").value.trim();
        const nts = tr.querySelector(".col-notes").value.trim();

        if (mat && qty > 0) {
            items.push({
                package_no: pkg,
                block_no: blk,
                material_name: mat,
                qty: qty,
                length: len,
                width: wid,
                area: area,
                price: prc,
                total: tot,
                is_free: isFree,
                notes: nts
            });
        }
    });

    if (items.length === 0) {
        alert("يرجى إضافة بند واحد على الأقل في الفاتورة!");
        return;
    }

    const payload = {
        invoice_no: invNo,
        invoice_date: invDate,
        client_name: client,
        driver_name: document.getElementById("meta-driver-name").value.trim(),
        car_no: document.getElementById("meta-car-no").value.trim(),
        loading_place: document.getElementById("meta-loading-place").value.trim(),
        supervisor: document.getElementById("meta-supervisor").value.trim(),
        discount: parseFloat(document.getElementById("meta-discount").value) || 0,
        paid_amount: parseFloat(document.getElementById("meta-paid").value) || 0,
        notes: document.getElementById("meta-notes").value.trim(),
        items: items
    };

    const isEdit = Boolean(currentViewingInvoiceId);
    const url = isEdit ? `/api/invoices/${currentViewingInvoiceId}` : "/api/invoices";
    const method = isEdit ? "PUT" : "POST";

    // Immediate Local Persistence
    try {
        let totQty = 0, totArea = 0, totAmt = 0;
        items.forEach(it => {
            totQty += (it.qty || 0);
            totArea += (it.area || 0);
            totAmt += (it.total || 0);
        });
        const dVal = parseFloat(document.getElementById("meta-discount").value) || 0;
        const pVal = parseFloat(document.getElementById("meta-paid").value) || 0;
        const nAmt = Math.round((totAmt - dVal) * 100) / 100;
        const rAmt = Math.round((nAmt - pVal) * 100) / 100;

        const localRecord = Object.assign({}, payload, {
            id: currentViewingInvoiceId,
            total_pieces: totQty,
            total_area: Math.round(totArea * 1000) / 1000,
            total_amount: totAmt,
            discount: dVal,
            net_amount: nAmt,
            paid_amount: pVal,
            remaining_amount: rAmt
        });

        const localInvoices = JSON.parse(localStorage.getItem("erp_local_invoices_v16") || "{}");
        if (currentViewingInvoiceId) {
            localInvoices[currentViewingInvoiceId] = localRecord;
        }
        if (invNo) {
            localInvoices[invNo] = localRecord;
        }
        localStorage.setItem("erp_local_invoices_v16", JSON.stringify(localInvoices));
    } catch(errLocal) {
        console.error("Local storage error:", errLocal);
    }

    try {
        const token = localStorage.getItem("erp_token") || "";
        const saveHeaders = {"Content-Type": "application/json"};
        if (token) saveHeaders["Authorization"] = `Bearer ${token}`;

        const res = await fetch(url, {
            method: method,
            headers: saveHeaders,
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            currentViewingInvoiceId = data.invoice_id;
            document.getElementById("btn-send-whatsapp").style.display = "inline-flex";
            document.getElementById("btn-attach-photos").style.display = "inline-flex";
            document.getElementById("btn-export-excel-current").style.display = "inline-flex";
        const pdfBtnView = document.getElementById("btn-export-pdf-current");
        if (pdfBtnView) pdfBtnView.style.display = "inline-flex";
            const pdfBtnSave = document.getElementById("btn-export-pdf-current");
            if (pdfBtnSave) pdfBtnSave.style.display = "inline-flex";

            const saveBtn = document.getElementById("btn-save-invoice");
            saveBtn.innerHTML = '<i class="fa-solid fa-check-double"></i> حفظ التعديلات على الفاتورة';
            saveBtn.className = "btn btn-primary";

            const actionMsg = isEdit ? "تم حفظ التعديلات بنجاح!" : `تم حفظ الفاتورة بنجاح برقم: ${data.invoice_no}`;
            let diskMsg = "";
            if (data.saved_to_disk) {
                diskMsg = `\n📁 تم حفظ ملف الإكسيل تلقائياً في فولدر العميل على جهازك:\n${data.saved_to_disk}`;
            }
            if (!silent) {
                alert(`✅ ${actionMsg}${diskMsg}`);
            }

            loadDashboardStats();
            loadInvoicesArchive();
            loadClientsList();
            loadRepository();
        } else {
            alert("حدث خطأ أثناء الحفظ: " + (data.detail || ""));
        }
    } catch (e) {
        alert("فشل الاتصال بالخادم: " + e.message);
    }
}

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

function getCurrentInvoicePayload() {
    const invNo = document.getElementById("meta-inv-no").value.trim();
    const invDate = document.getElementById("meta-inv-date").value.trim();
    const client = document.getElementById("meta-client-name").value.trim();

    const rows = document.querySelectorAll("#invoice-items-tbody tr");
    const items = [];

    rows.forEach((tr, idx) => {
        const mat = tr.querySelector(".col-mat").value.trim();
        const qty = parseFloat(tr.querySelector(".col-qty").value) || 0;
        const len = parseFloat(tr.querySelector(".col-len").value) || 0;
        const wid = parseFloat(tr.querySelector(".col-wid").value) || 0;
        const area = parseFloat(tr.querySelector(".col-area").value) || 0;
        const isFree = tr.querySelector(".col-free").checked;
        const prc = isFree ? 0 : (parseFloat(tr.querySelector(".col-prc").value) || 0);
        const tot = isFree ? 0 : (parseFloat(tr.querySelector(".col-tot").value) || 0);
        const pkg = tr.querySelector(".col-pkg").value.trim();
        const blk = tr.querySelector(".col-blk").value.trim();
        const nts = tr.querySelector(".col-notes").value.trim();

        if (mat && qty > 0) {
            items.push({
                row_index: idx + 1,
                package_no: pkg,
                block_no: blk,
                material_name: mat,
                qty: qty,
                length: len,
                width: wid,
                area: area,
                price: prc,
                total: tot,
                is_free: isFree,
                notes: nts
            });
        }
    });

    return {
        invoice_no: invNo || "فاتورة",
        invoice_date: invDate || new Date().toISOString().split("T")[0],
        client_name: client || "عميل عام",
        driver_name: document.getElementById("meta-driver-name").value.trim(),
        car_no: document.getElementById("meta-car-no").value.trim(),
        loading_place: document.getElementById("meta-loading-place").value.trim(),
        supervisor: document.getElementById("meta-supervisor").value.trim(),
        discount: parseFloat(document.getElementById("meta-discount").value) || 0,
        paid_amount: parseFloat(document.getElementById("meta-paid").value) || 0,
        notes: document.getElementById("meta-notes").value.trim(),
        items: items
    };
}

async function exportCurrentInvoicePDF() {
    const payload = getCurrentInvoicePayload();
    if (payload.items.length === 0) {
        alert("يرجى إضافة بند واحد على الأقل في الفاتورة!");
        return;
    }

    const btn = document.getElementById("btn-export-pdf-current");
    const origText = btn ? btn.innerHTML : "";
    if (btn) btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> جاري التجهيز...';

    // Auto-save in background
    try { saveCurrentInvoice(true); } catch(e) {}

    try {
        const token = localStorage.getItem("erp_token") || "";
        const headers = {"Content-Type": "application/json"};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch("/api/invoices/export-pdf-direct", {
            method: "POST",
            headers: headers,
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            throw new Error(`خطأ في التصدير (${res.status})`);
        }

        const blob = await res.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        window.open(blobUrl, "_blank");
    } catch(err) {
        alert("فشل تصدير PDF المباشر: " + err.message);
    } finally {
        if (btn) btn.innerHTML = origText;
    }
}

async function exportCurrentInvoiceExcel() {
    const payload = getCurrentInvoicePayload();
    if (payload.items.length === 0) {
        alert("يرجى إضافة بند واحد على الأقل في الفاتورة!");
        return;
    }

    const btn = document.getElementById("btn-export-excel-current");
    const origText = btn ? btn.innerHTML : "";
    if (btn) btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> جاري التجهيز...';

    // Auto-save in background
    try { saveCurrentInvoice(true); } catch(e) {}

    try {
        const token = localStorage.getItem("erp_token") || "";
        const headers = {"Content-Type": "application/json"};
        if (token) headers["Authorization"] = `Bearer ${token}`;

        const res = await fetch("/api/invoices/export-excel-direct", {
            method: "POST",
            headers: headers,
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            throw new Error(`خطأ في التصدير (${res.status})`);
        }

        const blob = await res.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = blobUrl;
        a.download = `فاتورة_${payload.invoice_no}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    } catch(err) {
        alert("فشل تصدير الإكسيل المباشر: " + err.message);
    } finally {
        if (btn) btn.innerHTML = origText;
    }
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

        if (document.getElementById("stat-sales")) document.getElementById("stat-sales").innerText = Number(data.total_sales).toLocaleString() + " ج.م";
        if (document.getElementById("stat-receivables")) document.getElementById("stat-receivables").innerText = Number(data.total_receivables || 0).toLocaleString() + " ج.م";
        if (document.getElementById("stat-paid")) document.getElementById("stat-paid").innerText = Number(data.total_paid || 0).toLocaleString() + " ج.م";
        if (document.getElementById("stat-pieces")) document.getElementById("stat-pieces").innerText = Number(data.total_pieces).toLocaleString() + " قطعة";
        if (document.getElementById("stat-area")) document.getElementById("stat-area").innerText = Number(data.total_area).toLocaleString() + " م٢";
        if (document.getElementById("stat-disk-files")) document.getElementById("stat-disk-files").innerText = `${data.disk_files_count || 0} ملف في المستودع`;

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
                        <a href="/api/invoices/${inv.id}/export-pdf" target="_blank" class="btn btn-danger" style="padding:4px 8px; font-size:0.8rem; background:#dc2626; border-color:#dc2626;">📄 PDF</a>
                </td>
            `;
            recTbody.appendChild(tr);
        });
    } catch (e) {
        console.error("Error loading stats:", e);
    }
}

// ----------------- INVOICES ARCHIVE -----------------

let currentArchiveFilterClient = "";

function filterArchiveByClient(clientName) {
    currentArchiveFilterClient = clientName;
    const searchInput = document.getElementById("archive-search");
    if (searchInput) searchInput.value = "";
    loadInvoicesArchive();
}

async function loadInvoicesArchive() {
    const searchVal = document.getElementById("archive-search") ? document.getElementById("archive-search").value : "";
    let url = `/api/invoices?search=${encodeURIComponent(searchVal)}`;
    if (currentArchiveFilterClient) {
        url += `&client=${encodeURIComponent(currentArchiveFilterClient)}`;
    }
    try {
        const res = await fetch(url);
        const list = await res.json();
        const tbody = document.getElementById("archive-tbody");
        tbody.innerHTML = "";

        if (!list || list.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:25px; color:#64748b; font-weight:700; font-size:1rem;">لا توجد فواتير مطابقة لهذا البحث أو الفلتر.</td></tr>`;
            return;
        }

        const token = localStorage.getItem("erp_token") || "";
        const tokenParam = token ? `?token=${encodeURIComponent(token)}` : "";

        const localInvoices = JSON.parse(localStorage.getItem("erp_local_invoices_v16") || "{}");
        list.forEach(inv => {
            const loc = localInvoices[inv.id] || localInvoices[inv.invoice_no];
            if (loc) {
                inv.total_amount = loc.total_amount !== undefined ? loc.total_amount : inv.total_amount;
                inv.net_amount = loc.net_amount !== undefined ? loc.net_amount : inv.net_amount;
                inv.total_pieces = loc.total_pieces !== undefined ? loc.total_pieces : inv.total_pieces;
                inv.total_area = loc.total_area !== undefined ? loc.total_area : inv.total_area;
                inv.paid_amount = loc.paid_amount !== undefined ? loc.paid_amount : inv.paid_amount;
                inv.remaining_amount = (inv.net_amount !== undefined ? inv.net_amount : inv.total_amount) - (inv.paid_amount || 0);
            }
            const tr = document.createElement("tr");

            // Client badge colors
            let clientBadge = `<span class="badge badge-blue">${inv.client_name}</span>`;
            if (inv.client_name === "الحاج صلاح") {
                clientBadge = `<span class="badge" style="background:#fef08a; color:#854d0e; font-weight:800; border:1px solid #eab308;">👑 الحاج صلاح</span>`;
            } else if (inv.client_name === "أحمد رضا") {
                clientBadge = `<span class="badge" style="background:#ccfbf1; color:#0f766e; font-weight:800; border:1px solid #14b8a6;">📄 أحمد رضا</span>`;
            } else if (inv.client_name === "أدهم") {
                clientBadge = `<span class="badge" style="background:#f3e8ff; color:#6b21a8; font-weight:800; border:1px solid #a855f7;">💼 أدهم</span>`;
            } else if (inv.client_name === "صديق جعفر") {
                clientBadge = `<span class="badge" style="background:#ffedd5; color:#9a3412; font-weight:800; border:1px solid #f97316;">🤝 صديق جعفر</span>`;
            }

            tr.innerHTML = `
                <td><b style="font-size:0.95rem; color:#1e3a8a;">${inv.invoice_no}</b></td>
                <td><span style="font-weight:700; color:#475569;">${inv.invoice_date}</span></td>
                <td>${clientBadge}</td>
                <td>${inv.driver_name || '-'} ${inv.car_no ? '/ ' + inv.car_no : ''}</td>
                <td><b>${inv.total_pieces}</b> ق (${Number(inv.total_area).toLocaleString()} م٢)</td>
                <td><b style="color:#1e3a8a; font-size:1.05rem;">${Number(inv.net_amount || inv.total_amount).toLocaleString()} ج.م</b></td>
                <td>
                    <div style="display:flex; gap:0.35rem; flex-wrap:wrap;">
                        <a href="/api/invoices/${inv.id}/export-pdf${tokenParam}" target="_blank" class="btn btn-danger" style="padding:4px 9px; font-size:0.8rem; background:#dc2626; border-color:#dc2626; font-weight:800;" title="تحميل أو معاينة الفاتورة بصيغة PDF المنسقة الرسمية">📄 PDF</a>
                        <a href="/api/invoices/${inv.id}/export-excel${tokenParam}" class="btn btn-success" style="padding:4px 9px; font-size:0.8rem; font-weight:700;">📥 إكسيل</a>
                        <button class="btn btn-outline" style="padding:4px 9px; font-size:0.8rem; font-weight:700;" onclick="viewInvoiceDetail(${inv.id})">✏️ تعديل</button>
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
        let inv = await res.json();

        // Check and apply local edits if present
        try {
            const localInvoices = JSON.parse(localStorage.getItem("erp_local_invoices_v16") || "{}");
            if (localInvoices[id] || (inv && localInvoices[inv.invoice_no])) {
                const loc = localInvoices[id] || localInvoices[inv.invoice_no];
                inv = Object.assign({}, inv, loc);
            }
        } catch(eLoc) {}

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

        document.getElementById("stmt-client-title").innerText = `كشف حساب وسجل حركات: ${stmt.client_name}`;
        
        // Update summary cards (Debit, Credit, Net Remaining)
        const debitEl = document.getElementById("stmt-debit");
        const creditEl = document.getElementById("stmt-credit");
        const balanceEl = document.getElementById("stmt-balance");

        if (debitEl) debitEl.innerText = `${Number(stmt.total_active_invoices || 0).toLocaleString()} ج.م`;
        if (creditEl) creditEl.innerText = `${Number(stmt.total_payments || 0).toLocaleString()} ج.م`;
        if (balanceEl) balanceEl.innerText = `${Number(stmt.net_remaining || 0).toLocaleString()} ج.م`;

        const specialBtn = document.getElementById("stmt-download-special-btn");
        if (specialBtn) {
            if (["الحاج صلاح", "أحمد رضا", "أدهم", "صديق جعفر"].includes(stmt.client_name)) {
                specialBtn.style.display = "inline-flex";
                specialBtn.href = `/api/special-files/${encodeURIComponent(stmt.client_name)}/download`;
            } else {
                specialBtn.style.display = "none";
            }
        }

        // Build chronological combined ledger (7 columns)
        const ledger = [];
        const invoices = (stmt.active_invoices && stmt.active_invoices.length > 0) ? stmt.active_invoices : (stmt.invoices || []);
        const localInvoices = JSON.parse(localStorage.getItem("erp_local_invoices_v16") || "{}");
        
        let calcDebit = 0;
        invoices.forEach(inv => {
            const loc = localInvoices[inv.id] || localInvoices[inv.invoice_no];
            if (loc) {
                inv.net_amount = loc.net_amount !== undefined ? loc.net_amount : (loc.total_amount || inv.net_amount);
                inv.total_pieces = loc.total_pieces !== undefined ? loc.total_pieces : inv.total_pieces;
                inv.total_area = loc.total_area !== undefined ? loc.total_area : inv.total_area;
                if (loc.notes) inv.notes = loc.notes;
            }
            calcDebit += Number(inv.net_amount || 0);

            ledger.push({
                type: 'invoice',
                date: inv.invoice_date || '',
                doc_no: inv.invoice_no,
                details: `${inv.total_pieces || 0} ق (${inv.total_area || 0} م٢)${inv.notes ? ' - ' + inv.notes : ''}`,
                debit: Number(inv.net_amount || 0),
                credit: 0,
                id: inv.id
            });
        });

        // Recalculate and update top summary cards with live modified totals
        const totalPayments = Number(stmt.total_payments || 0);
        const calcRemaining = calcDebit - totalPayments;
        if (debitEl) debitEl.innerText = `${calcDebit.toLocaleString()} ج.م`;
        if (creditEl) creditEl.innerText = `${totalPayments.toLocaleString()} ج.م`;
        if (balanceEl) balanceEl.innerText = `${calcRemaining.toLocaleString()} ج.م`;

        (stmt.payments || []).forEach(p => {
            ledger.push({
                type: 'payment',
                date: p.payment_date || '',
                doc_no: `إيصال دفع ${p.id || ''}`,
                details: `واصل منه (${p.payment_method || 'نقداً'})${p.notes ? ' - ' + p.notes : ''}`,
                debit: 0,
                credit: Number(p.amount_egp || p.amount || 0),
                id: p.id
            });
        });

        // Sort by date
        ledger.sort((a, b) => (a.date > b.date ? 1 : -1));

        let runningBalance = 0;
        const tbody = document.getElementById("stmt-tbody");
        tbody.innerHTML = "";

        if (ledger.length > 0) {
            ledger.forEach(item => {
                runningBalance += (item.debit - item.credit);
                const tr = document.createElement("tr");
                const token = localStorage.getItem("erp_token") || "";
                const tokenParam = token ? `?token=${encodeURIComponent(token)}` : "";

                if (item.type === 'invoice') {
                    tr.innerHTML = `
                        <td>${item.date}</td>
                        <td><span class="badge badge-blue">فاتورة توريد</span></td>
                        <td><b>${item.doc_no}</b></td>
                        <td>${item.details}</td>
                        <td style="color:#b91c1c; font-weight:800;">${item.debit.toLocaleString()} ج.م</td>
                        <td style="color:#64748b;">-</td>
                        <td style="font-weight:900; color:#1e3a8a;">${runningBalance.toLocaleString()} ج.م</td>
                    `;
                } else {
                    tr.innerHTML = `
                        <td>${item.date}</td>
                        <td><span class="badge badge-green" style="background:#dcfce7; color:#15803d; padding:3px 8px; border-radius:4px; font-weight:700;">دفعة مسددة</span></td>
                        <td><b>${item.doc_no}</b></td>
                        <td>${item.details}</td>
                        <td style="color:#64748b;">-</td>
                        <td style="color:#15803d; font-weight:800;">${item.credit.toLocaleString()} ج.م</td>
                        <td style="font-weight:900; color:#1e3a8a;">${runningBalance.toLocaleString()} ج.م</td>
                    `;
                }
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:15px; color:#64748b;">لا توجد حركات مسجلة لهذا العميل بعد.</td></tr>`;
        }

        document.getElementById("client-statement-modal").style.display = "flex";
    } catch (e) {
        alert("فشل تحميل كشف الحساب: " + e.message);
    }
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

let appInitialized = false;

async function checkAuthAndInit() {
    const token = localStorage.getItem("erp_token");
    if (!token) {
        showLoginScreen();
        return;
    }

    // Immediately unlock with saved user to prevent UI flicker
    const savedUser = localStorage.getItem("erp_user") || "admin";
    unlockApp(savedUser);

    // Verify silently in the background
    try {
        const res = await fetch("/api/auth/me");
        if (res.ok) {
            const data = await res.json();
            const navUser = document.getElementById("nav-username");
            if (navUser && data.username) navUser.innerText = data.username;
        } else if (res.status === 401) {
            console.warn("Session expired on server");
            handleLogout(false);
        }
    } catch (e) {
        console.warn("Offline or transient network issue - preserving session:", e);
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

    if (!appInitialized) {
        appInitialized = true;
        initTabs();
        loadDashboardStats();
        loadMaterials();
        loadClients();
        setupInitialInvoiceRows();
        loadInvoicesArchive();
        loadRepository();
    }
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
            localStorage.setItem("erp_user", data.username || username);
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
    localStorage.removeItem("erp_user");
    sessionStorage.clear();
    document.cookie = "auth_token=; path=/; max-age=0; SameSite=Lax";
    try {
        await fetch("/api/auth/logout", { method: "POST" });
    } catch (e) {}

    appInitialized = false;
    showLoginScreen();
    if (notify) {
        alert("تم تسجيل الخروج بنجاح وإقفال المنظومة. يمكنك الآن ترك الجهاز بأمان.");
    }
}
