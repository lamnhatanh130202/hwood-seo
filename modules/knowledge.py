import os
import glob

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def viet_hoa_tieu_de(s):
    """Viết hoa đầu mỗi từ tiếng Việt mà không bị lỗi dấu"""
    if not s:
        return ""
    return " ".join(w[:1].upper() + w[1:] for w in s.split())

def phan_loai_chu_de(tu_khoa):
    """Tự động phân loại bài viết theo danh mục sản phẩm chính thức của HWOOD"""
    tk = str(tu_khoa).lower()
    if any(w in tk for w in ["bàn", "ghế", "texilene", "polywood", "cafe", "công viên", "combo"]):
        return "🪑 Bàn Ghế Sân Vườn & Ngoài Trời"
    elif any(w in tk for w in ["sàn", "hồ bơi", "vỉ", "lót sàn", "140a25", "145ce21", "138ce23", "wpc"]):
        return "🏊 Sàn Gỗ Nhựa Ngoài Trời & Vỉ"
    elif any(w in tk for w in ["lam sóng", "sóng", "lam 3 sóng", "lam 4 sóng", "lam 5 sóng"]):
        return "🌊 Tấm Ốp Lam Sóng"
    elif any(w in tk for w in ["nano", "trần giật cấp", "ốp nano"]):
        return "🛋️ Tấm Ốp Nano & Trần Giật Cấp"
    elif any(w in tk for w in ["vân đá", "pvc vân đá", "hoa cương", "cẩm thạch"]):
        return "🏛️ Tấm PVC Vân Đá Cẩm Thạch"
    elif any(w in tk for w in ["pergola", "thanh lam", "trụ", "lam hộp", "chắn nắng"]):
        return "☀️ Thanh Lam Hộp & Trụ Pergola"
    elif any(w in tk for w in ["đa năng", "cổng", "hàng rào", "rào"]):
        return "🚪 Thanh Đa Năng & Cổng Rào"
    elif any(w in tk for w in ["tấm ốp ngoài trời", "ốp ngoài trời", "ban công"]):
        return "🏡 Tấm Ốp Gỗ Nhựa Ngoài Trời"
    else:
        return "📂 Chủ Đề Khác"

def lay_tri_thuc_phu_hop(tu_khoa, current_dir=None):
    """Trích lọc và ưu tiên các tài liệu tri thức HWOOD có độ liên quan cao nhất với từ khóa bài viết"""
    base_dir = current_dir or CURRENT_DIR
    md_files = sorted(glob.glob(os.path.join(base_dir, "*.md")))
    if not md_files:
        return ""
    
    kw_clean = str(tu_khoa).lower()
    kw_words = [w for w in kw_clean.split() if len(w) > 2]
    
    scored_files = []
    tong_quan_content = ""
    
    for f in md_files:
        base = os.path.basename(f)
        # Bỏ qua tài liệu quy chuẩn chung và bài viết mẫu để tránh làm phình prompt vô ích
        if any(k in base for k in ['Bai_Viet_Mau', 'Quy_Chuan_Viet_Bai', 'Tong_Quan_Doanh_Nghiep']):
            continue
        try:
            with open(f, "r", encoding="utf-8") as fp:
                c = fp.read()
            score = 0
            base_lower = base.lower()
            c_lower = c.lower()
            for w in kw_words:
                if w in base_lower:
                    score += 15
                score += c_lower.count(w)
            scored_files.append((score, base, c))
        except Exception:
            pass
            
    scored_files.sort(key=lambda x: x[0], reverse=True)
    output_parts = []
    
    # Tài liệu khớp nhất được đưa lên ĐẦU TIÊN và dán nhãn ưu tiên tuyệt đối
    if scored_files and scored_files[0][0] > 0:
        top_score, top_name, top_content = scored_files[0]
        output_parts.append(f"""⭐ TÀI LIỆU KỸ THUẬT CỐT LÕI (BẮT BUỘC ĐỌC KỸ & TUÂN THỦ 100% THÔNG SỐ, MÃ HÀNG, ĐƠN GIÁ):
Tệp: {top_name}
{top_content}""")
        for s, name, content in scored_files[1:3]:
            if s > 0:
                output_parts.append(f"""--- TÀI LIỆU BỔ TRỢ: {name} ---
{content[:2500]}""")
    else:
        for _, name, content in scored_files[:2]:
            output_parts.append(f"--- TÀI LIỆU: {name} ---\n{content[:2500]}\n")
            
    return "\n\n".join(output_parts)

def lay_tri_thuc_tinh_gon(tu_khoa, current_dir=None, max_chars=3200):
    """
    Skill Tiết Kiệm Token (Knowledge Graph RAG):
    Trích lọc ĐÚNG các bảng giá, thông số kỹ thuật (mã hàng, quy cách, kích thước, vật liệu)
    của từ khóa, loại bỏ văn bản dông dài, giúp giảm 50% - 70% token đầu vào.
    """
    base_dir = current_dir or CURRENT_DIR
    md_files = sorted(glob.glob(os.path.join(base_dir, "*.md")))
    if not md_files:
        return ""
    
    kw_clean = str(tu_khoa).lower()
    kw_words = [w for w in kw_clean.split() if len(w) > 2]
    
    scored_files = []
    for f in md_files:
        base = os.path.basename(f)
        if any(k in base for k in ['Bai_Viet_Mau', 'Quy_Chuan_Viet_Bai', 'Tong_Quan_Doanh_Nghiep']):
            continue
        try:
            with open(f, "r", encoding="utf-8") as fp:
                c = fp.read()
            score = 0
            base_lower = base.lower()
            c_lower = c.lower()
            for w in kw_words:
                if w in base_lower:
                    score += 20
                score += c_lower.count(w)
            scored_files.append((score, base, c))
        except Exception:
            pass
            
    scored_files.sort(key=lambda x: x[0], reverse=True)
    if not scored_files or scored_files[0][0] == 0:
        return ""

    top_name, top_content = scored_files[0][1], scored_files[0][2]

    # Trích xuất các bảng Markdown (| ... |) và các đoạn thông số cốt lõi
    extracted_blocks = []
    lines = top_content.splitlines()
    in_table = False
    table_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            in_table = True
            table_lines.append(line)
        else:
            if in_table and table_lines:
                extracted_blocks.append("\n".join(table_lines))
                table_lines = []
                in_table = False
            if any(k in stripped.lower() for k in ["kích thước", "quy cách", "đơn vị", "đơn giá", "vat", "bảo hành", "mã hàng", "cấu tạo", "hdpe", "asa", "polymer", "nano", "lam sóng"]):
                if len(stripped) < 250:
                    extracted_blocks.append(line)

    if in_table and table_lines:
        extracted_blocks.append("\n".join(table_lines))

    condensed_text = "\n".join(extracted_blocks)
    if len(condensed_text) < 500:
        condensed_text = top_content[:max_chars]
    else:
        condensed_text = condensed_text[:max_chars]

    return f"⭐ DỮ LIỆU KỸ THUẬT & BÁO GIÁ CỐT LÕI (Từ: {top_name}):\n{condensed_text}"

def doc_kho_tri_thuc(current_dir=None):
    """Đọc toàn bộ các tài liệu tri thức .md hiện có trong thư mục"""
    base_dir = current_dir or CURRENT_DIR
    md_files = sorted(glob.glob(os.path.join(base_dir, "*.md")))
    noi_dung_tong_hop = ""
    danh_sach_file = []

    for file_path in md_files:
        ten_file = os.path.basename(file_path)
        danh_sach_file.append(ten_file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                noi_dung = f.read()
                noi_dung_tong_hop += f"\n\n=== TÀI LIỆU: {ten_file} ===\n{noi_dung}\n"
        except Exception:
            pass

    return noi_dung_tong_hop.strip(), len(danh_sach_file), danh_sach_file
