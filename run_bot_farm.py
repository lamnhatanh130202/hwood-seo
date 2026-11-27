# -*- coding: utf-8 -*-
"""
CHẠY HỆ THỐNG 5 BOT TỪ DÒNG LỆNH (KHÔNG CẦN STREAMLIT)
======================================================
File này đọc cấu hình từ các file cùng thư mục (do Streamlit tab hoặc bạn tự tạo):
  - bot_keywords.txt   : mỗi dòng 1 từ khóa (5 bot dùng chung, lấy ngẫu nhiên)
  - bot_proxies.json   : cấu hình 5 proxy/VPN (xem bot_proxies.json.example)
  - bot_settings.json  : tùy chọn (max_pages, dwell_min, dwell_max, visit_pages, headless)
Nếu không có file nào thì dùng giá trị mặc định bên dưới.

Cách chạy:  python run_bot_farm.py
Kết quả:    lich_su_bot_farm.json  +  bot_farm_progress.json (tiến độ thời gian thực)
"""
import sys
import os
import json
import time

# Đảm bảo UTF-8 cho stdout/stderr trên Windows khi redirect file log
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.bot_farm import chay_5_bot, doc_ket_qua, doc_proxy_config, append_live_log, PROGRESS_FILE

BASE = os.path.dirname(os.path.abspath(__file__))


def doc_tu_khoa_tu_file() -> list:
    path = os.path.join(BASE, "bot_keywords.txt")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
            if lines:
                return lines
        except Exception:
            pass
    # Mặc định: bộ từ khóa mẫu HWOOD
    return [
        "gỗ nhựa ngoài trời", "tấm nhựa ốp tường", "trần nano",
        "sàn gỗ nhựa ngoài trời", "bàn ghế sân vườn",
        "báo giá gỗ nhựa ngoài trời", "tấm pvc vân đá",
        "lam sóng ốp tường", "cổng gỗ nhựa ngoài trời", "hwood việt nam",
    ]


def doc_cai_dat() -> dict:
    path = os.path.join(BASE, "bot_settings.json")
    default = {
        "max_pages": 5,
        "delay_min": 8,
        "delay_max": 15,
        "dwell_min": 60,
        "dwell_max": 90,
        "visit_pages": True,
        "deep_browse": True,
        "steady_pacing": True,
        "headless": False,
        "click_zalo": False,
    }
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                default.update(json.load(f))
        except Exception:
            pass
    return default


if __name__ == "__main__":
    tu_khoa = doc_tu_khoa_tu_file()
    bots_cfg = doc_proxy_config()
    settings = doc_cai_dat()

    print(f"📋 Đã nạp {len(tu_khoa)} từ khóa | {len(bots_cfg)} bot | Quét tới trang {settings['max_pages']}")

    ket_qua, bots = chay_5_bot(
        danh_sach_tu_khoa=tu_khoa,
        danh_sach_bot=bots_cfg,
        max_pages=int(settings.get("max_pages", 5)),
        dwell_min=int(settings.get("dwell_min", 60)),
        dwell_max=int(settings.get("dwell_max", 90)),
        visit_pages=bool(settings.get("visit_pages", True)),
        deep_browse=bool(settings.get("deep_browse", True)),
        headless=bool(settings.get("headless", False)),
        click_zalo=bool(settings.get("click_zalo", False)),
        delay_between_min=int(settings.get("delay_min", 8)),
        delay_between_max=int(settings.get("delay_max", 15)),
        steady_pacing=bool(settings.get("steady_pacing", True)),
    )

    for b in bots:
        while b.is_alive():
            time.sleep(1)

    from modules.bot_farm import append_live_log, PROGRESS_FILE, doc_tien_do
    append_live_log(f"[{time.strftime('%H:%M:%S')}] [HỆ THỐNG] 🎉 TẤT CẢ BOT ĐÃ HOÀN THÀNH QUÉT! Đã lưu đầy đủ kết quả.")
    if os.path.exists(PROGRESS_FILE):
        for _ in range(5):
            try:
                prog = doc_tien_do()
                prog.setdefault("_summary", {})["status"] = "finished"
                for k, v in prog.items():
                    if k != "_summary" and isinstance(v, dict):
                        v["status"] = "done"
                        v["detail"] = f"Hoàn thành {v.get('processed', 0)} từ khóa"
                with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                    json.dump(prog, f, ensure_ascii=False, indent=2)
                break
            except Exception:
                time.sleep(0.05)

    print("\n" + "=" * 60)
    print("✅ TẤT CẢ BOT ĐÃ HOÀN THÀNH")
    print(f"📊 Tổng số kết quả ghi nhận: {len(doc_ket_qua())}")
    print("📂 File kết quả: lich_su_bot_farm.json")
    print("=" * 60)
