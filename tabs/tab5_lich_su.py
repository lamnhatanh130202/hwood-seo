import os
import re
import json
import math
import requests
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components

from modules.history_manager import lay_danh_sach_lich_su, luu_bai_viet_lich_su
from modules.ai_engine import viet_tiep_bai_dang_do, thuc_hien_tinh_chinh_ai
from modules.file_handler import (
    doc_noi_dung_file_dinh_kem,
    chuan_hoa_bang_html_hwood,
    tao_file_word_tu_html,
    xuat_bang_html_ra_csv,
    xoa_dau_tieng_viet
)
from modules.wordpress_api import dang_bai_len_wordpress
from modules.media_planner import (
    tao_ke_hoach_media_seo,
    xuat_csv_ke_hoach_media,
    chen_anh_that_vao_html,
    tao_bang_html_ke_hoach_media,
    tao_preview_co_khung_vi_tri_anh
)

def render_tab5(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, wp_username="", **kwargs):
    """Giao diện Tab 5: Thư Viện Lịch Sử Bài Viết (Phân Chia Theo Chủ Đề Sản Phẩm)"""
    wp_username = wp_username or kwargs.get("wp_username") or st.session_state.get("wp_username", "hwoodhplus@gmail.com")
    royal_api_key = royal_api_key or kwargs.get("royal_api_key") or st.session_state.get("wp_app_pass", "Wh7M rPPJ Dp4j UxP5 52HR LEU0")
    st.markdown("### 📚 Thư Viện Lịch Sử Bài Viết (Phân Chia Theo Chủ Đề Sản Phẩm)")
    ds_ls = lay_danh_sach_lich_su()
    
    if ds_ls:
        # Bộ lọc phân loại chủ đề
        danh_muc_co_san = sorted(list(set(item.get("danh_muc", "📂 Chủ Đề Khác") for item in ds_ls)))
        danh_muc_filter = ["Tất Cả Chủ Đề"] + danh_muc_co_san

        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        with col_f1:
            loc_chu_de = st.selectbox("📂 Lọc theo nhóm sản phẩm / chủ đề:", options=danh_muc_filter, key="filter_cat_tab3")
        with col_f2:
            tim_kiem_lich_su = st.text_input("🔎 Tìm kiếm theo từ khóa bài viết:", placeholder="Nhập từ khóa cần tìm...", key="search_keyword_tab3")
        with col_f3:
            so_bai_ls_tren_trang = st.selectbox("Số bài/trang:", options=[5, 10, 15, 20], index=0, key="limit_ls_tab3")

        # Lọc danh sách bài viết
        ds_hien_thi = ds_ls
        if loc_chu_de != "Tất Cả Chủ Đề":
            ds_hien_thi = [item for item in ds_hien_thi if item.get("danh_muc") == loc_chu_de]
        if tim_kiem_lich_su.strip():
            ds_hien_thi = [item for item in ds_hien_thi if tim_kiem_lich_su.lower() in item.get("tu_khoa", "").lower()]

        # Tính toán phân trang
        total_ls = len(ds_hien_thi)
        total_ls_pages = max(1, math.ceil(total_ls / so_bai_ls_tren_trang))
        if st.session_state.history_page_num > total_ls_pages:
            st.session_state.history_page_num = 1

        start_ls = (st.session_state.history_page_num - 1) * so_bai_ls_tren_trang
        end_ls = start_ls + so_bai_ls_tren_trang
        ds_trang_nay = ds_hien_thi[start_ls : end_ls]

        st.info(f"Đang hiển thị **Trang {st.session_state.history_page_num}/{total_ls_pages}** ({len(ds_trang_nay)} bài viết trên tổng số {total_ls} bài):")
        st.write("")

        # Hiển thị từng bài viết thuộc trang này
        for idx, item in enumerate(ds_trang_nay):
            item_id = str(item.get("id") or idx)
            tieu_de_bai = item.get("tu_khoa", "")
            danh_muc_bai = item.get("danh_muc", "📂 Chủ Đề Khác")
            thoi_gian_bai = item.get("thoi_gian", "")
            noi_dung_bai = item.get("noi_dung", "")
            meta_t = item.get("meta_title", "")
            meta_d = item.get("meta_desc", "")
            so_tu_bai = len(re.findall(r'\b\w+\b', re.sub(r'<[^>]*>', ' ', noi_dung_bai)))

            with st.expander(f"📄 [{danh_muc_bai}] {tieu_de_bai.title()} — 🕒 {thoi_gian_bai} (~{so_tu_bai:,} từ)", expanded=(idx == 0)):
                # Thanh thao tác với bài này
                c_act1, c_act2, c_act2b, c_act3, c_act4 = st.columns([1.2, 1.4, 1.4, 1.1, 0.7])
                
                with c_act1:
                    st.download_button(
                        label="📥 Tải .html",
                        data=noi_dung_bai,
                        file_name=f"bai_viet_{tieu_de_bai.replace(' ', '_')}.html",
                        mime="text/html",
                        key=f"dl_history_{item_id}",
                        use_container_width=True
                    )
                with c_act2:
                    if st.button("✍️ Đưa sang Tab 1", key=f"edit_history_{item_id}", use_container_width=True, help="Tải bài viết này vào Tab 1 để sử dụng công cụ Góp ý & Tinh chỉnh"):
                        st.session_state.noi_dung_bai_viet = noi_dung_bai
                        st.session_state.tu_khoa_hien_tai = tieu_de_bai
                        st.session_state.meta_title = meta_t
                        st.session_state.meta_desc = meta_d
                        st.session_state.bai_duoc_chuyen_sang_tab1 = tieu_de_bai
                        st.toast(f"Đã chuyển bài '{tieu_de_bai}' sang Tab 1!", icon="✍️")
                        st.rerun()
                with c_act2b:
                    if st.button("⏩ Viết tiếp bài này", key=f"cont_history_{item_id}", use_container_width=True, help="Nếu bài viết này bị dừng giữa chừng, bấm để AI viết tiếp liền mạch đến hết bài!"):
                        if not api_key:
                            st.error("Thiếu DeepSeek API Key!")
                        else:
                            with st.spinner("🤖 Đang viết tiếp phần còn thiếu và nối liền mạch... Vui lòng đợi vài giây!"):
                                try:
                                    bai_viet_moi = viet_tiep_bai_dang_do(noi_dung_bai, tieu_de_bai, api_key, chon_model)
                                    file_p = item.get("file_path")
                                    if file_p and os.path.exists(file_p):
                                        with open(file_p, "r", encoding="utf-8") as f_old:
                                            item_data = json.load(f_old)
                                        item_data["noi_dung"] = bai_viet_moi
                                        item_data["thoi_gian"] = datetime.now().strftime("%d/%m/%Y %H:%M") + " (Đã viết tiếp hoàn chỉnh)"
                                        with open(file_p, "w", encoding="utf-8") as f_save:
                                            json.dump(item_data, f_save, ensure_ascii=False, indent=2)
                                    else:
                                        luu_bai_viet_lich_su(tieu_de_bai, bai_viet_moi, meta_t, meta_d)
                                    st.session_state.noi_dung_bai_viet = bai_viet_moi
                                    st.toast("🎉 Đã viết tiếp hoàn thiện bài viết!", icon="✅")
                                    st.rerun()
                                except Exception as ex_ch:
                                    st.error(f"Lỗi khi viết tiếp: {ex_ch}")
                with c_act3:
                    if ket_noi_wp and wp_site_url and royal_api_key:
                        if st.button("📤 Đăng lên WP", key=f"wp_history_{item_id}", use_container_width=True):
                            try:
                                with st.spinner("Đang gửi bài và tự động điền Yoast SEO lên WordPress..."):
                                    ls_slug = re.sub(r'[^a-z0-9\-]+', '-', xoa_dau_tieng_viet(tieu_de_bai)).strip('-')
                                    thanh_cong, ket_qua = dang_bai_len_wordpress(
                                        site_url=wp_site_url,
                                        title=tieu_de_bai,
                                        content=noi_dung_bai,
                                        status="draft",
                                        wp_username=wp_username,
                                        api_key=royal_api_key,
                                        focus_kw=tieu_de_bai,
                                        meta_title=meta_t,
                                        meta_desc=meta_d,
                                        slug=ls_slug
                                    )
                                    if thanh_cong:
                                        p_id = ket_qua.get('id', '')
                                        p_link = ket_qua.get('link', '')
                                        st.success(f"🎉 Đã tạo bản nháp và TỰ ĐỘNG ĐIỀN YOAST SEO thành công! (ID: {p_id})")
                                        if p_link:
                                            st.markdown(f"👉 [Xem bài nháp]({p_link})")
                                    else:
                                        st.error(f"Lỗi: {ket_qua}")
                                        if "rest_cannot_create" in str(ket_qua) or "401" in str(ket_qua):
                                            st.warning("⚠️ **WordPress yêu cầu Tên đăng nhập WP + Mật khẩu ứng dụng** ở cột bên trái.")
                            except Exception as ex_wp:
                                st.error(f"Lỗi kết nối: {ex_wp}")
                with c_act4:
                    if st.button("🗑️ Xóa", key=f"del_history_{item_id}", use_container_width=True):
                        try:
                            os.remove(item["file_path"])
                            st.toast("Đã xóa bài viết khỏi lịch sử!", icon="🗑️")
                            st.rerun()
                        except Exception as ex_d:
                            st.error(f"Lỗi: {ex_d}")

                st.markdown("<hr style='margin: 10px 0; border: 0.5px solid #eee;'>", unsafe_allow_html=True)

                # MỞ XEM TRỰC TIẾP TẠI CHỖ VÀ GÓP Ý CHỈNH SỬA
                t_view, t_media, t_code, t_meta, t_manual, t_feedback = st.tabs([
                    "👁️ Xem Trước Bài Viết (Preview)", 
                    "📸 Kế Hoạch Hình Ảnh & Video",
                    "📋 Khối Mã HTML Để Copy", 
                    "🎯 Thẻ Meta Title & Description",
                    "✏️ Sửa Nhanh Bằng Tay",
                    "💬 Góp Ý & Sửa Bài Bằng AI"
                ])
                
                with t_view:
                    ls_slug = re.sub(r'[^a-z0-9\-]+', '-', xoa_dau_tieng_viet(tieu_de_bai)).strip('-')
                    st.markdown("##### 📥 Xuất file bài viết:")
                    exp_col1, exp_col2, exp_col3 = st.columns(3)
                    with exp_col1:
                        try:
                            doc_buf = tao_file_word_tu_html(
                                html_str=noi_dung_bai,
                                title=tieu_de_bai,
                                meta_title=meta_t,
                                meta_desc=meta_d,
                                focus_kw=tieu_de_bai
                            )
                            st.download_button(
                                label="📄 Tải File Word (.docx)",
                                data=doc_buf,
                                file_name=f"bai_viet_{ls_slug}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True,
                                key=f"dl_docx_ls_{item_id}"
                            )
                        except Exception as ex_d:
                            st.error(f"Lỗi tạo file Word: {ex_d}")
                    with exp_col2:
                        st.download_button(
                            label="🌐 Tải File HTML (.html)",
                            data=noi_dung_bai,
                            file_name=f"bai_viet_{ls_slug}.html",
                            mime="text/html",
                            use_container_width=True,
                            key=f"dl_html_ls_{item_id}"
                        )
                    with exp_col3:
                        csv_data = xuat_bang_html_ra_csv(noi_dung_bai)
                        if csv_data:
                            st.download_button(
                                label="📊 Tải Bảng Excel (.csv)",
                                data=csv_data,
                                file_name=f"bang_{ls_slug}.csv",
                                mime="text/csv",
                                use_container_width=True,
                                key=f"dl_csv_ls_{item_id}"
                            )
                        else:
                            st.button("📊 Không có bảng", disabled=True, use_container_width=True, key=f"nobang_{item_id}")

                    st.markdown("<hr style='margin: 12px 0; border: 0.5px solid #eee;'>", unsafe_allow_html=True)
                    
                    ds_media_ls = tao_ke_hoach_media_seo(noi_dung_bai, tieu_de_bai, danh_muc_bai)
                    with st.expander("📸 BẢNG GHI CHÚ VỊ TRÍ GẮN HÌNH ẢNH & VIDEO CHUẨN SEO (BẤM ĐỂ MỞ/ĐÓNG)", expanded=True):
                        st.markdown(tao_bang_html_ke_hoach_media(ds_media_ls), unsafe_allow_html=True)
                        st.caption("💡 Bảng trên thống kê chi tiết: Vị trí cần chèn ảnh trong bài, tên file ảnh WebP không dấu, thẻ Alt chuẩn SEO và gợi ý góc chụp.")

                    col_pvls1, col_pvls2 = st.columns([2.5, 1.3])
                    with col_pvls1:
                        st.markdown("##### Giao diện thực tế hiển thị trên website:")
                    with col_pvls2:
                        hien_thi_khung_ls = st.toggle("📍 Đánh dấu vị trí ảnh trong bài", value=True, key=f"tg_media_box_{item_id}", help="Hiển thị các khung ghi chú màu xanh đánh dấu chính xác nơi gắn từng hình ảnh trong nội dung bài viết để bạn dễ quan sát.")

                    if hien_thi_khung_ls:
                        html_view_final = tao_preview_co_khung_vi_tri_anh(chuan_hoa_bang_html_hwood(noi_dung_bai), ds_media_ls)
                    else:
                        html_view_final = chuan_hoa_bang_html_hwood(noi_dung_bai)

                    view_html = f"""
                    <div style="font-family: Arial, sans-serif; line-height: 1.7; color: #333; max-width: 900px; margin: 10px auto;">
                        {html_view_final}
                    </div>
                    """
                    components.html(view_html, height=800, scrolling=True)

                with t_media:
                    st.markdown("##### 📸 Bảng Kế Hoạch Hình Ảnh & Video Chuẩn SEO")
                    st.caption("Danh sách hình ảnh/video đề xuất cho bài viết này, chuẩn hóa tên file WebP không dấu, thẻ Alt chuẩn SEO và bối cảnh chụp:")
                    
                    ds_media_ls = tao_ke_hoach_media_seo(noi_dung_bai, tieu_de_bai, danh_muc_bai)
                    
                    col_mls1, col_mls2 = st.columns([3, 1.4])
                    with col_mls1:
                        so_anh_ls = sum(1 for m in ds_media_ls if "video" not in m["loai_media"].lower())
                        so_vid_ls = sum(1 for m in ds_media_ls if "video" in m["loai_media"].lower())
                        st.info(f"💡 Đề xuất: **{so_anh_ls} hình ảnh WebP** + **{so_vid_ls} video thực tế** chuẩn SEO.")
                    with col_mls2:
                        csv_media_ls = xuat_csv_ke_hoach_media(ds_media_ls)
                        st.download_button(
                            label="📊 Xuất Excel Media (.csv)",
                            data=csv_media_ls,
                            file_name=f"ke_hoach_media_{ls_slug}.csv",
                            mime="text/csv",
                            use_container_width=True,
                            key=f"dl_med_csv_ls_{item_id}"
                        )

                    # HIỂN THỊ TRỰC TIẾP TOÀN BỘ BẢNG DẠNG TABLE NỀN XANH CHỮ TRẮNG
                    st.markdown(tao_bang_html_ke_hoach_media(ds_media_ls), unsafe_allow_html=True)

                    for m in ds_media_ls:
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
                                st.markdown("**📁 Tên file ảnh chuẩn SEO:**")
                                st.code(t_file, language="text")
                                st.markdown("**🏷️ Thẻ Alt chuẩn SEO:**")
                                st.code(t_alt, language="text")
                                st.markdown(f"**📐 Loại & Kích thước:** `{l_media}` ({k_thuoc})")
                            with c_m2:
                                st.markdown("**🎬 Gợi ý góc chụp (Visual Brief):**")
                                st.info(y_tuong)
                                st.markdown("**📝 Chú thích (Caption):**")
                                st.caption(f"*{caption_txt}*")

                    st.markdown("---")
                    st.markdown("##### 🛠️ Chèn Link Ảnh Thật Vào Bài Viết Này:")
                    c_in1, c_in2, c_in3 = st.columns([1.6, 2.4, 1])
                    with c_in1:
                        opt_m_pos = st.selectbox(
                            "Chọn vị trí ảnh:",
                            options=[f"Ảnh {m['stt']}: {m['vi_tri']}" for m in ds_media_ls],
                            key=f"sb_m_pos_{item_id}"
                        )
                    with c_in2:
                        real_url_ls = st.text_input(
                            "Link URL ảnh trên web:",
                            placeholder="https://hwood.vn/wp-content/uploads/2026/11/ten-anh.webp",
                            key=f"txt_url_ls_{item_id}"
                        )
                    with c_in3:
                        st.write("")
                        if st.button("🚀 Chèn Vào Bài", key=f"btn_apply_img_ls_{item_id}", use_container_width=True):
                            if real_url_ls.strip():
                                sel_stt_ls = int(opt_m_pos.split(":")[0].replace("Ảnh", "").strip())
                                updated_html_ls = chen_anh_that_vao_html(
                                    html_str=noi_dung_bai,
                                    vi_tri_stt=sel_stt_ls,
                                    url_anh=real_url_ls.strip(),
                                    ds_media=ds_media_ls
                                )
                                file_p = item.get("file_path")
                                if file_p and os.path.exists(file_p):
                                    with open(file_p, "r", encoding="utf-8") as f_old:
                                        item_data = json.load(f_old)
                                    item_data["noi_dung"] = updated_html_ls
                                    item_data["thoi_gian"] = datetime.now().strftime("%d/%m/%Y %H:%M") + " (Đã chèn ảnh)"
                                    with open(file_p, "w", encoding="utf-8") as f_save:
                                        json.dump(item_data, f_save, ensure_ascii=False, indent=2)
                                st.toast("🎉 Đã chèn ảnh thật vào bài viết!", icon="📸")
                                st.success("🎉 Đã chèn ảnh thành công!")
                                st.rerun()
                            else:
                                st.warning("Vui lòng dán link URL ảnh!")

                with t_code:
                    st.info("💡 Bấm biểu tượng Copy ở góc trên bên phải khối code để dán vào website.")
                    st.code(chuan_hoa_bang_html_hwood(noi_dung_bai), language="html")

                with t_meta:
                    ls_slug = re.sub(r'[^a-z0-9\-]+', '-', xoa_dau_tieng_viet(tieu_de_bai)).strip('-')
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.markdown("**📌 Cụm từ khóa chính (Focus Keyphrase):**")
                        st.code(tieu_de_bai, language="text")
                        st.markdown(f"**🏷️ Tiêu đề SEO (Title Tag)** *({len(meta_t)} ký tự)*:")
                        st.code(meta_t or f"{tieu_de_bai} - HWOOD VIỆT NAM", language="text")
                    with col_m2:
                        st.markdown("**🔗 Đường dẫn tĩnh (Slug URL):**")
                        st.code(ls_slug, language="text")
                        st.markdown(f"**📝 Thẻ mô tả (Meta Description)** *({len(meta_d)} ký tự)*:")
                        st.code(meta_d or f"Bài viết chi tiết về {tieu_de_bai} từ thương hiệu HWOOD.", language="text")

                with t_manual:
                    st.info("💡 Chỉnh sửa câu từ hoặc **dán mã HTML mới** vào ô bên dưới. Bài viết sẽ được **hiển thị giao diện thực tế trực quan ngay bên dưới**!")
                    manual_text_ls = st.text_area(
                        "Mã HTML bài viết (Chỉnh sửa hoặc dán mã mới):",
                        value=noi_dung_bai,
                        height=450,
                        key=f"txt_manual_ls_{item_id}"
                    )
                    col_smls1, col_smls2 = st.columns([1.5, 3])
                    with col_smls1:
                        if st.button("💾 Lưu Thay Đổi Vào Bài Viết Này", type="primary", use_container_width=True, key=f"btn_save_man_{item_id}"):
                            file_p = item.get("file_path")
                            if file_p and os.path.exists(file_p):
                                with open(file_p, "r", encoding="utf-8") as f_old:
                                    item_data = json.load(f_old)
                                item_data["noi_dung"] = manual_text_ls
                                item_data["thoi_gian"] = datetime.now().strftime("%d/%m/%Y %H:%M") + " (Đã sửa tay)"
                                with open(file_p, "w", encoding="utf-8") as f_save:
                                    json.dump(item_data, f_save, ensure_ascii=False, indent=2)
                            else:
                                luu_bai_viet_lich_su(tieu_de_bai, manual_text_ls, meta_t, meta_d, gop_y_note="Sửa trực tiếp bằng tay")
                            st.session_state.noi_dung_bai_viet = manual_text_ls
                            st.toast("🎉 Đã lưu bài viết thành công!", icon="✅")
                            st.success("🎉 Bài viết đã được lưu! Đang tải lại...")
                            st.rerun()
                    with col_smls2:
                        st.caption(f"Độ dài mã HTML: **{len(manual_text_ls):,} ký tự**")

                    st.markdown("---")
                    st.markdown("##### 👁️ Giao diện bài viết hiển thị thực tế (Live Preview theo mã HTML ở trên):")
                    view_manual_ls_html = f"""
                    <div style="font-family: Arial, sans-serif; line-height: 1.7; color: #333; max-width: 900px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; padding: 25px; background-color: #ffffff;">
                        {manual_text_ls}
                    </div>
                    """
                    components.html(view_manual_ls_html, height=800, scrolling=True)

                with t_feedback:
                    st.markdown("#### 💬 Góp ý & Tinh chỉnh bài viết này bằng AI:")
                    st.markdown("Bạn có thể **copy dán nội dung góp ý** vào ô bên dưới, hoặc **đính kèm file tài liệu / hình ảnh** (ảnh chụp màn hình, bảng giá, file Word `.docx`, PDF, file Text).")
                    
                    che_do_sua_tab5 = st.radio(
                        "🎯 Chọn chế độ sửa bài bằng AI:",
                        options=[
                            "✨ Tự động thông minh (Khuyên dùng: Tự nhận diện sửa triệt để 100% nếu có danh sách nhiều lỗi, hoặc sửa cục bộ nếu chỉnh 1-2 vị trí)",
                            "🔄 Sửa toàn diện theo Checklist góp ý (Cam kết sửa đủ 100% mọi lỗi được liệt kê, không bỏ sót)",
                            "🎯 Sửa cục bộ: Chỉ thay thế 1-2 vị trí nhỏ (Bảo toàn 100% các đoạn khác)"
                        ],
                        index=0,
                        key=f"radio_mode_{item_id}"
                    )
                    if "Tự động" in che_do_sua_tab5:
                        che_do_param_tab5 = "tu_dong"
                    elif "Sửa toàn diện" in che_do_sua_tab5:
                        che_do_param_tab5 = "toan_bai"
                    else:
                        che_do_param_tab5 = "cuc_bo"

                    if item.get("lich_su_gop_y"):
                        with st.expander(f"📜 Nhật ký {len(item['lich_su_gop_y'])} lần góp ý trước đó của bài này"):
                            for gy in reversed(item["lich_su_gop_y"]):
                                st.markdown(f"**🕒 Thời gian:** `{gy.get('thoi_gian')}`")
                                if gy.get("yeu_cau"):
                                    st.info(gy.get("yeu_cau"))
                                if gy.get("file_dinh_kem"):
                                    st.caption(f"📎 File đính kèm: `{gy.get('file_dinh_kem')}`")
                                st.markdown("<hr style='margin: 4px 0; border: 0.5px dashed #eee;'>", unsafe_allow_html=True)

                    col_fb1, col_fb2 = st.columns([1.5, 1])
                    with col_fb1:
                        fb_text = st.text_area(
                            "📝 Nhập hoặc dán nội dung góp ý cần sửa (Copy qua đây):",
                            placeholder="Ví dụ:\n- Thêm bảng báo giá bàn ghế sân vườn mới nhất 2026\n- Viết lại đoạn mở đầu cho lôi cuốn hơn\n- Sửa giá nan polywood trong bảng thành 1.250.000đ...",
                            height=140,
                            key=f"txt_fb_{item_id}"
                        )
                    with col_fb2:
                        fb_file = st.file_uploader(
                            "📎 Đính kèm hình ảnh hoặc file góp ý:",
                            type=["png", "jpg", "jpeg", "webp", "docx", "pdf", "txt", "md"],
                            key=f"file_fb_{item_id}",
                            help="Hỗ trợ ảnh chụp, file Word .docx, PDF hoặc file text"
                        )
                        if fb_file:
                            f_text, f_summary, f_b64 = doc_noi_dung_file_dinh_kem(fb_file)
                            st.success(f_summary)
                            if f_b64:
                                st.image(fb_file, caption=f"🖼️ Ảnh đính kèm: {fb_file.name}", width=200)

                    btn_do_fb = st.button("🚀 Gửi Góp Ý & Cập Nhật Lại Bài Viết Bằng AI", key=f"btn_apply_fb_{item_id}", type="primary", use_container_width=True)
                    if btn_do_fb:
                        if not fb_text.strip() and not fb_file:
                            st.warning("⚠️ Vui lòng nhập nội dung góp ý hoặc đính kèm file/ảnh trước khi bấm sửa!")
                        elif not api_key:
                            st.error("⚠️ Thiếu DeepSeek API Key trong thanh điều hướng bên trái!")
                        else:
                            with st.spinner("🤖 Đang đọc góp ý, phân tích tài liệu và xử lý..."):
                                try:
                                    f_text, _, f_b64 = doc_noi_dung_file_dinh_kem(fb_file) if fb_file else ("", "", None)
                                    new_html, is_ok, msg_edit = thuc_hien_tinh_chinh_ai(
                                        noi_dung_cu=noi_dung_bai,
                                        yeu_cau_text=fb_text,
                                        file_text=f_text,
                                        tu_khoa_bai=tieu_de_bai,
                                        api_key=api_key,
                                        model_name=chon_model,
                                        img_b64=f_b64,
                                        che_do_sua=che_do_param_tab5
                                    )
                                    if not is_ok:
                                        st.warning(msg_edit)
                                    else:
                                        # Lưu cập nhật vào file JSON lịch sử này
                                        file_p = item.get("file_path")
                                        if file_p and os.path.exists(file_p):
                                            with open(file_p, "r", encoding="utf-8") as f_old:
                                                item_data = json.load(f_old)
                                            item_data["noi_dung"] = new_html
                                            item_data["thoi_gian"] = datetime.now().strftime("%d/%m/%Y %H:%M") + " (Đã sửa theo góp ý)"
                                            if "lich_su_gop_y" not in item_data or not isinstance(item_data["lich_su_gop_y"], list):
                                                item_data["lich_su_gop_y"] = []
                                            item_data["lich_su_gop_y"].append({
                                                "thoi_gian": datetime.now().strftime("%d/%m/%Y %H:%M"),
                                                "yeu_cau": fb_text,
                                                "file_dinh_kem": fb_file.name if fb_file else "",
                                                "che_do": che_do_sua_tab5
                                            })
                                            with open(file_p, "w", encoding="utf-8") as f_save:
                                                json.dump(item_data, f_save, ensure_ascii=False, indent=2)
                                        else:
                                            luu_bai_viet_lich_su(tieu_de_bai, new_html, meta_t, meta_d, gop_y_note=fb_text, file_dinh_kem_name=fb_file.name if fb_file else "")
                                        
                                        st.session_state.noi_dung_bai_viet = new_html
                                        st.toast("🎉 " + msg_edit, icon="✅")
                                        st.success(msg_edit)
                                        st.rerun()
                                except Exception as ex_fb:
                                    st.error(f"Lỗi khi tinh chỉnh bài viết: {ex_fb}")

        # Nút chuyển trang cho Lịch sử bài viết
        if total_ls_pages > 1:
            st.markdown("<br>", unsafe_allow_html=True)
            col_lsp_1, col_lsp_2, col_lsp_3 = st.columns([1, 2, 1])
            with col_lsp_1:
                if st.button("⬅️ Trang trước", key="btn_ls_prev", disabled=(st.session_state.history_page_num <= 1), use_container_width=True):
                    st.session_state.history_page_num -= 1
                    st.rerun()
            with col_lsp_2:
                st.markdown(f"<div style='text-align: center; padding-top: 6px; font-weight: bold;'>Trang {st.session_state.history_page_num} / {total_ls_pages}</div>", unsafe_allow_html=True)
            with col_lsp_3:
                if st.button("Trang sau ➡️", key="btn_ls_next", disabled=(st.session_state.history_page_num >= total_ls_pages), use_container_width=True):
                    st.session_state.history_page_num += 1
                    st.rerun()

    else:
        st.info("Hiện tại chưa có bài viết nào được lưu. Khi bạn tạo bài mới ở Tab 1 hoặc bấm nút 'Lưu vào Lịch sử', toàn bộ bài viết sẽ hiển thị tại đây!")
