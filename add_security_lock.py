import shutil
import re

# 1. Update index.html
path_html = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\static\index.html"
with open(path_html, "r", encoding="utf-8") as f:
    html = f.read()

login_overlay_html = """
    <!-- ================= FULLSCREEN SECURITY LOCK SCREEN ================= -->
    <div id="login-overlay" style="display:flex; position:fixed; top:0; left:0; width:100vw; height:100vh; background:linear-gradient(135deg, #0f172a 0%, #1e293b 100%); z-index:999999; justify-content:center; align-items:center; padding:1.25rem; font-family:'Cairo', sans-serif;">
        <div style="background:#ffffff; border-radius:18px; padding:2.5rem 2rem; width:100%; max-width:430px; box-shadow:0 25px 50px -12px rgba(0,0,0,0.6); text-align:center;">
            <div style="background:#eff6ff; width:75px; height:75px; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 1.25rem auto;">
                <i class="fa-solid fa-shield-halved" style="font-size:2.2rem; color:#2563eb;"></i>
            </div>
            <h2 style="font-size:1.45rem; font-weight:900; color:#1e293b; margin:0 0 0.5rem 0;">منظومة الرخام والجرانيت</h2>
            <p style="font-size:0.88rem; color:#64748b; margin:0 0 1.5rem 0; font-weight:600;">منطقة محمية ومشفرة - يتطلب تسجيل الدخول</p>

            <form id="login-form" onsubmit="handleLoginSubmit(event)" style="text-align:right;">
                <div style="margin-bottom:1.2rem;">
                    <label style="display:block; font-size:0.85rem; font-weight:700; color:#334155; margin-bottom:6px;">
                        <i class="fa-solid fa-user" style="color:#2563eb; margin-left:4px;"></i> اسم المستخدم
                    </label>
                    <input type="text" id="login-username" class="form-control" placeholder="اسم المستخدم (admin)" required autocomplete="username" style="width:100%; padding:10px 12px; font-size:0.95rem; border:1px solid #cbd5e1; border-radius:8px;">
                </div>

                <div style="margin-bottom:1.2rem;">
                    <label style="display:block; font-size:0.85rem; font-weight:700; color:#334155; margin-bottom:6px;">
                        <i class="fa-solid fa-lock" style="color:#2563eb; margin-left:4px;"></i> كلمة المرور
                    </label>
                    <input type="password" id="login-password" class="form-control" placeholder="••••••••" required autocomplete="current-password" style="width:100%; padding:10px 12px; font-size:0.95rem; border:1px solid #cbd5e1; border-radius:8px;">
                </div>

                <div id="login-error-msg" style="display:none; background:#fee2e2; color:#b91c1c; padding:8px 12px; border-radius:6px; font-size:0.85rem; font-weight:700; margin-bottom:1.2rem; text-align:center;">
                    اسم المستخدم أو كلمة المرور غير صحيحة!
                </div>

                <button type="submit" id="login-submit-btn" class="btn btn-primary" style="width:100%; padding:12px; font-size:1rem; font-weight:800; border-radius:8px; display:flex; justify-content:center; align-items:center; gap:8px;">
                    <i class="fa-solid fa-right-to-bracket"></i> دخول آمن إلى النظام
                </button>
            </form>

            <div style="margin-top:1.5rem; font-size:0.75rem; color:#94a3b8; font-weight:600; display:flex; align-items:center; justify-content:center; gap:6px;">
                <i class="fa-solid fa-lock"></i> نظام التحقق السحابي المشفر 2026
            </div>
        </div>
    </div>

    <!-- ================= MAIN APP WRAPPER (LOCKED UNTIL LOGIN) ================= -->
    <div id="app-wrapper" style="display:none;">
"""

navbar_user_html = """            <div style="display:flex; align-items:center; gap:0.75rem; margin-right:auto;">
                <span class="badge" style="background:#e0f2fe; color:#0369a1; font-weight:800; padding:5px 12px; border-radius:12px; font-size:0.82rem;">
                    <i class="fa-solid fa-user-shield"></i> <span id="nav-username">admin</span>
                </span>
                <button class="btn btn-outline" onclick="handleLogout()" style="background:#fee2e2; color:#991b1b; border:1px solid #f87171; font-size:0.82rem; font-weight:800; padding:5px 12px; border-radius:8px; cursor:pointer;" title="تسجيل الخروج الآمن (مهم لو في سايبر أو جهاز مشترك)">
                    <i class="fa-solid fa-arrow-right-from-bracket"></i> خروج آمن
                </button>
            </div>
        </div>
    </header>"""

# Replace <body> with login_overlay_html + app-wrapper
html_norm = html.replace("\r\n", "\n")

if "id=\"login-overlay\"" not in html_norm:
    html_norm = html_norm.replace("<body>\n", f"<body>\n{login_overlay_html}\n", 1)
    
    # Add user badge and logout button to navbar
    old_nav_end = "        </div>\n    </header>"
    assert old_nav_end in html_norm, "Navbar end not found!"
    html_norm = html_norm.replace(old_nav_end, navbar_user_html, 1)

    # Close app-wrapper before <script src="/static/app.js">
    old_script_tag = "    <script src=\"/static/app.js\"></script>"
    assert old_script_tag in html_norm, "Script tag not found!"
    html_norm = html_norm.replace(old_script_tag, f"    </div> <!-- End app-wrapper -->\n{old_script_tag}", 1)

    with open(path_html, "w", encoding="utf-8") as f:
        f.write(html_norm)

    shutil.copy2(path_html, r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\public\index.html")
    print("Updated static/index.html and public/index.html with Login Screen and Safe Logout!")
else:
    print("Login overlay already present in HTML.")

# 2. Update app.js
path_js = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\static\app.js"
with open(path_js, "r", encoding="utf-8") as f:
    js_content = f.read()

js_norm = js_content.replace("\r\n", "\n")

auth_interceptor_code = """// Smart API routing & Universal Authentication Interceptor
(function() {
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        options = options || {};
        options.headers = options.headers || {};

        if (typeof window !== "undefined" && window.location && window.location.hostname.includes("vercel.app")) {
            if (typeof url === "string" && url.startsWith("/api/")) {
                url = url.substring(4);
            }
        }

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
"""

auth_manager_functions = """
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
"""

# Replace top interceptor in app.js
old_top_comment = "// Smart API routing for Vercel vs Local"
if old_top_comment in js_norm:
    end_of_old_interceptor = "}\n}"
    idx1 = js_norm.find(old_top_comment)
    idx2 = js_norm.find(end_of_old_interceptor, idx1) + len(end_of_old_interceptor)
    js_norm = auth_interceptor_code + js_norm[idx2:]

# Replace DOMContentLoaded handler with checkAuthAndInit()
old_dom_ready = """document.addEventListener("DOMContentLoaded", () => {
    initTabs();
    loadDashboardStats();
    loadMaterials();
    loadClients();
    setupInitialInvoiceRows();
    loadInvoicesArchive();
    loadPartnersSummary();
    loadFactories();
    loadRepository();
});"""

new_dom_ready = """document.addEventListener("DOMContentLoaded", () => {
    checkAuthAndInit();
});"""

if old_dom_ready in js_norm:
    js_norm = js_norm.replace(old_dom_ready, new_dom_ready, 1)

# Append auth manager functions if not present
if "function checkAuthAndInit" not in js_norm:
    js_norm += "\n" + auth_manager_functions

with open(path_js, "w", encoding="utf-8") as f:
    f.write(js_norm)

shutil.copy2(path_js, r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\public\static\app.js")
print("Updated static/app.js and public/static/app.js with Auth Guard & Cyber Safe Logout!")
