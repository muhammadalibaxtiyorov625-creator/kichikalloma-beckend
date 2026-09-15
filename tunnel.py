import subprocess
import time
import urllib.request
import json
import sys
import re

def start_tunnel():
    print("="*60)
    print("  INTERNET ORQALI ULASH TIZIMI (PUBLIC LINK SHARING)")
    print("="*60)
    print("Public HTTPS havola tayyorlanmoqda, iltimos kuting...\n")

    # 1. Sinab ko'rish: Ngrok
    try:
        proc = subprocess.Popen(["ngrok", "http", "3009", "--log=stdout"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        time.sleep(3)
        
        try:
            with urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels", timeout=5) as res:
                data = json.loads(res.read().decode("utf-8"))
                tunnels = data.get("tunnels", [])
                if tunnels:
                    public_url = tunnels[0].get("public_url")
                    print("\n" + "="*60)
                    print("  SIZNING DUNYO BO'YICHA PUBLIC HAVOLANGIZ (NGROK):")
                    print(f"  -> Admin Panel:    {public_url}")
                    print(f"  -> Swagger Docs:   {public_url}/docs")
                    print(f"  -> Sayyoralar API: {public_url}/api/website/planets")
                    print("="*60)
                    print("\nUshbu havolani dostlaringizga yoki istalgan kishiga tashlasangiz,")
                    print("ular o'z telefonlari yoki boshqa notebooklaridan kirib ko'rishlari mumkin!\n")
                    print("Eslatma: Birinchi marta kirganda ko'k 'Visit Site' tugmasini bosish kerak.\n")
                    print("(Oynani yopmang, havola ishlab turishi uchun ushbu oyna ochiq turishi kerak)\n")
                    sys.stdout.flush()
                    
                    while True:
                        time.sleep(1)
        except Exception:
            proc.kill()
    except Exception:
        pass

    # 2. Fallback: localhost.run
    print("Ngrok ulanmadi, muqobil SSH tunnel ishga tushirilmoqda...")
    cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=30", "-R", "80:localhost:3009", "nokey@localhost.run"]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, encoding="utf-8", errors="ignore")
        for line in iter(proc.stdout.readline, ''):
            match = re.search(r'(https://[a-zA-Z0-9\-_\.]+\.lhr\.life)', line.strip())
            if match:
                public_url = match.group(1)
                print("\n" + "="*60)
                print("  SIZNING DUNYO BO'YICHA PUBLIC HAVOLANGIZ:")
                print(f"  -> Admin Panel:    {public_url}")
                print(f"  -> Swagger Docs:   {public_url}/docs")
                print(f"  -> Sayyoralar API: {public_url}/api/website/planets")
                print("="*60)
                print("\nUshbu havolani boshqalarga tashlab berishingiz mumkin!")
                sys.stdout.flush()
                break
        while True:
            time.sleep(1)
    except Exception as e:
        print(f"Xatolik: {e}")

if __name__ == "__main__":
    start_tunnel()
