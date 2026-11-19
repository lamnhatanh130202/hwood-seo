import re
import requests
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

from modules.knowledge import lay_tri_thuc_phu_hop, viet_hoa_tieu_de
from modules.history_manager import luu_bai_viet_lich_su
from modules.ai_engine import (
    goi_ai_tao_va_noi_bai,
    viet_tiep_bai_dang_do,
    thuc_hien_tinh_chinh_ai,
    tao_bai_viet_hwood_chuan_seo
)
from modules.file_handler import (
    doc_noi_dung_file_dinh_kem, 
    chuan_hoa_bang_html_hwood, 
    tao_file_word_tu_html, 
    xuat_bang_html_ra_csv, 
    xoa_dau_tieng_viet
)
from modules.keyword_matrix import goi_y_goc_nhin_tu_khoa_ve_tinh, BO_32_CLUSTER_HWOOD
from modules.chat_advisor import lay_noi_dung_quy_chuan_cho_prompt
from modules.wordpress_api import dang_bai_len_wordpress
from modules.media_planner import (
    tao_ke_hoach_media_seo,
    xuat_csv_ke_hoach_media,
    chen_anh_that_vao_html,
    tao_bang_html_ke_hoach_media,
    tao_preview_co_khung_vi_tri_anh
)


def render_soan_thao_thu_cong(ket_noi_wp, wp_site_url, royal_api_key, wp_username):
    """Khu vực tự soạn thảo thủ công, dán mã HTML, xem trước trực quan và lưu vào lịch sử bài viết"""
    st.markdown("""
    <div style="background-color: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 14px 18px; margin-bottom: 15px;">
        <b style="color: #1e293b; font-size: 1.05rem;">✍️ Không Gian Tự Soạn Thảo & Dán Mã HTML Thủ Công</b>
        <div style="color: #475569; font-size: 0.9rem; margin-top: 3px;">
            Dán mã HTML từ WordPress, Google Docs hoặc công cụ khác vào ô bên trái để <b>hiển thị giao diện thực tế trực quan ở ô bên phải</b>. Bạn có thể tự do chỉnh sửa, chuẩn hóa bảng HWOOD và bấm nút <b>Lưu Vào Lịch Sử Bài Viết</b> bất cứ lúc nào!
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Nút nạp nhanh từ AI hoặc xóa trắng
    c_tool1, c_tool2, c_tool3 = st.columns([2, 1.2, 1.5])
    with c_tool1:
        if st.session_state.get("noi_dung_bai_viet"):
            if st.button("📥 Nạp nội dung đang có từ Trợ lý AI vào đây để sửa tay", key="btn_pull_ai_to_manual", use_container_width=True):
                st.session_state["manual_html"] = st.session_state.noi_dung_bai_viet
                st.session_state["manual_kw"] = st.session_state.get("tu_khoa_hien_tai", "")
                st.session_state["manual_title"] = st.session_state.get("meta_title", "")
                st.session_state["manual_desc"] = st.session_state.get("meta_desc", "")
                st.toast("Đã nạp toàn bộ bài viết từ Trợ lý AI sang ô soạn thảo!", icon="📥")
                st.rerun()
    with c_tool2:
        if st.button("🗑️ Xóa trắng để viết mới", key="btn_clear_manual", use_container_width=True):
            st.session_state["manual_html"] = ""
            st.session_state["manual_kw"] = ""
            st.session_state["manual_title"] = ""
            st.session_state["manual_desc"] = ""
            st.session_state["manual_slug"] = ""
            st.toast("Đã làm sạch ô soạn thảo!", icon="🧹")
            st.rerun()
    with c_tool3:
        boc_cuc_opt = st.radio("Bố cục:", ["2 Cột Song Song", "Toàn Màn Hình"], horizontal=True, key="rd_layout_manual")

    # 1. Khối thông tin SEO
    col_k1, col_k2, col_k3 = st.columns([1.5, 2.3, 1.2])
    with col_k1:
        manual_kw = st.text_input(
            "📌 Cụm từ khóa chính (Focus Keyword):",
            value=st.session_state.get("manual_kw", ""),
            placeholder="Ví dụ: Bàn ghế sân vườn ngoài trời...",
            key="input_manual_kw"
        )
        if manual_kw != st.session_state.get("manual_kw"):
            st.session_state["manual_kw"] = manual_kw
    with col_k2:
        cur_title = st.session_state.get("manual_title", "")
        manual_title = st.text_input(
            f"🏷️ Tiêu đề bài viết (Title Tag - {len(cur_title)}/60 ký tự):",
            value=cur_title,
            placeholder="Tiêu đề chuẩn SEO chứa từ khóa chính ở đầu...",
            key="input_manual_title"
        )
        if manual_title != cur_title:
            st.session_state["manual_title"] = manual_title
    with col_k3:
        def_slug = re.sub(r'[^a-z0-9\-]+', '-', xoa_dau_tieng_viet(manual_kw or manual_title)).strip('-')
        manual_slug = st.text_input(
            "🔗 Slug URL đề xuất:",
            value=st.session_state.get("manual_slug", def_slug),
            placeholder="ban-ghe-san-vuon...",
            key="input_manual_slug"
        )
        if manual_slug != st.session_state.get("manual_slug"):
            st.session_state["manual_slug"] = manual_slug

    cur_desc = st.session_state.get("manual_desc", "")
    manual_desc = st.text_area(
        f"📝 Thẻ mô tả (Meta Description - {len(cur_desc)}/155 ký tự - Khuyến nghị 140-155 ký tự để đèn xanh Yoast SEO):",
        value=cur_desc,
        height=68,
        placeholder="Đoạn trích dẫn hấp dẫn chứa từ khóa chính tự nhiên và lời kêu gọi hành động (CTA)...",
        key="input_manual_desc"
    )
    if manual_desc != cur_desc:
        st.session_state["manual_desc"] = manual_desc

    st.markdown("---")

    # 2. Hai cột: Cột trái dán mã HTML - Cột phải hiển thị giao diện
    noi_dung_hien_tai = st.session_state.get("manual_html", "")

    if boc_cuc_opt == "2 Cột Song Song":
        col_code, col_view = st.columns([1.05, 0.95])
    else:
        col_code = st.container()
        col_view = st.container()

    with col_code:
        st.markdown("#### 📋 1. Ô Dán Mã HTML / Tự Soạn Thảo:")
        manual_html_input = st.text_area(
            "Mã HTML bài viết:",
            value=noi_dung_hien_tai,
            height=600 if boc_cuc_opt == "2 Cột Song Song" else 350,
            key="txt_area_manual_code",
            placeholder="""<h2>Mục Lục Bài Viết</h2>\n<p>Dán mã HTML hoặc tự gõ câu từ tại đây...</p>\n<table>\n  <tr><th>Tiêu chí</th><th>Thông số</th></tr>\n  <tr><td>Chất liệu</td><td>HDPE + Gỗ</td></tr>\n</table>""",
            label_visibility="collapsed"
        )
        if manual_html_input != noi_dung_hien_tai:
            st.session_state["manual_html"] = manual_html_input
            noi_dung_hien_tai = manual_html_input

        # Các nút tiện ích cho mã HTML
        c_ut1, c_ut2 = st.columns(2)
        with c_ut1:
            if st.button("🎨 Chuẩn Hóa Bảng HWOOD (#2e7d32)", key="btn_manual_format_table", use_container_width=True, help="Tự động biến tất cả thẻ <table> thành bảng màu xanh HWOOD chuẩn, chữ trắng, xen kẽ dòng và in đậm tiêu chí."):
                formatted_html = chuan_hoa_bang_html_hwood(noi_dung_hien_tai)
                st.session_state["manual_html"] = formatted_html
                st.toast("🎉 Đã chuẩn hóa toàn bộ bảng sang giao diện Forest Green #2e7d32!", icon="🎨")
                st.rerun()
        with c_ut2:
            if st.button("🧹 Làm Sạch Mã (Bỏ ký tự lạ, dọn rác)", key="btn_manual_clean_html", use_container_width=True):
                cleaned_html = noi_dung_hien_tai.replace("\u00a0", " ").replace("&nbsp;", " ")
                cleaned_html = re.sub(r'<p>\s*</p>', '', cleaned_html)
                cleaned_html = re.sub(r'<h3\s*>\s*</h3>', '', cleaned_html)
                st.session_state["manual_html"] = cleaned_html
                st.toast("🧹 Đã làm sạch mã HTML!", icon="✨")
                st.rerun()

        with st.expander("➕ Chèn Nhanh Các Mẫu Đoạn Mã Chuẩn HWOOD Vào Bài", expanded=False):
            st.caption("Bấm nút để tự động nối thêm mẫu HTML vào cuối bài viết của bạn:")
            c_tpl1, c_tpl2 = st.columns(2)
            with c_tpl1:
                if st.button("➕ Thêm Mẫu Bảng So Sánh HWOOD", key="btn_tpl_table", use_container_width=True):
                    tpl = """\n<div style="overflow-x: auto; margin: 18px 0;">\n<table style="width: 100%; border-collapse: collapse; border: 1px solid #333333; font-size: 15px;">\n<thead>\n<tr>\n  <th style="background-color: #2e7d32; color: #ffffff; font-weight: 700; padding: 12px 10px; border: 1px solid #1b5e20; text-align: center;">TIÊU CHÍ KỸ THUẬT</th>\n  <th style="background-color: #2e7d32; color: #ffffff; font-weight: 700; padding: 12px 10px; border: 1px solid #1b5e20; text-align: center;">DÒNG SẢN PHẨM 1</th>\n  <th style="background-color: #2e7d32; color: #ffffff; font-weight: 700; padding: 12px 10px; border: 1px solid #1b5e20; text-align: center;">DÒNG SẢN PHẨM 2</th>\n</tr>\n</thead>\n<tbody>\n<tr>\n  <td style="padding: 10px; border: 1px solid #cccccc; color: #1a2e22; font-weight: 700; background-color: #f8fafc;">Cấu tạo & Bề mặt</td>\n  <td style="padding: 10px; border: 1px solid #cccccc; color: #222222; background-color: #ffffff;">Thông số dòng 1</td>\n  <td style="padding: 10px; border: 1px solid #cccccc; color: #222222; background-color: #ffffff;">Thông số dòng 2</td>\n</tr>\n<tr>\n  <td style="padding: 10px; border: 1px solid #cccccc; color: #1a2e22; font-weight: 700; background-color: #f8fafc;">Đơn giá (VAT 8%)</td>\n  <td style="padding: 10px; border: 1px solid #cccccc; color: #222222; background-color: #f2f6f3;">Đơn giá 1</td>\n  <td style="padding: 10px; border: 1px solid #cccccc; color: #222222; background-color: #f2f6f3;">Đơn giá 2</td>\n</tr>\n</tbody>\n</table>\n</div>\n"""
                    st.session_state["manual_html"] = noi_dung_hien_tai + tpl
                    st.toast("Đã chèn mẫu bảng!", icon="➕")
                    st.rerun()
                if st.button("➕ Thêm Khối Trả Lời Nhanh (GEO)", key="btn_tpl_quick", use_container_width=True):
                    tpl = """\n<div style="background-color: #f3f8f1; border-left: 4px solid #2e7d32; padding: 14px 18px; margin: 16px 0; border-radius: 6px;">\n<p style="margin: 0; color: #1a2e22; font-size: 1.02rem;"><strong>Trả lời nhanh:</strong> [Tóm tắt trực diện cấu tạo, đơn giá hoặc câu trả lời dưới 60 từ để AI Search dễ trích dẫn nguồn hwood.vn]</p>\n</div>\n"""
                    st.session_state["manual_html"] = noi_dung_hien_tai + tpl
                    st.toast("Đã chèn khối Trả lời nhanh!", icon="➕")
                    st.rerun()
            with c_tpl2:
                if st.button("➕ Thêm Khối CTA Zalo & Hotline", key="btn_tpl_cta", use_container_width=True):
                    tpl = """\n<div style="background-color: #f3f8f1; border: 1.5px solid #2e7d32; border-radius: 8px; padding: 22px; margin-top: 35px; text-align: center;">\n  <h3 style="color: #2e7d32; margin-top: 0; font-size: 1.3rem; font-weight: 700;">HWOOD VIỆT NAM - TỔNG KHO VẬT LIỆU NỘI & NGOẠI THẤT CAO CẤP</h3>\n  <p style="margin: 8px 0; color: #555;"><em>"Save Tree, Beautify Home!" - Đồng hành cùng các siêu dự án Landmark 81, Novaworld Phan Thiết, Vinpearl Phú Quốc.</em></p>\n  <p style="margin: 6px 0;"><b>Trụ sở chính:</b> 148/72 Đường Trường Lưu, Phường Long Trường, Thành Phố Hồ Chí Minh</p>\n  <p style="margin: 6px 0; font-size: 1.15rem; font-weight: bold; color: #2e7d32;">Hotline / Zalo tư vấn & Báo giá nhanh: 0912 565 353 - 0919 741 080</p>\n  <p style="margin: 6px 0; font-size: 1rem; color: #333;"><b>Email:</b> sales@hwood.vn | <b>Website:</b> hwood.vn</p>\n  <p style="margin: 4px 0; font-size: 0.95rem; color: #666;">(Chính sách: Miễn phí vận chuyển bán kính ≤ 25km tại TP.HCM cho đơn từ 25 triệu chưa VAT - Cung cấp bộ mẫu sản phẩm miễn phí toàn quốc - Bảo hành 5 năm dòng HWOOD và 1 năm dòng TENOWOOD)</p>\n  <div style="margin-top: 15px;">\n    <a href="https://zalo.me/0912565353" target="_blank" style="display: inline-block; background-color: #0068ff; color: #ffffff !important; font-weight: bold; padding: 12px 28px; border-radius: 6px; text-decoration: none; font-size: 1rem; box-shadow: 0 2px 6px rgba(0,104,255,0.3);">💬 Nhận Tư Vấn Kỹ Thuật & Báo Giá Qua Zalo (0912 565 353)</a>\n  </div>\n</div>\n"""
                    st.session_state["manual_html"] = noi_dung_hien_tai + tpl
                    st.toast("Đã chèn khối CTA chốt đơn!", icon="➕")
                    st.rerun()
                if st.button("➕ Thêm Khung FAQ Schema JSON-LD", key="btn_tpl_faq", use_container_width=True):
                    tpl = """\n<script type="application/ld+json">\n{\n  "@context": "https://schema.org",\n  "@type": "FAQPage",\n  "mainEntity": [\n    {\n      "@type": "Question",\n      "name": "Câu hỏi thường gặp 1?",\n      "acceptedAnswer": {\n        "@type": "Answer",\n        "text": "Câu trả lời ngắn gọn dưới 50 từ chính xác chuẩn HWOOD."\n      }\n    }\n  ]\n}\n</script>\n"""
                    st.session_state["manual_html"] = noi_dung_hien_tai + tpl
                    st.toast("Đã chèn khung FAQ Schema!", icon="➕")
                    st.rerun()

    with col_view:
        # Thống kê nhanh chỉ số bài viết
        so_tu_m = len(re.findall(r'\b\w+\b', re.sub(r'<[^>]*>', ' ', noi_dung_hien_tai)))
        so_h2_m = len(re.findall(r'<h2\b', noi_dung_hien_tai, re.I))
        so_h3_m = len(re.findall(r'<h3\b', noi_dung_hien_tai, re.I))
        so_bang_m = len(re.findall(r'<table\b', noi_dung_hien_tai, re.I))
        so_anh_m = len(re.findall(r'<img\b|<figure\b', noi_dung_hien_tai, re.I))

        st.markdown(f"#### 👁️ 2. Giao Diện Hiển Thị Thực Tế (Live Preview):")
        st.markdown(f"""
        <div style="display: flex; gap: 12px; font-size: 0.88rem; background: #f0fdf4; border: 1px solid #bbf7d0; padding: 6px 12px; border-radius: 6px; margin-bottom: 8px;">
            <span>📝 <b>{so_tu_m:,}</b> từ</span>
            <span>📑 <b>{so_h2_m}</b> thẻ H2</span>
            <span>📌 <b>{so_h3_m}</b> thẻ H3</span>
            <span>📊 <b>{so_bang_m}</b> bảng</span>
            <span>🖼️ <b>{so_anh_m}</b> ảnh</span>
        </div>
        """, unsafe_allow_html=True)

        if not noi_dung_hien_tai.strip():
            st.info("👈 Hãy dán mã HTML hoặc tự gõ câu từ vào ô bên trái để xem giao diện thực tế hiển thị ngay tại đây!")
        else:
            preview_clean_m = chuan_hoa_bang_html_hwood(noi_dung_hien_tai)
            preview_html_m = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.7; color: #222; max-width: 900px; margin: 0 auto; padding: 18px; border: 1.5px solid #e2e8f0; border-radius: 8px; background: #ffffff; box-shadow: 0 1px 4px rgba(0,0,0,0.05);">
                {preview_clean_m}
            </div>
            """
            components.html(preview_html_m, height=560 if boc_cuc_opt == "2 Cột Song Song" else 750, scrolling=True)

    st.markdown("---")

    # 3. Hàng nút Lưu vào lịch sử & xuất file
    st.markdown("#### 💾 Thao Tác Bài Viết:")
    btn_m1, btn_m2, btn_m3, btn_m4, btn_m5 = st.columns([1.8, 1.6, 1.3, 1.3, 1.8])

    with btn_m1:
        if st.button("💾 Lưu Vào Lịch Sử Bài Viết", key="btn_manual_save_history", type="primary", use_container_width=True, help="Lưu ngay bài viết này vào thư mục lịch sử bài viết (Tab 📚 Lịch Sử Bài Lưu)"):
            if not noi_dung_hien_tai.strip():
                st.warning("⚠️ Bài viết đang trống, vui lòng nhập nội dung trước khi lưu!")
            else:
                kw_to_save = manual_kw.strip() or manual_title.strip() or "Bài viết thủ công"
                title_to_save = manual_title.strip() or f"{kw_to_save} | HWOOD"
                desc_to_save = manual_desc.strip() or f"Bài viết {kw_to_save} chính hãng HWOOD VIỆT NAM."
                ok_save = luu_bai_viet_lich_su(
                    tu_khoa=kw_to_save,
                    noi_dung=noi_dung_hien_tai,
                    meta_title=title_to_save,
                    meta_desc=desc_to_save,
                    gop_y_note="✍️ Tự soạn thảo / Dán mã HTML thủ công"
                )
                if ok_save:
                    st.toast("🎉 Đã lưu bài viết vào Lịch sử thành công!", icon="💾")
                    st.success(f"🎉 **Đã lưu thành công bài viết `{kw_to_save}` vào Lịch sử!** Bạn có thể xem lại hoặc mở lại bất cứ lúc nào ở Tab **📚 Lịch Sử Bài Lưu**.")
                else:
                    st.error("❌ Không thể lưu vào file lịch sử. Vui lòng thử lại!")

    with btn_m2:
        if st.button("📥 Nạp Sang Bộ Nhớ Tab 1", key="btn_manual_push_to_tab1", use_container_width=True, help="Chuyển bài viết này sang làm nội dung chính của Tab 1 để dùng tiếp Trợ lý AI, Media Planner..."):
            if not noi_dung_hien_tai.strip():
                st.warning("⚠️ Bài viết đang trống!")
            else:
                st.session_state.noi_dung_bai_viet = noi_dung_hien_tai
                st.session_state.tu_khoa_hien_tai = manual_kw.strip() or manual_title.strip()
                st.session_state.meta_title = manual_title.strip()
                st.session_state.meta_desc = manual_desc.strip()
                st.toast("🎉 Đã nạp thành công bài viết sang Trợ lý AI!", icon="📥")
                st.success("🎉 Đã nạp bài viết sang Trợ lý AI! Bạn có thể chuyển qua tab 'Trợ Lý AI Viết Bài' để xem hoặc tinh chỉnh thêm.")

    with btn_m3:
        if noi_dung_hien_tai.strip():
            try:
                docx_buf = tao_file_word_tu_html(
                    html_str=noi_dung_hien_tai,
                    title=manual_title or manual_kw or "bai_viet_thu_cong",
                    meta_title=manual_title,
                    meta_desc=manual_desc,
                    focus_kw=manual_kw
                )
                st.download_button(
                    label="📄 Tải File Word (.docx)",
                    data=docx_buf,
                    file_name=f"bai_viet_{manual_slug or 'thu_cong'}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="btn_manual_download_docx"
                )
            except Exception as e_d:
                st.button("📄 Lỗi File Word", disabled=True, use_container_width=True)
        else:
            st.button("📄 Tải File Word", disabled=True, use_container_width=True)

    with btn_m4:
        if noi_dung_hien_tai.strip():
            st.download_button(
                label="🌐 Tải File HTML (.html)",
                data=noi_dung_hien_tai,
                file_name=f"bai_viet_{manual_slug or 'thu_cong'}.html",
                mime="text/html",
                use_container_width=True,
                key="btn_manual_download_html"
            )
        else:
            st.button("🌐 Tải File HTML", disabled=True, use_container_width=True)

    with btn_m5:
        if ket_noi_wp and wp_site_url and royal_api_key and noi_dung_hien_tai.strip():
            if st.button("🚀 Đăng Bản Nháp Lên WP", key="btn_manual_post_wp", use_container_width=True):
                try:
                    with st.spinner("Đang gửi bài viết thủ công lên WordPress..."):
                        thanh_cong, ket_qua = dang_bai_len_wordpress(
                            site_url=wp_site_url,
                            title=manual_title or manual_kw or "Bài viết thủ công",
                            content=noi_dung_hien_tai,
                            status="draft",
                            wp_username=wp_username,
                            api_key=royal_api_key,
                            focus_kw=manual_kw,
                            meta_title=manual_title,
                            meta_desc=manual_desc,
                            slug=manual_slug
                        )
                        if thanh_cong:
                            pid = ket_qua.get('id', '')
                            plink = ket_qua.get('link', '')
                            st.success(f"🎉 Đã đăng bản nháp lên WordPress thành công! (ID: {pid})")
                            if plink:
                                st.markdown(f"👉 [Xem bài nháp trên WordPress]({plink})")
                        else:
                            st.error(f"Lỗi đăng bài lên WordPress: {ket_qua}")
                except Exception as ex_p:
                    st.error(f"Lỗi kết nối WordPress: {ex_p}")
        else:
            st.button("🚀 Đăng Bản Nháp Lên WP", disabled=True, use_container_width=True, help="Yêu cầu kết nối WordPress và có nội dung bài viết")


def render_tab1(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, danh_sach_bai_viet_wp=None, wp_username="", **kwargs):
    """Giao diện Tab 1: Viết bài mới chuẩn SEO, xem trước, sửa nhanh bằng tay & góp ý tinh chỉnh bằng AI"""
    wp_username = wp_username or kwargs.get("wp_username") or st.session_state.get("wp_username", "hwoodhplus@gmail.com")
    royal_api_key = royal_api_key or kwargs.get("royal_api_key") or st.session_state.get("wp_app_pass", "Wh7M rPPJ Dp4j UxP5 52HR LEU0")

    tab_ai_writer, tab_manual_writer = st.tabs([
        "🤖 Trợ Lý AI Viết Bài Chuẩn SEO", 
        "✍️ Tự Viết Tay / Dán Mã HTML & Xem Trước"
    ])

    with tab_ai_writer:
        if st.session_state.get("bai_duoc_chuyen_sang_tab1"):
            st.success(f"🚀 **Đang nạp bài viết từ Kế Hoạch Nội Dung Tháng:** `{st.session_state.bai_duoc_chuyen_sang_tab1}`. Từ khóa chính và Định dạng bài viết đã được tự động nạp sẵn. Bạn có thể kiểm tra lại và bấm **Tạo Bài Viết** bên dưới!")

        col_kw, col_type, col_len = st.columns([2.2, 1.8, 1.2])
        with col_kw:
            tu_khoa = st.text_input(
                "Nhập từ khóa SEO hoặc chủ đề cần viết bài mới:",
                value=st.session_state.get("tu_khoa_hien_tai", ""),
                placeholder="Ví dụ: Bàn ghế sân vườn ngoài trời, Sàn gỗ hồ bơi Hwood, Lam sóng ốp tường..."
            )
            if tu_khoa != st.session_state.get("tu_khoa_hien_tai"):
                st.session_state.tu_khoa_hien_tai = tu_khoa
        with col_type:
            danh_sach_the_loai = [
                "🤖 Tự động nhận diện theo từ khóa (Mặc định)",
                "💰 Báo Giá (Price) + Bảng HTML kỹ thuật & VAT 8%",
                "⚖️ So Sánh (Comparison) - 2 hoặc 4 loại vật liệu",
                "🖼️ Mẫu & Thiết Kế (Gallery / Listicle) - Top mẫu đẹp xu hướng",
                "🛠️ Hướng Dẫn Kỹ Thuật (How-to) + Checklist thi công",
                "⭐ Review / Đánh Giá Thực Tế + Giải đáp thắc mắc Q&A",
                "🎯 Hướng Dẫn Chọn Mua + Kỹ thuật mã hàng",
                "🏡 Giải Pháp Ứng Dụng & Case Study theo không gian",
                "📖 Định Nghĩa & Giải Thích (Define) + Báo giá cơ bản"
            ]
            idx_the_loai = 0
            if st.session_state.get("the_loai_duoc_chon") in danh_sach_the_loai:
                idx_the_loai = danh_sach_the_loai.index(st.session_state.the_loai_duoc_chon)

            the_loai_bai = st.selectbox(
                "Định dạng bài viết (Search Intent):",
                options=danh_sach_the_loai,
                index=idx_the_loai,
                key="select_the_loai_bai"
            )
        with col_len:
            do_dai_bai = st.selectbox(
                "Độ dài bài viết:",
                options=["Tiêu chuẩn SEO (1.300 - 1.600 từ)", "Chuyên sâu / Pillar (1.800 - 2.200 từ)", "Ngắn gọn / Tư vấn (800 - 1.000 từ)"],
                key="select_do_dai"
            )

        with st.expander("⭐ Chọn nhanh từ bộ 32 Cụm Từ Khóa Cốt Lõi HWOOD (Đã kèm sẵn từ khóa phụ)", expanded=False):
            st.markdown("Chọn 1 chủ đề bất kỳ dưới đây để tự động nạp **Từ Khóa Chính** và **Bộ Từ Khóa Phụ LSI** chuẩn SEO:")
            col_c32_1, col_c32_2 = st.columns([3, 1])
            with col_c32_1:
                c32_options = list(BO_32_CLUSTER_HWOOD.keys())
                chon_c32 = st.selectbox("Danh sách 32 cụm từ khóa chuẩn:", options=c32_options, key="sb_chon_32_clusters")
                sec_kws_c32 = BO_32_CLUSTER_HWOOD.get(chon_c32, [])
                sec_tags_c32 = " ".join([f"`{s}`" for s in sec_kws_c32])
                st.markdown(f"📎 **Từ khóa phụ đi kèm:** {sec_tags_c32}")
            with col_c32_2:
                st.write("")
                st.write("")
                if st.button("🎯 Nạp Từ Khóa Này Để Viết", key="btn_apply_c32", use_container_width=True):
                    st.session_state.tu_khoa_hien_tai = chon_c32
                    st.toast(f"Đã chọn: {chon_c32}", icon="🎯")
                    st.rerun()

        # Rà soát từ khóa & Tự động đề xuất các góc nhìn vệ tinh (Topic Cluster)
        bai_viet_trung = []
        danh_sach_goc_nhin = []
        if tu_khoa.strip():
            bai_viet_trung, danh_sach_goc_nhin = goi_y_goc_nhin_tu_khoa_ve_tinh(tu_khoa, danh_sach_bai_viet_wp)

            if bai_viet_trung:
                with st.container():
                    st.warning(f"⚠️ **TỪ KHÓA NÀY ĐÃ CÓ BÀI TRÊN WEBSITE:** Phát hiện **{len(bai_viet_trung)} bài viết** đã có trên `hwood.vn`:")
                    for b in bai_viet_trung[:3]:
                        t_wp = b.get("title", {}).get("rendered", "")
                        l_wp = b.get("link", "")
                        st.markdown(f"- 🔗 [{t_wp}]({l_wp})")

                    st.markdown("""
                    <div style="background-color: #f0fdf4; border: 1.5px solid #86efac; border-radius: 8px; padding: 14px; margin: 10px 0;">
                        <b style="color: #166534; font-size: 1.02rem;">🎯 CHIẾN LƯỢC TOPIC CLUSTER: Chọn 1 Keyword Vệ Tinh làm Từ Khóa Chính</b>
                        <div style="color: #374151; font-size: 0.88rem; margin-top: 3px;">
                            Để không bị <b>ăn thịt từ khóa (Cannibalization)</b> và giúp HWOOD thống trị trọn bộ trang 1 Google, hãy bấm <b>chọn 1 góc nhìn chuyên sâu bên dưới</b> để làm Từ Khóa Chính cho bài mới:
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    for idx, g in enumerate(danh_sach_goc_nhin):
                        c_g1, c_g2 = st.columns([3.5, 1])
                        with c_g1:
                            st.markdown(f"**{g['intent']}** — `{g['status_badge']}`")
                            st.markdown(f"👉 **Từ khóa mới:** `<span style='color: #15803d; font-weight: bold;'>{g['tu_khoa_moi']}</span>`", unsafe_allow_html=True)
                            st.caption(f"Tiêu đề chuẩn SEO đề xuất: *{g['tieu_de_de_xuat']}* ({g['mo_ta_intent']})")
                        with c_g2:
                            st.write("")
                            if st.button("🎯 Chọn Góc Này", key=f"btn_pick_dup_angle_{idx}", use_container_width=True):
                                st.session_state.tu_khoa_hien_tai = g['tu_khoa_moi']
                                st.toast(f"Đã chọn từ khóa: {g['tu_khoa_moi']}!", icon="🎯")
                                st.rerun()
                        st.markdown("<hr style='margin: 4px 0; border: 0.5px dashed #bbf7d0;'>", unsafe_allow_html=True)

            elif danh_sach_goc_nhin:
                with st.expander(f"💡 Gợi ý các góc nhìn vệ tinh (Satellite Keywords) xoay quanh '{tu_khoa}'", expanded=False):
                    st.markdown("Bạn có thể viết bài này hoặc chọn các từ khóa ngách xoay quanh chủ đề này để mở rộng cụm bài viết Topic Cluster:")
                    for idx, g in enumerate(danh_sach_goc_nhin):
                        c_g1, c_g2 = st.columns([3.5, 1])
                        with c_g1:
                            st.markdown(f"**{g['intent']}** | `{g['status_badge']}`")
                            st.markdown(f"👉 **{g['tu_khoa_moi']}** — *{g['tieu_de_de_xuat']}*")
                        with c_g2:
                            st.write("")
                            if st.button("🎯 Chọn Từ Khóa Này", key=f"btn_pick_sub_angle_{idx}", use_container_width=True):
                                st.session_state.tu_khoa_hien_tai = g['tu_khoa_moi']
                                st.toast(f"Đã chọn từ khóa: {g['tu_khoa_moi']}!", icon="🎯")
                                st.rerun()
                        st.markdown("<hr style='margin: 4px 0; border: 0.5px dashed #eee;'>", unsafe_allow_html=True)

        col_btn_vb1, col_btn_vb2 = st.columns([1.6, 1.2])
        with col_btn_vb1:
            nut_viet_bai = st.button("🚀 Bắt đầu viết bài bằng AI", type="primary", use_container_width=True)
        with col_btn_vb2:
            toi_uu_token = st.checkbox(
                "⚡ Bật Skill Tiết Kiệm Token (Giảm ~65%)",
                value=st.session_state.get("toi_uu_token_active", True),
                key="cb_toi_uu_token_tab1",
                help="Sử dụng Knowledge Graph Prompt Optimizer để tinh gọn thông số, bảng giá VAT 8% và quy chuẩn cốt lõi, giảm chi phí token từ ~5.000 xuống ~1.400 token/bài."
            )
            st.session_state["toi_uu_token_active"] = toi_uu_token

        # Tự động kích hoạt viết bài nếu được chuyển từ Kế Hoạch Tháng
        auto_viet = st.session_state.pop("tu_dong_viet_bai", False)
        if auto_viet and tu_khoa.strip() and api_key:
            nut_viet_bai = True

        with st.expander("📥 Hoặc Dán Mã HTML Bài Viết Có Sẵn (Từ website / file ngoài) để hiển thị & sửa bài:", expanded=False):
            st.markdown("Nếu bạn đã có sẵn bài viết từ website `hwood.vn`, CMS WordPress hoặc file HTML riêng, hãy dán mã HTML vào đây để hệ thống hiển thị bài ra ngay:")
            c_p1, c_p2 = st.columns([2.5, 1])
            with c_p1:
                dan_tieu_de = st.text_input("Tiêu đề hoặc từ khóa bài viết:", placeholder="Ví dụ: Bàn Ghế Sân Vườn Ngoài Trời Polywood...", key="input_dan_tieu_de_tab1")
            with c_p2:
                st.write("")
                st.caption("💡 Tự động nhận diện tiêu đề từ thẻ Heading nếu để trống")
            
            dan_html = st.text_area(
                "Dán toàn bộ mã HTML bài viết vào đây:",
                height=200,
                placeholder="<h2>1. Giới thiệu vật liệu gỗ nhựa HWOOD...</h2>\n<p>Nội dung bài viết...</p>",
                key="txt_dan_html_tab1"
            )
            if st.button("👁️ Nạp & Hiển Thị Bài Viết Này Để Sửa", type="primary", key="btn_nap_html_tab1"):
                if not dan_html.strip():
                    st.warning("⚠️ Vui lòng dán mã HTML bài viết!")
                else:
                    tk_nap = dan_tieu_de.strip()
                    if not tk_nap:
                        h_match = re.search(r'<h[12][^>]*>(.*?)</h[12]>', dan_html, re.I)
                        if h_match:
                            tk_nap = re.sub(r'<[^>]*>', '', h_match.group(1)).strip()
                        else:
                            tk_nap = "Bài Viết Nạp Từ HTML"
                    st.session_state.noi_dung_bai_viet = dan_html.strip()
                    st.session_state.tu_khoa_hien_tai = tk_nap
                    st.session_state.meta_title = f"{tk_nap} - HWOOD VIỆT NAM"[:65]
                    st.session_state.meta_desc = f"Khám phá các mẫu {tk_nap.lower()} chính hãng HWOOD VIỆT NAM. Hotline tư vấn: 0912 565 353."[:160]
                    st.session_state.bai_duoc_chuyen_sang_tab1 = tk_nap
                    luu_bai_viet_lich_su(tk_nap, dan_html.strip(), st.session_state.meta_title, st.session_state.meta_desc, gop_y_note="Nạp từ mã HTML bên ngoài")
                    st.toast("🎉 Đã nạp bài viết và hiển thị thành công!", icon="✅")
                    st.rerun()

        if nut_viet_bai:
            if not api_key:
                st.error("⚠️ Vui lòng nhập DeepSeek API Key ở thanh bên trái trước khi bắt đầu!")
            elif not tu_khoa.strip():
                st.warning("⚠️ Vui lòng nhập từ khóa hoặc chủ đề cần viết bài!")
            else:
                with st.spinner("🤖 Trợ lý AI đang nghiên cứu dữ liệu chuyên sâu HWOOD và viết bài (Tự động nối tiếp nếu bài dài)..."):
                    try:
                        kh_item = st.session_state.get("ke_hoach_item_dang_viet") or {}
                        tieu_de_kh = kh_item.get("tieu_de", "") or st.session_state.get("bai_duoc_chuyen_sang_tab1", "")
                        tu_khoa_phu_kh = kh_item.get("tu_khoa_phu", [])
                        ghi_chu_kh = kh_item.get("ghi_chu", "")
                        intent_kh = kh_item.get("search_intent", "")
                        cluster_kh = kh_item.get("cum_chu_de", "")

                        noi_dung_bai_viet, meta_title_auto, meta_desc_auto = tao_bai_viet_hwood_chuan_seo(
                            tu_khoa=tu_khoa.strip(),
                            the_loai_bai=the_loai_bai,
                            do_dai_bai=do_dai_bai,
                            api_key=api_key,
                            chon_model=chon_model,
                            danh_sach_bai_viet_wp=danh_sach_bai_viet_wp,
                            tieu_de=tieu_de_kh,
                            tu_khoa_phu=tu_khoa_phu_kh,
                            ghi_chu_chien_luoc=ghi_chu_kh,
                            search_intent=intent_kh,
                            cum_chu_de=cluster_kh,
                            toi_uu_token=toi_uu_token
                        )
                        st.session_state.noi_dung_bai_viet = noi_dung_bai_viet
                        st.session_state.tu_khoa_hien_tai = tu_khoa.strip()
                        st.session_state.meta_title = meta_title_auto
                        st.session_state.meta_desc = meta_desc_auto
                        st.session_state.bai_duoc_chuyen_sang_tab1 = None

                        if toi_uu_token:
                            st.success("🎉 Bài viết đã được tạo thành công! (⚡ Skill Tiết Kiệm Token: Đã giảm ~65% input tokens DeepSeek!)")
                        else:
                            st.success("🎉 Bài viết đã được tạo thành công và tự động lưu vào Lịch sử!")
                        st.rerun()

                    except Exception as e:
                        err_str = str(e)
                        if "402" in err_str or "insufficient_balance" in err_str.lower():
                            st.error("❌ **Hết số dư tài khoản DeepSeek (Error 402: Insufficient Balance):** Tài khoản API của bạn đã hết tiền. Vui lòng nạp thêm tiền tại [platform.deepseek.com](https://platform.deepseek.com) hoặc đổi API Key khác ở thanh bên trái!")
                        else:
                            st.error(f"❌ Đã xảy ra lỗi trong quá trình tạo bài viết: {e}")

        # Hiển thị bài viết nếu đã có nội dung
        if st.session_state.noi_dung_bai_viet:
            bai_viet = st.session_state.noi_dung_bai_viet
            tu_khoa_goc = st.session_state.tu_khoa_hien_tai
            so_tu = len(re.findall(r'\b\w+\b', re.sub(r'<[^>]*>', ' ', bai_viet)))
            so_h2 = len(re.findall(r'<h2\b', bai_viet, re.I))
            so_h3 = len(re.findall(r'<h3\b', bai_viet, re.I))
            so_anh = len(re.findall(r'<img\b|<figure\b', bai_viet, re.I))
            so_bang = len(re.findall(r'<table\b', bai_viet, re.I))

            st.markdown("### 📊 Thống kê chỉ số SEO bài viết:")
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            with c1:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{so_tu:,}</div><div class="metric-label">Tổng số từ</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{so_h2}</div><div class="metric-label">Thẻ Heading H2</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{so_h3}</div><div class="metric-label">Thẻ Heading H3</div></div>', unsafe_allow_html=True)
            with c4:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{so_anh}</div><div class="metric-label">Hình ảnh gợi ý</div></div>', unsafe_allow_html=True)
            with c5:
                st.markdown(f'<div class="metric-box"><div class="metric-value">{so_bang}</div><div class="metric-label">Bảng biểu kỹ thuật</div></div>', unsafe_allow_html=True)
            with c6:
                st.markdown(f'<div class="metric-box" style="border-left: 4px solid #16a34a;"><div class="metric-value" style="color: #16a34a;">⚡ -65%</div><div class="metric-label">Tiết Kiệm Token</div></div>', unsafe_allow_html=True)

            st.write("")
        
            # Tự động chuẩn hóa toàn bộ các bảng trong bài viết theo đúng giao diện Forest Green HWOOD (Hình 2)
            bai_viet = chuan_hoa_bang_html_hwood(bai_viet)
            st.session_state.noi_dung_bai_viet = bai_viet

            slug_clean = re.sub(r'[^a-z0-9\-]+', '-', xoa_dau_tieng_viet(tu_khoa_goc)).strip('-')

            # KHỐI BẢNG CẤU HÌNH YOAST SEO / RANK MATH (TỰ ĐỘNG ĐIỀN ĐẦY ĐỦ KHI ĐĂNG WP - THEO HÌNH 1)
            with st.expander("🎯 Bảng Cấu Hình Yoast SEO & Rank Math (Tự động điền đầy đủ vào WordPress khi Đăng)", expanded=True):
                st.markdown("""
                <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 10px 14px; margin-bottom: 12px; font-size: 0.88rem; color: #166534;">
                    ✅ <strong>Hệ thống tự động đồng bộ:</strong> Khi bạn bấm nút <strong>'Đăng Bản Nháp lên WP'</strong>, toàn bộ 4 trường thông tin chuẩn SEO dưới đây sẽ được <strong>tự động điền thẳng vào plugin Yoast SEO / Rank Math</strong> trên web mà bạn không cần phải copy dán thủ công!
                </div>
                """, unsafe_allow_html=True)
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.markdown("**📌 Cụm từ khóa chính (Focus Keyphrase):**")
                    st.code(tu_khoa_goc, language="text")
                    st.markdown(f"**🏷️ Tiêu đề SEO (Title Tag)** *({len(st.session_state.meta_title)} ký tự)*:")
                    st.code(st.session_state.meta_title, language="text")
                with col_m2:
                    st.markdown("**🔗 Đường dẫn đề xuất (Slug URL):**")
                    st.code(slug_clean, language="text")
                    st.markdown(f"**📝 Thẻ mô tả (Meta Description)** *({len(st.session_state.meta_desc)} ký tự)*:")
                    st.code(st.session_state.meta_desc, language="text")

            st.markdown("#### 📥 Xuất File Bài Viết & Thao Tác Nhanh:")
            btn_c1, btn_c2, btn_c3, btn_c4, btn_c5 = st.columns([1.3, 1.2, 1.2, 1.2, 1.6])
        
            with btn_c1:
                try:
                    docx_buffer = tao_file_word_tu_html(
                        html_str=bai_viet,
                        title=tu_khoa_goc,
                        meta_title=st.session_state.meta_title,
                        meta_desc=st.session_state.meta_desc,
                        focus_kw=tu_khoa_goc
                    )
                    st.download_button(
                        label="📄 Tải File Word (.docx)",
                        data=docx_buffer,
                        file_name=f"bai_viet_{slug_clean}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        help="Xuất bài viết sang Word (.docx) chuẩn hóa Headings, hộp Yoast SEO và bảng nền xanh chữ trắng."
                    )
                except Exception as ex_docx:
                    st.error(f"Lỗi tạo file Word: {ex_docx}")
        
            with btn_c2:
                st.download_button(
                    label="🌐 Tải File HTML (.html)",
                    data=bai_viet,
                    file_name=f"bai_viet_seo_{slug_clean}.html",
                    mime="text/html",
                    use_container_width=True,
                    help="Tải file HTML chuẩn UTF-8 để mở xem trên trình duyệt hoặc dán vào web."
                )

            with btn_c3:
                csv_tbl_data = xuat_bang_html_ra_csv(bai_viet)
                if csv_tbl_data:
                    st.download_button(
                        label="📊 Tải Bảng Excel (.csv)",
                        data=csv_tbl_data,
                        file_name=f"bang_du_lieu_{slug_clean}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        help="Trích xuất tất cả các bảng dữ liệu so sánh/báo giá sang file CSV/Excel UTF-8 có dấu."
                    )
                else:
                    st.button("📊 Không có bảng", disabled=True, use_container_width=True)

            with btn_c4:
                if st.button("💾 Lưu Lịch Sử Bài", key="btn_save_tab1", use_container_width=True):
                    luu_bai_viet_lich_su(tu_khoa_goc, bai_viet, st.session_state.meta_title, st.session_state.meta_desc)
                    st.toast("✅ Đã lưu bài viết vào Lịch sử thành công!", icon="💾")
                    st.rerun()

            with btn_c5:
                if ket_noi_wp and wp_site_url and royal_api_key:
                    if st.button("🚀 Đăng Bản Nháp Lên WP", key="btn_wp_tab1", type="primary", use_container_width=True):
                        try:
                            with st.spinner("Đang gửi bài viết và tự động điền Yoast SEO lên WordPress..."):
                                thanh_cong, ket_qua = dang_bai_len_wordpress(
                                    site_url=wp_site_url,
                                    title=tu_khoa_goc,
                                    content=bai_viet,
                                    status="draft",
                                    wp_username=wp_username,
                                    api_key=royal_api_key,
                                    focus_kw=tu_khoa_goc,
                                    meta_title=st.session_state.meta_title,
                                    meta_desc=st.session_state.meta_desc,
                                    slug=slug_clean
                                )
                                if thanh_cong:
                                    post_id = ket_qua.get('id', '')
                                    post_link = ket_qua.get('link', '')
                                    st.success(f"🎉 Đã đăng Bản Nháp lên WordPress thành công! (ID: {post_id})")
                                    if post_link:
                                        st.markdown(f"👉 [Xem bài nháp trên WordPress]({post_link})")
                                    st.info("💡 **Lưu ý Yoast SEO:** Hệ thống đã gửi kèm thông tin SEO. Nếu trang web của bạn chưa mở quyền ghi `meta` REST API cho Yoast, bạn chỉ cần xem bảng **🎯 Cấu hình Yoast SEO** ở trên, bấm nút Copy rồi dán trực tiếp vào ô tương ứng trên WordPress.")
                                else:
                                    st.error(f"Lỗi đăng bài lên WordPress: {ket_qua}")
                                    if "rest_cannot_create" in str(ket_qua) or "401" in str(ket_qua):
                                        st.warning("⚠️ **WordPress yêu cầu Tên đăng nhập WP + Mật khẩu ứng dụng** ở cột bên trái.")
                        except Exception as ex_post:
                            st.error(f"Lỗi kết nối WordPress: {ex_post}")

            # Nút hỗ trợ viết tiếp nếu bài bị dừng giữa chừng
            nut_viet_tiep = st.button("⏩ Viết tiếp đoạn còn thiếu (Nếu bài bị ngắt giữa chừng)", key="btn_cont_tab1", help="Nếu bài viết bị dừng giữa chừng do quá dài, bấm nút này để AI tự động viết tiếp hoàn chỉnh đến hết bài!")
            if nut_viet_tiep:
                if not api_key:
                    st.error("Thiếu API Key!")
                else:
                    with st.spinner("🤖 Đang viết tiếp phần còn thiếu và nối liền mạch... Vui lòng đợi vài giây!"):
                        try:
                            bai_viet_moi = viet_tiep_bai_dang_do(bai_viet, tu_khoa_goc, api_key, chon_model)
                            bai_viet_moi = chuan_hoa_bang_html_hwood(bai_viet_moi)
                            st.session_state.noi_dung_bai_viet = bai_viet_moi
                            luu_bai_viet_lich_su(tu_khoa_goc, bai_viet_moi, st.session_state.meta_title, st.session_state.meta_desc)
                            st.success("🎉 Đã viết tiếp và hoàn thiện 100% bài viết!")
                            st.rerun()
                        except Exception as e_cont:
                            st.error(f"Lỗi khi viết tiếp: {e_cont}")

            tab_sub_view, tab_sub_media, tab_sub_code, tab_sub_manual = st.tabs([
                "👁️ Xem Trước Giao Diện (Preview)", 
                "📸 Kế Hoạch Hình Ảnh & Video Chuẩn SEO",
                "📋 Mã Code HTML để Copy", 
                "✏️ Trình Sửa Nhanh Bằng Tay"
            ])

            with tab_sub_view:
                st.markdown("### Giao diện thực tế hiển thị trên website:")
                html_hien_thi = chuan_hoa_bang_html_hwood(bai_viet)

                preview_html = f"""
                <div style="font-family: Arial, sans-serif; line-height: 1.7; color: #333; max-width: 900px; margin: 0 auto;">
                    {html_hien_thi}
                </div>
                """
                components.html(preview_html, height=1200, scrolling=True)

            with tab_sub_media:
                st.markdown("### 📸 Bảng Kế Hoạch Hình Ảnh & Video Chuẩn SEO")
                st.markdown("""
                Hệ thống tự động phân tích cấu trúc bài viết và lập **Bảng Kế Hoạch Hình Ảnh & Video Chuẩn SEO**:
                * **Tên file ảnh chuẩn SEO:** Đã bỏ dấu tiếng Việt, nối bằng dấu gạch ngang `-`, chuẩn định dạng WebP siêu nhẹ.
                * **Thẻ Alt:** Chứa từ khóa thực thể tự nhiên, mô tả đúng hình ảnh để Google Images xếp hạng Top.
                * **Gợi ý góc chụp & bối cảnh:** Giúp đội ngũ Media/Thiết kế nắm rõ bố cục ảnh cần sản xuất.
                """)
            
                ds_media = tao_ke_hoach_media_seo(bai_viet, tu_khoa_goc)
            
                col_med_top1, col_med_top2 = st.columns([3, 1.4])
                with col_med_top1:
                    so_anh = sum(1 for m in ds_media if "video" not in m["loai_media"].lower())
                    so_vid = sum(1 for m in ds_media if "video" in m["loai_media"].lower())
                    st.info(f"💡 Đề xuất bài viết: **{so_anh} hình ảnh WebP chuẩn SEO** + **{so_vid} video thực tế** để tối ưu trải nghiệm đọc và giữ chân khách hàng!")
                with col_med_top2:
                    csv_media = xuat_csv_ke_hoach_media(ds_media)
                    st.download_button(
                        label="📊 Xuất Bảng Media Ra Excel (.csv)",
                        data=csv_media,
                        file_name=f"ke_hoach_media_{slug_clean}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                # HIỂN THỊ TRỰC TIẾP TOÀN BỘ BẢNG KẾ HOẠCH HÌNH ẢNH DẠNG GRID/TABLE
                st.markdown(tao_bang_html_ke_hoach_media(ds_media), unsafe_allow_html=True)
                
                # Hiển thị từng vị trí ảnh với giao diện mở rộng
                for m in ds_media:
                    st_idx = m["stt"]
                    v_tri = m["vi_tri"]
                    t_file = m["ten_file"]
                    t_alt = m["the_alt"]
                    l_media = m["loai_media"]
                    k_thuoc = m["kich_thuoc"]
                    y_tuong = m["y_tuong_chup"]
                    caption_txt = m["caption"]
                
                    with st.expander(f"**{v_tri}** ➔ `{t_file}`", expanded=True if st_idx <= 2 else False):
                        c_m1, c_m2 = st.columns([1.8, 2.2])
                        with c_m1:
                            st.markdown("**📁 Tên file chuẩn SEO (Đổi tên trước khi tải lên WP):**")
                            st.code(t_file, language="text")
                            st.markdown("**🏷️ Thẻ Alt (Alt Text) chuẩn SEO:**")
                            st.code(t_alt, language="text")
                            st.markdown(f"**📐 Loại & Kích thước đề xuất:** `{l_media}` ({k_thuoc})")
                        with c_m2:
                            st.markdown("**🎬 Gợi ý góc chụp / bối cảnh (Visual Brief):**")
                            st.info(y_tuong)
                            st.markdown("**📝 Chú thích hiển thị dưới hình (Caption):**")
                            st.caption(f"*{caption_txt}*")

                st.markdown("---")
                st.markdown("#### 🛠️ Công Cụ Chèn Nhanh Ảnh Thật Vào Bài Viết:")
                st.caption("Sau khi đã tải ảnh lên WordPress Media Library, bạn chỉ cần dán đường link ảnh vào đây để hệ thống tự chèn thẻ `<figure><img>` vào đúng vị trí bài viết:")
            
                c_in1, c_in2, c_in3 = st.columns([1.6, 2.4, 1])
                with c_in1:
                    opt_media_pos = st.selectbox(
                        "Chọn vị trí ảnh:",
                        options=[f"Ảnh {m['stt']}: {m['vi_tri']}" for m in ds_media],
                        key="sb_select_insert_media"
                    )
                with c_in2:
                    real_img_url = st.text_input(
                        "Link URL ảnh trên web:",
                        placeholder="https://hwood.vn/wp-content/uploads/2026/11/ten-anh.webp",
                        key="txt_real_img_url"
                    )
                with c_in3:
                    st.write("")
                    if st.button("🚀 Chèn Vào Bài", key="btn_apply_insert_img", use_container_width=True):
                        if real_img_url.strip():
                            sel_stt = int(opt_media_pos.split(":")[0].replace("Ảnh", "").strip())
                            updated_html = chen_anh_that_vao_html(
                                html_str=bai_viet,
                                vi_tri_stt=sel_stt,
                                url_anh=real_img_url.strip(),
                                ds_media=ds_media
                            )
                            st.session_state.noi_dung_bai_viet = updated_html
                            luu_bai_viet_lich_su(tu_khoa_goc, updated_html, st.session_state.meta_title, st.session_state.meta_desc)
                            st.toast("🎉 Đã chèn ảnh thật vào đúng vị trí!", icon="📸")
                            st.success("🎉 Đã chèn ảnh thành công! Bấm qua tab 'Xem Trước Giao Diện' để xem kết quả.")
                            st.rerun()
                        else:
                            st.warning("Vui lòng dán link URL ảnh trước!")

            with tab_sub_code:
                st.info("💡 Bạn có thể bấm vào biểu tượng Copy ở góc trên bên phải của khối code dưới đây để dán thẳng vào CMS.")
                st.code(bai_viet, language="html")

            with tab_sub_manual:
                st.info("💡 Bạn có thể chỉnh sửa câu từ hoặc **dán mã HTML mới** vào ô bên dưới. Bài viết sẽ được **hiển thị giao diện thực tế trực quan ngay bên dưới**!")
            
                noi_dung_sua_tay = st.text_area(
                    "Mã HTML bài viết (Chỉnh sửa hoặc dán mã mới vào đây):",
                    value=bai_viet,
                    height=450,
                    key="txt_area_manual_tab1"
                )
                col_smt1, col_smt2 = st.columns([1.5, 3])
                with col_smt1:
                    if st.button("💾 Lưu Thay Đổi Vào Bài Viết", type="primary", use_container_width=True, key="btn_save_manual_tab1"):
                        st.session_state.noi_dung_bai_viet = noi_dung_sua_tay
                        luu_bai_viet_lich_su(tu_khoa_goc, noi_dung_sua_tay, st.session_state.meta_title, st.session_state.meta_desc, gop_y_note="Sửa trực tiếp bằng tay")
                        st.toast("🎉 Đã lưu bài viết thành công!", icon="✅")
                        st.success("🎉 Đã lưu bài viết thành công!")
                        st.rerun()
                with col_smt2:
                    st.caption(f"Độ dài mã HTML hiện tại: **{len(noi_dung_sua_tay):,} ký tự**")

                st.markdown("---")
                st.markdown("##### 👁️ Giao diện bài viết hiển thị thực tế (Live Preview theo mã HTML ở trên):")
                preview_manual_html = f"""
                <div style="font-family: Arial, sans-serif; line-height: 1.7; color: #333; max-width: 900px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 25px; background-color: #ffffff;">
                    {noi_dung_sua_tay}
                </div>
                """
                components.html(preview_manual_html, height=800, scrolling=True)

            st.markdown("---")
            st.markdown("### 💬 Góp ý & Tinh chỉnh bài viết bằng AI")
            st.markdown("Bạn có thể **copy dán nội dung góp ý** vào ô bên dưới, hoặc **tải lên file đính kèm** (Hình ảnh mẫu thiết kế/chụp màn hình, bảng giá, file Word `.docx`, PDF, file text).")
        
            che_do_sua_tab1 = st.radio(
                "🎯 Chọn chế độ sửa bài bằng AI:",
                options=[
                    "✨ Tự động thông minh (Khuyên dùng: Tự nhận diện sửa triệt để 100% nếu có danh sách nhiều lỗi, hoặc sửa cục bộ nếu chỉnh 1-2 vị trí)",
                    "🔄 Sửa toàn diện theo Checklist góp ý (Cam kết sửa đủ 100% mọi lỗi được liệt kê, không bỏ sót)",
                    "🎯 Sửa cục bộ: Chỉ thay thế 1-2 vị trí nhỏ (Bảo toàn 100% các đoạn khác)"
                ],
                index=0,
                key="radio_che_do_sua_tab1"
            )
            if "Tự động" in che_do_sua_tab1:
                che_do_param_tab1 = "tu_dong"
            elif "Sửa toàn diện" in che_do_sua_tab1:
                che_do_param_tab1 = "toan_bai"
            else:
                che_do_param_tab1 = "cuc_bo"

            col_gy1, col_gy2 = st.columns([1.5, 1])
            with col_gy1:
                gop_y_text = st.text_area(
                    "📝 Nhập hoặc dán nội dung góp ý cần sửa (Copy qua đây):",
                    placeholder="Ví dụ:\n- Thêm bảng báo giá bàn ghế sân vườn mới nhất 2026\n- Viết lại đoạn mở đầu cho lôi cuốn hơn\n- Sửa giá nan polywood trong bảng thành 1.250.000đ...",
                    height=140,
                    key="input_gop_y_tab1"
                )
            with col_gy2:
                file_dinh_kem_tab1 = st.file_uploader(
                    "📎 Đính kèm hình ảnh hoặc file góp ý:",
                    type=["png", "jpg", "jpeg", "webp", "docx", "pdf", "txt", "md"],
                    key="file_uploader_tab1",
                    help="Hỗ trợ ảnh chụp, file Word .docx, PDF hoặc file text"
                )
                if file_dinh_kem_tab1:
                    f_tab1_text, f_tab1_summary, f_tab1_b64 = doc_noi_dung_file_dinh_kem(file_dinh_kem_tab1)
                    st.success(f_tab1_summary)
                    if f_tab1_b64:
                        st.image(file_dinh_kem_tab1, caption=f"🖼️ Ảnh đính kèm: {file_dinh_kem_tab1.name}", width=200)

            nut_sua_bai = st.button("🚀 Gửi Góp Ý & Tinh Chỉnh Lại Bài Viết Bằng AI", type="primary", use_container_width=True, key="btn_sua_tab1")

            if nut_sua_bai:
                if not gop_y_text.strip() and not file_dinh_kem_tab1:
                    st.warning("⚠️ Vui lòng nhập nội dung góp ý hoặc đính kèm file/ảnh trước khi bấm sửa!")
                elif not api_key:
                    st.error("⚠️ Thiếu DeepSeek API Key trong thanh điều hướng bên trái!")
                else:
                    with st.spinner("🤖 Đang đọc góp ý, phân tích tài liệu và xử lý..."):
                        try:
                            f_tab1_text, _, f_tab1_b64 = doc_noi_dung_file_dinh_kem(file_dinh_kem_tab1) if file_dinh_kem_tab1 else ("", "", None)
                            edited_html, is_ok, msg_edit = thuc_hien_tinh_chinh_ai(
                                noi_dung_cu=st.session_state.noi_dung_bai_viet,
                                yeu_cau_text=gop_y_text,
                                file_text=f_tab1_text,
                                tu_khoa_bai=tu_khoa_goc,
                                api_key=api_key,
                                model_name=chon_model,
                                img_b64=f_tab1_b64,
                                che_do_sua=che_do_param_tab1
                            )
                            if is_ok:
                                st.session_state.noi_dung_bai_viet = edited_html
                                luu_bai_viet_lich_su(tu_khoa_goc, edited_html, st.session_state.meta_title, st.session_state.meta_desc, gop_y_note=gop_y_text, file_dinh_kem_name=file_dinh_kem_tab1.name if file_dinh_kem_tab1 else "")
                                st.toast("🎉 " + msg_edit, icon="✅")
                                st.success(msg_edit)
                                st.rerun()
                            else:
                                st.warning(msg_edit)
                        except Exception as ex_edit:
                            st.error(f"Lỗi khi tinh chỉnh bài viết: {ex_edit}")


    with tab_manual_writer:
        render_soan_thao_thu_cong(ket_noi_wp, wp_site_url, royal_api_key, wp_username)
