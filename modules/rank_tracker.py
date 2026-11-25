import os
import re
import json
import html
import requests
import urllib.parse
import csv
import io
from datetime import datetime
from modules.file_handler import xoa_dau_tieng_viet

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RANK_HISTORY_FILE = os.path.join(CURRENT_DIR, "lich_su_thu_hang.json")
KEYWORD_DATABASE_FILE = os.path.join(CURRENT_DIR, "lich_su_keywords_database.json")

def doc_lich_su_thu_hang():
    if os.path.exists(RANK_HISTORY_FILE):
        try:
            with open(RANK_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def luu_lich_su_thu_hang(data):
    try:
        with open(RANK_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

BO_TU_KHOA_HWOOD_PRESETS = {
    "🎯 [30 Key Chính] Toàn Bộ Từ Khóa Chính Của 30 Bài Viết HWOOD (30 từ)": [
        "trần nhựa nano",
        "mẫu trần nhựa nano",
        "mẫu trần nhựa nano đẹp cho phòng khách",
        "trần nano giật cấp",
        "cách làm trần nhựa nano phẳng",
        "tấm ốp nano",
        "báo giá tấm ốp nano",
        "có nên dùng tấm nhựa ốp tường",
        "tấm nhựa nano ốp vách",
        "tấm ốp lam sóng nội thất",
        "tấm ốp pvc vân đá",
        "giá tấm nhựa pvc",
        "gỗ nhựa ngoài trời",
        "gỗ nhựa composite",
        "có nên dùng gỗ nhựa ngoài trời",
        "tấm ốp asa ngoài trời",
        "tấm asa golden silk teak",
        "tấm ốp ngoài trời dark grey hw148w21",
        "lam sóng ngoài trời",
        "thanh lam gỗ nhựa ngoài trời",
        "trụ gỗ nhựa ngoài trời",
        "giá lam trụ gỗ nhựa ngoài trời",
        "vật liệu gỗ ốp cổng",
        "sàn gỗ nhựa ngoài trời",
        "báo giá sàn gỗ nhựa ngoài trời",
        "nên lát sân vườn bằng gì",
        "bàn ghế sân vườn",
        "kinh nghiệm chọn mua bàn ghế sân vườn",
        "keo dán gỗ nhựa loại nào tốt",
        "keo dán đa năng 3x-bond",
    ],
    "🪑 [Gỡ Kẹt Bàn Ghế] Bàn Ghế Sân Vườn & Ngoài Trời (Mồi từ khóa dài -> ngắn)": [
        "bàn ghế sân vườn hwood",
        "bảng giá bàn ghế sân vườn 2026",
        "bàn ghế ngoài trời polywood",
        "bàn ghế sân vườn polywood",
        "bàn ghế sân vườn bền trên 10 năm",
        "kinh nghiệm chọn mua bàn ghế sân vườn",
        "chọn mua bàn ghế cafe ngoài trời",
        "báo giá bàn ghế ngoài trời",
        "bảng giá bàn ghế sân vườn",
        "bàn ghế sân vườn",
    ],
    "💰 [Báo Giá Hot] Báo Giá Các Loại Tấm Ốp Tường, Tấm Ốp Nano & PVC (18 từ - Chạy 3.5p)": [
        "báo giá tấm ốp tường",
        "giá tấm ốp tường",
        "báo giá tấm ốp nano",
        "giá tấm ốp nano",
        "giá của tấm ốp",
        "báo giá tấm ốp",
        "giá tấm ốp",
        "báo giá tấm ốp ngoài trời",
        "giá tấm ốp ngoài trời",
        "báo giá tấm ốp lam sóng",
        "giá tấm ốp lam sóng",
        "báo giá tấm pvc vân đá",
        "giá tấm pvc vân đá",
        "giá tấm ốp tường giả gỗ",
        "báo giá thi công tấm ốp tường",
        "giá thi công tấm ốp nano",
        "giá tấm ốp tường bao nhiêu 1m2",
        "bảng giá tấm ốp tường nhựa 2026"
    ],
    "💰 [Báo Giá Hot] Báo Giá Sàn Gỗ Nhựa, Lam Sóng & Gỗ Nhựa Ngoài Trời (18 từ - Chạy 3.5p)": [
        "báo giá sàn gỗ nhựa ngoài trời",
        "giá sàn gỗ nhựa ngoài trời",
        "giá sàn nhựa ngoài trời",
        "báo giá gỗ nhựa ngoài trời",
        "giá gỗ nhựa ngoài trời",
        "báo giá lam sóng gỗ nhựa ngoài trời",
        "giá thanh lam gỗ nhựa ngoài trời",
        "báo giá thi công gỗ nhựa ngoài trời",
        "báo giá vỉ gỗ nhựa ban công",
        "giá vỉ gỗ nhựa lót sàn",
        "báo giá trần nhựa nano",
        "giá thi công trần nhựa nano",
        "báo giá trần gỗ nhựa ngoài trời",
        "báo giá cổng gỗ nhựa ngoài trời",
        "báo giá giàn hoa pergola ngoài trời",
        "báo giá bàn ghế sân vườn",
        "giá vật tư hwood tại kho",
        "báo giá gỗ nhựa hwood 2026"
    ],
    "🎯 [Pillar 1] Trần Nhựa Nano & Trần Lam Sóng (18 từ - Chạy 3.5p)": [
        "trần nhựa giả gỗ",
        "trần nano",
        "mẫu trần nano đẹp",
        "trần lam sóng",
        "tấm trần nhựa nano",
        "trần nhựa nano giật cấp",
        "trần nhựa nano phẳng",
        "giá thi công trần nhựa nano",
        "giá trần nhựa",
        "báo giá trần gỗ nhựa",
        "ốp trần nhựa giả gỗ",
        "trần nhựa vân gỗ",
        "tấm nhựa ốp trần",
        "nhựa nano ốp trần",
        "tấm ốp trần",
        "khung xương trần nhựa nano",
        "thi công trần nhựa nano",
        "trần gỗ nhựa"
    ],
    "🎯 [Pillar 1 - Mở Rộng] Trần Giật Cấp, La Phông & Mẫu Trần (14 từ - Chạy 3p)": [
        "la phông nhựa giả gỗ",
        "trần nhựa giả gỗ phòng khách",
        "trần nhựa lam sóng",
        "gỗ nhựa ốp trần",
        "trần nhựa nano giả gỗ",
        "tấm nano ốp trần",
        "giá trần nhựa giả gỗ",
        "trần nhựa giả gỗ đẹp",
        "tấm nhựa ốp trần pvc",
        "lam sóng ốp trần",
        "trần lam gỗ nhựa",
        "tấm ốp trần nhựa",
        "trần nhựa nano phòng ngủ",
        "trần giật cấp nhựa nano"
    ],
    "🎯 [Pillar 2] Tấm Nhựa Ốp Tường Nano & Báo Giá (18 từ - Chạy 3.5p)": [
        "báo giá tấm ốp tường",
        "giá tấm ốp tường",
        "báo giá tấm ốp nano",
        "giá tấm ốp nano",
        "giá của tấm ốp",
        "tấm nhựa ốp tường",
        "tấm ốp tường nano",
        "tấm ốp tường pvc",
        "nhựa giả gỗ ốp tường",
        "tấm nhựa giả gỗ",
        "nhựa nano ốp tường",
        "giá tấm nhựa ốp tường",
        "báo giá tấm ốp ngoài trời",
        "báo giá tấm ốp lam sóng",
        "báo giá thi công tấm ốp tường",
        "giá thi công tấm ốp nano",
        "tấm ốp tường chống ẩm",
        "bảng giá tấm ốp tường nhựa 2026"
    ],
    "🎯 [Pillar 2 - Mở Rộng] Lam Sóng Nội Thất & Vách Phòng Khách (18 từ - Chạy 3.5p)": [
        "tấm ốp lam sóng",
        "lam sóng nhựa",
        "vách nhựa nano",
        "tấm ốp nhựa nano",
        "nhựa pvc ốp tường",
        "ốp tường phòng khách",
        "ốp nhựa phòng khách",
        "báo giá tấm nhựa giả gỗ ốp tường",
        "lam gỗ nhựa",
        "ốp tường nhựa giả gỗ",
        "nhựa ốp tường giả gỗ",
        "thanh lam nhựa giả gỗ",
        "lam sóng nhựa giả gỗ",
        "nhựa giả gỗ ốp tường phòng khách",
        "ốp tường nano",
        "lam sóng gỗ nhựa",
        "vách nhựa ốp tường",
        "vách ngăn nhựa nano"
    ],
    "🎯 [Pillar 3] Tấm PVC Vân Đá & Nhựa Giả Đá Hoa Cương (18 từ - Chạy 3.5p)": [
        "tấm pvc vân đá",
        "tấm nhựa giả đá",
        "pvc vân đá",
        "nhựa giả đá",
        "tấm nhựa pvc giả đá",
        "tấm nhựa ốp tường giả đá",
        "tấm ốp tường giả đá",
        "tấm giả đá",
        "tấm nhựa pvc vân đá",
        "tấm ốp giả đá",
        "tấm pvc giả đá",
        "pvc giả đá",
        "tấm nhựa vân đá",
        "tấm vân đá",
        "tấm ốp vân đá",
        "tấm pvc giả đá vân mây",
        "nhựa vân đá",
        "tấm pvc tráng gương"
    ],
    "🎯 [Pillar 3 - Mở Rộng] Vách Tivi & Tranh Đá Đối Xứng (14 từ - Chạy 3p)": [
        "ốp nhựa giả đá phòng khách",
        "vách tivi pvc vân đá",
        "tấm pvc vân đá trắng",
        "pvc vân đá vàng",
        "tấm ốp tường vân đá",
        "tấm ốp 3d vân đá hoa cương",
        "giá tấm nhựa pvc vân đá",
        "tấm ốp vân đá cẩm thạch",
        "tấm ốp vân đá hoa cương",
        "giá tấm pvc vân đá",
        "vách giả đá",
        "giá tấm ốp tường pvc",
        "pvc vân đá đối xứng",
        "kích thước tấm pvc vân đá"
    ],
    "🎯 [Pillar 4] Gỗ Nhựa Ngoài Trời & Cửa Cổng WPC (18 từ - Chạy 3.5p)": [
        "gỗ nhựa ngoài trời",
        "gỗ nhựa",
        "tấm nhựa ngoài trời",
        "nhựa ngoài trời",
        "lam gỗ nhựa ngoài trời",
        "nhựa giả gỗ ngoài trời",
        "lam nhựa ngoài trời",
        "tấm gỗ nhựa",
        "tấm ốp tường ngoài trời",
        "lam sóng nhựa ngoài trời",
        "tấm gỗ nhựa ngoài trời",
        "tấm ốp nhựa ngoài trời",
        "vật liệu ốp tường ngoài trời",
        "tấm nhựa giả gỗ ngoài trời",
        "giá gỗ nhựa ngoài trời",
        "thanh lam gỗ nhựa ngoài trời",
        "cửa sắt ốp nhựa giả gỗ",
        "vật liệu gỗ ốp cổng"
    ],
    "🎯 [Pillar 4 - Mở Rộng] Lam Gỗ Nhựa & Trần Mái Hiên (13 từ - Chạy 2.5p)": [
        "trần gỗ nhựa ngoài trời",
        "báo giá gỗ ngoài trời",
        "trần nhựa ngoài trời",
        "tấm nhựa ốp tường ngoài trời",
        "lam gỗ ngoài trời",
        "giá thanh lam gỗ nhựa ngoài trời",
        "lam nhựa giả gỗ ngoài trời",
        "thanh gỗ nhựa composite ngoài trời",
        "thi công lam gỗ nhựa ngoài trời",
        "trần nhựa giả gỗ ngoài trời",
        "báo giá trần gỗ nhựa ngoài trời",
        "trần nhựa giả gỗ ban công",
        "lam chắn nắng gỗ nhựa"
    ],
    "🎯 [Pillar 5] Sàn Gỗ Nhựa Ngoài Trời & Vỉ Ban Công (18 từ - Chạy 3.5p)": [
        "sàn gỗ nhựa ngoài trời",
        "sàn nhựa ngoài trời",
        "vỉ gỗ nhựa ban công",
        "sàn gỗ nhựa hồ bơi",
        "tấm lót sàn ban công",
        "tấm lót ban công",
        "tấm nhựa lót sàn ngoài trời",
        "tấm lót sàn ngoài trời",
        "giá sàn gỗ nhựa ngoài trời",
        "báo giá sàn gỗ nhựa ngoài trời",
        "sàn nhựa chịu lực ngoài trời",
        "thi công sàn gỗ nhựa ngoài trời",
        "tấm sàn composite",
        "sàn nhựa ngoài trời giá rẻ",
        "sàn nhựa ban công",
        "sàn composite",
        "sàn nhựa giả gỗ hồ bơi",
        "gỗ nhựa ban công"
    ],
    "🎯 [Pillar 5 - Mở Rộng] Báo Giá Sàn Ngoài Trời & Sàn SPC (16 từ - Chạy 3p)": [
        "sàn nhựa",
        "sàn giả gỗ",
        "sàn nhựa vân gỗ",
        "giá sàn nhựa giả gỗ",
        "sàn nhựa giả gỗ trong nhà",
        "tấm lót sàn nhựa giả gỗ",
        "sàn nhựa giả gỗ chống nước",
        "sàn nhựa giả gỗ giá rẻ",
        "sàn gỗ nhựa trong nhà",
        "thi công sàn nhựa giả gỗ",
        "giá sàn nhựa giả gỗ hèm khóa",
        "sàn vinyl giả gỗ",
        "giá thi công sàn nhựa giả gỗ",
        "báo giá sàn nhựa giả gỗ ngoài trời",
        "sàn nhựa giả gỗ cao cấp",
        "sàn nhựa giả gỗ có bền không"
    ],
    "🎯 [Pillar 6] Bàn Ghế Sân Vườn, Pergola & Thương Hiệu HWOOD (15 từ - Chạy 3p)": [
        "bàn ghế sân vườn ngoài trời",
        "bàn ghế polywood ngoài trời",
        "bàn ghế nhôm đúc ngoài trời",
        "bàn ghế công viên ngoài trời",
        "bàn ghế cafe ngoài trời",
        "báo giá bàn ghế sân vườn",
        "bàn ghế ngoài trời chịu nắng mưa",
        "ghế băng công viên",
        "bàn ăn ngoài trời polywood",
        "pergola gỗ nhựa ngoài trời",
        "giàn hoa pergola ngoài trời",
        "gỗ nhựa hwood",
        "hwood việt nam",
        "tổng kho gỗ nhựa hwood",
        "báo giá gỗ nhựa hwood 2026"
    ],
    "⭐ [Top Đột Phá] 32 Cụm Từ Khóa Cốt Lõi Toàn Diện HWOOD (32 từ)": [
        "gỗ nhựa ngoài trời",
        "tấm nhựa ốp tường",
        "trần nano",
        "sàn gỗ nhựa ngoài trời",
        "bàn ghế ngoài trời",
        "có nên dùng gỗ nhựa ngoài trời",
        "gỗ nhựa 1 lớp vs polymer vs asa",
        "báo giá gỗ nhựa ngoài trời",
        "vật liệu gỗ ốp cổng",
        "cách nhận biết gỗ nhựa asa chính hãng",
        "cách vệ sinh gỗ nhựa asa",
        "lam sóng gỗ nhựa ngoài trời",
        "báo giá tấm pvc vân đá ốp tường",
        "tấm nhựa ốp tường chống ẩm",
        "so sánh tấm nano vs pvc vân đá vs đá thật",
        "ốp phòng thờ bằng nhựa nano",
        "cách thi công tấm nhựa ốp tường nano",
        "vách tivi ốp nhựa giả đá",
        "trần nano là gì",
        "mẫu trần nano đẹp",
        "ốp trần mái hiên bằng gì",
        "trần lam sóng ngoài trời",
        "trần nhựa giả gỗ",
        "báo giá sàn gỗ nhựa ngoài trời",
        "vỉ nhựa lắp ghép vs sàn gỗ nhựa",
        "sàn nhựa giả gỗ có bền không",
        "nên lát sân vườn bằng gì",
        "cách thi công sàn gỗ nhựa ngoài trời",
        "báo giá bàn ghế ngoài trời polywood",
        "bàn ghế nhôm đúc ngoài trời có tốt không",
        "pergola gỗ nhựa ngoài trời",
        "keo dán gỗ nhựa loại nào tốt"
    ],
    "💎 [Toàn Ngành] 50 Từ Khóa Trọng Điểm HWOOD (50 từ)": [
        "gỗ nhựa ngoài trời",
        "sàn gỗ nhựa ngoài trời",
        "báo giá sàn gỗ nhựa ngoài trời",
        "sàn gỗ nhựa hồ bơi",
        "vỉ gỗ nhựa ban công",
        "gỗ nhựa phủ asa",
        "tấm ốp gỗ nhựa ngoài trời",
        "thanh lam gỗ nhựa ngoài trời",
        "thanh đa năng gỗ nhựa",
        "cổng gỗ nhựa ngoài trời",
        "hàng rào gỗ nhựa",
        "giàn hoa pergola ngoài trời",
        "thanh lam hộp gỗ nhựa",
        "tấm nhựa ốp tường",
        "tấm pvc vân đá",
        "báo giá tấm pvc vân đá",
        "tấm nhựa pvc vân đá tráng gương",
        "tấm ốp nano",
        "tấm ốp tường nano phẳng",
        "trần nhựa nano giật cấp",
        "báo giá thi công trần nhựa nano",
        "vách tivi pvc vân đá",
        "tấm nhựa ốp tường phòng khách",
        "keo dán pvc 3x-bond",
        "lam sóng ốp tường",
        "tấm ốp lam sóng giả gỗ",
        "lam sóng 3 sóng",
        "lam sóng 4 sóng cao",
        "lam chắn nắng ngoài trời",
        "lam sóng ốp trần phòng khách",
        "bàn ghế sân vườn ngoài trời",
        "bàn ghế polywood ngoài trời",
        "bàn ghế nhôm đúc ngoài trời",
        "bàn ghế công viên ngoài trời",
        "bàn ghế cafe ngoài trời",
        "báo giá bàn ghế sân vườn",
        "bàn ghế ngoài trời chịu nắng mưa",
        "ghế băng công viên",
        "bàn ăn ngoài trời polywood",
        "hwood việt nam",
        "gỗ nhựa hwood",
        "tổng kho gỗ nhựa hwood",
        "báo giá thi công gỗ nhựa ngoài trời",
        "quy cách ván sàn gỗ nhựa",
        "độ bền gỗ nhựa ngoài trời",
        "tấm ốp ban công ngoài trời",
        "tấm pvc vân đá cẩm thạch",
        "vách ngăn lam sóng",
        "bộ bàn ghế sân vườn cao cấp",
        "báo giá thi công tấm nhựa ốp tường"
    ]
}

def tim_bai_viet_khop_nhat_wp(keyword, danh_sach_bai_viet_wp):
    """Tìm trang hoặc bài viết trên website hwood.vn khớp chính xác nhất với từ khóa tìm kiếm (đặc biệt ưu tiên Landing Page con)."""
    if not danh_sach_bai_viet_wp or not keyword:
        return None
        
    kw_raw = keyword.strip()
    kw_clean = xoa_dau_tieng_viet(kw_raw).lower().strip()
    kw_slug = re.sub(r'[^a-z0-9]+', '-', kw_clean).strip('-')
    kw_words = [w for w in re.split(r'\s+', kw_clean) if len(w) > 1]
    
    # Các từ khóa phụ / ý định tìm kiếm đặc thù
    intent_modifiers = ["bao-gia", "báo giá", "gia", "giá", "bang-gia", "bảng giá", "thi-cong", "thi công", "mau", "mẫu", "so-sanh", "so sánh", "la-gi", "là gì"]
    is_modifier_in_kw = any(m in kw_clean for m in intent_modifiers)

    best_post = None
    best_score = -999
    
    for p in danh_sach_bai_viet_wp:
        title_raw = p.get("title", {}).get("rendered", "") if isinstance(p.get("title"), dict) else str(p.get("title", ""))
        clean_title = html.unescape(title_raw).strip()
        title_ascii = xoa_dau_tieng_viet(clean_title).lower()
        slug = p.get("slug", "").lower().strip()
        link = p.get("link", "").strip()
        post_type = p.get("type", "post")
        
        score = 0
        
        # 1. Khớp chính xác hoàn toàn Slug URL (VD: 'tam-op-nano' == 'tam-op-nano') -> CỰC KỲ QUAN TRỌNG
        if slug == kw_slug:
            score += 160
        elif slug.replace("-", "") == kw_slug.replace("-", ""):
            score += 140
        elif kw_slug in slug:
            score += 45
            
        # 2. Khớp nguyên cụm từ khóa trong Tiêu đề
        if kw_clean in title_ascii:
            score += 50
        elif title_ascii.startswith(kw_clean):
            score += 25
            
        # 3. Khớp từng từ đơn lẻ trong Tiêu đề và Slug
        for w in kw_words:
            if w in title_ascii:
                score += 5
            if w in slug:
                score += 6
                
        # 4. Phạt nặng nếu từ khóa tìm kiếm là chung chung (VD: "tấm ốp nano") mà bài viết lại là bài phái sinh (VD: "báo giá tấm ốp nano")
        if not is_modifier_in_kw:
            for mod in intent_modifiers:
                mod_ascii = xoa_dau_tieng_viet(mod)
                if mod_ascii in slug or mod in clean_title.lower():
                    score -= 30
                    break
                    
        # 5. Ưu tiên trang Landing Page (pages) và danh mục sản phẩm hơn bài blog thông thường khi tìm kiếm từ khóa ngành
        if post_type in ["page", "product"]:
            score += 15
            
        if score > best_score:
            best_score = score
            raw_content = p.get("content", {}).get("rendered", "") if isinstance(p.get("content"), dict) else str(p.get("content", ""))
            best_post = {
                "id": p.get("id"),
                "title": clean_title,
                "slug": slug,
                "link": link,
                "type": post_type,
                "content": raw_content,
                "score": score
            }
            
    if best_score >= 15:
        return best_post
    return None


def tao_link_google_search(keyword):
    """Tạo đường link mở trực tiếp kết quả tìm kiếm Google Việt Nam đã TẮT CÁ NHÂN HÓA HOÀN TOÀN (pws=0)"""
    encoded = urllib.parse.quote_plus(keyword.strip())
    return f"https://www.google.com.vn/search?q={encoded}&hl=vi&gl=vn&pws=0"


def nhap_ket_qua_spineditor(van_ban_paste, danh_sach_bai_viet_wp=None):
    """
    Phân tích văn bản sao chép từ SpinEditor (spineditor.com) hoặc bảng thứ hạng:
    Hỗ trợ hoàn hảo:
    1. SpinEditor 'Copy All' (7 cột): STT \t Từ khóa \t Vị trí \t Vị trí cũ \t Vị trí tốt nhất \t Cập nhật \t Liên kết
    2. Cột cách nhau bởi Tab/Phẩy/Gạch đứng: [Từ khóa] \t [Thứ hạng] \t [Link URL (tùy chọn)]
    3. Dòng cú pháp: 'tấm ốp nano - 2' hoặc 'tấm ốp nano: Top 2'
    """
    from datetime import datetime
    if not van_ban_paste or not van_ban_paste.strip():
        return []

    lines = [l.strip() for l in van_ban_paste.strip().splitlines() if l.strip()]
    parsed_results = []
    now_str = datetime.now().strftime("%d/%m/%Y")
    
    for idx, line in enumerate(lines, 1):
        tokens = [t.strip() for t in re.split(r'[\t;|]', line)]
        
        kw = ""
        rank_val = None
        rank_best = None
        link_val = ""
        date_val = now_str
        diff_str = "-"
        
        # Trường hợp 1: SpinEditor Copy All đầy đủ (7 cột: STT, Từ khóa, Vị trí, Vị trí cũ, Tốt nhất, Ngày, Link)
        if len(tokens) >= 5 and tokens[0].isdigit():
            kw = tokens[1]
            raw_rk = tokens[2]
            m_r = re.search(r'(\d+)', raw_rk)
            rank_val = int(m_r.group(1)) if m_r else None
            
            # Biến động
            if "↑" in raw_rk or "+" in raw_rk:
                diff_str = f"⬆️ Tăng {rank_val}"
            elif "↓" in raw_rk or "-" in raw_rk:
                diff_str = f"⬇️ Giảm"
            elif rank_val:
                diff_str = f"⭐ Top {rank_val}"
            else:
                diff_str = "⚪ n/a"
                
            # Vị trí tốt nhất
            if len(tokens) > 4:
                m_b = re.search(r'(\d+)', tokens[4])
                rank_best = int(m_b.group(1)) if m_b else rank_val
            else:
                rank_best = rank_val
                
            # Ngày cập nhật
            if len(tokens) > 5 and "/" in tokens[5]:
                date_val = tokens[5]
                
            # Link URL
            if len(tokens) > 6 and tokens[6].startswith("http"):
                link_val = tokens[6]
                
        # Trường hợp 2: Bảng 2 - 4 cột (Từ khóa \t Thứ hạng \t Link)
        elif len(tokens) >= 2:
            kw = tokens[0]
            m_rank = re.search(r'\b(\d+)\b', tokens[1])
            if m_rank:
                rank_val = int(m_rank.group(1))
                rank_best = rank_val
                diff_str = f"⭐ Top {rank_val}"
            elif any(x in tokens[1].lower() for x in ["ngoai", "not", "50+", "n/a"]):
                rank_val = None
                diff_str = "⚪ Ngoài Top 50"
                
            if len(tokens) >= 3 and tokens[2].startswith("http"):
                link_val = tokens[2]
        else:
            # Trường hợp 3: Văn bản dạng dòng 'tấm ốp nano: Top 2' hoặc 'tấm ốp nano - 2'
            m = re.match(r'^([^:\-]+)[\:\-]\s*(?:top\s*)?(\d+)(.*)$', line, re.IGNORECASE)
            if m:
                kw = m.group(1).strip()
                rank_val = int(m.group(2))
                rank_best = rank_val
                diff_str = f"⭐ Top {rank_val}"
                rest = m.group(3).strip()
                m_url = re.search(r'(https?://[^\s]+)', rest)
                if m_url:
                    link_val = m_url.group(1)
            else:
                kw = line
                rank_val = None
                diff_str = "⚪ Chưa có thứ hạng"

        if not kw or kw.lower() in ["stt", "từ khóa", "keyword"]:
            continue
            
        matched_page = tim_bai_viet_khop_nhat_wp(kw, danh_sach_bai_viet_wp)
        matched_title = ""
        if matched_page:
            matched_title = matched_page.get("title", "")
            if not link_val:
                link_val = matched_page.get("link", "")
                
        rank_str = f"Top {rank_val}" if rank_val else "Ngoài Top 50"
        parsed_results.append({
            "stt": idx,
            "tu_khoa": kw,
            "rank": rank_val,
            "rank_best": rank_best or rank_val,
            "rank_str": rank_str,
            "bien_dong_str": diff_str,
            "link": link_val,
            "title": matched_title,
            "thoi_gian": date_val
        })
        
    return parsed_results


# CẤU HÌNH TRÌNH DUYỆT CHROME QUÉT THỨ HẠNG THẬT TRÊN GOOGLE (LIVE SERP SCRAPER)
import subprocess
import tempfile

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = os.path.join(tempfile.gettempdir(), "hwood_rank_chrome_profile")


def trich_xuat_urls_tu_dom(text):
    """Trích xuất danh sách tất cả các URL organic sạch từ DOM rendered của Google"""
    if not text:
        return []
        
    found_urls = re.findall(r'&quot;(https?://(?!www\.google|encrypted-tbn|schema|w3|support\.google|policies)[^&"\s]+)&quot;', text)
    a_hrefs = re.findall(r'<a\s+[^>]*href=["\'](https?://(?!www\.google|encrypted-tbn|schema|w3|support\.google|policies)[^"\']+)["\']', text)
    
    clean_urls = []
    for u in found_urls + a_hrefs:
        u_clean = u.replace('\\u003d', '=').replace('\\u0026', '&').split('?')[0].split('#')[0].rstrip('/')
        if any(ig in u_clean.lower() for ig in ['gstatic.com', 'google.com', 'google.com.vn', 'youtube.com', 'facebook.com', 'w3.org']):
            continue
        if u_clean.startswith("http") and u_clean not in clean_urls:
            clean_urls.append(u_clean)
            
    return clean_urls


def quet_google_live_chrome(keyword, start=0):
    """
    Sử dụng Google Chrome chạy ngầm với anti-detection và profile cô lập
    để tải DOM thực tế 100% không bị chặn enablejs của Google.
    """
    if not os.path.exists(CHROME_PATH):
        return None, "chrome_not_found"

    encoded = urllib.parse.quote_plus(keyword.strip())
    url = f"https://www.google.com.vn/search?q={encoded}&hl=vi&gl=vn"
    if start > 0:
        url += f"&start={start}"

    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--disable-gpu",
        "--disable-ipv6",
        "--disable-http2",
        "--disable-quic",
        f"--user-data-dir={PROFILE_DIR}",
        "--disable-blink-features=AutomationControlled",
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "--dump-dom",
        url
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=12)
        text = res.stdout or ""
        if not text:
            return None, "empty_response"
        if "captcha-form" in text or "unusual traffic" in text.lower():
            return None, "captcha"
        return text, "ok"
    except Exception as e:
        return None, str(e)


def check_thu_hang_google_keyword(keyword, target_domain="hwood.vn", danh_sach_bai_viet_wp=None, max_pages=2):
    """
    Kiểm tra thứ hạng từ khóa THỰC TẾ trên Google Việt Nam (Top 20 organic)
    - Tự động dùng Google Chrome headless lấy DOM kết quả thật
    - Tuyệt đối KHÔNG gán thứ hạng ảo hay dữ liệu cứng
    - Trả về: (found_rank, found_link, status_code)
      status_code: 'ok', 'not_in_top', 'captcha', 'chrome_not_found', 'error'
    """
    clean_kw = keyword.strip()
    if not clean_kw:
        return None, None, "empty_keyword"
        
    clean_target = target_domain.lower().replace("https://", "").replace("http://", "").strip().rstrip("/")
    
    # 1. Tìm trước link bài viết đích tương ứng từ WordPress làm phương án đối chiếu
    bai_viet_dich = tim_bai_viet_khop_nhat_wp(clean_kw, danh_sach_bai_viet_wp)
    fallback_link = bai_viet_dich["link"] if bai_viet_dich else ""

    total_clean_urls = []
    
    # Quét trang 1 (Top 1-10) và trang 2 (Top 11-20) nếu cần
    for p_idx in range(max_pages):
        start_offset = p_idx * 10
        dom_text, status = quet_google_live_chrome(clean_kw, start=start_offset)
        
        if status == "captcha":
            return None, fallback_link, "captcha"
        if status != "ok" or not dom_text:
            if p_idx == 0:
                # Nếu trang 1 lỗi, thử fallback sang requests với desktop headers
                try:
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
                    }
                    encoded = urllib.parse.quote_plus(clean_kw)
                    r = requests.get(f"https://www.google.com.vn/search?q={encoded}&hl=vi&gl=vn", headers=headers, timeout=8)
                    if "captcha" in r.text.lower():
                        return None, fallback_link, "captcha"
                    dom_text = r.text
                except Exception:
                    return None, fallback_link, "error"
            else:
                break
                
        page_urls = trich_xuat_urls_tu_dom(dom_text)
        for u in page_urls:
            if u not in total_clean_urls:
                total_clean_urls.append(u)
                
        # Kiểm tra xem target_domain đã xuất hiện trong danh sách chưa
        hwood_hits = []
        for rank_pos, u in enumerate(total_clean_urls, 1):
            if clean_target in u.lower():
                hwood_hits.append((rank_pos, u))
                
        if hwood_hits:
            best_rank, best_url = hwood_hits[0]
            return best_rank, best_url, "ok"

    # Nếu đã quét hết mà không tìm thấy target_domain
    return None, fallback_link, "not_in_top"



def xuat_csv_thu_hang(danh_sach_rank):
    """Xuất danh sách thứ hạng từ khóa thành chuỗi CSV chuẩn UTF-8 BOM cho Excel"""
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow([
        "STT", 
        "Từ Khóa", 
        "Thứ Hạng Google", 
        "Biến Động", 
        "URL Bài Viết Đang Lên Top", 
        "Thời Gian Kiểm Tra"
    ])
    for idx, row in enumerate(danh_sach_rank, 1):
        writer.writerow([
            idx,
            row.get("tu_khoa", ""),
            row.get("rank_str", "Ngoài Top 50"),
            row.get("bien_dong_str", "-"),
            row.get("link", ""),
            row.get("thoi_gian", "")
        ])
    return output.getvalue()


# ==============================================================================
# HỆ THỐNG CƠ SỞ DỮ LIỆU TỪ KHÓA ĐÃ THEO DÕI (TRACKED KEYWORDS DATABASE)
# ==============================================================================
def doc_database_keywords():
    """Đọc toàn bộ cơ sở dữ liệu từ khóa đã tra cứu và theo dõi (Tracked Keywords Database)"""
    from modules.knowledge import phan_loai_chu_de, viet_hoa_tieu_de
    
    db = {}
    if os.path.exists(KEYWORD_DATABASE_FILE):
        try:
            with open(KEYWORD_DATABASE_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
        except Exception:
            db = {}
            
    # Nếu DB rỗng, tự động khởi tạo từ lịch sử hiện có (lọc sạch bài nháp/admin)
    if not db:
        old_hist = doc_lich_su_thu_hang()
        for kw_raw, val in old_hist.items():
            if not kw_raw or any(x in kw_raw.lower() for x in ["thủ công", "bản nháp", "giới thiệu", "liên hệ"]):
                continue
            rk = val.get("rank")
            rk_best = val.get("rank_best") or rk
            k_clean = kw_raw.lower().strip()
            db[k_clean] = {
                "tu_khoa": viet_hoa_tieu_de(kw_raw),
                "tu_khoa_key": k_clean,
                "loai": "Chính",
                "chuyen_muc": phan_loai_chu_de(kw_raw),
                "url_dich": val.get("link", ""),
                "tieu_de_bai": val.get("title", ""),
                "rank_hien_tai": rk,
                "rank_tot_nhat": rk_best,
                "bien_dong": f"Top {rk}" if rk else "n/a",
                "ngay_tra_cuoi": val.get("thoi_gian", "12/11/2026"),
                "lich_su_rank": [
                    {"ngay": val.get("thoi_gian", "12/11/2026"), "rank": rk}
                ] if rk else [],
                "ghi_chu": "Tự động đồng bộ từ lịch sử"
            }
        if db:
            luu_database_keywords(db)
            
    return db


def luu_database_keywords(data):
    """Lưu toàn bộ cơ sở dữ liệu từ khóa theo dõi"""
    try:
        with open(KEYWORD_DATABASE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def dong_bo_ket_qua_quet_vao_db(danh_sach_ket_qua, danh_sach_bai_viet_wp=None):
    """Tự động đồng bộ kết quả quét Google / SpinEditor vào Cơ sở dữ liệu từ khóa đã tra cứu"""
    from datetime import datetime
    from modules.knowledge import phan_loai_chu_de, viet_hoa_tieu_de
    
    if not danh_sach_ket_qua:
        return
        
    db = doc_database_keywords()
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    today_date = datetime.now().strftime("%d/%m/%Y")
    
    for item in danh_sach_ket_qua:
        kw = item.get("tu_khoa", "").strip()
        if not kw or any(x in kw.lower() for x in ["thủ công", "bản nháp", "giới thiệu", "liên hệ"]):
            continue
            
        k_key = kw.lower().strip()
        rk = item.get("rank")
        rk_best_candidate = item.get("rank_best") or rk
        link = item.get("link", "")
        title = item.get("title", "")
        time_check = item.get("thoi_gian") or now_str
        
        # Nếu chưa có link hoặc title, tìm bài khớp trên WP
        if (not link or not title) and danh_sach_bai_viet_wp:
            matched = tim_bai_viet_khop_nhat_wp(kw, danh_sach_bai_viet_wp)
            if matched:
                if not link:
                    link = matched.get("link", "")
                if not title:
                    title = matched.get("title", "")
                    
        if k_key in db:
            record = db[k_key]
            old_rank = record.get("rank_hien_tai")
            old_best = record.get("rank_tot_nhat")
            
            # Tính toán thứ hạng tốt nhất
            new_best = old_best
            if rk is not None:
                if old_best is None:
                    new_best = rk
                else:
                    new_best = min(old_best, rk)
            elif rk_best_candidate is not None:
                new_best = rk_best_candidate if old_best is None else min(old_best, rk_best_candidate)
                
            # Tính biến động
            diff_str = "-"
            if rk is not None and old_rank is not None:
                diff = old_rank - rk
                if diff > 0:
                    diff_str = f"▲ +{diff}"
                elif diff < 0:
                    diff_str = f"▼ {diff}"
                else:
                    diff_str = "▬ 0"
            elif rk is not None:
                diff_str = f"★ Top {rk}"
            else:
                diff_str = "n/a"

            record["rank_hien_tai"] = rk
            record["rank_tot_nhat"] = new_best
            record["bien_dong"] = diff_str
            record["ngay_tra_cuoi"] = time_check
            if link:
                record["url_dich"] = link
            if title:
                record["tieu_de_bai"] = title
                
            # Lưu lịch sử rank
            hist_list = record.get("lich_su_rank", [])
            if not any(h.get("ngay") == today_date for h in hist_list):
                hist_list.append({"ngay": today_date, "rank": rk})
            else:
                for h in hist_list:
                    if h.get("ngay") == today_date:
                        h["rank"] = rk
            record["lich_su_rank"] = hist_list
        else:
            db[k_key] = {
                "tu_khoa": viet_hoa_tieu_de(kw),
                "tu_khoa_key": k_key,
                "loai": "Chính",
                "chuyen_muc": phan_loai_chu_de(kw),
                "url_dich": link,
                "tieu_de_bai": title,
                "rank_hien_tai": rk,
                "rank_tot_nhat": rk,
                "bien_dong": f"★ Top {rk}" if rk else "n/a",
                "ngay_tra_cuoi": time_check,
                "lich_su_rank": [{"ngay": today_date, "rank": rk}] if rk else [],
                "ghi_chu": "Mới thêm từ kết quả quét"
            }
            
    luu_database_keywords(db)


def them_tu_khoa_vao_db(danh_sach_tu_khoa, loai="Chính", chuyen_muc="", danh_sach_bai_viet_wp=None):
    """Thêm danh sách từ khóa vào Database theo dõi"""
    from datetime import datetime
    from modules.knowledge import phan_loai_chu_de, viet_hoa_tieu_de
    
    if not danh_sach_tu_khoa:
        return 0
        
    db = doc_database_keywords()
    now_str = datetime.now().strftime("%d/%m/%Y")
    count_added = 0
    
    for kw in danh_sach_tu_khoa:
        kw_clean = kw.strip()
        if not kw_clean or len(kw_clean) < 3:
            continue
        k_key = kw_clean.lower()
        if k_key in db:
            continue
            
        matched_link = ""
        matched_title = ""
        if danh_sach_bai_viet_wp:
            m = tim_bai_viet_khop_nhat_wp(kw_clean, danh_sach_bai_viet_wp)
            if m:
                matched_link = m.get("link", "")
                matched_title = m.get("title", "")
                
        db[k_key] = {
            "tu_khoa": viet_hoa_tieu_de(kw_clean),
            "tu_khoa_key": k_key,
            "loai": loai,
            "chuyen_muc": chuyen_muc or phan_loai_chu_de(kw_clean),
            "url_dich": matched_link,
            "tieu_de_bai": matched_title,
            "rank_hien_tai": None,
            "rank_tot_nhat": None,
            "bien_dong": "Chưa quét",
            "ngay_tra_cuoi": now_str,
            "lich_su_rank": [],
            "ghi_chu": "Thêm thủ công"
        }
        count_added += 1
        
    if count_added > 0:
        luu_database_keywords(db)
    return count_added


def xoa_tu_khoa_khoi_db(tu_khoa_key):
    """Xóa một từ khóa khỏi cơ sở dữ liệu theo dõi"""
    db = doc_database_keywords()
    k_key = tu_khoa_key.lower().strip()
    if k_key in db:
        del db[k_key]
        luu_database_keywords(db)
        return True
    return False


def xuat_csv_database_keywords(db_dict):
    """Xuất toàn bộ Cơ sở dữ liệu từ khóa thành CSV chuẩn UTF-8 BOM để mở trong Excel"""
    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow([
        "STT", 
        "Từ Khóa", 
        "Loại Từ Khóa", 
        "Chuyên Mục HWOOD", 
        "Thứ Hạng Hiện Tại", 
        "Thứ Hạng Tốt Nhất", 
        "Biến Động", 
        "Ngày Kiểm Tra Cuối", 
        "URL Bài Viết Đang Lên Top", 
        "Tiêu Đề Bài Viết", 
        "Số Lần Đã Quét", 
        "Ghi Chú"
    ])
    
    for idx, (k_key, item) in enumerate(db_dict.items(), 1):
        rk_cur = item.get("rank_hien_tai")
        rk_cur_str = f"Top {rk_cur}" if rk_cur else "Ngoài Top 50"
        rk_best = item.get("rank_tot_nhat")
        rk_best_str = f"Top {rk_best}" if rk_best else "-"
        num_scans = len(item.get("lich_su_rank", []))
        
        writer.writerow([
            idx,
            item.get("tu_khoa", k_key),
            item.get("loai", "Chính"),
            item.get("chuyen_muc", "Tổng hợp"),
            rk_cur_str,
            rk_best_str,
            item.get("bien_dong", "-"),
            item.get("ngay_tra_cuoi", ""),
            item.get("url_dich", ""),
            item.get("tieu_de_bai", ""),
            num_scans,
            item.get("ghi_chu", "")
        ])
    return output.getvalue()
