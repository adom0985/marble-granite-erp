import shutil

path_js = "static/app.js"
with open(path_js, "r", encoding="utf-8") as f:
    c = f.read()

c_norm = c.replace("\r\n", "\n")

old_block = """        if (typeof window !== "undefined" && window.location && window.location.hostname.includes("vercel.app")) {
            if (typeof url === "string" && url.startsWith("/api/")) {
                url = url.substring(4);
            }
        }"""

if old_block in c_norm:
    c_norm = c_norm.replace(old_block, "")
    with open(path_js, "w", encoding="utf-8") as f:
        f.write(c_norm)
    shutil.copy2(path_js, "public/static/app.js")
    print("Cleaned up interceptor in static and public app.js!")
else:
    print("Block not found, might already be clean.")
