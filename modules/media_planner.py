import re
import html
import io
import csv
from modules.file_handler import xoa_dau_tieng_viet
from modules.knowledge import viet_hoa_tieu_de

def xoa_hop_placeholder_anh(html_str):
    """Làm sạch toàn bộ các hộp placeholder giả lập và ghi chú gợi ý vị trí ảnh khỏi bài viết để tiết kiệm token và làm sạch HTML"""
    if not html_str:
        return ""
    # Xóa thẻ figure chứa ghi chú gợi ý ảnh hoặc placeholder
    clean = re.sub(r'<figure[^>]*>.*?\[(?:GỢI Ý|ẢNH|HÌNH ẢNH|VỊ TRÍ).*?</figure>', '', html_str, flags=re.IGNORECASE | re.DOTALL)
    # Xóa các dòng [GỢI Ý ...] dạng text
    clean = re.sub(r'\[(?:GỢI Ý|VỊ TRÍ CHÈN|ẢNH MINH HỌA)[^\]]*\]', '', clean, flags=re.IGNORECASE)
    # Xóa figcaption chứa gợi ý
    clean = re.sub(r'<figcaption[^>]*>.*?(?:gợi ý|placeholder|chèn ảnh).*?</figcaption>', '', clean, flags=re.IGNORECASE | re.DOTALL)
    # Xóa các dòng Thẻ Alt đề xuất thừa nếu có
    clean = re.sub(r'🎯\s*<b>Thẻ Alt đề xuất:</b>[^\n<]*', '', clean, flags=re.IGNORECASE)
    # Xóa comment HTML gợi ý ảnh
    clean = re.sub(r'<!--\s*(?:gợi ý|vị trí|chèn ảnh).*?-->', '', clean, flags=re.IGNORECASE | re.DOTALL)
    return clean.strip()


def tao_ke_hoach_media_seo(html_str, tu_khoa_chinh, danh_muc=""):
    """
    Tự động phân tích cấu trúc bài viết HTML để tạo Bảng Kế Hoạch Hình Ảnh & Video chuẩn SEO:
    - Vị trí từng ảnh/video trong bài (Dưới H2/H3 nào)
    - Tên file chuẩn SEO (chữ thường, không dấu, nối bằng dấu gạch ngang, chứa từ khóa)
    - Thẻ Alt chuẩn SEO (mô tả chính xác, tối ưu thực thể)
    - Loại media & Kích thước đề xuất (16:9 1200x675, 3:2 1200x800, WebP < 150KB)
    - Gợi ý bối cảnh & góc chụp (Visual Brief cho designer/nhiếp ảnh)
    - Chú thích hiển thị (Caption)
    """
    clean_kw = tu_khoa_chinh.strip()
    slug_kw = re.sub(r'[^a-z0-9\-]+', '-', xoa_dau_tieng_viet(clean_kw)).strip('-')
    
    # Bóc tách tất cả các thẻ H2 trong bài viết
    h2_tags = re.findall(r'<h2[^>]*>(.*?)</h2>', html_str, re.IGNORECASE | re.DOTALL)
    clean_h2_list = []
    for h in h2_tags:
        t = re.sub(r'<[^>]+>', '', h).strip()
        t = html.unescape(t)
        if t and len(t) > 3:
            clean_h2_list.append(t)
            
    media_list = []
    
    # 1. Ảnh đại diện bắt buộc (Featured Image / Hero Banner)
    media_list.append({
        "stt": 1,
        "vi_tri": "📸 Ảnh 1: Ảnh đại diện bài viết (Featured Image / Hero Banner)",
        "vi_tri_code": "top",
        "h2_target": "Đầu bài viết (Dưới H1 & Đoạn mở bài)",
        "ten_file": f"{slug_kw}-chinh-hang-hwood.webp",
        "the_alt": f"{viet_hoa_tieu_de(clean_kw)} cao cấp chính hãng thương hiệu HWOOD",
        "loai_media": "Ảnh Ngang 16:9 (Hero Image)",
        "kich_thuoc": "1200 x 675 px (Định dạng WebP, dung lượng < 150 KB)",
        "y_tuong_chup": f"Chụp toàn cảnh phối cảnh đẹp nhất của {clean_kw} trong không gian sân vườn/biệt thự sang trọng, ánh sáng tự nhiên ban ngày.",
        "caption": f"Hình 1: Toàn cảnh {clean_kw} chất lượng cao mang thương hiệu HWOOD Việt Nam."
    })
    
    # 2. Tạo ảnh cho từng phân đoạn H2 quan trọng
    current_idx = 2
    for h2 in clean_h2_list:
        h2_lower = h2.lower()
        h2_clean_name = re.sub(r'^[0-9\.\-\s]+', '', h2).strip()
        h2_slug_part = re.sub(r'[^a-z0-9\-]+', '-', xoa_dau_tieng_viet(h2_clean_name)).strip('-')[:35]
        
        # Bỏ qua nếu là mục FAQ hoặc Liên hệ
        if any(w in h2_lower for w in ["faq", "câu hỏi", "liên hệ", "hotline", "kết luận"]):
            continue
            
        ten_file = f"{slug_kw}-{h2_slug_part}.webp"
        
        if any(w in h2_lower for w in ["báo giá", "giá", "bảng giá", "combo", "chi phí"]):
            loai = "Ảnh Infographic / Bảng Giá Thực Tế"
            size = "1200 x 800 px (WebP < 180 KB)"
            alt = f"Bảng báo giá chi tiết và combo {clean_kw} niêm yết chính hãng HWOOD"
            brief = f"Thiết kế ảnh infographic hoặc chụp ảnh combo {clean_kw} kèm tem nhãn kiểm định, hiển thị rõ giá và chính sách VAT 8%."
            cap = f"Bảng giá niêm yết minh bạch các dòng {clean_kw} thương hiệu HWOOD."
        elif any(w in h2_lower for w in ["cấu tạo", "vật liệu", "kỹ thuật", "thông số", "đặc tính", "nan polywood"]):
            loai = "Ảnh Cận Cảnh Chi Tiết (Close-up Macro)"
            size = "1200 x 800 px (WebP < 150 KB)"
            alt = f"Cận cảnh cấu tạo chất liệu chịu lực của {clean_kw} HWOOD"
            brief = f"Chụp cận cảnh góc 45 độ bề mặt vân gỗ, độ hoàn thiện tinh xảo của mối ghép, ốc vít inox và khung sơn tĩnh điện của {clean_kw}."
            cap = f"Chi tiết vật liệu cao cấp cấu thành nên độ bền vượt trội của {clean_kw} HWOOD."
        elif any(w in h2_lower for w in ["màu", "bộ sưu tập", "phối màu", "mẫu"]):
            loai = "Ảnh Bộ Sưu Tập Màu Sắc (Color Palette / Swatch)"
            size = "1200 x 675 px (WebP < 150 KB)"
            alt = f"Bộ sưu tập các tông phối màu thực tế của {clean_kw} HWOOD"
            brief = "Chụp hoặc ghép các góc màu thực tế (Nhôm trắng - Gỗ vàng, Nhôm đen - Gỗ nâu, All Black) đặt cạnh nhau trong cùng 1 khung hình."
            cap = f"Các tông phối màu chủ đạo của dòng {clean_kw} HWOOD phù hợp mọi phong cách kiến trúc."
        elif any(w in h2_lower for w in ["thi công", "lắp đặt", "hướng dẫn", "quy trình", "nghiệm thu"]):
            loai = "Video Review / Hướng Dẫn Lắp Đặt (YouTube Embed hoặc Ảnh Quy Trình)"
            size = "Video 16:9 1080p Embed / Ảnh 1200x675 px"
            alt = f"Quy trình đóng module và lắp đặt nhanh chóng {clean_kw} HWOOD"
            brief = "Quay video ngắn hoặc chụp 3 bước mở thùng module phụ kiện đồng bộ và lắp ráp hoàn chỉnh sản phẩm."
            cap = f"Quy cách đóng thùng module đồng bộ giúp việc lắp đặt {clean_kw} cực kỳ nhanh chóng và tiện lợi."
        elif any(w in h2_lower for w in ["ứng dụng", "cafe", "resort", "sân vườn", "công trình", "không gian"]):
            loai = "Ảnh Dự Án Thực Tế (Project Showcase)"
            size = "1200 x 800 px (WebP < 160 KB)"
            alt = f"Không gian công trình sân vườn thực tế lắp đặt {clean_kw} HWOOD"
            brief = f"Chụp toàn cảnh góc rộng khuôn viên quán cafe sân vườn, homestay hoặc resort ven biển đang sử dụng {clean_kw} của HWOOD."
            cap = f"Dự án thực tế sử dụng {clean_kw} HWOOD nâng tầm cảnh quan và tối ưu chi phí đầu tư."
        else:
            loai = "Ảnh Thực Tế Sản Phẩm (Product In-Situ)"
            size = "1200 x 800 px (WebP < 150 KB)"
            alt = f"Hình ảnh thực tế {clean_kw} phục vụ công trình ngoài trời"
            brief = f"Chụp góc ngang mắt nhìn bộ sản phẩm {clean_kw} đặt trên nền sàn gỗ nhựa hoặc thảm cỏ ngoài trời."
            cap = f"Sản phẩm {clean_kw} đạt tiêu chuẩn chất lượng cao phục vụ các dự án ngoài trời."
            
        media_list.append({
            "stt": current_idx,
            "vi_tri": f"📸 Ảnh {current_idx}: Dưới mục '{h2_clean_name}'",
            "vi_tri_code": h2,
            "h2_target": h2,
            "ten_file": ten_file,
            "the_alt": alt,
            "loai_media": loai,
            "kich_thuoc": size,
            "y_tuong_chup": brief,
            "caption": f"Hình {current_idx}: {cap}"
        })
        current_idx += 1
        
        # Giới hạn tối đa 6 ảnh cho các thẻ H2
        if current_idx > 6:
            break
            
    # Thêm gợi ý Video YouTube chuyên sâu
    has_video = any("video" in m["loai_media"].lower() for m in media_list)
    if not has_video:
        media_list.append({
            "stt": current_idx,
            "vi_tri": f"🎥 Video {current_idx}: Trải nghiệm thực tế (Trước FAQ & Liên hệ)",
            "vi_tri_code": "faq",
            "h2_target": "Trước mục Câu Hỏi Thường Gặp FAQ hoặc Liên hệ",
            "ten_file": f"video-review-thuc-te-{slug_kw}-hwood.mp4",
            "the_alt": f"Video review thực tế độ bền và khả năng chịu nước của {clean_kw} HWOOD",
            "loai_media": "Video YouTube Embed (16:9 Full HD)",
            "kich_thuoc": "Video 1920x1080 (Nhúng qua thẻ iframe YouTube / TikTok)",
            "y_tuong_chup": f"Video thực tế 1 - 2 phút kiểm tra khả năng xịt nước, chịu lực và cảm nhận thực tế của khách hàng về {clean_kw} HWOOD.",
            "caption": f"Video: Trải nghiệm thực tế chất lượng và độ bền của {clean_kw} tại tổng kho HWOOD."
        })
        
    return media_list


def xuat_csv_ke_hoach_media(ds_media):
    """Xuất danh sách kế hoạch media ra định dạng CSV/Excel UTF-8 BOM để mở tiếng Việt không lỗi font"""
    if not ds_media:
        return ""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "STT", 
        "VỊ TRÍ CHÈN TRONG BÀI", 
        "TÊN FILE CHUẨN SEO", 
        "THẺ ALT (ALT TEXT)", 
        "LOẠI MEDIA & KÍCH THƯỚC ĐỀ XUẤT", 
        "GỢI Ý GÓC CHỤP & BỐI CẢNH (VISUAL BRIEF)",
        "CHÚ THÍCH HIỂN THỊ (CAPTION)"
    ])
    for m in ds_media:
        writer.writerow([
            m.get("stt", ""),
            m.get("vi_tri", ""),
            m.get("ten_file", ""),
            m.get("the_alt", ""),
            f"{m.get('loai_media', '')} - {m.get('kich_thuoc', '')}",
            m.get("y_tuong_chup", ""),
            m.get("caption", "")
        ])
    return "\ufeff" + output.getvalue()


def tao_bang_html_ke_hoach_media(ds_media):
    """
    Tạo bảng HTML chuẩn giao diện thương hiệu HWOOD (Header nền xanh #237a3b, chữ trắng in đậm)
    hiển thị trọn vẹn thông tin: Vị trí trong bài, Tên file WebP chuẩn SEO, Thẻ Alt, Kích thước, Gợi ý chụp.
    """
    if not ds_media:
        return ""
    rows = []
    for m in ds_media:
        stt = m.get("stt", "")
        v_tri = m.get("vi_tri", "")
        t_file = m.get("ten_file", "")
        t_alt = m.get("the_alt", "")
        l_media = m.get("loai_media", "")
        k_thuoc = m.get("kich_thuoc", "")
        y_tuong = m.get("y_tuong_chup", "")
        rows.append(f"""
        <tr style="border-bottom: 1px solid #e2e8f0; transition: background 0.2s;" onmouseover="this.style.backgroundColor='#f8fafc'" onmouseout="this.style.backgroundColor='transparent'">
            <td style="border: 1px solid #cbd5e1; padding: 10px 8px; font-weight: bold; text-align: center; background-color: #f8fafc; color: #166534; font-size: 13px;">Ảnh {stt}</td>
            <td style="border: 1px solid #cbd5e1; padding: 10px 12px; font-weight: 600; color: #15803d; font-size: 13px;">📍 {v_tri}</td>
            <td style="border: 1px solid #cbd5e1; padding: 10px 12px; font-size: 13px;"><code style="background-color: #f1f5f9; padding: 3px 6px; border-radius: 4px; color: #0284c7; font-weight: bold; font-family: monospace;">{t_file}</code></td>
            <td style="border: 1px solid #cbd5e1; padding: 10px 12px; font-size: 13px; color: #334155;">{t_alt}</td>
            <td style="border: 1px solid #cbd5e1; padding: 10px 12px; font-size: 12px; color: #475569;"><b>{l_media}</b><br><span style="color: #64748b;">({k_thuoc})</span></td>
            <td style="border: 1px solid #cbd5e1; padding: 10px 12px; font-size: 12px; color: #475569;"><em>💡 {y_tuong}</em></td>
        </tr>
        """)
    rows_html = "".join(rows)
    table_html = f"""
    <div style="overflow-x: auto; margin: 15px 0; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); border: 1px solid #cbd5e1;">
        <table style="width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; font-size: 13px; line-height: 1.5; background: #ffffff;">
            <thead>
                <tr style="background-color: #237a3b; color: #ffffff;">
                    <th style="border: 1px solid #237a3b; padding: 11px 8px; font-weight: bold; text-align: center; width: 65px; color: #ffffff;">STT</th>
                    <th style="border: 1px solid #237a3b; padding: 11px 12px; font-weight: bold; text-align: left; width: 230px; color: #ffffff;">VỊ TRÍ GẮN TRONG BÀI</th>
                    <th style="border: 1px solid #237a3b; padding: 11px 12px; font-weight: bold; text-align: left; width: 230px; color: #ffffff;">TÊN FILE CHUẨN SEO (.webp)</th>
                    <th style="border: 1px solid #237a3b; padding: 11px 12px; font-weight: bold; text-align: left; width: 220px; color: #ffffff;">THẺ ALT (ALT TEXT)</th>
                    <th style="border: 1px solid #237a3b; padding: 11px 12px; font-weight: bold; text-align: left; width: 170px; color: #ffffff;">LOẠI & KÍCH THƯỚC</th>
                    <th style="border: 1px solid #237a3b; padding: 11px 12px; font-weight: bold; text-align: left; color: #ffffff;">GỢI Ý GÓC CHỤP & BỐI CẢNH</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    return table_html


def tao_preview_co_khung_vi_tri_anh(html_str, ds_media):
    """
    Chỉ dùng riêng cho chế độ xem trước trực quan (Preview):
    Tự động chèn các khung định vị màu xanh nổi bật vào đúng các vị trí H2/Đầu bài,
    giúp người biên tập thấy rõ ràng ảnh nào nên đặt ở vị trí nào mà không làm ảnh hưởng bài viết thật.
    """
    if not html_str or not ds_media:
        return html_str
    
    preview_content = html_str
    # Sắp xếp ngược thứ tự từ lớn về bé để khi chèn không làm lệch vị trí tìm kiếm
    for m in sorted(ds_media, key=lambda x: x.get("stt", 0), reverse=True):
        stt = m.get("stt", "")
        v_tri = m.get("vi_tri", "")
        t_file = m.get("ten_file", "")
        t_alt = m.get("the_alt", "")
        l_media = m.get("loai_media", "")
        k_thuoc = m.get("kich_thuoc", "")
        y_tuong = m.get("y_tuong_chup", "")
        h2_target = m.get("h2_target", "")
        
        banner_box = f"""
<div style="background-color: #f0fdf4; border: 2px dashed #237a3b; border-radius: 8px; padding: 14px 18px; margin: 22px auto; max-width: 850px; font-family: Arial, sans-serif; text-align: left; box-sizing: border-box;">
    <div style="color: #166534; font-weight: bold; font-size: 15px; margin-bottom: 6px; display: flex; align-items: center; gap: 8px;">
        <span style="background-color: #237a3b; color: #ffffff; padding: 3px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">📍 VỊ TRÍ GẮN ẢNH {stt}</span>
        <span style="color: #15803d;">{v_tri}</span>
    </div>
    <div style="font-size: 13px; color: #334155; line-height: 1.6; margin-top: 6px;">
        📁 <b>Tên file ảnh chuẩn SEO:</b> <code style="background-color: #e2e8f0; padding: 2px 6px; border-radius: 4px; color: #0284c7; font-weight: bold; font-family: monospace;">{t_file}</code><br>
        🏷️ <b>Thẻ Alt đề xuất:</b> {t_alt}<br>
        📐 <b>Quy cách:</b> {l_media} — {k_thuoc}<br>
        🎬 <b>Gợi ý góc chụp:</b> <em>💡 {y_tuong}</em>
    </div>
</div>
"""
        # Nếu là vị trí 1 (Đầu bài)
        if stt == 1 or "đầu bài" in str(h2_target).lower():
            m_p = re.search(r'</p>', preview_content, re.IGNORECASE)
            if m_p:
                pos = m_p.end()
                preview_content = preview_content[:pos] + "\n" + banner_box + "\n" + preview_content[pos:]
            else:
                preview_content = banner_box + "\n" + preview_content
        elif h2_target and h2_target in preview_content:
            pos = preview_content.find(h2_target)
            end_h2 = preview_content.find("</h2>", pos)
            if end_h2 != -1:
                after_h2 = end_h2 + 5
                m_next_p = re.search(r'</p>', preview_content[after_h2:], re.IGNORECASE)
                if m_next_p:
                    insert_pos = after_h2 + m_next_p.end()
                    preview_content = preview_content[:insert_pos] + "\n" + banner_box + "\n" + preview_content[insert_pos:]
                else:
                    preview_content = preview_content[:after_h2] + "\n" + banner_box + "\n" + preview_content[after_h2:]
    return preview_content


def chen_anh_that_vao_html(html_str, vi_tri_stt, url_anh, the_alt="", caption="", ds_media=None):
    """
    Chèn một thẻ <figure><img> thật vào đúng vị trí tương ứng trong bài viết HTML
    """
    if not html_str or not url_anh:
        return html_str
        
    alt_val = the_alt
    cap_val = caption
    h2_target = ""
    
    # Tìm thông tin trong ds_media nếu có
    if ds_media:
        for m in ds_media:
            if m.get("stt") == vi_tri_stt:
                if not alt_val:
                    alt_val = m.get("the_alt", "")
                if not cap_val:
                    cap_val = m.get("caption", "")
                h2_target = m.get("h2_target", "")
                break
                
    if not alt_val:
        alt_val = "Hình ảnh sản phẩm HWOOD chính hãng"
    if not cap_val:
        cap_val = alt_val

    # Tạo khối figure chuẩn responsive
    figure_html = f"""
<figure style="margin: 26px auto; text-align: center; max-width: 850px;">
    <img src="{url_anh}" alt="{alt_val}" style="width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); display: block;" loading="lazy">
    <figcaption style="font-size: 0.88rem; color: #64748b; font-style: italic; margin-top: 8px;">{cap_val}</figcaption>
</figure>
"""

    # Trường hợp 1: Chèn vào đầu bài viết
    if vi_tri_stt == 1 or "đầu bài" in str(h2_target).lower():
        # Tìm đoạn kết thúc của thẻ paragraph đầu tiên <p>...</p>
        m_p = re.search(r'</p>', html_str, re.IGNORECASE)
        if m_p:
            pos = m_p.end()
            return html_str[:pos] + "\n" + figure_html + "\n" + html_str[pos:]
        else:
            return figure_html + "\n" + html_str

    # Trường hợp 2: Chèn dưới một thẻ H2 cụ thể
    if h2_target and h2_target in html_str:
        pos = html_str.find(h2_target)
        # Tìm thẻ đóng </h2> của thẻ này
        end_h2 = html_str.find("</h2>", pos)
        if end_h2 != -1:
            # Tìm đoạn văn <p>...</p> ngay sau H2 để đặt ảnh dưới đoạn văn mở đầu mục đó
            after_h2 = end_h2 + 5
            m_next_p = re.search(r'</p>', html_str[after_h2:], re.IGNORECASE)
            if m_next_p:
                insert_pos = after_h2 + m_next_p.end()
                return html_str[:insert_pos] + "\n" + figure_html + "\n" + html_str[insert_pos:]
            else:
                return html_str[:after_h2] + "\n" + figure_html + "\n" + html_str[after_h2:]

    # Trường hợp dự phòng: Chèn trước FAQ hoặc cuối bài
    if "faq" in html_str.lower():
        pos_faq = html_str.lower().find("faq")
        # Tìm thẻ <h trước chữ faq
        last_h = html_str.rfind("<h", 0, pos_faq)
        if last_h != -1:
            return html_str[:last_h] + "\n" + figure_html + "\n" + html_str[last_h:]
            
    return html_str + "\n" + figure_html
