# -*- coding: utf-8 -*-
"""
MODULE CHIẾN LƯỢC ĐỘT PHÁ TOP 1 - 5: CHẨN ĐOÁN & TỐI ƯU TỪ KHÓA NGOÀI TOP 5
Dành riêng cho thương hiệu HWOOD VIỆT NAM (https://hwood.vn)
Tự động phát hiện nguyên nhân rớt Top, đề xuất hành động 1-click chuyển tiếp sang:
- Tab 1: Viết bài mới bứt phá Top
- Tab 2: Sửa & Nâng cấp bài cũ chuẩn On-page
- Tab 5: Đưa vào Kế hoạch biên tập tháng
- Tab 8: Đưa vào hàng đợi 5 Bot quét thứ hạng & đẩy tương tác
"""

import os
import re
import json
from datetime import datetime
from modules.file_handler import xoa_dau_tieng_viet
from modules.knowledge import phan_loai_chu_de, viet_hoa_tieu_de

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN_DIR = os.path.join(BASE_DIR, "ke_hoach_noi_dung")


# ==============================================================================
# 1. HÀM CHẨN ĐOÁN CHI TIẾT TỪ KHÓA NGOÀI TOP 5
# ==============================================================================
def chan_doan_tu_khoa_ngoai_top(item_data, danh_sach_bai_viet_wp=None):
    """
    Phân tích một từ khóa đang nằm ngoài Top 5 và sinh ra báo cáo chẩn đoán:
    - Phân tầng ưu tiên (Tier 1: Top 6-10, Tier 2: Top 11-20, Tier 3: Ngoài Top 20)
    - Nguyên nhân rớt Top (Cannibalization, Lệch Search Intent, Thin Content, Thiếu Bảng Giá, v.v.)
    - Danh sách lỗi phát hiện (Tags)
    - Đề xuất phương án bứt phá Top cụ thể chuẩn HWOOD (Bảng giá VAT 8%, Quick Answer <60 từ, ASA Quatest 3, v.v.)
    - Tiêu đề & Thể loại bài viết đề xuất
    - Nút hành động ưu tiên
    """
    kw = item_data.get("tu_khoa", "").strip()
    rank = item_data.get("rank_hien_tai")
    if rank is None:
        rank = item_data.get("rank")
    url_dich = item_data.get("url_dich") or item_data.get("link") or ""
    tieu_de_bai = item_data.get("tieu_de_bai") or item_data.get("title") or ""
    chuyen_muc = item_data.get("chuyen_muc") or phan_loai_chu_de(kw)
    
    kw_lower = kw.lower()
    kw_ascii = xoa_dau_tieng_viet(kw_lower)
    
    # 1. Xác định Tier phân tầng
    if rank is not None and 6 <= rank <= 10:
        tier = 1
        tier_name = "⚡ Tier 1: Cận Top (Top 6 - 10)"
        tier_badge = "cận_top"
        uu_tien_str = "ƯU TIÊN SỐ 1: BỨT PHÁ TOP 1 - 3 NGAY (Chỉ cần tối ưu On-page nhẹ)"
    elif rank is not None and 11 <= rank <= 20:
        tier = 2
        tier_name = "🔄 Tier 2: Lệch Intent / Trang 2 (Top 11 - 20)"
        tier_badge = "lech_intent"
        uu_tien_str = "ƯU TIÊN SỐ 2: CẤU TRÚC LẠI NỘI DUNG & INTERNAL LINK"
    else:
        tier = 3
        tier_name = "🎯 Tier 3: Khoảng Trống Nội Dung (Ngoài Top 20 / n/a)"
        tier_badge = "khoang_trong"
        uu_tien_str = "ƯU TIÊN SỐ 3: VIẾT MỚI PILLAR PAGE HOẶC LÊN KẾ HOẠCH THÁNG"

    # 2. Nhận diện Search Intent
    is_price = any(w in kw_lower for w in ["báo giá", "bao gia", "giá", "gia", "bảng giá", "bang gia", "chi phí", "nhiêu tiền", "đơn giá"])
    is_gallery = any(w in kw_lower for w in ["mẫu", "mau", "thiết kế", "thiet ke", "hình ảnh", "hinh anh", "phối cảnh"])
    is_howto = any(w in kw_lower for w in ["cách", "cach", "hướng dẫn", "huong dan", "thi công", "thi cong", "lắp đặt", "lap dat", "quy trình", "vệ sinh", "keo"])
    is_compare = any(w in kw_lower for w in ["so sánh", "so sanh", "vs", "có bền không", "co ben khong", "loại nào tốt", "loai nao tot", "có nên", "co nen", "đánh giá", "review"])
    is_head_term = not (is_price or is_gallery or is_howto or is_compare)

    # 3. Kiểm tra các lỗi On-page & SERP phổ biến
    loi_phat_hien = []
    nguyen_nhan_list = []
    de_xuat_list = []
    
    # Kiểm tra Cannibalization qua Trang Chủ (hwood.vn / hwood.vn/)
    is_homepage_cannibalization = False
    clean_url = url_dich.rstrip("/")
    if clean_url in ["https://hwood.vn", "http://hwood.vn"] and not any(w in kw_lower for w in ["hwood", "hwood việt nam"]):
        is_homepage_cannibalization = True
        loi_phat_hien.append("⚠️ Ăn thịt từ khóa qua Trang Chủ (Cannibalization)")
        nguyen_nhan_list.append("Google đang xếp hạng Trang chủ (hwood.vn) thay vì Landing Page chuyên biệt của danh mục/sản phẩm này, làm giảm độ liên quan và rớt hạng.")
        de_xuat_list.append("Tạo hoặc trỏ liên kết nội bộ về đúng URL danh mục chuyên sâu (không để trang chủ gánh từ khóa cụ thể này).")

    # Kiểm tra Intent Mismatch
    if is_price and ("co-nen" in url_dich or "quy-trinh" in url_dich or "top-5" in url_dich):
        loi_phat_hien.append("⚠️ Lệch Search Intent (Khách tìm Giá nhưng bài là Cẩm nang/Hướng dẫn)")
        nguyen_nhan_list.append("Người dùng có nhu cầu tham khảo đơn giá và dự toán chi phí, nhưng Google đang trỏ vào bài cẩm nang lý thuyết hoặc tin tức chung.")
        de_xuat_list.append("Chuyển hướng hoặc bổ sung ngay Bảng Báo Giá chi tiết dạng HTML Table có phân chia VAT 8% lên đầu bài.")

    # Kiểm tra bài viết rớt Top 6-10 (Cận Top)
    if tier == 1:
        loi_phat_hien.append("📌 Thiếu Quick Answer Snippet (<60 chữ)")
        loi_phat_hien.append("📌 CTR chưa tối ưu (Meta Title thiếu mốc năm 2026)")
        nguyen_nhan_list.append("Bài viết đã lọt vào trang 1 (Top 6-10) nhưng thiếu định nghĩa súc tích (<60 chữ) để Google bốc lên Featured Snippet Top 0-3.")
        de_xuat_list.append("Chèn đoạn tóm tắt Quick Answer 40-55 từ ngay dưới tiêu đề H1.")
        de_xuat_list.append("Thêm mốc thời gian 'Mới Nhất 2026' và ưu đãi 'Bảo Hành 10-15 Năm' vào Thẻ Tiêu Đề để kéo CTR vượt đối thủ.")
        if is_price:
            loi_phat_hien.append("📌 Thiếu Bảng giá HTML có VAT 8%")
            de_xuat_list.append("Chèn Bảng báo giá HTML chi tiết: Đơn giá vật tư theo mét dài/thanh/m2 + Đơn giá thi công hoàn thiện trọn gói.")

    elif tier == 2:
        loi_phat_hien.append("📌 Thiếu Internal Link vệ tinh (Topic Cluster)")
        loi_phat_hien.append("📌 Mật độ từ khóa chính chưa đồng đều")
        nguyen_nhan_list.append("Từ khóa đang nằm ở trang 2 (Top 11-20) do thiếu sức mạnh hỗ trợ từ các bài viết vệ tinh trong cùng cụm chủ đề.")
        de_xuat_list.append("Viết bổ sung 2-3 bài viết vệ tinh xung quanh từ khóa này và đặt Anchor Text chính xác trỏ về trang đích.")
        de_xuat_list.append("Bổ sung thẻ H2/H3 chứa đúng từ khóa chính và 3-4 từ khóa phụ LSI liên quan.")

    elif tier == 3:
        loi_phat_hien.append("📌 Khoảng trống nội dung (Content Gap)")
        loi_phat_hien.append("📌 Chưa có bài Pillar chuyên đề riêng biệt")
        nguyen_nhan_list.append("Website chưa có bài viết chuyên sâu độc lập đáp ứng đúng nhu cầu tìm kiếm này của khách hàng; đối thủ đang chiếm lĩnh toàn bộ SERP.")
        de_xuat_list.append("Khởi tạo ngay 1 bài viết mới chuẩn SEO (1.300 - 1.600 từ) hoặc đưa vào Kế hoạch biên tập tháng.")
        de_xuat_list.append("Tích hợp đầy đủ thông số kỹ thuật HWOOD (Quatest 3, ASA, thép hộp mạ kẽm, nẹp nắp chụp HW-SET120, keo 3X-BOND).")

    # Bổ sung góc nhìn kỹ thuật HWOOD theo từng ngành hàng
    if "gỗ nhựa" in kw_lower or "sàn" in kw_lower or "wpc" in kw_lower:
        de_xuat_list.append("Kỹ thuật HWOOD: Khẳng định vật liệu phủ ASA chống bay màu tia UV; chứng nhận Quatest 3 độ giãn nở <1%; khung xương đà cách nhau tối đa 30-35cm.")
    elif "nano" in kw_lower or "pvc" in kw_lower or "vân đá" in kw_lower:
        de_xuat_list.append("Kỹ thuật HWOOD: Khuyên dùng keo dán chuyên dụng 3X-BOND kết hợp băng keo xốp; chống ẩm mốc vách tường triệt để.")
    elif "pergola" in kw_lower or "lam" in kw_lower:
        de_xuat_list.append("Kỹ thuật HWOOD: Bắt buộc lồng lõi thép hộp mạ kẽm 1.4 - 1.8mm bên trong thanh lam/trụ hộp để chịu lực giông bão ngoài trời.")
    elif "bàn ghế" in kw_lower or "polywood" in kw_lower:
        de_xuat_list.append("Kỹ thuật HWOOD: Nhấn mạnh nan gỗ nhựa Polywood cao cấp không thấm nước kết hợp khung nhôm đúc sơn tĩnh điện chống rỉ sét.")

    # 4. Gợi ý Tiêu đề & Thể loại bài viết tối ưu chuẩn HWOOD
    now_year = datetime.now().year
    title_suggest = ""
    the_loai_suggest = ""
    
    if is_price:
        the_loai_suggest = "💰 Báo Giá (Price) + Bảng HTML kỹ thuật & VAT 8%"
        title_suggest = f"Báo Giá {viet_hoa_tieu_de(kw)} Mới Nhất {now_year}: Bảng Giá Chi Tiết & Chiết Khấu - HWOOD"
    elif is_compare:
        the_loai_suggest = "⚖️ So Sánh (Comparison) - 2 hoặc 4 loại vật liệu"
        title_suggest = f"{viet_hoa_tieu_de(kw)}: Phân Tích Thực Tế & Lời Khuyên Chuyên Gia HWOOD"
    elif is_howto:
        the_loai_suggest = "🛠️ Hướng Dẫn Kỹ Thuật (How-to) + Checklist thi công"
        title_suggest = f"Quy Trình Thi Công {viet_hoa_tieu_de(kw)} Chuẩn Kỹ Thuật Chi Tiết Từ A-Z - HWOOD"
    elif is_gallery:
        the_loai_suggest = "🖼️ Mẫu & Thiết Kế (Gallery / Listicle) - Top mẫu đẹp xu hướng"
        title_suggest = f"Top 25+ {viet_hoa_tieu_de(kw)} Xu Hướng Đẹp Nhất {now_year} - HWOOD"
    else:
        the_loai_suggest = "🎯 Hướng Dẫn Chọn Mua + Kỹ thuật mã hàng"
        title_suggest = f"{viet_hoa_tieu_de(kw)} Là Gì? Phân Loại, Ưu Điểm & Ứng Dụng Chuẩn - HWOOD"

    # Lời khuyên chiến lược
    ghi_chu_chien_luoc = f"Tập trung đánh vào USP cốt lõi của HWOOD: Tổng kho sỉ giá gốc, chứng chỉ Quatest 3, chính sách bảo hành 10-15 năm, hotline 0912 565 353 gửi mẫu tận nơi."

    return {
        "tu_khoa": kw,
        "rank": rank,
        "rank_str": f"Top {rank}" if rank else "Ngoài Top 20 (n/a)",
        "tier": tier,
        "tier_name": tier_name,
        "tier_badge": tier_badge,
        "uu_tien_str": uu_tien_str,
        "url_dich": url_dich,
        "tieu_de_bai": tieu_de_bai,
        "chuyen_muc": chuyen_muc,
        "loi_phat_hien": loi_phat_hien,
        "nguyen_nhan": " ".join(nguyen_nhan_list) if nguyen_nhan_list else "Từ khóa chưa được tối ưu các yếu tố On-page chuyên sâu hoặc thiếu liên kết nội bộ chất lượng.",
        "phuong_an_de_xuat": de_xuat_list,
        "tieu_de_de_xuat": title_suggest,
        "the_loai_de_xuat": the_loai_suggest,
        "ghi_chu_chien_luoc": ghi_chu_chien_luoc,
        "is_homepage_cannibalization": is_homepage_cannibalization,
        "is_price": is_price,
        "is_howto": is_howto
    }


# ==============================================================================
# 2. LẤY TOÀN BỘ DANH SÁCH TỪ KHÓA NGOÀI TOP 5 & PHÂN TẦNG
# ==============================================================================
def lay_toan_bo_chan_doan_ngoai_top(db_tracked=None, danh_sach_bai_viet_wp=None):
    """
    Quét cơ sở dữ liệu từ khóa, lọc ra toàn bộ từ khóa ngoài Top 5,
    trả về cấu trúc phân tầng Tier 1 (Cận Top 6-10), Tier 2 (Top 11-20), Tier 3 (Ngoài Top 20/n/a).
    """
    from modules.rank_tracker import doc_database_keywords
    
    if db_tracked is None:
        db_tracked = doc_database_keywords()

    tier1 = []
    tier2 = []
    tier3 = []
    
    for k_key, v in db_tracked.items():
        rk = v.get("rank_hien_tai")
        if rk is not None and 1 <= rk <= 5:
            # Đã vững vàng trong Top 1-5 -> Bỏ qua
            continue
            
        diag = chan_doan_tu_khoa_ngoai_top(v, danh_sach_bai_viet_wp)
        t = diag["tier"]
        if t == 1:
            tier1.append(diag)
        elif t == 2:
            tier2.append(diag)
        else:
            tier3.append(diag)

    # Sắp xếp theo mức độ ưu tiên
    tier1.sort(key=lambda x: (x.get("rank") or 99))
    tier2.sort(key=lambda x: (x.get("rank") or 99))
    tier3.sort(key=lambda x: x.get("tu_khoa", ""))

    return {
        "tier1": tier1,
        "tier2": tier2,
        "tier3": tier3,
        "tong_so_ngoai_top": len(tier1) + len(tier2) + len(tier3),
        "dem_tier1": len(tier1),
        "dem_tier2": len(tier2),
        "dem_tier3": len(tier3)
    }


# ==============================================================================
# 3. HÀM ĐƯA NHANH TỪ KHÓA VÀO KẾ HOẠCH BIÊN TẬP THÁNG (TAB 5)
# ==============================================================================
def dua_vao_ke_hoach_thang_nhanh(kw, tieu_de, the_loai, ghi_chu, cum_chu_de, tu_khoa_phu=None, thang_nam=None):
    """
    Thêm một từ khóa hoặc bài viết chiến lược vào file kế hoạch tháng (ke_hoach_Tháng_...json)
    trực tiếp mà không ghi đè dữ liệu cũ.
    """
    from modules.content_planner import lay_ke_hoach_thang, luu_ke_hoach_thang
    
    if not thang_nam:
        now = datetime.now()
        thang_nam = f"Tháng {now.month:02d}/{now.year}"
        
    danh_sach_bai = lay_ke_hoach_thang(thang_nam)
    
    # Kiểm tra xem từ khóa này đã có trong kế hoạch chưa
    kw_clean = kw.lower().strip()
    for item in danh_sach_bai:
        if item.get("tu_khoa_chinh", "").lower().strip() == kw_clean:
            return False, f"Từ khóa '{kw}' đã có sẵn trong kế hoạch {thang_nam}!"

    # Tính tuần và thứ kế tiếp
    so_bai_hien_tai = len(danh_sach_bai)
    so_tuan = (so_bai_hien_tai // 3) + 1
    tuan_str = f"Tuần {min(4, so_tuan)}"
    
    thu_list = ["Thứ 2", "Thứ 4", "Thứ 6", "Thứ 3", "Thứ 5"]
    thu_str = thu_list[so_bai_hien_tai % len(thu_list)]
    
    intent_val = "Thương mại (Mua hàng)"
    if "Báo Giá" in the_loai:
        intent_val = "Tham khảo giá"
    elif "Hướng Dẫn" in the_loai:
        intent_val = "Kỹ thuật thi công"
    elif "Mẫu" in the_loai:
        intent_val = "Tìm ý tưởng thiết kế"
    elif "So Sánh" in the_loai:
        intent_val = "So sánh đánh giá"

    if not tu_khoa_phu:
        tu_khoa_phu = [
            f"{kw} hwood",
            f"{kw} giá rẻ",
            f"{kw} chất lượng cao",
            f"{kw} mới nhất"
        ]

    new_item = {
        "tuan": tuan_str,
        "thu": thu_str,
        "tieu_de": tieu_de,
        "tu_khoa_chinh": kw,
        "tu_khoa_phu": tu_khoa_phu,
        "the_loai": the_loai,
        "search_intent": intent_val,
        "cum_chu_de": cum_chu_de or "Gỗ nhựa ngoài trời WPC",
        "ghi_chu": ghi_chu or "Bứt phá Top 1-5 Google bằng cấu trúc On-page chuẩn HWOOD",
        "trang_thai": "Chưa viết"
    }

    danh_sach_bai.append(new_item)
    success = luu_ke_hoach_thang(thang_nam, danh_sach_bai)
    if success:
        return True, f"Đã thêm thành công '{kw}' vào Kế hoạch {thang_nam} ({tuan_str} - {thu_str})!"
    return False, "Không thể lưu vào file kế hoạch tháng!"


# ==============================================================================
# 4. HÀM ĐƯA TỪ KHÓA VÀO HÀNG ĐỢI 5 BOT (TAB 8)
# ==============================================================================
def dua_vao_bot_farm_queue(kw):
    """
    Thêm từ khóa vào file bot_keywords.txt để hệ thống 5 Bot quét thứ hạng và tương tác.
    """
    bot_kw_file = os.path.join(BASE_DIR, "bot_keywords.txt")
    existing_kws = []
    if os.path.exists(bot_kw_file):
        try:
            with open(bot_kw_file, "r", encoding="utf-8") as f:
                existing_kws = [line.strip() for line in f if line.strip()]
        except Exception:
            existing_kws = []
            
    kw_clean = kw.strip()
    if kw_clean.lower() not in [k.lower() for k in existing_kws]:
        existing_kws.append(kw_clean)
        try:
            with open(bot_kw_file, "w", encoding="utf-8") as f:
                f.write("\n".join(existing_kws) + "\n")
            return True, f"Đã thêm '{kw_clean}' vào danh sách quét của 5 Bot!"
        except Exception as e:
            return False, f"Lỗi ghi file bot_keywords.txt: {e}"
    return True, f"Từ khóa '{kw_clean}' đã có sẵn trong danh sách 5 Bot!"
