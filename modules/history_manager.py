import os
import re
import json
import glob
from datetime import datetime
from modules.knowledge import phan_loai_chu_de

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_DIR = os.path.join(CURRENT_DIR, "lich_su_bai_viet")
os.makedirs(HISTORY_DIR, exist_ok=True)
CUSTOM_KEYWORDS_FILE = os.path.join(HISTORY_DIR, "tu_khoa_tuy_chinh.json")

def doc_tu_khoa_tuy_chinh():
    """Đọc từ điển từ khóa do người dùng tùy chỉnh hoặc gán riêng cho từng bài viết"""
    if os.path.exists(CUSTOM_KEYWORDS_FILE):
        try:
            with open(CUSTOM_KEYWORDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def luu_tu_khoa_tuy_chinh(pid_or_slug, tu_khoa_moi):
    """Lưu từ khóa tùy chỉnh cho bài viết để hiển thị chính xác theo ý muốn"""
    data = doc_tu_khoa_tuy_chinh()
    data[str(pid_or_slug)] = tu_khoa_moi.strip()
    try:
        with open(CUSTOM_KEYWORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def luu_bai_viet_lich_su(tu_khoa, noi_dung, meta_title="", meta_desc="", gop_y_note="", file_dinh_kem_name=""):
    """Lưu bài viết vào thư mục lịch sử dạng JSON có kèm danh mục sản phẩm và nhật ký góp ý"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r'[^\w\s-]', '', tu_khoa).strip().lower()
        slug = re.sub(r'[-\s]+', '_', slug)[:25]
        file_name = f"{timestamp}_{slug}.json"
        file_path = os.path.join(HISTORY_DIR, file_name)
        
        danh_muc = phan_loai_chu_de(tu_khoa)
        data = {
            "id": timestamp,
            "tu_khoa": tu_khoa,
            "danh_muc": danh_muc,
            "thoi_gian": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "meta_title": meta_title,
            "meta_desc": meta_desc,
            "noi_dung": noi_dung,
            "lich_su_gop_y": []
        }
        if gop_y_note or file_dinh_kem_name:
            data["lich_su_gop_y"].append({
                "thoi_gian": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "yeu_cau": gop_y_note,
                "file_dinh_kem": file_dinh_kem_name
            })
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False

def lay_danh_sach_lich_su():
    """Lấy danh sách các bài viết đã lưu từ trước tới nay (mới nhất lên đầu) kèm phân loại chủ đề"""
    files = glob.glob(os.path.join(HISTORY_DIR, "*.json"))
    files.sort(key=os.path.getmtime, reverse=True)
    danh_sach = []
    for fp in files:
        try:
            with open(fp, "r", encoding="utf-8") as f:
                d = json.load(f)
                d["file_path"] = fp
                if "danh_muc" not in d or not d["danh_muc"]:
                    d["danh_muc"] = phan_loai_chu_de(d.get("tu_khoa", ""))
                danh_sach.append(d)
        except Exception:
            continue
    return danh_sach
