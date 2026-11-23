import re
import html
import csv
import io
from collections import Counter
import streamlit as st
from modules.knowledge import viet_hoa_tieu_de, phan_loai_chu_de
from modules.file_handler import xoa_dau_tieng_viet
from modules.history_manager import doc_tu_khoa_tuy_chinh

# DANH SÁCH CÁC TIÊU ĐỀ RÁC / TRANG QUẢN TRỊ / TIỆN ÍCH / BẢN NHÁP CẦN LOẠI BỎ 100% KHỎI TỪ KHÓA
DANH_SACH_TRANG_RAC_ADMIN = [
    "bài viết thủ công", "bai viet thu cong", "bản nháp", "draft", "bài viết mẫu",
    "bài viết lưu trữ", "giới thiệu", "liên hệ", "chính sách", "điều khoản", "bảo hành",
    "tuyển dụng", "thanh lý", "hàng thanh lý", "giỏ hàng", "tài khoản", "thanh toán",
    "trang chủ", "sản phẩm mẫu", "mẫu bài", "test", "demo", "sample", "tin tức",
    "dự án", "catalog", "catalogue", "chính sách đại lý", "hwood việt nam", "hwood",
    "bài viết:", "bài viết"
]

def kiem_tra_tieu_de_rac(tieu_de, pslug=""):
    """Kiểm tra xem tiêu đề hoặc slug có phải là trang quản trị, bài nháp hoặc trang tiện ích không phải keyword SEO không"""
    if not tieu_de:
        return True
    t = str(tieu_de).lower().strip()
    s = str(pslug).lower().strip()
    
    if len(t) < 3 or t in ["-", "n/a", "none"]:
        return True
        
    for rac in DANH_SACH_TRANG_RAC_ADMIN:
        if rac == t or rac == s:
            return True
        if rac in ["bài viết thủ công", "bản nháp", "giới thiệu", "liên hệ", "chính sách", "tuyển dụng", "hàng thanh lý", "giỏ hàng", "thanh toán"]:
            if rac in t or rac in s:
                return True
                
    if t.startswith("bài viết thủ công") or t.startswith("bai viet thu cong") or t.startswith("bản nháp"):
        return True
        
    return False

# BẢNG 32 CỤM TỪ KHÓA CỐT LÕI HWOOD (TỪ KHÓA CHÍNH VÀ CÁC TỪ KHÓA PHỤ ĐI KÈM CHUẨN TOPIC CLUSTER)
BO_32_CLUSTER_HWOOD = {
    "gỗ nhựa ngoài trời": ["gỗ nhựa composite", "tấm ốp ASA", "lam sóng gỗ nhựa", "gỗ nhựa chống mối mọt", "tuổi thọ gỗ nhựa"],
    "tấm nhựa ốp tường": ["tấm pvc vân đá", "tấm nano ốp tường", "tấm ốp chống ẩm", "vách tivi nhựa", "giá tấm ốp tường m2"],
    "trần nano": ["trần nhựa giả gỗ", "trần lam sóng", "trần mái hiên", "mẫu trần nano đẹp", "thi công trần nhựa"],
    "sàn gỗ nhựa ngoài trời": ["sàn nhựa giả gỗ", "vỉ nhựa lắp ghép", "sàn ban công", "lát sân vườn", "thi công sàn gỗ nhựa"],
    "bàn ghế ngoài trời": ["bàn ghế polywood", "nhôm đúc", "bàn ghế cafe sân vườn", "ghế băng công viên", "bàn ghế ngoài trời chịu nắng mưa"],
    "có nên dùng gỗ nhựa ngoài trời": ["gỗ nhựa có bền không", "gỗ nhựa vs gỗ tự nhiên", "gỗ nhựa ở Việt Nam", "nhược điểm gỗ nhựa"],
    "gỗ nhựa 1 lớp vs polymer vs asa": ["phân loại gỗ nhựa", "asa là gì", "polymer coating", "dòng gỗ nhựa nào tốt"],
    "báo giá gỗ nhựa ngoài trời": ["giá gỗ nhựa m2", "bảng giá gỗ nhựa 2026", "giá thi công trọn gói"],
    "vật liệu gỗ ốp cổng": ["cổng lam sóng", "thanh lam gỗ nhựa", "ốp cổng mặt tiền", "giá cổng gỗ nhựa"],
    "cách nhận biết gỗ nhựa asa chính hãng": ["gỗ nhựa asa giả", "phân biệt asa thật giả", "kiểm tra gỗ nhựa"],
    "cách vệ sinh gỗ nhựa asa": ["bảo dưỡng gỗ nhựa", "xử lý vết xước gỗ nhựa", "làm sạch sàn gỗ nhựa"],
    "lam sóng gỗ nhựa ngoài trời": ["giá lam sóng m2", "lam sóng 2 mặt asa", "lam sóng làm cổng", "phân loại lam sóng"],
    "báo giá tấm pvc vân đá ốp tường": ["giá tấm pvc vân đá tấm", "giá thi công tấm ốp tường", "tấm nano giá bao nhiêu"],
    "tấm nhựa ốp tường chống ẩm": ["ốp nhà tắm bằng gì", "tấm ốp nhà vệ sinh chống ẩm", "vách ướt chống ẩm"],
    "so sánh tấm nano vs pvc vân đá vs đá thật": ["tấm giả đá nào tốt", "tấm ốp đá hoa cương", "giá đá thật vs nhựa"],
    "ốp phòng thờ bằng nhựa nano": ["mẫu phòng thờ nano", "giá ốp phòng thờ", "vách thờ gia tiên"],
    "cách thi công tấm nhựa ốp tường nano": ["quy trình dán tấm ốp tường", "keo dán tấm nano", "thi công tấm pvc"],
    "vách tivi ốp nhựa giả đá": ["mẫu vách tivi nano", "phối màu vách tivi", "lam treo phòng khách", "lam hộp"],
    "trần nano là gì": ["phân loại trần nano", "giá trần nano m2", "quy trình thi công trần nano"],
    "mẫu trần nano đẹp": ["trần nano phòng khách", "trần nano giật cấp", "trần nano phòng ngủ"],
    "ốp trần mái hiên bằng gì": ["tấm ốp trần mái hiên", "trần mái hiên chống nắng", "so sánh trần thạch cao vs nhựa"],
    "trần lam sóng ngoài trời": ["trần lam sóng mái hiên", "trần ban công chống mưa", "lam sóng trần giá"],
    "trần nhựa giả gỗ": ["trần giả gỗ ấm cúng", "trần nhà gỗ nhựa", "giá trần nhựa giả gỗ"],
    "báo giá sàn gỗ nhựa ngoài trời": ["giá sàn gỗ nhựa m2", "bảng giá sàn gỗ nhựa 2026", "sàn gỗ nhựa chính hãng"],
    "vỉ nhựa lắp ghép vs sàn gỗ nhựa": ["ván lót sàn ngoài trời", "vỉ gỗ nhựa", "lát sân vườn nhanh", "giá vỉ nhựa"],
    "sàn nhựa giả gỗ có bền không": ["sàn nhựa hem khóa", "sàn spc ngoài trời", "tuổi thọ sàn nhựa", "sàn nhựa có độc không"],
    "nên lát sân vườn bằng gì": ["vật liệu lát sân vườn", "so sánh gạch đá vs gỗ nhựa", "sân vườn tiết kiệm"],
    "cách thi công sàn gỗ nhựa ngoài trời": ["quy trình lát sàn gỗ nhựa", "khung đà sàn", "độ dốc thoát nước", "lỗi thi công sàn"],
    "báo giá bàn ghế ngoài trời polywood": ["giá bàn ghế sân vườn", "bàn ghế nhôm đúc", "bộ bàn cafe ngoài trời"],
    "bàn ghế nhôm đúc ngoài trời có tốt không": ["so sánh nhôm đúc vs polywood vs gỗ", "nhôm đúc có nóng không", "giá nhôm đúc"],
    "pergola gỗ nhựa ngoài trời": ["chòi nghỉ sân vườn", "giàn hoa gỗ nhựa", "trụ gỗ nhựa", "giá pergola"],
    "keo dán gỗ nhựa loại nào tốt": ["keo 3x-bond", "keo silicone", "chốt inox gỗ nhựa", "phụ kiện lắp đặt"]
}

# Danh mục các thực thể / từ khóa sản phẩm cốt lõi của HWOOD (sắp xếp dài trước ngắn sau)
DANH_SACH_SAN_PHAM_HWOOD = list(BO_32_CLUSTER_HWOOD.keys()) + [
    "bộ bàn vuông ngoài trời ghế lưới texilene", "bộ bàn vuông ngoài trời", "bàn vuông ngoài trời",
    "bàn cafe ngoài trời mặt oval polywood", "bàn cafe ngoài trời polywood", "bàn cafe ngoài trời",
    "bàn ghế lưới texilene", "ghế lưới texilene", "bàn ghế texilene", "bàn nan polywood",
    "bàn ghế sân vườn ngoài trời", "bàn ghế polywood ngoài trời", "bàn ghế nhôm đúc ngoài trời",
    "bàn ghế công viên ngoài trời", "bàn ghế cafe ngoài trời", "bàn ghế sân vườn", "bàn ghế ngoài trời",
    "bàn ghế polywood", "bàn ghế nhôm đúc", "ghế băng công viên", "bàn ghế ban công",
    "sàn gỗ nhựa ngoài trời", "sàn gỗ nhựa hồ bơi", "vỉ gỗ nhựa ban công", "vỉ gỗ nhựa lót sàn",
    "sàn gỗ ngoài trời", "vỉ gỗ nhựa", "ván sàn gỗ nhựa", "gỗ nhựa phủ asa",
    "tấm ốp trần ban công", "tấm ốp gỗ nhựa ngoài trời", "tấm ốp ngoài trời", "tấm ốp ban công",
    "giàn treo hoa ban công", "giàn hoa ban công", "giàn hoa pergola ngoài trời", "giàn hoa pergola",
    "thanh lam gỗ nhựa ngoài trời", "thanh lam hộp gỗ nhựa", "thanh lam chắn nắng", "thanh lam hộp",
    "thanh lam ngoài trời", "thanh đa năng gỗ nhựa", "cổng gỗ nhựa ngoài trời", "hàng rào gỗ nhựa",
    "cổng gỗ nhựa", "trụ pergola gỗ nhựa", "trụ pergola",
    "tấm pvc vân đá tráng gương", "tấm pvc vân đá", "tấm nhựa pvc vân đá", "pvc vân đá",
    "tấm ốp tường nano phẳng", "trần nhựa nano giật cấp", "tấm ốp tường nano", "tấm ốp nano",
    "trần nhựa nano", "trần nano giật cấp", "trần nano", "tấm nhựa ốp tường",
    "lam sóng ốp tường", "lam sóng ốp trần", "tấm ốp lam sóng", "lam sóng 3 sóng", "lam sóng 4 sóng",
    "lam chắn nắng ngoài trời", "lam sóng nội thất", "vách tivi pvc vân đá", "vách tivi lam sóng",
    "keo dán pvc 3x-bond", "keo dán 3x-bond", "keo 3x-bond", "phào chỉ pvc", "phào chỉ vân đá",
    "báo giá tấm ốp tường", "giá tấm ốp tường", "báo giá tấm ốp nano", "giá tấm ốp nano", "giá của tấm ốp",
    "báo giá tấm ốp ngoài trời", "giá tấm ốp ngoài trời", "báo giá tấm ốp lam sóng", "giá tấm ốp lam sóng",
    "báo giá tấm ốp pvc", "giá tấm ốp pvc", "báo giá tấm ốp giả gỗ", "giá tấm ốp tường giả gỗ",
    "báo giá thi công tấm ốp tường", "giá thi công tấm ốp nano", "bảng giá tấm ốp tường nhựa", "giá 1m2 tấm ốp tường",
    "báo giá trần nhựa nano", "giá trần nhựa nano", "báo giá sàn gỗ nhựa ngoài trời", "giá sàn gỗ nhựa ngoài trời",
    "báo giá vỉ gỗ nhựa ban công", "giá vỉ gỗ nhựa lót sàn", "báo giá lam sóng gỗ nhựa ngoài trời",
    "báo giá cổng gỗ nhựa ngoài trời", "báo giá giàn hoa pergola ngoài trời", "báo giá gỗ nhựa hwood 2026",
    "cửa sắt ốp nhựa giả gỗ", "tấm lót sàn ban công", "vách ngăn nhựa nano", "trần giật cấp nhựa nano",
    "báo giá lam sóng gỗ nhựa", "la phông nhựa giả gỗ", "sàn nhựa ngoài trời", "nhựa giả gỗ ngoài trời",
    "tấm nhựa giả gỗ", "tấm ốp pvc", "tấm giả đá", "nhựa vân đá", "tấm pvc tráng gương",
    "gỗ nhựa hwood", "hwood việt nam"
]
DANH_SACH_SAN_PHAM_HWOOD = sorted(list(set(DANH_SACH_SAN_PHAM_HWOOD)), key=lambda x: len(x), reverse=True)


def trich_xuat_focus_and_secondary_kw(tieu_de, noi_dung="", pslug="", pid=""):
    """Bóc tách Từ khóa chính (Focus Keyword) và Các từ khóa phụ đi kèm (Secondary/LSI) từ tiêu đề & nội dung chuẩn Yoast SEO"""
    clean_title = html.unescape(tieu_de or "").strip()
    if kiem_tra_tieu_de_rac(clean_title, pslug):
        return "", []

    title_lower = clean_title.lower()

    # 1. TÌM TỪ KHÓA CHÍNH (FOCUS KEYWORD)
    focus_kw = None

    # Bước 1.0: Kiểm tra từ điển từ khóa tùy chỉnh do người dùng lưu
    custom_kws = doc_tu_khoa_tuy_chinh()
    if pid and str(pid) in custom_kws:
        focus_kw = custom_kws[str(pid)]
    elif pslug and str(pslug) in custom_kws:
        focus_kw = custom_kws[str(pslug)]
    elif clean_title.lower() in [k.lower() for k in custom_kws.keys()]:
        for k, v in custom_kws.items():
            if k.lower() == clean_title.lower():
                focus_kw = v
                break

    # Bước 1.1: Quét khớp thực thể ngành hàng HWOOD chuẩn trước
    # Đối với các sản phẩm như 'Bàn Cafe Ngoài Trời Mặt Oval Polywood HW-BD04A/B', ta cần bóc ra
    # Focus Keyword người dùng thực sự search: 'Bàn Cafe Ngoài Trời Polywood' hoặc 'Bàn Cafe Ngoài Trời'
    if not focus_kw:
        # Làm sạch trước mã model và quy cách hình dáng
        s_clean = re.sub(r'\s+(HW-?[A-Z0-9\/\-]+|[A-Z]{1,3}\d{2,4}[A-Z]?)\b', '', clean_title, flags=re.IGNORECASE)
        s_clean_shape = re.sub(r'\s+(mặt oval|mặt vuông\s*\d*c?m?|mặt tròn\s*d?\d*|chữ nhật\s*\d*m?\d*|mặt nan)\b', '', s_clean, flags=re.IGNORECASE).strip()
        s_shape_lower = s_clean_shape.lower()
        
        for sp in DANH_SACH_SAN_PHAM_HWOOD:
            if sp in s_shape_lower:
                focus_kw = sp
                break
        if not focus_kw:
            for sp in DANH_SACH_SAN_PHAM_HWOOD:
                if sp in title_lower:
                    focus_kw = sp
                    break

    # Bước 1.2: So khớp thông minh với URL Slug
    if not focus_kw and pslug and len(pslug) > 5:
        slug_clean = re.sub(r'-(hw-)?[a-z]{1,3}\d{2,4}[a-z]?$', '', pslug, flags=re.IGNORECASE)
        slug_clean = re.sub(r'-202[0-9]$', '', slug_clean)
        slug_words = [w for w in slug_clean.split('-') if w and not w.isdigit()]
        title_words = re.findall(r'[\w\+]+', clean_title)
        
        matched = []
        s_idx = 0
        for tw in title_words:
            tw_ascii = xoa_dau_tieng_viet(tw)
            if s_idx < len(slug_words) and tw_ascii == slug_words[s_idx]:
                matched.append(tw)
                s_idx += 1
        if len(matched) >= 2 and len(matched) >= len(slug_words) * 0.5:
            focus_kw = ' '.join(matched)

    # Bước 1.3: Bóc tách ngữ pháp tiêu đề chuẩn SEO
    if not focus_kw:
        s = clean_title
        s = re.sub(r'\s*[-–—|]\s*(HWOOD.*|hwood.*)$', '', s, flags=re.IGNORECASE)
        s = re.sub(r'[\(\[\{]\s*202[0-9]\s*[\)\]\}]', '', s)
        s = re.sub(r'\s+202[0-9]\b', '', s)
        s = re.sub(r'\s+(HW-?[A-Z0-9\/\-]+|[A-Z]{1,3}\d{2,4}[A-Z]?)\b', '', s, flags=re.IGNORECASE).strip()
        
        parts = re.split(r'\s*[-–—|:?]\s*', s)
        first_part = parts[0].strip() if parts else s
        first_part = re.sub(r'\s+(là gì|có tốt không|ở đâu|giá bao nhiêu|mua ở đâu)$', '', first_part, flags=re.IGNORECASE).strip()

        kw = re.sub(r'^(top)\s*\d+\+?\s*', r'\1 ', first_part, flags=re.IGNORECASE).strip()
        kw = re.sub(r'^\d+\+?\s*', '', kw).strip()
        kw = kw.rstrip('?!:;,.-')
        
        if len(kw.split()) >= 2 and len(kw) > 4 and not kiem_tra_tieu_de_rac(kw):
            focus_kw = kw

    if not focus_kw:
        if not kiem_tra_tieu_de_rac(clean_title):
            focus_kw = clean_title[:40]
        else:
            return "", []

    # 2. TÌM CÁC TỪ KHÓA PHỤ ĐI KÈM (SECONDARY / LSI KEYWORDS)
    secondary = []
    
    # 2.1: Thêm biến thể chi tiết của chính bài viết/sản phẩm (ví dụ mặt oval, mặt vuông, báo giá, v.v.)
    clean_no_brackets = re.sub(r'[\(\[\{].*?[\)\]\}]', '', clean_title)
    clean_no_model = re.sub(r'\s+(HW-?[A-Z0-9\/\-]+|[A-Z]{1,3}\d{2,4}[A-Z]?)\b', '', clean_no_brackets, flags=re.IGNORECASE).strip()
    
    if clean_no_model.lower() != focus_kw.lower() and len(clean_no_model.split()) >= 3 and not kiem_tra_tieu_de_rac(clean_no_model):
        secondary.append(clean_no_model.lower())
        
    parts_all = re.split(r'[-–—|:]', clean_no_brackets)
    for p in parts_all[1:]:
        p_clean = p.strip()
        if p_clean and len(p_clean) > 3 and "hwood" not in p_clean.lower() and not kiem_tra_tieu_de_rac(p_clean):
            secondary.append(p_clean.lower())

    # Trích xuất từ thẻ H2 nếu có nội dung HTML
    if noi_dung:
        h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', noi_dung, re.IGNORECASE)
        for h in h2s:
            clean_h = re.sub(r'<[^>]*>', '', h).strip()
            clean_h = re.sub(r'^[0-9IVXLCDMivxlcdm\.\s\-]+', '', clean_h).strip()
            if clean_h and len(clean_h) > 4 and clean_h.lower() not in secondary and not kiem_tra_tieu_de_rac(clean_h):
                secondary.append(clean_h.lower())

    # Bổ sung LSI keywords ngữ cảnh ngành vật liệu HWOOD (Ưu tiên bộ 32 Cluster chuẩn)
    tk_lower = focus_kw.lower()
    matched_32 = False
    for c_key, c_secs in BO_32_CLUSTER_HWOOD.items():
        if c_key in tk_lower or c_key in title_lower:
            secondary = [s.lower() for s in c_secs] + secondary
            matched_32 = True
            break

    if not matched_32:
        if any(w in tk_lower for w in ["bàn", "ghế", "polywood", "texilene", "cafe"]):
            secondary.extend(["báo giá bàn ghế ngoài trời 2026", "bàn ghế polywood nhôm đúc", "ghế băng công viên ngoài trời", "bàn ghế sân vườn chịu nước", "ghế lưới texilene hwood", "bàn cafe ngoài trời chịu mưa nắng"])
        elif any(w in tk_lower for w in ["sàn", "vỉ", "wpc"]):
            secondary.extend(["báo giá thi công sàn gỗ nhựa", "ván sàn wpc ngoài trời", "vỉ gỗ nhựa ban công", "sàn hồ bơi chống trơn trượt"])
        elif any(w in tk_lower for w in ["vân đá", "pvc"]):
            secondary.extend(["tấm pvc vân đá tráng gương", "báo giá tấm ốp tường vân đá", "keo dán pvc 3x-bond", "thi công tấm pvc vân đá trọn gói"])
        elif any(w in tk_lower for w in ["nano", "trần"]):
            secondary.extend(["trần nhựa nano giật cấp", "tấm ốp nano phẳng", "báo giá thi công trần nhựa", "trần nhựa giả gỗ phòng khách"])
        elif any(w in tk_lower for w in ["lam sóng", "sóng"]):
            secondary.extend(["lam sóng ốp tường trang trí", "tấm ốp lam 3 sóng", "tấm ốp lam 4 sóng", "vách tivi lam sóng"])
        elif any(w in tk_lower for w in ["pergola", "thanh lam", "trụ", "lam hộp"]):
            secondary.extend(["thanh lam hộp chắn nắng", "trụ pergola gỗ nhựa", "giàn hoa ngoài trời pergola", "hệ lam hộp gỗ nhựa"])
        elif any(w in tk_lower for w in ["cổng", "hàng rào", "đa năng"]):
            secondary.extend(["thanh đa năng gỗ nhựa", "cổng gỗ nhựa ngoài trời", "hàng rào gỗ nhựa wpc"])
        else:
            secondary.extend([f"báo giá {focus_kw.lower()}", f"hướng dẫn thi công {focus_kw.lower()}", f"{focus_kw.lower()} chính hãng"])

    # Lọc trùng và giới hạn 6-8 từ khóa phụ tiêu biểu nhất
    unique_sec = []
    for s in secondary:
        s_norm = s.strip()
        if s_norm and s_norm.lower() != focus_kw.lower() and s_norm.lower() not in [x.lower() for x in unique_sec] and not kiem_tra_tieu_de_rac(s_norm):
            unique_sec.append(s_norm)

    return viet_hoa_tieu_de(focus_kw), unique_sec[:8]


def trich_xuat_danh_sach_keyword_chuan_hwood(danh_sach_bai_viet_wp=None, ds_ls=None, che_do="chinh", loc_chuyen_muc="Tất cả"):
    """
    Trích xuất danh sách từ khóa thực tế chuẩn SEO (Focus & Secondary/LSI) từ các bài viết & sản phẩm trên hwood.vn.
    - Lọc bỏ hoàn toàn các bài nháp, bài viết thủ công, trang admin/tiện ích.
    - Phân tách Từ khóa chính (Focus Keywords) và Từ khóa phụ (Secondary / LSI).
    - Hỗ trợ lọc theo chuyên mục (Gỗ nhựa ngoài trời, Tấm ốp Nano/PVC, Lam sóng, Bàn ghế ngoài trời...)
    """
    matrix = lay_ma_tran_toan_bo_keyword(danh_sach_bai_viet_wp, ds_ls)
    
    kws_chinh = []
    kws_phu = []
    
    for item in matrix:
        kw_c = item.get("tu_khoa_chinh", "").strip()
        kw_p_list = item.get("tu_khoa_phu", [])
        cat = item.get("danh_muc", "")
        
        # Kiểm tra lọc chuyên mục nếu có yêu cầu
        if loc_chuyen_muc and loc_chuyen_muc != "Tất cả":
            cat_clean = cat.lower()
            loc_clean = loc_chuyen_muc.lower()
            if loc_clean not in cat_clean:
                if not any(w in kw_c.lower() for w in loc_clean.split()):
                    continue
                    
        if kw_c and not kiem_tra_tieu_de_rac(kw_c):
            if kw_c.lower() not in [x.lower() for x in kws_chinh]:
                kws_chinh.append(kw_c)
                
        for kp in kw_p_list:
            kp_str = kp.strip()
            if kp_str and not kiem_tra_tieu_de_rac(kp_str):
                if kp_str.lower() not in [x.lower() for x in kws_chinh] and kp_str.lower() not in [x.lower() for x in kws_phu]:
                    kws_phu.append(kp_str)
                    
    # Nếu danh sách từ WP rỗng, dự phòng bằng bộ từ khóa chuẩn của HWOOD
    if not kws_chinh:
        for k_core, secs in BO_32_CLUSTER_HWOOD.items():
            k_name = viet_hoa_tieu_de(k_core)
            if k_name not in kws_chinh:
                kws_chinh.append(k_name)
            for s in secs:
                if s not in kws_phu:
                    kws_phu.append(s)

    if che_do == "chinh":
        return kws_chinh
    elif che_do == "phu":
        return kws_phu
    else:
        all_res = []
        for c in kws_chinh:
            if c not in all_res:
                all_res.append(c)
        for p in kws_phu:
            if p not in all_res:
                all_res.append(p)
        return all_res


@st.cache_data(ttl=1800, show_spinner=False)
def lay_ma_tran_toan_bo_keyword(ds_wp=None, ds_ls=None):
    """Tổng hợp ma trận toàn bộ từ khóa chính và phụ từ Website WordPress và Lịch sử lưu trữ (ĐÃ LỌC SẠCH BÀI NHÁP/ADMIN)"""
    ma_tran = []
    
    # 1. Từ bài viết trên website WordPress
    if ds_wp:
        for p in ds_wp:
            pid = p.get("id")
            raw_title = p.get("title", {}).get("rendered", "") if isinstance(p.get("title"), dict) else str(p.get("title", ""))
            clean_title = html.unescape(raw_title).strip()
            plink = p.get("link", "")
            pdate = p.get("date", "")[:10]
            pslug = p.get("slug", "")

            # BỎ QUA NGAY CÁC TRANG RÁC / ADMIN / TIỆN ÍCH / BÀI NHÁP
            if kiem_tra_tieu_de_rac(clean_title, pslug):
                continue

            # ƯU TIÊN SỐ 1: Bóc tách trực tiếp từ ô "Cụm từ khóa chính" của Yoast SEO / Rank Math
            wp_focus = None
            meta_data = p.get("meta") or {}
            yoast_data = p.get("yoast_head_json") or {}
            
            if isinstance(meta_data, dict):
                wp_focus = meta_data.get("_yoast_wpseo_focuskw") or meta_data.get("yoast_wpseo_focuskw") or meta_data.get("rank_math_focus_keyword")
            if not wp_focus and isinstance(yoast_data, dict):
                wp_focus = yoast_data.get("focus_keyword")

            if wp_focus and str(wp_focus).strip() and not kiem_tra_tieu_de_rac(str(wp_focus)):
                p_focus = viet_hoa_tieu_de(str(wp_focus).strip())
                _, p_sec = trich_xuat_focus_and_secondary_kw(clean_title, pslug=pslug, pid=str(pid))
            else:
                p_focus, p_sec = trich_xuat_focus_and_secondary_kw(clean_title, pslug=pslug, pid=str(pid))

            if not p_focus or kiem_tra_tieu_de_rac(p_focus):
                continue

            p_cat = phan_loai_chu_de(clean_title)
            
            ma_tran.append({
                "id": str(pid),
                "tieu_de": clean_title,
                "tu_khoa_chinh": p_focus,
                "tu_khoa_phu": p_sec,
                "tu_khoa_phu_str": ", ".join(p_sec),
                "danh_muc": p_cat,
                "nguon": "🌐 Website hwood.vn",
                "link": plink,
                "ngay": pdate,
                "slug": pslug
            })
            
    # 2. Từ bài viết trong thư viện lịch sử (LỌC BỎ BÀI VIẾT THỦ CÔNG / BẢN NHÁP)
    wp_titles_lower = [item["tieu_de"].lower() for item in ma_tran]
    wp_focus_lower = [item["tu_khoa_chinh"].lower() for item in ma_tran]
    
    if ds_ls:
        for item in ds_ls:
            focus_raw = item.get("tu_khoa", "")
            meta_t = item.get("meta_title", "")
            display_title = html.unescape(meta_t).strip() if meta_t else (f"Bài viết: {viet_hoa_tieu_de(focus_raw)}" if focus_raw else "")
            
            # BỎ QUA NẾU LÀ BÀI VIẾT THỦ CÔNG HOẶC CHỨA TIÊU ĐỀ RÁC
            if kiem_tra_tieu_de_rac(focus_raw) or kiem_tra_tieu_de_rac(display_title):
                continue
                
            if display_title and display_title.lower() not in wp_titles_lower:
                p_focus = viet_hoa_tieu_de(focus_raw) if focus_raw else ""
                if not p_focus or kiem_tra_tieu_de_rac(p_focus):
                    continue
                    
                if p_focus.lower() in wp_focus_lower:
                    continue
                    
                _, p_sec = trich_xuat_focus_and_secondary_kw(display_title, item.get("noi_dung", ""), pid=item.get("id", ""))
                p_cat = item.get("danh_muc") or phan_loai_chu_de(display_title)
                
                ma_tran.append({
                    "id": item.get("id", ""),
                    "tieu_de": display_title,
                    "tu_khoa_chinh": p_focus,
                    "tu_khoa_phu": p_sec,
                    "tu_khoa_phu_str": ", ".join(p_sec),
                    "danh_muc": p_cat,
                    "nguon": "💻 Thư Viện Máy Tính",
                    "link": "",
                    "ngay": item.get("thoi_gian", "")[:10],
                    "slug": ""
                })

    # 3. Tính toán tần suất và cảnh báo Ăn thịt từ khóa (Keyword Cannibalization)
    counts = Counter([x["tu_khoa_chinh"].lower() for x in ma_tran])
    for item in ma_tran:
        c = counts[item["tu_khoa_chinh"].lower()]
        item["tan_suat"] = c
        item["trung_lap"] = (c > 1)
        item["canh_bao_str"] = f"⚠️ Trùng {c} bài" if c > 1 else "✅ Độc nhất"

    return ma_tran


def xuat_csv_ma_tran_keyword(danh_sach_matrix):
    """Xuất danh sách ma trận từ khóa thành chuỗi CSV chuẩn UTF-8 BOM cho Excel"""
    output = io.StringIO()
    output.write('\ufeff') # UTF-8 BOM
    writer = csv.writer(output)
    writer.writerow([
        "STT", 
        "Tiêu Đề Bài Viết", 
        "Từ Khóa Chính (Focus Keyword)", 
        "Từ Khóa Phụ Đi Kèm (Secondary Keywords)", 
        "Cụm Chủ Đề (Topic Cluster)", 
        "Nguồn Bài Viết", 
        "Tình Trạng Trùng Lặp (Cannibalization)", 
        "Số Lần Xuất Hiện", 
        "Link Bài Viết / ID"
    ])
    for idx, row in enumerate(danh_sach_matrix, 1):
        writer.writerow([
            idx,
            row.get("tieu_de", ""),
            row.get("tu_khoa_chinh", ""),
            row.get("tu_khoa_phu_str", ""),
            row.get("danh_muc", ""),
            row.get("nguon", ""),
            row.get("canh_bao_str", ""),
            row.get("tan_suat", 1),
            row.get("link", "") or row.get("id", "")
        ])
    return output.getvalue()


def goi_y_goc_nhin_tu_khoa_ve_tinh(tu_khoa_goc, danh_sach_bai_viet_wp=None):
    """
    Rà soát xem từ khóa gốc đã có bài viết trên website chưa,
    đồng thời tự động tạo 6-8 từ khóa phụ làm Keyword chính cho bài viết vệ tinh (Topic Cluster)
    xoay quanh thực thể đó để tránh ăn thịt từ khóa (Cannibalization).
    """
    kw_raw = tu_khoa_goc.strip().lower()
    if not kw_raw:
        return [], []

    kw_clean = re.sub(r'^(báo giá|giá thi công|tổng hợp|mẫu|top\s*\d*\+?|hướng dẫn|so sánh|độ bền|kinh nghiệm)\s+', '', kw_raw).strip()
    kw_clean = re.sub(r'\s+(202[0-9]|giá rẻ|hwood|uy tín|chính hãng)$', '', kw_clean).strip()
    if not kw_clean:
        kw_clean = kw_raw

    bai_viet_trung = []
    wp_titles_lower = []
    if danh_sach_bai_viet_wp:
        for bv in danh_sach_bai_viet_wp:
            t = bv.get("title", {}).get("rendered", "")
            t_lower = t.lower()
            wp_titles_lower.append(t_lower)
            if kw_clean in t_lower or kw_raw in t_lower:
                bai_viet_trung.append(bv)

    kw_title_case = viet_hoa_tieu_de(kw_clean)
    
    goc_nhin_list = [
        {
            "intent": "💰 Báo Giá & Chi Phí (Tỷ lệ chốt sale cao nhất)",
            "tu_khoa_moi": f"Báo giá {kw_clean} 2026",
            "tieu_de_de_xuat": f"Báo Giá {kw_title_case} Mới Nhất 2026 (Kèm Chi Phí Thi Công Hoàn Thiện)",
            "mo_ta_intent": "Khách hàng đã có nhu cầu và muốn so sánh giá trước khi liên hệ tư vấn mua hàng."
        },
        {
            "intent": "🎨 Mẫu Đẹp & Xu Hướng (Khách đang tìm ý tưởng)",
            "tu_khoa_moi": f"Tổng hợp mẫu {kw_clean} đẹp",
            "tieu_de_de_xuat": f"Tổng Hợp 15+ Mẫu {kw_title_case} Đẹp Hiện Đại Xu Hướng 2026",
            "mo_ta_intent": "Khách hàng muốn xem thực tế mẫu mã, phối cảnh công trình đẹp mắt."
        }
    ]

    if any(w in kw_clean for w in ["ốp", "tấm", "nano", "lam", "asa", "sóng", "vân đá"]):
        goc_nhin_list.append({
            "intent": "🛠️ Ứng Dụng Hạng Mục: Ốp Trần",
            "tu_khoa_moi": f"Ốp trần bằng {kw_clean}",
            "tieu_de_de_xuat": f"Ốp Trần Bằng {kw_title_case}: Hướng Dẫn Kỹ Thuật & Đánh Giá Độ Bền Thực Tế",
            "mo_ta_intent": "Đánh đúng khách hàng có nhu cầu làm trần ban công, trần phòng khách cụ thể."
        })
        goc_nhin_list.append({
            "intent": "🏡 Ứng Dụng Hạng Mục: Ban Công & Mặt Tiền",
            "tu_khoa_moi": f"{kw_clean} trang trí ban công",
            "tieu_de_de_xuat": f"Thiết Kế Ban Công Đẹp Sang Trọng Với {kw_title_case} Chịu Nắng Mưa",
            "mo_ta_intent": "Nhắm vào phân khúc căn hộ chung cư, nhà phố muốn cải tạo ban công."
        })
    elif any(w in kw_clean for w in ["sàn", "vỉ"]):
        goc_nhin_list.append({
            "intent": "🏊 Ứng Dụng Hạng Mục: Hồ Bơi & Sân Vườn",
            "tu_khoa_moi": f"Lót sàn {kw_clean} hồ bơi",
            "tieu_de_de_xuat": f"Thi Công Sàn {kw_title_case} Cho Hồ Bơi & Sân Vườn Chống Trơn Trượt",
            "mo_ta_intent": "Giải pháp chống trơn trượt, chịu nước 100% ngoài trời."
        })
    elif any(w in kw_clean for w in ["bàn", "ghế"]):
        goc_nhin_list.append({
            "intent": "☕ Ứng Dụng Hạng Mục: Quán Cafe & Resort",
            "tu_khoa_moi": f"Bàn ghế {kw_clean} quán cafe sân vườn",
            "tieu_de_de_xuat": f"Top Mẫu Bàn Ghế {kw_title_case} Cho Quán Cafe Sân Vườn & Resort Ven Biển",
            "mo_ta_intent": "Chủ quán cafe, nhà đầu tư homestay, resort tìm mua số lượng lớn."
        })
    else:
        goc_nhin_list.append({
            "intent": "🛠️ Ứng Dụng Hạng Mục Thực Tế",
            "tu_khoa_moi": f"Ứng dụng {kw_clean} trong thiết kế",
            "tieu_de_de_xuat": f"Ứng Dụng Thực Tế Của {kw_title_case} Trong Thiết Kế Nội Ngoại Thất Hiện Đại",
            "mo_ta_intent": "Giúp khách hàng hình dung rõ các không gian có thể áp dụng vật liệu này."
        })

    goc_nhin_list.extend([
        {
            "intent": "⚖️ So Sánh & Tư Vấn Chọn Mua",
            "tu_khoa_moi": f"Độ bền của {kw_clean}",
            "tieu_de_de_xuat": f"Độ Bền Thực Tế Của {kw_title_case}: Có Bị Cong Vênh Hay Bay Màu Không?",
            "mo_ta_intent": "Giải quyết triệt để nỗi sợ lớn nhất của khách hàng về độ bền và bảo hành."
        },
        {
            "intent": "📋 Hướng Dẫn Kỹ Thuật & Thi Công",
            "tu_khoa_moi": f"Hướng dẫn thi công {kw_clean}",
            "tieu_de_de_xuat": f"Hướng Dẫn Thi Công {kw_title_case} Đúng Chuẩn Kỹ Thuật Từ Chuyên Gia HWOOD",
            "mo_ta_intent": "Thầu thợ, kiến trúc sư và chủ nhà tự giám sát tìm kiếm quy trình lắp đặt chuẩn."
        }
    ])

    for g in goc_nhin_list:
        kw_test = g["tu_khoa_moi"].lower()
        kw_test_words = [w for w in kw_test.split() if len(w) > 2]
        
        da_trung = False
        for t_low in wp_titles_lower:
            match_count = sum(1 for w in kw_test_words if w in t_low)
            if match_count >= len(kw_test_words) - 1:
                da_trung = True
                break
                
        g["da_co_tren_web"] = da_trung
        g["status_badge"] = "⚠️ Đã có bài gần giống" if da_trung else "🟢 Mới 100% (Khuyên dùng)"

    return bai_viet_trung, goc_nhin_list
