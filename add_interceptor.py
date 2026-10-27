import shutil

path = r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\static\app.js"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

interceptor = """// Smart API routing for Vercel vs Local
if (typeof window !== "undefined" && window.location && window.location.hostname.includes("vercel.app")) {
    const originalFetch = window.fetch;
    window.fetch = function(url, options) {
        if (typeof url === "string" && url.startsWith("/api/")) {
            url = url.substring(4);
        }
        return originalFetch(url, options);
    };
}

"""

if "// Smart API routing" not in content:
    new_content = interceptor + content
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Added interceptor to static/app.js")

# Copy to public/static/app.js
shutil.copy2(path, r"C:\Users\الادهم\.gemini\antigravity\scratch\marble_granite_erp\public\static\app.js")
print("Synced to public/static/app.js")
