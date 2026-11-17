import re
from openai import OpenAI
from modules.knowledge import lay_tri_thuc_phu_hop, lay_tri_thuc_tinh_gon
from modules.chat_advisor import lay_noi_dung_quy_chuan_cho_prompt

def goi_chat_completion_an_toan(client, model, **kwargs):
    """
    Gọi chat completion với cơ chế tương thích thông minh:
    - Mặc định ưu tiên model deepseek-chat (DeepSeek-V3 - bản rẻ và tối ưu nhất hiện nay).
    - Tự động chuyển deepseek-flash sang deepseek-chat trực tiếp, tránh mất 1 lượt request lỗi timeout.
    """
    target_model = model or "deepseek-chat"
    if target_model == "deepseek-flash":
        target_model = "deepseek-chat"
    try:
        return client.chat.completions.create(model=target_model, **kwargs)
    except Exception as e:
        err_msg = str(e).lower()
        if ("not found" in err_msg or "does not exist" in err_msg or "model" in err_msg or "invalid" in err_msg) and target_model != "deepseek-chat":
            return client.chat.completions.create(model="deepseek-chat", **kwargs)
        raise e

def goi_ai_tao_va_noi_bai(client, model, messages, max_tokens=8192, max_loops=1):
    """Gọi AI sinh bài viết với cơ chế TỰ ĐỘNG NỐI TIẾP LIỀN MẠCH (Auto-Continuation) nếu chạm trần token"""
    cur_messages = [dict(m) for m in messages]
    full_output = ""
    
    for loop_idx in range(max_loops + 1):
        resp = goi_chat_completion_an_toan(
            client=client,
            model=model,
            messages=cur_messages,
            max_tokens=max_tokens,
            temperature=0.7,
            stream=False
        )
        choice = resp.choices[0]
        content = choice.message.content.strip()
        
        # Làm sạch markdown blocks nếu có
        clean_content = content
        if clean_content.startswith("```"):
            lines = clean_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            clean_content = "\n".join(lines).strip()
            
        if not full_output:
            full_output = clean_content
        else:
            full_output = full_output + "\n" + clean_content
            
        # Kiểm tra nếu bài viết đã hoàn thiện khối liên hệ cuối bài thì dừng ngay, không chạy thêm vòng lặp
        if "0912 565 353" in full_output and ("zalo.me/0912565353" in full_output or "sales@hwood.vn" in full_output or "hwood.vn" in full_output):
            break

        # Nếu AI dừng vì hết token (finish_reason == 'length') và chưa hết số vòng cho phép
        if choice.finish_reason == "length" and loop_idx < max_loops:
            cur_messages.append({"role": "assistant", "content": clean_content})
            cur_messages.append({
                "role": "user",
                "content": "Bài viết trên của bạn vừa bị ngắt giữa chừng do chạm giới hạn độ dài token. Hãy VIẾT TIẾP LIỀN MẠCH từ đúng câu/thẻ HTML cuối cùng ở trên đến hết bài. BẮT BUỘC giữ nguyên cấu trúc HTML và viết tiếp cho đến hết khối liên hệ hotline HWOOD 0912 565 353 cuối bài!"
            })
        else:
            break
            
    from modules.file_handler import chuan_hoa_bang_html_hwood
    full_output = chuan_hoa_bang_html_hwood(full_output)
    return full_output


def viet_tiep_bai_dang_do(noi_dung_dang_do, tu_khoa_bai, api_key, model_name):
    """Viết tiếp một bài viết bất kỳ đang bị dừng giữa chừng và nối liền mạch lại với nhau"""
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=90.0)
    
    doan_cuoi = noi_dung_dang_do[-1500:] if len(noi_dung_dang_do) > 1500 else noi_dung_dang_do
    tri_thuc_lien_quan = lay_tri_thuc_phu_hop(tu_khoa_bai)
    
    prompt_tiep = f"""Bạn là Chuyên gia Biên tập Nội dung cao cấp của HWOOD VIỆT NAM.
Dưới đây là đoạn kết thúc của bài viết HTML về từ khóa "{tu_khoa_bai}" đang viết thì BỊ DỪNG GIỮA CHỪNG:

--- ĐOẠN CUỐI CỦA BÀI VIẾT HIỆN TẠI (ĐANG DANG DỞ) ---
{doan_cuoi}
--- HẾT ĐOẠN CUỐI ---

TÀI LIỆU CHÍNH HÃNG HWOOD:
{tri_thuc_lien_quan}

NHIỆM VỤ CỦA BẠN:
1. Hãy VIẾT TIẾP LIỀN MẠCH từ đúng điểm dừng cuối cùng của đoạn văn/thẻ HTML ở trên.
2. TUYỆT ĐỐI KHÔNG lặp lại những gì đã viết ở trên.
3. Hoàn thiện toàn bộ các phần còn thiếu: các mục heading tiếp theo, bảng báo giá (nếu chưa có), câu hỏi thường gặp FAQ, và BẮT BUỘC kết thúc bằng Khung Liên hệ & Hotline 0912 565 353 của HWOOD VIỆT NAM.
4. Trả về trực tiếp mã HTML viết tiếp (không bọc trong ```html)."""

    cont_text = goi_ai_tao_va_noi_bai(
        client=client,
        model=model_name,
        messages=[{"role": "user", "content": prompt_tiep}],
        max_tokens=8192
    )
    return noi_dung_dang_do.rstrip() + "\n\n" + cont_text.lstrip()


def kiem_tra_gop_y_toan_dien(yeu_cau_text):
    """Tự động phát hiện xem góp ý là danh sách nhiều lỗi (Audit checklist) cần sửa toàn diện bài viết không"""
    if not yeu_cau_text:
        return False
    txt = yeu_cau_text.lower()
    # Các từ khóa nhận diện danh sách audit nhiều lỗi
    if any(k in txt for k in ["lỗi 1", "lỗi 2", "12 lỗi", "các lỗi", "toàn bộ lỗi", "mục lục", "xóa bỏ hoàn toàn", "cần sửa ngay", "bản thảo này đang mắc"]):
        return True
    lines = [l.strip() for l in yeu_cau_text.splitlines() if l.strip()]
    numbered_items = len([l for l in lines if re.match(r'^(?:lỗi\s*\d+|\d+[\.\)\-]|[-*•])', l, re.IGNORECASE)])
    if numbered_items >= 3 or len(yeu_cau_text) > 350:
        return True
    return False


def parse_and_apply_patch(original_html, ai_response):
    """Bóc tách các khối thay thế <<<THAY_THE>>> để sửa cục bộ với cơ chế so khớp thông minh không phân biệt khoảng trắng"""
    blocks = re.findall(r'<<<THAY_THE>>>(.*?)<<<HET_THAY_THE>>>', ai_response, re.DOTALL)
    if blocks:
        patched = original_html
        applied_count = 0
        for b in blocks:
            cu_m = re.search(r'<<<DOAN_CU>>>(.*?)<<<HET_DOAN_CU>>>', b, re.DOTALL)
            moi_m = re.search(r'<<<DOAN_MOI>>>(.*?)<<<HET_DOAN_MOI>>>', b, re.DOTALL)
            if cu_m and moi_m:
                cu = cu_m.group(1).strip()
                moi = moi_m.group(1).strip()
                if cu in patched:
                    patched = patched.replace(cu, moi, 1)
                    applied_count += 1
                else:
                    # So khớp mềm dẻo (bỏ qua khác biệt về khoảng trắng / xuống dòng)
                    cu_words = [re.escape(w) for w in cu.split()]
                    if cu_words:
                        cu_pattern = r'\s+'.join(cu_words)
                        try:
                            patched_new, count = re.subn(cu_pattern, moi.replace('\\', r'\\'), patched, count=1)
                            if count > 0:
                                patched = patched_new
                                applied_count += 1
                        except Exception:
                            pass
        if applied_count > 0:
            return patched, True, f"🎉 Đã sửa thành công {applied_count}/{len(blocks)} vị trí! Toàn bộ các phần còn lại được bảo toàn nguyên vẹn 100%."
    
    # Nếu AI không dùng cấu trúc <<<THAY_THE>>> mà trả về bài hoàn chỉnh
    clean = ai_response.strip()

    # 1. Bóc tách ruột khối mã nếu AI bọc trong markdown ```html ... ``` hoặc ``` ... ```
    code_match = re.search(r'```(?:html)?\s*([\s\S]*?)\s*```', clean, re.IGNORECASE)
    if code_match:
        extracted = code_match.group(1).strip()
        if len(extracted) > 200:
            clean = extracted

    # 2. Loại bỏ các đoạn văn mở đầu trò chuyện (trước thẻ HTML đầu tiên)
    first_tag = re.search(r'<(?:h2|div|p|table|ul|ol|header|section)\b', clean, re.IGNORECASE)
    if first_tag and first_tag.start() > 0:
        prefix = clean[:first_tag.start()]
        if not re.search(r'<(?:h2|div|p|table|ul|ol)', prefix, re.IGNORECASE):
            clean = clean[first_tag.start():].strip()

    # 3. Loại bỏ các lời thoại / kết bài / tóm tắt sau thẻ HTML kết thúc cuối cùng
    last_tags = [m.end() for m in re.finditer(r'</(?:div|script|p|table|section|article|footer|ul|ol|h2|h3)>', clean, re.IGNORECASE)]
    if last_tags:
        last_end = max(last_tags)
        suffix = clean[last_end:].strip()
        if suffix and not re.search(r'<(?:div|p|table|script)', suffix, re.IGNORECASE):
            clean = clean[:last_end].strip()

    # 4. Loại bỏ các dòng markdown ``` còn sót
    clean = re.sub(r'^```(?:html)?\s*', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s*```$', '', clean)

    if len(clean) < len(original_html) * 0.35 and len(original_html) > 800:
        return original_html, False, "⚠️ AI chỉ trả về một đoạn ngắn thay vì cả bài. Hệ thống đã giữ nguyên bài viết gốc để tránh làm mất nội dung!"
        
    return clean, True, "🎉 Đã cập nhật bài viết thành công!"


def thuc_hien_tinh_chinh_ai(noi_dung_cu, yeu_cau_text, file_text, tu_khoa_bai, api_key, model_name, img_b64=None, che_do_sua="tu_dong"):
    """
    Gọi AI tinh chỉnh bài viết theo cơ chế thông minh:
    1. Nếu góp ý là danh sách kiểm tra nhiều lỗi (Audit checklist) -> Tự động sửa toàn diện 100% từng lỗi một
    2. Nếu góp ý là 1-2 vị trí cụ thể -> Sửa cục bộ bảo toàn 100% các phần còn lại
    """
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=90.0)
    tri_thuc_lien_quan = lay_tri_thuc_phu_hop(tu_khoa_bai)
    quy_chuan_toan_he_thong = lay_noi_dung_quy_chuan_cho_prompt()

    # Nhận diện xem có phải danh sách nhiều lỗi không
    is_multi_error = kiem_tra_gop_y_toan_dien(yeu_cau_text)

    # Nếu người dùng chọn viết lại toàn bài, HOẶC góp ý chứa danh sách nhiều lỗi
    if che_do_sua == "toan_bai" or is_multi_error or che_do_sua == "tu_dong":
        prompt_toan_dien = f"""Bạn là Giám đốc Kiểm duyệt Nội dung & Trưởng ban Kỹ thuật Vật liệu của HWOOD VIỆT NAM (hwood.vn).
Nhiệm vụ tối cao của bạn: Tiếp thu 100% GÓP Ý CỦA NGƯỜI DÙNG để sửa chữa, hoàn thiện bài viết đạt chuẩn kỹ thuật tuyệt đối, KHÔNG BỊA ĐẶT THÔNG SỐ.

BẢNG QUY CHUẨN THÔNG SỐ VÀNG HWOOD (BẮT BUỘC ĐỐI CHIẾU CHUẨN XÁC KHI SỬA):
1. Tấm Nano & Lam sóng nội thất:
   - Cấu tạo 4 lớp: Lớp UV chống trầy, Lớp màng film 5 nhóm hoa văn (vân gỗ, vân bê tông, vân giả đá, vân vải, đơn sắc), Lớp keo Kleiberit nhập khẩu Đức, Cốt hạt nhựa PVC nguyên sinh cấu trúc rỗng tổ ong.
   - Kích thước chuẩn: Rộng 400mm × Dày 9mm × Dài 3000mm.
   - Đơn giá vật tư: HWOOD cốt cứng (6,0 kg/tấm) = 147.000 đ/m² (176.400 đ/tấm); TENOWOOD cốt mềm (5,0 kg/tấm) = 120.000 đ/m² (144.000 đ/tấm).
   - Tuyệt đối KHÔNG dùng từ "3D" cho tấm Nano phẳng. Thi công tường ẩm bắt buộc dùng khung xương sắt hộp mạ kẽm cách ẩm.
2. Gỗ nhựa ngoài trời WPC (Phân biệt rõ 3 dòng):
   - 1 lớp HDPE: 60% bột gỗ + 30% HDPE + 10% phụ gia (đồng chất).
   - 2 lớp phủ ASA: 60% HDPE + 20% bột gỗ + 10% phụ gia + 10% lớp phủ ASA toàn bề mặt (nhựa kỹ thuật dùng làm vỏ xe ô tô, Quatest 3 mã KT3-00698BXD5 ngày 28/05/2025 độ trương nở ngâm nước siêu thấp 0,08%). Mã tiêu biểu tấm ốp phẳng ASA vân 3D sâu HW123W16ASA (100×16×2900mm, 2,13 kg/thanh, 77.220 đ/md = 223.938 đ/thanh đã VAT 8%).
   - 2 lớp phủ Polymer: 60% hạt nhựa HDPE + 20% bột gỗ + 10% phụ gia + 10% lớp phủ Polymer (HW146CE21 120.431 đ/md).
3. Thi công cửa cổng ngoài trời:
   - BẮT BUỘC chỉ dùng tấm phẳng dày: HW123W16ASA hoặc Polymer HW146CE21 bắt vít inox 304 vào khung sắt hộp mạ kẽm.
   - TUYỆT ĐỐI CẤM dùng lam sóng, thanh lam hộp rỗng hay tấm mỏng làm cánh cổng.
4. Thanh lam hộp & Trụ ngoài trời:
   - BẮT BUỘC luồn lõi thép hộp mạ kẽm bên trong; đầu trên chụp nắp, chân trụ và điểm tiếp giáp phải chừa khe thoát nước tự nhiên (TUYỆT ĐỐI CẤM bịt kín keo).
5. Bàn ghế ngoài trời Polywood:
   - Nan nhựa composite cao cấp PS/HDPE chịu lực ngoài trời, HOÀN TOÀN KHÔNG CHỨA BỘT GỖ. Khung nhôm sơn tĩnh điện. Đóng module nguyên kiện đã kèm đủ ốc vít. Ghế công viên chuẩn: HW-GB03 (có tựa) và HW-GB04 (không tựa).
6. Keo & Phụ kiện chính hãng:
   - Keo đa năng ngoại thất 3X-BOND (38.340 đ/chai), Silicone X500 (47.520 đ/chai), Chốt Inox 430 HW-P10ASA (1.026 đ/cái), Ke Inox 304 bắt tấm Nano (2.000 đ/cái).
7. Thông tin thương hiệu & Chính sách:
   - Tên chuẩn: HWOOD VIỆT NAM | Slogan: "Save Tree, Beautify Home!"
   - Địa chỉ duy nhất: 148/72 Đường Trường Lưu, Phường Long Trường, Thành Phố Hồ Chí Minh (tuyệt đối không ghi TP. Thủ Đức).
   - Hotline/Zalo: 0912 565 353 | Hotline phụ: 0919 741 080 | Zalo OA: https://zalo.me/0912565353
   - Vận chuyển: Miễn phí vận chuyển bán kính ≤ 25km tại TP.HCM cho đơn từ 25 triệu chưa VAT. Hỗ trợ gửi "bộ mẫu sản phẩm" miễn phí toàn quốc.
   - Bảo hành: 5 năm cho dòng HWOOD và 1 năm cho dòng TENOWOOD.

TÀI LIỆU KỸ THUẬT CHUYÊN SÂU:
{tri_thuc_lien_quan}

📄 BÀI VIẾT HIỆN TẠI (Đang cần sửa chữa):
--- BẮT ĐẦU BÀI VIẾT HIỆN TẠI ---
{noi_dung_cu}
--- KẾT THÚC BÀI VIẾT HIỆN TẠI ---

🔥 YÊU CẦU GÓP Ý TỪ NGƯỜI DÙNG (BẮT BUỘC SỬA ĐÚNG 100%, ĐẶC BIỆT LÀ THÔNG SỐ KỸ THUẬT):
"{yeu_cau_text if yeu_cau_text.strip() else 'Sửa toàn bộ bài viết theo tài liệu đính kèm bên dưới'}"

{file_text}

Từ khóa chính: "{tu_khoa_bai}"

NHIỆM VỤ SỬA BÀI CỦA BẠN:
1. TIẾP THU VÀ SỬA 100% CÁC Ý GÓP Ý CỦA NGƯỜI DÙNG:
   - Đọc kỹ từng câu, từng ý và từng con số trong góp ý của người dùng để sửa chính xác vào bài viết.
   - Sửa triệt để các thông số kỹ thuật sai: Kích thước, cấu tạo, dòng sản phẩm, đơn giá, phụ kiện thi công phải khớp đúng theo BẢNG QUY CHUẨN THÔNG SỐ VÀNG HWOOD ở trên.
2. BẢO TỒN NGUYÊN VẸN CÁC PHẦN ĐÃ ĐÚNG:
   - Toàn bộ các đoạn văn, tiêu đề H2/H3, khối Quick Answer, FAQ Schema và các bảng số liệu đã đúng phải được giữ nguyên vẹn, không viết lại tùy tiện làm xáo trộn bài.
3. BẢNG BIỂU DỮ LIỆU:
   - Mọi bảng so sánh và bảng báo giá BẮT BUỘC phải có đầy đủ ruột số liệu (hàng <tr> và cột <td>). TUYỆT ĐỐI CẤM để trống bảng!
   - Không cần tự viết inline style dài dòng trong <td>, hệ thống Python sẽ tự động phủ màu xanh #2e7d32.
4. BỎ HOÀN TOÀN GỢI Ý VỊ TRÍ ẢNH:
   - TUYỆT ĐỐI KHÔNG sinh bất kỳ khối gợi ý vị trí chèn ảnh hoặc placeholder hình ảnh nào để tiết kiệm tối đa token out.
5. ĐỊNH DẠNG ĐẦU RA SẠCH 100%:
   - BẮT BUỘC trả về toàn bộ mã HTML bài viết hoàn chỉnh (bắt đầu từ thẻ <h2> mục lục đến hết thẻ </div> hotline cuối bài).
   - TUYỆT ĐỐI KHÔNG viết lời chào mở đầu ("Dưới đây là..."), TUYỆT ĐỐI KHÔNG viết bản tổng kết/tóm tắt ở cuối bài!"""

        raw_response = goi_ai_tao_va_noi_bai(
            client=client,
            model=model_name,
            messages=[{"role": "user", "content": prompt_toan_dien}],
            max_tokens=8192
        )
        full_html, is_patched, msg = parse_and_apply_patch(noi_dung_cu, raw_response)
        from modules.media_planner import xoa_hop_placeholder_anh
        from modules.file_handler import chuan_hoa_bang_html_hwood
        full_html = xoa_hop_placeholder_anh(full_html)
        full_html = chuan_hoa_bang_html_hwood(full_html)
        return full_html, True, "🎉 Đã tiếp thu 100% góp ý và cập nhật chuẩn xác thông số kỹ thuật HWOOD vào bài viết!"

    else:
        # Chế độ sửa cục bộ cho 1-2 vị trí đơn lẻ
        prompt_chinh_sua = f"""Bạn là Chuyên gia Biên tập Kỹ thuật của HWOOD VIỆT NAM (hwood.vn).
Nhiệm vụ: Sửa đúng vị trí người dùng yêu cầu, bảo đảm thông số kỹ thuật chính xác 100%.

BẢNG QUY CHUẨN THÔNG SỐ VÀNG HWOOD:
- Tấm Nano phẳng: Rộng 400mm × Dày 9mm × Dài 3000mm. HWOOD cốt cứng 6kg = 147.000 đ/m², TENOWOOD cốt mềm 5kg = 120.000 đ/m². Keo Kleiberit Đức, cốt PVC nguyên sinh rỗng tổ ong.
- Gỗ nhựa ngoài trời: 1 lớp HDPE (60% gỗ + 30% HDPE), 2 lớp ASA (HW123W16ASA 100×16×2900mm 77.220 đ/md Quatest 3 trương nở 0.08%), 2 lớp Polymer (HW146CE21 120.431 đ/md).
- Cổng ngoài trời: Chỉ dùng HW123W16ASA hoặc HW146CE21, cấm dùng lam sóng/lam hộp.
- Lam hộp & trụ: Bắt buộc luồn lõi thép mạ kẽm, chừa khe thoát nước tự nhiên.
- Keo & phụ kiện: 3X-BOND 38.340 đ, Silicone X500 47.520 đ, Chốt HW-P10ASA 1.026 đ, Ke Inox 304 bắt tấm Nano 2.000 đ.
- Hotline: 0912 565 353 | Trụ sở: 148/72 Đường Trường Lưu, Phường Long Trường, TP.HCM | Bảo hành 5 năm (HWOOD), 1 năm (TENOWOOD).

BÀI VIẾT HIỆN TẠI (MÃ HTML ĐẦY ĐỦ):
--- BẮT ĐẦU BÀI VIẾT HIỆN TẠI ---
{noi_dung_cu}
--- KẾT THÚC BÀI VIẾT HIỆN TẠI ---

Từ khóa chính: "{tu_khoa_bai}"

🔥 YÊU CẦU SỬA TỪ NGƯỜI DÙNG:
"{yeu_cau_text if yeu_cau_text.strip() else 'Xử lý theo tài liệu đính kèm bên dưới'}"

{file_text}

QUY TẮC BẮT BUỘC:
Người dùng chỉ muốn sửa hoặc bổ sung vào 1 hoặc 2 vị trí cụ thể. Hãy trả về theo ĐÚNG cú pháp sau để hệ thống tự động tìm và thay thế đúng vị trí đó:

<<<THAY_THE>>>
<<<DOAN_CU>>>
[Trích dẫn chính xác đoạn mã HTML cũ trong bài viết hiện tại cần thay thế]
<<<HET_DOAN_CU>>>
<<<DOAN_MOI>>>
[Đoạn mã HTML mới đã được sửa chính xác thông số kỹ thuật theo yêu cầu]
<<<HET_DOAN_MOI>>>
<<<HET_THAY_THE>>>

LƯU Ý QUAN TRỌNG:
- Đoạn trong <<<DOAN_CU>>> phải sao chép chính xác từ bài viết hiện tại để hệ thống tìm thấy và thay thế.
- TUYỆT ĐỐI KHÔNG viết lan man ra ngoài cấu trúc <<<THAY_THE>>>."""

        resp_raw = goi_chat_completion_an_toan(
            client=client,
            model=model_name,
            messages=[{"role": "user", "content": prompt_chinh_sua}],
            max_tokens=8192,
            temperature=0.3,
            stream=False
        )
        ai_resp_text = resp_raw.choices[0].message.content.strip()
        patched_html, ok, msg = parse_and_apply_patch(noi_dung_cu, ai_resp_text)
        from modules.file_handler import chuan_hoa_bang_html_hwood
        patched_html = chuan_hoa_bang_html_hwood(patched_html)
        return patched_html, ok, msg


def tao_bai_viet_hwood_chuan_seo(
    tu_khoa, 
    the_loai_bai="🤖 Tự động nhận diện theo từ khóa (Mặc định)", 
    do_dai_bai="Tiêu chuẩn SEO (1.300 - 1.600 từ)", 
    api_key="", 
    chon_model="deepseek-flash", 
    danh_sach_bai_viet_wp=None,
    tieu_de="",
    tu_khoa_phu=None,
    ghi_chu_chien_luoc="",
    search_intent="",
    cum_chu_de="",
    toi_uu_token=True
):
    """
    Hàm tạo bài viết SEO chuẩn toàn diện của HWOOD VIỆT NAM:
    - Tích hợp Skill Tiết Kiệm Token (Knowledge Graph Prompt Optimizer): Giảm 50% - 70% token đầu vào
    - Vận hành qua Hội đồng 5 Bot phản biện độc lập
    - Tuân thủ nghiêm ngặt 3 Phần Quy Chuẩn (Kỹ thuật/Thương hiệu, Yoast SEO/GEO, Giao diện HTML #2e7d32)
    - Tự động nối tiếp nếu bài dài (Auto-Continuation)
    - Chuẩn hóa bảng HTML HWOOD (#2e7d32, chữ trắng, viền #cccccc, cột đầu tiên #1a2e22 bold, ĐIỀN ĐỦ RUỘT)
    - Tự động tạo Meta Title & Meta Description đạt chuẩn Yoast SEO
    - Tự động lưu vào lịch sử bài viết
    """
    if not api_key:
        raise ValueError("Thiếu API Key để tạo bài viết!")
    if not tu_khoa or not tu_khoa.strip():
        raise ValueError("Thiếu từ khóa SEO!")
        
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com", timeout=90.0)
    clean_kw = tu_khoa.strip()

    internal_links_context = ""
    if danh_sach_bai_viet_wp:
        internal_links_context = (
            "\nDANH SÁCH BÀI VIẾT THỰC TẾ TRÊN WEBSITE HWOOD "
            "(CHỌN 1-2 BÀI LIÊN QUAN ĐỂ CHÈN INTERNAL LINK CHUẨN: "
            "'Xem chi tiết quy cách & báo giá tại → <a href=\"...\">[Tên sản phẩm]</a>'):\n"
        )
        # Nếu bật tối ưu token: chỉ lấy 4 bài liên quan nhất thay vì 8
        limit_links = 4 if toi_uu_token else 8
        filtered_links = []
        kw_lower = clean_kw.lower()
        for bv in danh_sach_bai_viet_wp:
            t = bv.get("title", {}).get("rendered", "")
            l = bv.get("link", "")
            score = sum(1 for w in kw_lower.split() if w in t.lower())
            filtered_links.append((score, t, l))
        filtered_links.sort(key=lambda x: x[0], reverse=True)
        for _, t, l in filtered_links[:limit_links]:
            internal_links_context += f"- {t}: {l}\n"

    # Trích xuất tri thức chuyên sâu (ưu tiên tri thức tinh gọn nếu bật tối ưu token)
    if toi_uu_token:
        tri_thuc_chuyen_sau = lay_tri_thuc_tinh_gon(clean_kw)
        if not tri_thuc_chuyen_sau:
            tri_thuc_chuyen_sau = lay_tri_thuc_phu_hop(clean_kw)
    else:
        tri_thuc_chuyen_sau = lay_tri_thuc_phu_hop(clean_kw)

    quy_chuan_toan_he_thong = lay_noi_dung_quy_chuan_cho_prompt()

    context_ke_hoach = ""
    if tieu_de:
        context_ke_hoach += f"\n🎯 TIÊU ĐỀ CHIẾN LƯỢC BẮT BUỘC BÁM SÁT: {tieu_de}\n"
    if tu_khoa_phu and isinstance(tu_khoa_phu, list) and len(tu_khoa_phu) > 0:
        context_ke_hoach += f"🎯 BỘ TỪ KHÓA PHỤ LSI (BẮT BUỘC LỒNG GHÉP TỰ NHIÊN VÀO BÀI): {', '.join(tu_khoa_phu)}\n"
    if ghi_chu_chien_luoc:
        context_ke_hoach += (
            f"🎯 ĐỊNH HƯỚNG NỘI DUNG & YÊU CẦU CHIẾN LƯỢC TỪ KẾ HOẠCH NỘI DUNG:\n"
            f"{ghi_chu_chien_luoc}\n"
            f"👉 YÊU CẦU BẮT BUỘC: Bạn phải triển khai đúng 100% các ý định, cấu trúc, số lượng chủng loại/mẫu hoặc case study được yêu cầu trong ghi chú trên! Tuyệt đối không viết lan man đi chệch khỏi định hướng chiến lược này!\n"
        )
    if search_intent:
        context_ke_hoach += f"🎯 Ý ĐỊNH TÌM KIẾM CỦA KHÁCH HÀNG (SEARCH INTENT): {search_intent}\n"
    if cum_chu_de:
        context_ke_hoach += f"🎯 CỤM CHỦ ĐỀ (TOPIC CLUSTER): {cum_chu_de}\n"

    if toi_uu_token:
        # SYSTEM PROMPT TINH GỌN (Giảm ~70% Token nhưng giữ trọn 100% quy chuẩn HWOOD):
        system_prompt = f"""Bạn là Chuyên gia Content SEO & Kỹ thuật Vật liệu HWOOD VIỆT NAM (https://hwood.vn).
Viết bài SEO qua Hội đồng 5 Bot phản biện độc lập (Vật liệu, Thi công, Giá, SEO/GEO, CRO), tuân thủ nghiêm ngặt:

{tri_thuc_chuyen_sau if tri_thuc_chuyen_sau else "Tuân thủ tài liệu kỹ thuật chính hãng HWOOD."}

{context_ke_hoach}
{internal_links_context}

QUY CHUẨN KỸ THUẬT & DỮ LIỆU CỐT LÕI HWOOD (BẮT BUỘC):
1. Thương hiệu: HWOOD VIỆT NAM ("Save Tree, Beautify Home!"). Trụ sở: 148/72 Đường Trường Lưu, P. Long Trường, TP.HCM. Hotline/Zalo: 0912 565 353 - 0919 741 080. Bảo hành 5 năm (dòng HWOOD), 1 năm (dòng TENOWOOD). Miễn phí vận chuyển ≤25km tại TP.HCM cho đơn từ 25 triệu chưa VAT. Gửi mẫu miễn phí toàn quốc.
2. Cấu tạo & Thông số kỹ thuật:
   - Tấm Nano & Lam sóng nội thất: 4 lớp (Lớp UV, Lớp film 5 nhóm vân, Lớp keo Kleiberit Đức, Lớp đế PVC nguyên sinh tổ ong rỗng). Tuyệt đối CẤM dùng từ '3D' cho tấm Nano/PVC/lam sóng; chỉ dùng 'tạo điểm nhấn sang trọng'. Trần: 'hệ khung xương sắt hộp mạ kẽm định hình các tầng cao độ'.
   - Gỗ nhựa ngoài trời: Phân biệt rõ 3 dòng:
     * Dòng 1 lớp HDPE: 60% bột gỗ + 30% HDPE + 10% phụ gia (đồng chất).
     * Dòng 2 lớp phủ ASA: 60% HDPE + 20% bột gỗ + 10% phụ gia + 10% lớp phủ ASA toàn bề mặt (Quatest 3 KT3-00698BXD5 trương nở nước siêu thấp 0,08%).
     * Dòng 2 lớp phủ Polymer: 60% hạt nhựa HDPE + 20% bột gỗ + 10% phụ gia + 10% lớp phủ bề mặt Polymer.
   - Thi công ngoài trời: Lam hộp & trụ bắt buộc luồn lõi thép hộp mạ kẽm bên trong, nắp chụp đầu trên, chân trụ chừa khe thoát nước tự nhiên (CẤM bịt kín keo). Cổng ngoài trời: Dùng tấm phẳng ASA HW123W16ASA hoặc Polymer HW146CE21. CẤM dùng lam rỗng hay tấm mỏng 12mm làm cổng.
   - Phụ kiện chuẩn: Keo đa năng 3X-BOND, Silicone X500, Chốt Inox 430 HW-P10ASA, Nẹp góc V phủ ASA HW45G35ASA. Nan bàn ghế Polywood hoàn toàn KHÔNG bột gỗ, không dùng keo 3X-BOND cho bàn ghế.
   - Giá: Đã gồm VAT 8%, tính theo khổ rộng hiệu dụng.

QUY CHUẨN SEO ON-PAGE & ĐỊNH DẠNG HTML:
1. Meta data: Meta Title ≤60 ký tự, Meta Description 140-155 ký tự.
2. Khối Quick Answer: Ngay đầu bài có khối trả lời nhanh (<60 từ) tóm tắt quy cách/giá để AI Search trích dẫn.
3. Thẻ Tiêu đề: KHÔNG dùng <h1>. Thẻ <h2>: màu xanh lá đậm #2e7d32, in đậm, kẻ viền dưới 2px solid #2e7d32. Thẻ <h3>: màu xanh #2e7d32.
4. Bảng HTML (BẮT BUỘC ĐIỀN ĐỦ RUỘT & BÁO GIÁ): Dùng <table>, <thead>, <tbody>, <tr>, <th>, <td> đầy đủ hàng/cột với số liệu thực tế có VAT 8%. CẤM để trống ruột bảng!
5. Cuối bài: 3-5 câu FAQ ngắn (<50 từ) kèm JSON-LD Schema FAQPage + Khối CTA HWOOD Hotline/Zalo 0912 565 353.
6. TIẾT KIỆM TOKEN: TUYỆT ĐỐI KHÔNG sinh bất kỳ gợi ý ảnh, placeholder hay figure/img giả lập. Chỉ xuất mã HTML sạch, không viết lời thoại mở đầu hay kết thúc.

THÔNG TIN BÀI VIẾT:
- Từ khóa chính: "{clean_kw}"
- Định dạng: {the_loai_bai}
- Yêu cầu độ dài: {do_dai_bai}
"""
    else:
        system_prompt = f"""Bạn là chuyên gia Content SEO & Kỹ thuật Vật liệu của HWOOD VIỆT NAM (https://hwood.vn).
Khi viết bài mới hoặc biên tập lại bài cũ, bạn BẮT BUỘC vận hành qua Hội đồng 5 Bot phản biện độc lập (Kỹ thuật vật liệu – Thi công cơ học – Giá & Kinh doanh – SEO On-Page/GEO – Biên tập & CRO) và xuất bản nội dung theo đúng quy chuẩn kỹ thuật & giao diện website dưới đây:

BỘ QUY CHUẨN & LỖI SAI CHUNG BẮT BUỘC TUÂN THỦ (TOÀN HỆ THỐNG):
{quy_chuan_toan_he_thong if quy_chuan_toan_he_thong else "Tuân thủ tiêu chuẩn chất lượng cao nhất của HWOOD VIỆT NAM."}

BỘ NÃO TRI THỨC VÀ TÀI LIỆU CHÍNH THỨC CỦA HWOOD VIỆT NAM CHO TỪ KHÓA NÀY:
{tri_thuc_chuyen_sau if tri_thuc_chuyen_sau else "Tuân thủ tài liệu kỹ thuật chính hãng HWOOD."}

{context_ke_hoach}

{internal_links_context}

I. QUY CHUẨN KỸ THUẬT & DỮ LIỆU HWOOD (BẮT BUỘC TUÂN THỦ):
1. Thông tin thương hiệu & Liên hệ:
   - Tên chuẩn: HWOOD VIỆT NAM | Slogan: "Save Tree, Beautify Home!"
   - Địa chỉ duy nhất: 148/72 Đường Trường Lưu, Phường Long Trường, Thành Phố Hồ Chí Minh (tuyệt đối không ghi TP. Thủ Đức).
   - Hotline/Zalo: 0912 565 353 | Hotline phụ: 0919 741 080 | Link Zalo: https://zalo.me/0912565353
   - Email: sales@hwood.vn | Web: hwood.vn
   - Quy mô & Uy tín: >12 năm kinh nghiệm, tổng kho sức chứa 500 container.
   - Thời hạn bảo hành: Bảo hành 5 năm (dòng HWOOD) và 1 năm (dòng TENOWOOD).
   - Chính sách vận chuyển: Miễn phí vận chuyển bán kính ≤ 25km tại TP.HCM cho đơn hàng từ 25 triệu đồng (chưa VAT). Hỗ trợ gửi "bộ mẫu sản phẩm" miễn phí toàn quốc cho đại lý và thầu thợ.
2. Chuẩn xác thông số kỹ thuật (Tuyệt đối KHÔNG bịa đặt, KHÔNG báo cáo láo):
   - Tấm Nano & Lam sóng nội thất: Cấu tạo 4 lớp (Lớp UV, Lớp màng film trang trí gồm 5 nhóm: vân gỗ, vân bê tông, vân giả đá, vân vải và đơn sắc, Lớp keo Kleiberit Đức, Lớp đế làm từ hạt nhựa PVC nguyên sinh cấu trúc rỗng tổ ong). Tuyệt đối KHÔNG dùng từ "3D" cho tấm Nano phẳng, PVC vân đá, lam sóng nội thất; chỉ dùng "tạo điểm nhấn sang trọng, hiện đại". Trần dùng thuật ngữ "hệ khung xương sắt hộp mạ kẽm định hình các tầng cao độ".
   - Gỗ nhựa ngoài trời: Phân biệt rõ 3 dòng:
     * Dòng 1 lớp HDPE: 60% bột gỗ + 30% HDPE + 10% phụ gia (đồng chất 1 lớp).
     * Dòng 2 lớp phủ ASA: 60% HDPE + 20% bột gỗ + 10% phụ gia + 10% lớp phủ ASA toàn bề mặt (nhựa kỹ thuật dùng làm vỏ xe ô tô/mái ngói, Quatest 3 mã KT3-00698BXD5 ngày 28/05/2025 trương nở ngâm nước siêu thấp 0,08%).
     * Dòng 2 lớp phủ Polymer: 60% hạt nhựa HDPE + 20% bột gỗ + 10% phụ gia + 10% lớp phủ bề mặt Polymer.
   - Thi công ngoài trời: Thanh lam hộp & trụ là lớp vỏ trang trí, BẮT BUỘC luồn lõi thép hộp mạ kẽm bên trong; đầu trên dùng nắp chụp, chân trụ & điểm tiếp giáp phải chừa khe hở thoát nước tự nhiên (TUYỆT ĐỐI CẤM bịt kín keo). Cửa cổng chỉ khuyến khích tấm phẳng ASA vân 3D sâu HW123W16ASA (100x16x2900mm, 2,13 kg, 77.220đ/md = 223.938đ/thanh đã VAT 8%) hoặc Polymer HW146CE21 (4,40 kg, 120.431đ/md). CẤM dùng lam sóng, thanh lam hộp rỗng luồn thép hay tấm mỏng 12mm làm cổng.
   - Phụ kiện thi công ngoài trời chuẩn: Keo đa năng ngoại thất 3X-BOND (38.340đ/chai), Silicone X500 (47.520đ/chai), Chốt Inox 430 HW-P10ASA (1.026đ/cái), Nẹp góc V phủ ASA HW45G35ASA (194.184đ/thanh = 66.960đ/md), Bộ nắp chụp + chân đế trụ vuông 120x120 HW-SET120 (631.800đ/bộ, chỉ dùng cho trụ 120x120).
   - Nan bàn ghế Polywood: Là nhựa composite cao cấp PS/HDPE chịu lực ngoài trời, HOÀN TOÀN KHÔNG CHỨA BỘT GỖ. Bàn ghế đóng module nguyên kiện đã kèm đủ ốc vít, không bán lẻ vít/chốt, không dùng keo 3X-BOND cho bàn ghế.
   - Bảng giá: Đã bao gồm VAT 8%, tính trên khổ rộng hiệu dụng. Bảng dự toán tổng kho chỉ tính vật tư HWOOD cung ứng, tách riêng chi phí khung sắt và nhân công.

II. QUY CHUẨN SEO ON-PAGE, YOAST SEO & AI SEARCH (GEO):
1. Khối thông tin Meta đặt đầu phản hồi:
   - Meta Title: ≤ 60 ký tự, chứa từ khóa chính ở đầu, không dùng từ so sánh nhất khó chứng minh.
   - Meta Description: 140 – 155 ký tự, chứa từ khóa chính và lời kêu gọi hành động (CTA).
   - Slug: Ngắn gọn, không dấu, gạch ngang.
2. Cấu trúc nội dung & Yoast Readability (Đèn xanh 100%):
   - KHÔNG chèn thẻ <h1> vào mã HTML nội dung (vì theme WordPress tự động lấy tiêu đề bài viết làm thẻ H1).
   - Ngay đầu bài bắt buộc có khối "Trả lời nhanh" (Quick Answer < 60 từ) tóm tắt trực diện thông số/giá để AI Search (ChatGPT, Claude, Google AI Overviews) dễ trích dẫn.
   - Câu văn ngắn gọn dưới 20 từ, mỗi đoạn tối đa 3–4 câu. Dưới mỗi thẻ H2/H3 không viết đoạn văn liên tục quá 300 từ (phải ngắt nhỏ bằng H3, bảng biểu hoặc danh sách).
   - Cuối bài có mục FAQ (3–5 câu hỏi, trả lời súc tích < 50 từ) kèm đoạn mã JSON-LD Schema FAQPage.
   - TIẾT KIỆM TỐI ĐA TOKEN OUTPUT (BỎ HOÀN TOÀN GỢI Ý VỊ TRÍ ẢNH): TUYỆT ĐỐI KHÔNG sinh bất kỳ đoạn gợi ý vị trí chèn ảnh nào, KHÔNG sinh placeholder [GỢI Ý ẢNH...], [GỢI Ý VỊ TRÍ...], <figure> hay <img> giả lập. Chỉ tập trung 100% token output vào nội dung kỹ thuật chuẩn, thông số thực tế và bảng giá HWOOD.

III. QUY CHUẨN ĐỊNH DẠNG MÃ HTML CHUẨN GIAO DIỆN HWOOD:
1. Thẻ Tiêu đề H2: Màu xanh lá đậm thương hiệu (#2e7d32), in đậm, có đường viền kẻ ngang màu xanh bên dưới:
   <h2 style="color: #2e7d32; font-weight: 700; border-bottom: 2px solid #2e7d32; padding-bottom: 6px; margin-top: 28px; margin-bottom: 14px;">Tiêu đề mục H2</h2>
2. Thẻ Tiêu đề phụ H3: Màu xanh lá thương hiệu (#2e7d32), in đậm:
   <h3 style="color: #2e7d32; font-weight: 700; margin-top: 20px; margin-bottom: 10px;">Tiêu đề mục phụ H3</h3>
3. Bảng so sánh & Bảng báo giá (BẮT BUỘC ĐIỀN ĐỦ RUỘT & DỮ LIỆU SỐ HỌC):
   - Sử dụng các thẻ HTML chuẩn: <table>, <thead>, <tbody>, <tr>, <th>, <td>.
   - TIẾT KIỆM TOKEN: KHÔNG cần tự gõ thuộc tính style="..." dài dòng trong từng ô thẻ (Hệ thống Python tự động chuẩn hóa màu xanh thương hiệu #2e7d32, viền và responsive cho toàn bộ bảng).
   - BẮT BUỘC có đầy đủ hàng và cột với dữ liệu kỹ thuật và báo giá thực tế. TUYỆT ĐỐI CẤM để trống ruột bảng!
4. Khối CTA Chốt đơn cuối bài:
   <div style="background-color: #f3f8f1; border: 1.5px solid #2e7d32; border-radius: 8px; padding: 22px; margin-top: 35px; text-align: center;">
     <h3 style="color: #2e7d32; margin-top: 0; font-size: 1.3rem; font-weight: 700;">HWOOD VIỆT NAM - TỔNG KHO VẬT LIỆU NỘI & NGOẠI THẤT CAO CẤP</h3>
     <p style="margin: 8px 0; color: #555;"><em>"Save Tree, Beautify Home!" - Đồng hành cùng các siêu dự án Landmark 81, Novaworld Phan Thiết, Vinpearl Phú Quốc.</em></p>
     <p style="margin: 6px 0;"><b>Trụ sở chính:</b> 148/72 Đường Trường Lưu, Phường Long Trường, Thành Phố Hồ Chí Minh</p>
     <p style="margin: 6px 0; font-size: 1.15rem; font-weight: bold; color: #2e7d32;">Hotline / Zalo tư vấn & Báo giá nhanh: 0912 565 353 - 0919 741 080</p>
     <p style="margin: 6px 0; font-size: 1rem; color: #333;"><b>Email:</b> sales@hwood.vn | <b>Website:</b> hwood.vn</p>
     <p style="margin: 4px 0; font-size: 0.95rem; color: #666;">(Chính sách: Miễn phí vận chuyển bán kính ≤ 25km tại TP.HCM cho đơn từ 25 triệu chưa VAT - Cung cấp bộ mẫu sản phẩm miễn phí toàn quốc - Bảo hành 5 năm dòng HWOOD và 1 năm dòng TENOWOOD)</p>
     <div style="margin-top: 15px;">
       <a href="https://zalo.me/0912565353" target="_blank" style="display: inline-block; background-color: #0068ff; color: #ffffff !important; font-weight: bold; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-size: 1rem; box-shadow: 0 2px 6px rgba(0,104,255,0.3);">💬 Nhận Tư Vấn Kỹ Thuật & Báo Giá Qua Zalo (0912 565 353)</a>
     </div>
   </div>
5. Quy chuẩn Liên kết nội bộ (Internal Link - Bắt buộc theo cấu trúc hwood.vn):
   - Từ Bài viết / Hướng dẫn -> Trang Sản phẩm chi tiết (/san-pham/ten-san-pham/): Gắn link trực tiếp vào tên hoặc mã sản phẩm kèm mẫu câu điều hướng: "Xem chi tiết quy cách & báo giá tại → [Tên sản phẩm]".
   - Từ Bài viết tổng hợp / So sánh -> Nhiều bài chi tiết & Danh mục (/danh-muc-san-pham/ten-nhom/): Gắn link tự nhiên ở từng mục con.
   - Nguyên tắc bảo toàn URL: Tuyệt đối KHÔNG tự bịa đường dẫn lạ, KHÔNG dẫn link sang các bài xả kho/thanh lý cũ (đã Noindex).

THÔNG TIN BÀI VIẾT CẦN TẠO:
- Từ khóa chính: "{clean_kw}"
- Định dạng thể loại: {the_loai_bai}
- Yêu cầu độ dài: {do_dai_bai}
"""

    if "Báo Giá" in the_loai_bai:
        system_prompt += "\n6. CHỈ DẪN BÁO GIÁ: Bắt buộc có bảng HTML chuẩn giao diện HWOOD (#2e7d32) chi tiết biểu giá mới nhất 2026 với ĐẦY ĐỦ các hàng sản phẩm, ghi rõ thuế VAT 8%."
    elif "So Sánh" in the_loai_bai:
        system_prompt += "\n6. CHỈ DẪN SO SÁNH: Bắt buộc có 1 bảng so sánh đối đầu HTML chuẩn giao diện HWOOD (#2e7d32) theo 6-8 tiêu chí kỹ thuật chuẩn với ĐẦY ĐỦ dữ liệu đối chiếu."
    elif "Chọn Mua" in the_loai_bai:
        system_prompt += "\n6. CHỈ DẪN HƯỚNG DẪN CHỌN MUA: Hướng dẫn phân biệt cấu tạo vật liệu theo nhu cầu và bảng giá dự toán vật tư HWOOD có ĐẦY ĐỦ quy cách và số liệu."

    user_msg = f"Hãy viết một bài viết SEO toàn diện, xuất sắc và tuân thủ 100% quy chuẩn 3 phần của HWOOD VIỆT NAM cho từ khóa: '{clean_kw}'."
    if tieu_de:
        user_msg += f" Tiêu đề bài viết: '{tieu_de}'."
    if ghi_chu_chien_luoc:
        user_msg += f" Định hướng chiến lược bắt buộc: '{ghi_chu_chien_luoc}'."
    user_msg += f" Định dạng thể loại: {the_loai_bai}. YÊU CẦU ĐỘ DÀI: {do_dai_bai}. BẮT BUỘC khống chế độ dài bài viết đúng trong khoảng {do_dai_bai} (khoảng 5 - 6 mục H2 trọng tâm, không viết lan man quá dài). BẮT BUỘC viết đầy đủ trọn vẹn từ Mục lục, Khối trả lời nhanh, Nội dung, Bảng CÓ ĐẦY ĐỦ RUỘT VÀ SỐ LIỆU (TUYỆT ĐỐI KHÔNG ĐỂ TRỐNG BẢNG), FAQ có JSON-LD Schema đến Khối CTA Zalo OA 0912 565 353 cuối bài. CHỈ xuất mã HTML sạch, không viết lời thoại mở đầu hay kết thúc. BẮT BUỘC BỎ HOÀN TOÀN gợi ý vị trí chèn ảnh hoặc placeholder hình ảnh để tiết kiệm tối đa token out."

    noi_dung_bai = goi_ai_tao_va_noi_bai(
        client=client,
        model=chon_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg}
        ],
        max_tokens=8192
    )

    clean_html, _, _ = parse_and_apply_patch("", noi_dung_bai)
    from modules.media_planner import xoa_hop_placeholder_anh
    clean_html = xoa_hop_placeholder_anh(clean_html)

    from modules.file_handler import chuan_hoa_bang_html_hwood
    from modules.knowledge import viet_hoa_tieu_de
    from modules.history_manager import luu_bai_viet_lich_su

    # Tự động chuẩn hóa toàn bộ các bảng trong bài theo chuẩn giao diện HWOOD
    noi_dung_bai = chuan_hoa_bang_html_hwood(clean_html)

    if tieu_de:
        meta_title = tieu_de[:60]
    else:
        tieu_de_dep = viet_hoa_tieu_de(clean_kw)
        meta_title = f"{tieu_de_dep} - Báo Giá & Quy Cách Chuẩn | HWOOD"
        if len(meta_title) > 60:
            meta_title = f"{tieu_de_dep} - Báo Giá Chuẩn HWOOD"[:60]

    meta_desc = f"Khám phá các dòng {clean_kw.lower()} chính hãng HWOOD VIỆT NAM. Đạt chuẩn Quatest 3, bảo hành 5 năm, giao hàng nhanh. Hotline tư vấn: 0912 565 353."
    if len(meta_desc) > 155:
        meta_desc = meta_desc[:155]
    elif len(meta_desc) < 140:
        meta_desc = f"Tìm hiểu thông số, ưu điểm và báo giá {clean_kw.lower()} chính hãng HWOOD VIỆT NAM. Bảo hành đến 5 năm, miễn phí giao hàng 25km. Hotline: 0912 565 353."[:155]

    luu_bai_viet_lich_su(clean_kw, noi_dung_bai, meta_title, meta_desc)
    return noi_dung_bai, meta_title, meta_desc
