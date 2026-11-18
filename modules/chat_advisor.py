import os
import json
import re
from openai import OpenAI

FILE_QUY_CHUAN_CHUNG = "quy_chuan_seo_chung.json"
FILE_LICH_SU_CHAT = "lich_su_chat_advisor.json"

DEFAULT_QUY_CHUAN = [
    "Thông tin thương hiệu chuẩn: HWOOD VIỆT NAM | Slogan: 'Save Tree, Beautify Home!' | Trụ sở: 148/72 Đường Trường Lưu, P. Long Trường, TP.HCM (tuyệt đối không ghi TP. Thủ Đức). Hotline/Zalo: 0912 565 353 – 0919 741 080 | Zalo OA: https://zalo.me/3061490811747253783 | Email: sales@hwood.vn | Bảo hành: 5 năm (HWOOD) và 1 năm (TENOWOOD). Miễn phí ship <=25km tại TP.HCM cho đơn từ 25 triệu chưa VAT hoặc từ 50 thùng keo. Quà tặng mẫu: 'bộ mẫu sản phẩm'.",
    "Định vị nhà phân phối sỉ: HWOOD chỉ cung ứng vật tư xuất kho, dự toán chỉ tính 100% chi phí vật tư, tách riêng chi phí khung sắt và thợ thi công thành lưu ý tham khảo.",
    "Giá sản phẩm và thi công phải luôn minh bạch, ghi rõ đã bao gồm thuế VAT 8% hoặc kèm ghi chú rõ ràng về thuế VAT 8% theo khổ rộng hiệu dụng.",
    "Tấm Ốp Nội Thất (Nano, PVC Vân Đá, Lam Sóng): Cấu tạo 4 lớp (Lớp UV, Lớp film 5 nhóm vân, Lớp keo Kleiberit Đức, Lớp đế PVC nguyên sinh tổ ong rỗng). Tuổi thọ 10-15 năm (CẤM ghi 20 năm). Nano 5kg mềm (~120-131k/m²) ốp trần/tường; Nano 6kg cứng (~147k/m²) làm vách TV/trần giật cấp. PVC vân đá dán trực tiếp, KHÔNG hèm, CẤM dùng ke inox. Keo 3X-BOND: 1 chai 300ml dán 5-7m². CẤM dùng từ '3D' cho tấm phẳng nano/PVC.",
    "Gỗ Nhựa Ngoài Trời (WPC): Phân biệt 3 dòng: 1 lớp HDPE (đồng chất); 2 lớp phủ ASA (Quatest 3 KT3-00698BXD5 nở nước 0,08%); 2 lớp phủ Polymer 360 độ. HWOOD TUYỆT ĐỐI KHÔNG CÓ SÀN PHỦ ASA (chỉ có sàn 1 lớp HDPE và sàn 2 lớp Polymer).",
    "Thi công sàn ngoài trời: Xương đà khoảng cách 30-35cm (rỗng) hoặc 35-40cm (đặc). BẮT BUỘC ĐI ĐÀ ĐÔI tại điểm nối đối đầu 2 thanh sàn. Khe giãn nở 3-5mm, cách tường 8-15mm. Nền bê tông dốc 1-2% thoát nước.",
    "Hệ Lam & Trụ Pergola: Bắt buộc luồn lõi thép hộp mạ kẽm (trụ 120 luồn 80x80/90x90; trụ 100 luồn 50x50), nắp chụp trên đỉnh, CHÂN TRỤ BẮT BUỘC CHỪA KHE THOÁT NƯỚC TỰ NHIÊN (CẤM BỊT KÍN KEO).",
    "Cửa cổng ngoài trời: Dùng tấm phẳng ASA HW123W16ASA hoặc Polymer HW146CE21. CẤM dùng lam rỗng xếp khít, sàn polymer hay tấm mỏng 12mm.",
    "Keo & Silicone 3X-BOND: Dùng từ 'trám trít' hoặc 'trám khe'. Silicone trung tính X500 (57k, 7 màu), Silicone axit X300 (59k, 3 màu: Trắng trong, Trắng sữa, Xám Xingfa - TUYỆT ĐỐI KHÔNG CÓ MÀU ĐEN; axit ăn mòn kim loại).",
    "Semantic SEO (Koray): 4 câu đầu tiên (<60 từ) Quick Answer (Định nghĩa + Giá VAT 8% + Ứng dụng). 1/3 đầu trang có Bảng tóm tắt giá hoặc Bảng thông số. H2/H3 <300 từ; câu <20 từ; đoạn 3-4 câu. Từ cấm: 'tốt nhất', 'số 1', '100%', 'tuyệt đối', 'vĩnh cửu', 'không mối mọt', 'mưa axit', 'dẻo dai'.",
    "Khối CTA chốt đơn cuối bài: Hotline 0912 565 353 – 0919 741 080 | Nút Zalo OA chuẩn: https://zalo.me/3061490811747253783."
]

def doc_quy_chuan_chung():
    """Đọc bộ quy chuẩn & lưu ý lỗi sai chung của thương hiệu HWOOD"""
    if os.path.exists(FILE_QUY_CHUAN_CHUNG):
        try:
            with open(FILE_QUY_CHUAN_CHUNG, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data
        except Exception:
            pass
    # Nếu chưa có thì khởi tạo mặc định
    luu_quy_chuan_chung(DEFAULT_QUY_CHUAN)
    return DEFAULT_QUY_CHUAN

def luu_quy_chuan_chung(danh_sach_quy_chuan):
    """Lưu danh sách quy chuẩn vào file JSON"""
    try:
        clean_list = [q.strip() for q in danh_sach_quy_chuan if q and q.strip()]
        with open(FILE_QUY_CHUAN_CHUNG, "w", encoding="utf-8") as f:
            json.dump(clean_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def lay_noi_dung_quy_chuan_cho_prompt():
    """Trả về chuỗi text quy chuẩn chung để gắn vào System Prompt mọi bài viết"""
    qc = doc_quy_chuan_chung()
    if not qc:
        return ""
    lines = [f"- {item}" for item in qc]
    return "\n".join(lines)

def doc_lich_su_chat_advisor():
    """Đọc toàn bộ lịch sử tin nhắn trong khung chat chiến lược"""
    if os.path.exists(FILE_LICH_SU_CHAT):
        try:
            with open(FILE_LICH_SU_CHAT, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def luu_lich_su_chat_advisor(messages):
    """Lưu lịch sử chat vào file JSON"""
    try:
        with open(FILE_LICH_SU_CHAT, "w", encoding="utf-8") as f:
            json.dump(messages, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

def xoa_lich_su_chat_advisor():
    """Xóa lịch sử chat để bắt đầu phiên mới"""
    if os.path.exists(FILE_LICH_SU_CHAT):
        try:
            os.remove(FILE_LICH_SU_CHAT)
        except Exception:
            pass

def gui_tin_nhan_advisor(api_key, model, messages, file_context="", kho_tri_thuc=""):
    """Gửi tin nhắn trong cuộc trò chuyện chiến lược SEO HWOOD"""
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    quy_chuan_hien_tai = lay_noi_dung_quy_chuan_cho_prompt()
    
    system_prompt = f"""Bạn là Cố Vấn Chiến Lược SEO Cấp Cao & Giám Đốc Nội Dung của thương hiệu HWOOD VIỆT NAM (https://hwood.vn).
    
VAI TRÒ VÀ NHIỆM VỤ CỦA BẠN TRONG KHUNG CHAT NÀY:
1. Thảo luận, cố vấn chiến lược SEO tổng thể, kế hoạch nội dung, giải pháp kỹ thuật, phân tích đối thủ cạnh tranh và định hướng thương hiệu HWOOD.
2. Tiếp nhận các phản hồi, góp ý về LỖI SAI CHUNG mà các bài viết thường mắc phải từ người dùng.
3. Khi người dùng chỉ ra một lỗi sai hoặc quy định mới (ví dụ: 'Nhớ các bài sàn gỗ phải nhắc khung đà 30cm', 'Giá luôn phải có VAT 8%'), bạn hãy:
   - Tiếp thu sâu sắc và phân tích nguyên nhân / cách khắc phục.
   - Trình bày một hoặc nhiều NGUYÊN TẮC CỐT LÕI được đóng gói súc tích để người dùng có thể bấm 'Lưu vào Quy Chuẩn Hệ Thống'.
4. Tư vấn về cấu trúc bài viết, cách giải quyết Search Intent, cách tối ưu hình ảnh, cách cải thiện tỷ lệ chuyển đổi (CRO) và giữ chân khách hàng.

BỘ NGUYÊN TẮC & QUY CHUẨN CHUNG ĐANG ĐƯỢC TOÀN HỆ THỐNG ÁP DỤNG:
{quy_chuan_hien_tai}

KHO TRI THỨC VẬT LIỆU HWOOD (TRÍCH YẾU):
{kho_tri_thuc[:3500]}
"""
    if file_context:
        system_prompt += f"\n\nTÀI LIỆU / HÌNH ẢNH ĐÍNH KÈM TỪ NGƯỜI DÙNG:\n{file_context}"

    full_messages = [{"role": "system", "content": system_prompt}] + messages
    
    from modules.ai_engine import goi_chat_completion_an_toan
    resp = goi_chat_completion_an_toan(
        client=client,
        model=model,
        messages=full_messages,
        temperature=0.7,
        max_tokens=4000
    )
    return resp.choices[0].message.content.strip()

def ai_trich_xuat_quy_chuan_tu_chat(api_key, model, messages_history):
    """AI phân tích cuộc trò chuyện gần nhất để tự động rút ra các nguyên tắc mới cần thêm vào quy chuẩn chung"""
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    
    history_text = ""
    for m in messages_history[-6:]:
        history_text += f"{m['role'].upper()}: {m['content']}\n\n"
        
    prompt = f"""Dưới đây là đoạn hội thoại trao đổi giữa Trưởng bộ phận SEO HWOOD và Cố vấn AI:
{history_text}

NHIỆM VỤ:
Hãy trích xuất 1 đến 3 NGUYÊN TẮC / LƯU Ý KỸ THUẬT MỚI QUAN TRỌNG NHẤT mà người dùng yêu cầu tuân thủ.
Yêu cầu:
- Mỗi nguyên tắc viết thành 1 câu hoàn chỉnh, ngắn gọn, súc tích (1-2 câu).
- Trọng tâm vào quy định kỹ thuật, giá cả, thương hiệu hoặc cách hành văn.
- Định dạng trả về duy nhất là JSON Array các chuỗi string:
["Nguyên tắc 1...", "Nguyên tắc 2..."]"""

    from modules.ai_engine import goi_chat_completion_an_toan
    resp = goi_chat_completion_an_toan(
        client=client,
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000
    )
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r'^```json\s*', '', raw, flags=re.MULTILINE)
    raw = re.sub(r'^```\s*$', '', raw, flags=re.MULTILINE)
    try:
        data = json.loads(raw.strip())
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []
