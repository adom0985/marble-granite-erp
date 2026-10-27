import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from server import app
    from fastapi import Request

    @app.get("/api/index.py")
    def test_vercel_index_py(request: Request):
        return {
            "matched_index_py": True,
            "path": request.url.path,
            "query": str(request.url.query),
            "headers": dict(request.headers)
        }

    @app.get("/api/ping")
    def test_ping():
        return {"status": "pong"}

except Exception as e:
    import traceback
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    app = FastAPI()
    err_tb = traceback.format_exc()

    @app.get("/{full_path:path}")
    def error_fallback(full_path: str = ""):
        return HTMLResponse(f"<h3>Startup Error on Vercel:</h3><pre>{err_tb}</pre>", status_code=500)
