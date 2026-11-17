# -*- coding: utf-8 -*-
"""
TEST 5 PROXY - Chạy: python test_proxies.py
Kiểm tra từng proxy với cả 2 giao thức HTTP và SOCKS5, xem cái nào kết nối được Google.
"""
import os
import json
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PROXY_FILE = os.path.join(BASE, "bot_proxies.json")

def curl_test(proxy_url, test_url):
    """Gọi curl qua proxy, trả về (thanh_cong, noi_dung)."""
    try:
        r = subprocess.run(
            ["curl", "-x", proxy_url, "--max-time", "15", "-s", test_url],
            capture_output=True, text=True, timeout=20,
        )
        out = (r.stdout or "").strip()
        return (len(out) > 0 and r.returncode == 0), out[:60]
    except Exception as e:
        return False, str(e)[:50]

def main():
    if not os.path.exists(PROXY_FILE):
        print("❌ Không tìm thấy bot_proxies.json trong thư mục này!")
        sys.exit(1)

    with open(PROXY_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    bots = data.get("bots", [])
    print("=" * 70)
    print(f"TEST {len(bots)} PROXY | Kiểm tra cả HTTP và SOCKS5")
    print("=" * 70)

    for b in bots:
        server = b.get("proxy_server", "")
        user = b.get("proxy_username", "")
        pwd = b.get("proxy_password", "")
        name = b.get("name", b.get("bot_id", "?"))
        print(f"\n🔍 {name}: {server}")

        if not server:
            print("   ⚪ Để trống (dùng IP máy) — bỏ qua test.")
            continue

        # Tách IP:port từ server (bỏ http:// hay socks5://)
        ip_port = server.replace("http://", "").replace("socks5://", "").replace("socks5h://", "")
        auth = f"{user}:{pwd}@" if user else ""

        for proto in ["http", "socks5"]:
            proxy_url = f"{proto}://{auth}{ip_port}"
            # Test 1: Lấy IP thật
            ok1, ip = curl_test(proxy_url, "https://api.ipify.org")
            # Test 2: Kết nối Google
            ok2, _ = curl_test(proxy_url, "https://www.google.com.vn")
            status = "✅ HOẠT ĐỘNG" if (ok1 and ok2) else ("⚠️ Có IP nhưng chặn Google" if ok1 else "❌ Không kết nối")
            print(f"   {proto:7s}: {status}  | IP ra: {ip if ok1 else 'lỗi'}")

    print("\n" + "=" * 70)
    print("💡 Nếu SOCKS5 hoạt động mà HTTP không → đổi 'http://' thành 'socks5://' trong bot_proxies.json")
    print("💡 Nếu cả 2 đều lỗi → proxy đã chết/hết hạn, liên hệ shop đổi mới.")
    print("=" * 70)

if __name__ == "__main__":
    main()
