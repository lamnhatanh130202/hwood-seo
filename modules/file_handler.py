import os
import re
import unicodedata
import base64
import io
import csv
import html

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(CURRENT_DIR, "anh_dinh_kem")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def xoa_dau_tieng_viet(text):
    """Chuyển chữ tiếng Việt có dấu thành không dấu để so khớp slug và tiêu đề"""
    if not text:
        return ""
    text = unicodedata.normalize('NFD', str(text))
    text = re.sub(r'[\u0300-\u036f]', '', text)
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return text.lower()

def doc_noi_dung_file_dinh_kem(uploaded_file):
    """Trích xuất nội dung văn bản và thông tin từ file đính kèm (Word, PDF, Text, Ảnh)"""
    if uploaded_file is None:
        return "", "", None
    
    file_name = uploaded_file.name
    fname_lower = file_name.lower()
    text_content = ""
    summary_info = ""
    img_b64 = None
    
    try:
        # 1. File Word (.docx)
        if fname_lower.endswith(".docx"):
            import docx
            doc = docx.Document(uploaded_file)
            paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        paras.append(row_text)
            full_text = "\n".join(paras)
            word_count = len(full_text.split())
            text_content = f"--- [NỘI DUNG TỪ FILE WORD: {file_name}] ---\n{full_text}"
            summary_info = f"📄 Đã đọc {word_count:,} từ từ file Word: `{file_name}`"

        # 2. File PDF (.pdf)
        elif fname_lower.endswith(".pdf"):
            import pypdf
            reader = pypdf.PdfReader(uploaded_file)
            pages_text = []
            for i, page in enumerate(reader.pages):
                pt = page.extract_text()
                if pt and pt.strip():
                    pages_text.append(f"Trang {i+1}:\n{pt.strip()}")
            full_text = "\n\n".join(pages_text)
            word_count = len(full_text.split())
            text_content = f"--- [NỘI DUNG TỪ FILE PDF: {file_name}] ---\n{full_text}"
            summary_info = f"📑 Đã đọc {len(reader.pages)} trang ({word_count:,} từ) từ file PDF: `{file_name}`"

        # 3. File Text / Markdown / HTML (.txt, .md, .html)
        elif fname_lower.endswith((".txt", ".md", ".html", ".htm")):
            raw_bytes = uploaded_file.read()
            full_text = raw_bytes.decode("utf-8", errors="ignore")
            word_count = len(full_text.split())
            text_content = f"--- [NỘI DUNG TỪ FILE VĂN BẢN: {file_name}] ---\n{full_text}"
            summary_info = f"📝 Đã đọc {word_count:,} từ từ file văn bản: `{file_name}`"

        # 4. File Hình ảnh (.png, .jpg, .jpeg, .webp)
        elif fname_lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
            from PIL import Image
            img = Image.open(uploaded_file)
            w, h = img.size
            
            # Lưu file ảnh vào thư mục anh_dinh_kem
            save_path = os.path.join(UPLOAD_DIR, file_name)
            uploaded_file.seek(0)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.read())
            
            uploaded_file.seek(0)
            img_bytes = uploaded_file.read()
            mime = "image/png" if fname_lower.endswith(".png") else "image/jpeg"
            img_b64 = f"data:{mime};base64,{base64.b64encode(img_bytes).decode()}"
            
            text_content = f"--- [HÌNH ẢNH ĐÍNH KÈM TỪ NGƯỜI DÙNG: {file_name}] ---\nKích thước ảnh: {w}x{h} px.\nĐã lưu ảnh tại máy tính: {save_path}.\nNgười dùng đính kèm ảnh này làm tài liệu tham khảo hoặc muốn chèn vào bài viết."
            summary_info = f"🖼️ Đã tiếp nhận hình ảnh: `{file_name}` ({w}x{h} px)"
            
    except Exception as ex:
        text_content = f"[Lỗi khi đọc file {file_name}: {ex}]"
        summary_info = f"⚠️ Lỗi đọc file: {ex}"
        
    return text_content, summary_info, img_b64


def chuan_hoa_bang_html_hwood(html_str):
    """
    Tự động chuẩn hóa toàn bộ các bảng <table> trong bài viết chuẩn giao diện HWOOD:
    - Hàng đầu tiên (Header/Tiêu đề cột): Nền xanh lá đậm (#2e7d32), chữ trắng in đậm, căn giữa, viền #1b5e20.
    - Cột đầu tiên (Cột Tiêu chí / Hạng mục / Công năng): In đậm (#1a2e22), viền #cccccc.
    - Hàng nội dung xen kẽ trắng (#ffffff) và xám xanh nhạt (#f2f6f3), bọc ngoài <div style="overflow-x: auto; margin: 18px 0;">.
    - Bảo toàn 100% nội dung hàng/cột, đóng mở thẻ đúng chuẩn thead/tbody/table/div.
    """
    if not html_str or "<table" not in html_str.lower():
        return html_str

    def _replace_table(match):
        raw_table = match.group(0)
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', raw_table, re.IGNORECASE | re.DOTALL)
        if not rows:
            return raw_table
            
        header_rows = []
        body_rows = []
        is_first = True
        
        for r_idx, row_content in enumerate(rows):
            cells = re.findall(r'<(th|td)[^>]*>(.*?)</\1>', row_content, re.IGNORECASE | re.DOTALL)
            if not cells:
                continue
                
            is_header = is_first or ('<th' in row_content.lower())
            new_cells = []
            
            for c_idx, (tag, val) in enumerate(cells):
                clean_val = val.strip()
                if is_header:
                    new_cells.append(
                        f'<th style="background-color: #2e7d32; color: #ffffff; font-weight: 700; padding: 12px 10px; border: 1px solid #1b5e20; text-align: center;">{clean_val}</th>'
                    )
                else:
                    if c_idx == 0:
                        new_cells.append(
                            f'<td style="padding: 10px; border: 1px solid #cccccc; color: #1a2e22; font-weight: 700; background-color: #f8fafc;">{clean_val}</td>'
                        )
                    else:
                        bg_c = '#ffffff' if len(body_rows) % 2 == 0 else '#f2f6f3'
                        new_cells.append(
                            f'<td style="padding: 10px; border: 1px solid #cccccc; color: #222222; background-color: {bg_c};">{clean_val}</td>'
                        )
                        
            row_html = f"<tr>{''.join(new_cells)}</tr>"
            if is_header:
                header_rows.append(row_html)
            else:
                body_rows.append(row_html)
                
            is_first = False

        thead_html = f"<thead>{''.join(header_rows)}</thead>" if header_rows else ""
        tbody_html = f"<tbody>{''.join(body_rows)}</tbody>" if body_rows else ""
        
        table_html = (
            '<div style="overflow-x: auto; margin: 18px 0;">\n'
            '<table style="width: 100%; border-collapse: collapse; border: 1px solid #333333; font-size: 15px; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;">\n'
            f'{thead_html}\n'
            f'{tbody_html}\n'
            '</table>\n'
            '</div>'
        )
        return table_html

    # Dọn sạch các tàn tích bảng bị rỗng hoặc lỗi thẻ trước đó
    cleaned = re.sub(
        r'<div style="overflow-x: auto; margin: 18px 0;">\s*<table[^>]*><thead>\s*</div>',
        '',
        html_str,
        flags=re.IGNORECASE
    )

    # Chống bọc lồng 2 lần thẻ div overflow
    cleaned = re.sub(
        r'<div style="overflow-x: auto; margin: 18px 0;">\s*(<table[^>]*>.*?</table>)\s*</div>',
        r'\1',
        cleaned,
        flags=re.IGNORECASE | re.DOTALL
    )

    return re.sub(r'<table[^>]*>.*?</table>', _replace_table, cleaned, flags=re.IGNORECASE | re.DOTALL)


def xuat_bang_html_ra_csv(html_str):
    """Trích xuất tất cả các bảng dữ liệu trong bài viết sang định dạng CSV/Excel với UTF-8 BOM"""
    if not html_str:
        return ""
    tables = re.findall(r'<table[^>]*>(.*?)</table>', html_str, re.IGNORECASE | re.DOTALL)
    if not tables:
        return ""
    
    csv_output = io.StringIO()
    writer = csv.writer(csv_output)
    
    for t_idx, tbl in enumerate(tables, 1):
        if t_idx > 1:
            writer.writerow([])
            writer.writerow([f"--- BẢNG DỮ LIỆU {t_idx} ---"])
        rows = re.findall(r'<tr[^>]*>(.*?)</tr>', tbl, re.IGNORECASE | re.DOTALL)
        for r in rows:
            cells = re.findall(r'<(?:th|td)[^>]*>(.*?)</(?:th|td)>', r, re.IGNORECASE | re.DOTALL)
            row_data = [html.unescape(re.sub(r'<[^>]+>', '', c).strip()) for c in cells]
            if row_data:
                writer.writerow(row_data)
                
    return "\ufeff" + csv_output.getvalue()


def tao_file_word_tu_html(html_str, title="Bài viết HWOOD", meta_title="", meta_desc="", focus_kw="", them_ke_hoach_media=False):
    """
    Chuyển đổi bài viết HTML sang tài liệu Word (.docx) chuyên nghiệp:
    - Kiểu chữ Segoe UI hiện đại, chuẩn kích thước và khoảng cách dòng 1.25.
    - Giữ nguyên màu xanh thương hiệu HWOOD #2e7d32 cho tiêu đề H1, H2, H3.
    - Bảng thông tin Yoast SEO Metadata ở đầu trang có viền rõ nét.
    - Bảng dữ liệu (So sánh, Báo giá) chuẩn header xanh #2E7D32 chữ trắng, xen kẽ dòng.
    - Giữ nguyên định dạng in đậm (strong/b) và in nghiêng (em/i) trong các đoạn văn.
    """
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import parse_xml
    from docx.oxml.ns import nsdecls

    doc = docx.Document()
    
    # Thiết lập phong cách văn bản chuẩn mặc định
    try:
        style_norm = doc.styles['Normal']
        style_norm.font.name = 'Segoe UI'
        style_norm.font.size = Pt(11)
        style_norm.font.color.rgb = RGBColor(34, 34, 34)
        style_norm.paragraph_format.line_spacing = 1.25
        style_norm.paragraph_format.space_after = Pt(6)
    except Exception:
        pass

    def _chen_noi_dung_inline(p, html_text, base_font_size=Pt(11), default_color=RGBColor(34, 34, 34)):
        """Phân tích và giữ nguyên in đậm (strong/b), in nghiêng (em/i) trong đoạn văn Word"""
        tokens = re.split(r'(</?(?:strong|b|em|i)[^>]*>)', html_text, flags=re.IGNORECASE)
        is_bold = False
        is_italic = False
        for tok in tokens:
            if not tok:
                continue
            tok_lower = tok.lower()
            if tok_lower in ['<strong>', '<b>']:
                is_bold = True
            elif tok_lower in ['</strong>', '</b>']:
                is_bold = False
            elif tok_lower in ['<em>', '<i>']:
                is_italic = True
            elif tok_lower in ['</em>', '</i>']:
                is_italic = False
            else:
                clean = html.unescape(re.sub(r'<[^>]+>', '', tok))
                if clean:
                    r = p.add_run(clean)
                    r.font.name = 'Segoe UI'
                    r.font.size = base_font_size
                    r.font.color.rgb = default_color
                    r.bold = is_bold
                    r.italic = is_italic

    # 1. Khung hộp SEO Metadata (Tương ứng Yoast SEO / Rank Math)
    slug_val = re.sub(r'[^a-z0-9\-]+', '-', xoa_dau_tieng_viet(title)).strip('-')
    meta_tbl = doc.add_table(rows=4, cols=2)
    meta_tbl.style = 'Table Grid'
    meta_tbl.autofit = False
    
    labels = [
        ("📌 Cụm từ khóa chính (Focus Keyword):", focus_kw or title),
        ("🏷️ Tiêu đề SEO (Title Tag):", meta_title or f"{title} - HWOOD VIỆT NAM"),
        ("🔗 Đường dẫn tĩnh (Slug):", slug_val),
        ("📝 Thẻ mô tả (Meta Description):", meta_desc or f"Bài viết chi tiết về {title} từ thương hiệu HWOOD.")
    ]
    
    for idx, (lbl, val) in enumerate(labels):
        c0 = meta_tbl.rows[idx].cells[0]
        c1 = meta_tbl.rows[idx].cells[1]
        c0.text = lbl
        c1.text = val
        
        # Style cell 0
        shd0 = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F1F5F9"/>')
        c0._tc.get_or_add_tcPr().append(shd0)
        p0 = c0.paragraphs[0]
        if p0.runs:
            p0.runs[0].font.name = 'Segoe UI'
            p0.runs[0].font.bold = True
            p0.runs[0].font.size = Pt(9.5)
            p0.runs[0].font.color.rgb = RGBColor(30, 41, 59)
        
        # Style cell 1
        p1 = c1.paragraphs[0]
        if p1.runs:
            p1.runs[0].font.name = 'Segoe UI'
            p1.runs[0].font.size = Pt(9.5)
            p1.runs[0].font.color.rgb = RGBColor(15, 23, 42)
            
    doc.add_paragraph() # Dòng trống ngăn cách
    
    # 2. Tiêu đề H1 chính bài viết
    h1 = doc.add_heading(level=1)
    h1.paragraph_format.space_before = Pt(6)
    h1.paragraph_format.space_after = Pt(12)
    h1.paragraph_format.keep_with_next = True
    r1 = h1.add_run(title)
    r1.font.name = 'Segoe UI'
    r1.font.color.rgb = RGBColor(46, 125, 50)  # Chuẩn màu xanh HWOOD #2e7d32
    r1.font.size = Pt(18)
    r1.font.bold = True
        
    # 3. Phân tích nội dung HTML
    blocks = re.findall(r'<(h[2-4]|p|table|ul|ol)[^>]*>(.*?)</\1>', html_str, re.IGNORECASE | re.DOTALL)
    
    for tag, content in blocks:
        tag_lower = tag.lower()
        clean_text = re.sub(r'<[^>]+>', '', content).strip()
        clean_text = html.unescape(clean_text)
        
        if tag_lower == 'h2':
            h = doc.add_heading(level=2)
            h.paragraph_format.space_before = Pt(16)
            h.paragraph_format.space_after = Pt(6)
            h.paragraph_format.keep_with_next = True
            r = h.add_run(clean_text)
            r.font.name = 'Segoe UI'
            r.font.color.rgb = RGBColor(46, 125, 50)  # Chuẩn màu xanh HWOOD #2e7d32
            r.font.size = Pt(14)
            r.font.bold = True
        elif tag_lower == 'h3':
            h = doc.add_heading(level=3)
            h.paragraph_format.space_before = Pt(12)
            h.paragraph_format.space_after = Pt(4)
            h.paragraph_format.keep_with_next = True
            r = h.add_run(clean_text)
            r.font.name = 'Segoe UI'
            r.font.color.rgb = RGBColor(46, 125, 50)  # Chuẩn màu xanh HWOOD #2e7d32
            r.font.size = Pt(12.5)
            r.font.bold = True
        elif tag_lower == 'h4':
            h = doc.add_heading(level=4)
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(3)
            h.paragraph_format.keep_with_next = True
            r = h.add_run(clean_text)
            r.font.name = 'Segoe UI'
            r.font.color.rgb = RGBColor(27, 94, 32)
            r.font.size = Pt(11)
            r.font.bold = True
        elif tag_lower == 'p':
            if clean_text:
                p = doc.add_paragraph()
                p.paragraph_format.line_spacing = 1.25
                p.paragraph_format.space_after = Pt(6)
                _chen_noi_dung_inline(p, content, base_font_size=Pt(11))
        elif tag_lower in ['ul', 'ol']:
            items = re.findall(r'<li[^>]*>(.*?)</li>', content, re.IGNORECASE | re.DOTALL)
            for li in items:
                p = doc.add_paragraph(style='List Bullet')
                p.paragraph_format.space_after = Pt(3)
                _chen_noi_dung_inline(p, li, base_font_size=Pt(11))
        elif tag_lower == 'table':
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.IGNORECASE | re.DOTALL)
            if rows:
                parsed_table_data = []
                for r in rows:
                    cells = re.findall(r'<(?:th|td)[^>]*>(.*?)</(?:th|td)>', r, re.IGNORECASE | re.DOTALL)
                    parsed_table_data.append([c.strip() for c in cells])
                    
                if parsed_table_data:
                    num_rows = len(parsed_table_data)
                    num_cols = max(len(r) for r in parsed_table_data)
                    w_tbl = doc.add_table(rows=num_rows, cols=num_cols)
                    w_tbl.style = 'Table Grid'
                    
                    for r_idx, r_data in enumerate(parsed_table_data):
                        for c_idx, val in enumerate(r_data):
                            if c_idx < num_cols:
                                cell = w_tbl.rows[r_idx].cells[c_idx]
                                cell.text = ""
                                p = cell.paragraphs[0]
                                p.paragraph_format.space_after = Pt(2)
                                
                                # Hàng đầu tiên: Nền xanh lá đậm #2E7D32, chữ trắng in đậm
                                if r_idx == 0:
                                    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="2E7D32"/>')
                                    cell._tc.get_or_add_tcPr().append(shd)
                                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                    _chen_noi_dung_inline(p, val, base_font_size=Pt(9.5), default_color=RGBColor(255, 255, 255))
                                    for run in p.runs:
                                        run.font.bold = True
                                else:
                                    # Cột đầu tiên (Tiêu chí): In đậm, nền xám nhạt
                                    if c_idx == 0:
                                        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F1F5F9"/>')
                                        cell._tc.get_or_add_tcPr().append(shd)
                                        _chen_noi_dung_inline(p, val, base_font_size=Pt(9.5), default_color=RGBColor(26, 46, 34))
                                        for run in p.runs:
                                            run.font.bold = True
                                    else:
                                        if r_idx % 2 == 1:
                                            shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8FAFC"/>')
                                            cell._tc.get_or_add_tcPr().append(shd)
                                        _chen_noi_dung_inline(p, val, base_font_size=Pt(9.5), default_color=RGBColor(34, 34, 34))
                    doc.add_paragraph()
                    doc.add_paragraph()

    # 4. Tùy chọn thêm Bảng Kế Hoạch Hình Ảnh (Mặc định tắt để văn bản sạch đẹp theo chuẩn fa.docx)
    if them_ke_hoach_media:
        try:
            from modules.media_planner import tao_ke_hoach_media_seo
            ds_media = tao_ke_hoach_media_seo(html_str, focus_kw or title)
            if ds_media:
                doc.add_page_break()
                h_media = doc.add_heading("📸 BẢNG KẾ HOẠCH HÌNH ẢNH & VIDEO CHUẨN SEO", level=2)
                if h_media.runs:
                    h_media.runs[0].font.color.rgb = RGBColor(46, 125, 50)
                    h_media.runs[0].font.bold = True
                    
                p_desc = doc.add_paragraph("Bảng kế hoạch chi tiết vị trí chèn, tên file ảnh chuẩn SEO, thẻ Alt và gợi ý góc chụp/video cho nhân sự thiết kế và đăng bài website:")
                if p_desc.runs:
                    p_desc.runs[0].font.italic = True
                    p_desc.runs[0].font.size = Pt(9.5)
                
                headers_m = ["STT", "VỊ TRÍ CHÈN", "TÊN FILE CHUẨN SEO", "THẺ ALT (ALT TEXT)", "LOẠI & KÍCH THƯỚC", "GỢI Ý GÓC CHỤP"]
                m_tbl = doc.add_table(rows=len(ds_media) + 1, cols=6)
                
                # Format header row: nền xanh #2E7D32, chữ trắng in đậm
                for c_i, h_txt in enumerate(headers_m):
                    cell = m_tbl.rows[0].cells[c_i]
                    cell.text = h_txt
                    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="2E7D32"/>')
                    cell._tc.get_or_add_tcPr().append(shd)
                    p = cell.paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    if p.runs:
                        p.runs[0].font.bold = True
                        p.runs[0].font.size = Pt(8.5)
                        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
                        
                for r_i, m in enumerate(ds_media, 1):
                    row_cells = m_tbl.rows[r_i].cells
                    row_cells[0].text = str(m.get("stt", ""))
                    row_cells[1].text = str(m.get("vi_tri", ""))
                    row_cells[2].text = str(m.get("ten_file", ""))
                    row_cells[3].text = str(m.get("the_alt", ""))
                    row_cells[4].text = f"{m.get('loai_media', '')}\n({m.get('kich_thuoc', '')})"
                    row_cells[5].text = str(m.get("y_tuong_chup", ""))
                    
                    # Format cell styles
                    for c_i in range(6):
                        c = row_cells[c_i]
                        if c_i == 0:
                            shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F1F5F9"/>')
                            c._tc.get_or_add_tcPr().append(shd)
                        elif r_i % 2 == 1:
                            shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8FAFC"/>')
                            c._tc.get_or_add_tcPr().append(shd)
                        p = c.paragraphs[0]
                        if p.runs:
                            p.runs[0].font.size = Pt(8)
                            if c_i in [0, 2]:
                                p.runs[0].font.bold = True
        except Exception:
            pass
                    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
