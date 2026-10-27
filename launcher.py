import subprocess
import time
import os
import re
import sys
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLOUDFLARED = os.path.join(BASE_DIR, "cloudflared.exe")

def run():
    print("=" * 60)
    print("   نظام فواتير وحسابات الرخام والجرانيت - خالي أحمد جلال")
    print("=" * 60)
    print("\n1. جاري تشغيل خادم النظام الداخلي...")

    # Start uvicorn
    server_cmd = [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", "8000"]
    server_proc = subprocess.Popen(server_cmd, cwd=BASE_DIR)

    # Start Cloudflare Tunnel if available
    tunnel_url = None
    if os.path.exists(CLOUDFLARED):
        print("2. جاري إنشاء الرابط المباشر للموبايل (بدون فيزا وبدون اشتراكات)...")
        tunnel_proc = subprocess.Popen(
            [CLOUDFLARED, "tunnel", "--url", "http://127.0.0.1:8000"],
            cwd=BASE_DIR,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        # Read lines to find the URL
        start_time = time.time()
        while time.time() - start_time < 15:
            line = tunnel_proc.stderr.readline()
            if not line:
                time.sleep(0.5)
                continue
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                tunnel_url = match.group(0)
                break

    print("\n" + "=" * 60)
    print(" تم تشغيل النظام بنجاح!")
    print(f" رابط الكمبيوتر الداخلي: http://localhost:8000")
    if tunnel_url:
        print(f" رابط الموبايل (من أي مكان في العالم): {tunnel_url}")
    print("=" * 60)
    print("\nملاحظة: اترك هذه الشاشة مفتوحة أثناء استخدام النظام.\n")

    # Open local browser
    try:
        webbrowser.open("http://localhost:8000")
    except:
        pass

    try:
        server_proc.wait()
    except KeyboardInterrupt:
        print("\nجاري إيقاف النظام...")
        server_proc.terminate()
        if 'tunnel_proc' in locals():
            tunnel_proc.terminate()

if __name__ == "__main__":
    run()
