import os
import json
import re
from openai import OpenAI

FILE_QUY_CHUAN_CHUNG = "quy_chuan_seo_chung.json"
FILE_LICH_SU_CHAT = "lich_su_chat_advisor.json"

DEFAULT_QUY_CHUAN = [
    "Giá sản phẩm và thi công phải luôn minh bạch, ghi rõ đã bao gồm thuế VAT 8% hoặc kèm ghi chú rõ ràng về thuế VAT 8%.",
    "Tuyệt đối không nhầm lẫn giữa gỗ nhựa ngoài trời (WPC cốt bột gỗ + hạt nhựa PE/PP, phủ ASA) và tấm ốp nội thất (nhựa PVC nguyên sinh/Nano không chịu được nắng mưa ngoài trời).",
    "Trong các bài viết hướng dẫn thi công sàn gỗ nhựa ngoài trời, bắt buộc nhắc đến khoảng cách hệ khung đà sắt mạ kẽm (chuẩn 30 - 35cm), khe hở giãn nở nhiệt (3 - 5mm) và độ dốc thoát nước tối thiểu 1%.",
    "Khuyến nghị sử dụng keo chuyên dụng HWOOD 3X-BOND khi thi công tấm ốp tường PVC vân đá và tấm Nano, không dùng các loại keo silicone thông thường dễ bong tróc.",
    "Tone giọng bài viết luôn chuyên nghiệp, xưng hô 'HWOOD VIỆT NAM', tôn trọng thợ thầu và đại lý, cam kết bảo hành sản phẩm từ 5 đến 10 năm theo tiêu chuẩn nhà máy.",
    "Mỗi bài viết phải giải quyết triệt để Search Intent của từ khóa (Báo giá thì có bảng giá; So sánh thì có bảng đối đầu ưu/nhược điểm; Kỹ thuật thì có quy trình và checklist nghiệm thu)."
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
