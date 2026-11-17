import os
import json
import csv
import io
import re
from datetime import datetime
from openai import OpenAI
from modules.knowledge import viet_hoa_tieu_de
from modules.keyword_matrix import BO_32_CLUSTER_HWOOD

THU_MUC_PLAN = "ke_hoach_noi_dung"

def khoi_tao_thu_muc_plan():
    if not os.path.exists(THU_MUC_PLAN):
        os.makedirs(THU_MUC_PLAN, exist_ok=True)

def lay_ten_file_plan(thang_nam):
    """Tạo tên file theo định dạng ke_hoach_YYYY_MM.json"""
    khoi_tao_thu_muc_plan()
    clean_tn = re.sub(r'[^\w\-]', '_', thang_nam.strip())
    return os.path.join(THU_MUC_PLAN, f"ke_hoach_{clean_tn}.json")

def lay_ke_hoach_thang(thang_nam):
    """Đọc dữ liệu kế hoạch tháng từ file JSON"""
    file_path = lay_ten_file_plan(thang_nam)
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def luu_ke_hoach_thang(thang_nam, danh_sach_bai):
    """Lưu danh sách bài viết trong kế hoạch tháng vào file JSON"""
    file_path = lay_ten_file_plan(thang_nam)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(danh_sach_bai, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def lay_danh_sach_thang_da_co():
    """Lấy danh sách các tháng đã có kế hoạch"""
    khoi_tao_thu_muc_plan()
    ds = []
    for f in os.listdir(THU_MUC_PLAN):
        if f.startswith("ke_hoach_") and f.endswith(".json"):
            tn = f.replace("ke_hoach_", "").replace(".json", "")
            ds.append(tn)
    return sorted(ds, reverse=True)

def tao_ke_hoach_thang_ai(api_key, model, thang_nam, so_bai_tuan, chu_de_trong_tam, ds_wp=None, kho_tri_thuc=""):
    """Sử dụng DeepSeek để lập kế hoạch biên tập nội dung thông minh cho cả tháng"""
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=90.0)
    
    # Tổng hợp các từ khóa / tiêu đề đã có trên web để tránh trùng lặp
    bai_co_san = []
    if ds_wp:
        for p in ds_wp[:80]:
            bai_co_san.append(p.get("title", {}).get("rendered", ""))
    
    prompt = f"""Bạn là Giám Đốc Chiến Lược Nội Dung (SEO Content Director) của thương hiệu HWOOD VIỆT NAM (https://hwood.vn).
    
NHIỆM VỤ CỦA BẠN:
Lập bản KẾ HOẠCH BIÊN TẬP NỘI DUNG (Content Editorial Calendar) chi tiết cho tháng: {thang_nam}.
- Tần suất: {so_bai_tuan} bài viết / tuần (tổng cộng khoảng 4 tuần = {int(so_bai_tuan) * 4} bài viết).
- Trọng tâm ưu tiên tháng này: {chu_de_trong_tam}.

DANH SÁCH MỘT SỐ BÀI VIẾT ĐÃ CÓ TRÊN WEBSITE HWOOD.VN (BẮT BUỘC KHÔNG VIẾT TRÙNG LẶP TIÊU ĐỀ/TỪ KHÓA NÀY):
{bai_co_san[:40]}

BỘ NÃO 32 CỤM TỪ KHÓA CỐT LÕI & TOPIC CLUSTER HWOOD:
{list(BO_32_CLUSTER_HWOOD.keys())}

YÊU CẦU CẤU TRÚC KẾ HOẠCH NỘI DUNG THÁNG:
Mỗi bài viết phải là một đối tượng JSON chuẩn xác với các trường:
1. "tuan": Chuỗi (ví dụ "Tuần 1", "Tuần 2", "Tuần 3", "Tuần 4")
2. "thu": Chuỗi ngày trong tuần (ví dụ "Thứ 2", "Thứ 4", "Thứ 6")
3. "tieu_de": Tiêu đề bài viết hấp dẫn, chuẩn Yoast SEO (chứa từ khóa chính, độ dài 50-65 ký tự, không lặp từ)
4. "tu_khoa_chinh": Cụm từ khóa chính (Focus Keyword) chuẩn xác, có dung lượng tìm kiếm thực tế
5. "tu_khoa_phu": Danh sách 3-4 từ khóa phụ / LSI keywords đi kèm
6. "the_loai": 1 trong các thể loại sau:
   - "💰 Báo Giá (Price) + Bảng HTML kỹ thuật & VAT 8%"
   - "⚖️ So Sánh (Comparison) - 2 hoặc 4 loại vật liệu"
   - "🖼️ Mẫu & Thiết Kế (Gallery / Listicle) - Top mẫu đẹp xu hướng"
   - "🛠️ Hướng Dẫn Kỹ Thuật (How-to) + Checklist thi công"
   - "⭐ Review / Đánh Giá Thực Tế + Giải đáp thắc mắc Q&A"
   - "🎯 Hướng Dẫn Chọn Mua + Kỹ thuật mã hàng"
   - "🏡 Giải Pháp Ứng Dụng & Case Study theo không gian"
   - "📖 Định Nghĩa & Giải Thích (Define) + Báo giá cơ bản"
7. "search_intent": Mục đích tìm kiếm của người đọc ("Thương mại (Mua hàng)", "Tham khảo giá", "Kỹ thuật thi công", "Tìm ý tưởng thiết kế")
8. "cum_chu_de": 1 trong 5 cụm: "Gỗ nhựa ngoài trời WPC", "Tấm ốp tường PVC vân đá & Nano", "Trần nhựa nano giật cấp", "Sàn gỗ nhựa & Vỉ ban công", "Bàn ghế sân vườn polywood"
9. "ghi_chu": 1 câu định hướng ngắn gọn góc viết khác biệt để bài viết lên Top 1 Google.
10. "trang_thai": "Chưa viết"

BẮT BUỘC TRẢ VỀ DUY NHẤT 1 KHỐI JSON ARRAY HỢP LỆ THEO ĐỊNH DẠNG:
[
  {{
    "tuan": "Tuần 1",
    "thu": "Thứ 2",
    "tieu_de": "...",
    "tu_khoa_chinh": "...",
    "tu_khoa_phu": ["...", "..."],
    "the_loai": "...",
    "search_intent": "...",
    "cum_chu_de": "...",
    "ghi_chu": "...",
    "trang_thai": "Chưa viết"
  }},
  ...
]
TUYỆT ĐỐI KHÔNG VIẾT CHỮ DẪN DẮT NÀO KHÁC NGOÀI KHỐI JSON TRÊN."""

    from modules.ai_engine import goi_chat_completion_an_toan
    resp = goi_chat_completion_an_toan(
        client=client,
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=6000
    )
    raw = resp.choices[0].message.content.strip()
    
    # Bóc tách JSON an toàn
    raw = re.sub(r'^```json\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'^```\s*$', '', raw, flags=re.MULTILINE)
    raw = raw.strip()
    
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
    except Exception:
        # Dự phòng dùng regex bắt khối mảng
        match = re.search(r'\[\s*\{.*\}\s*\]', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    raise ValueError(f"AI không trả về đúng định dạng JSON danh sách bài viết. Phản hồi thô: {raw[:300]}...")


def xuat_csv_ke_hoach_thang(danh_sach_bai):
    """Xuất danh sách bài viết trong kế hoạch tháng ra chuỗi CSV chuẩn UTF-8 BOM cho Excel"""
    output = io.StringIO()
    output.write('\ufeff') # UTF-8 BOM
    writer = csv.writer(output)
    writer.writerow([
        "STT",
        "Tuần",
        "Ngày / Thứ",
        "Cụm Chủ Đề",
        "Tiêu Đề Bài Viết Đề Xuất",
        "Từ Khóa Chính (Focus Keyword)",
        "Từ Khóa Phụ Đi Kèm (Secondary/LSI)",
        "Thể Loại Định Dạng",
        "Mục Đích Tìm Kiếm (Search Intent)",
        "Ghi Chú Chiến Lược",
        "Trạng Thái"
    ])
    for idx, row in enumerate(danh_sach_bai, 1):
        sec_str = ", ".join(row.get("tu_khoa_phu", [])) if isinstance(row.get("tu_khoa_phu"), list) else str(row.get("tu_khoa_phu", ""))
        writer.writerow([
            idx,
            row.get("tuan", ""),
            row.get("thu", ""),
            row.get("cum_chu_de", ""),
            row.get("tieu_de", ""),
            row.get("tu_khoa_chinh", ""),
            sec_str,
            row.get("the_loai", ""),
            row.get("search_intent", ""),
            row.get("ghi_chu", ""),
            row.get("trang_thai", "Chưa viết")
        ])
    return output.getvalue()
