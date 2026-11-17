import math
import requests
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

from modules.knowledge import lay_tri_thuc_phu_hop, lay_tri_thuc_tinh_gon, doc_kho_tri_thuc
from modules.history_manager import luu_bai_viet_lich_su
from modules.file_handler import doc_noi_dung_file_dinh_kem
from modules.wordpress_api import lay_toan_bo_du_lieu_wp, cap_nhat_bai_wordpress

def render_tab2(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, kho_tri_thuc="", ds_file=None, wp_username="", **kwargs):
    """Giao diện Tab 2: Xem & Chỉnh Sửa Trang Sản Phẩm / Bài Viết Trên Website"""
    wp_username = wp_username or kwargs.get("wp_username") or st.session_state.get("wp_username", "hwoodhplus@gmail.com")
    royal_api_key = royal_api_key or kwargs.get("royal_api_key") or st.session_state.get("wp_app_pass", "Wh7M rPPJ Dp4j UxP5 52HR LEU0")
    if ds_file is None:
        ds_file = []

    st.markdown("### 🔍 Xem & Chỉnh Sửa Trang Sản Phẩm / Bài Viết Trên Website")
    st.markdown("Xem toàn bộ các **Trang Sản Phẩm (Pages)**, **Bài Viết Tin Tức (Posts)** hoặc **Sản Phẩm Cửa Hàng (WooCommerce)** hiện có trên `hwood.vn`. Bạn có thể chỉnh sửa trực tiếp nội dung hoặc để AI tự động kiểm toán & nâng cấp chuẩn SEO mới nhất rồi cập nhật ngay lên website!")

    # 1. BỘ CHỌN LOẠI NỘI DUNG WORDPRESS CẦN XEM & CHỈNH SỬA
    col_type1, col_type2 = st.columns([3, 1])
    with col_type1:
        loai_index = 0
        current_pt = st.session_state.get("wp_post_type", "san-pham")
        if current_pt == "posts":
            loai_index = 1
        elif current_pt == "pages":
            loai_index = 2
        elif current_pt == "du-an":
            loai_index = 3
        else:
            loai_index = 0

        loai_noi_dung_opt = st.radio(
            "📂 Loại nội dung website bạn muốn xem & chỉnh sửa:",
            options=[
                "📦 Sản Phẩm HWOOD (san-pham - 172 mục)",
                "📝 Bài Viết Tin Tức (Posts)",
                "📄 Trang Tĩnh / Giới Thiệu (Pages)",
                "🏗️ Dự Án Thực Tế (du-an)"
            ],
            index=loai_index,
            horizontal=True,
            key="radio_wp_type_selector"
        )
    with col_type2:
        st.write("")
        if st.button("🔄 Làm mới danh sách", key="btn_refresh_current_type", use_container_width=True):
            lay_toan_bo_du_lieu_wp.clear()
            st.toast("Đang tải lại dữ liệu mới nhất từ website...", icon="🔄")
            st.rerun()

    current_post_type = "san-pham"
    if "Bài Viết" in loai_noi_dung_opt:
        current_post_type = "posts"
    elif "Trang Tĩnh" in loai_noi_dung_opt or "Pages" in loai_noi_dung_opt:
        current_post_type = "pages"
    elif "Dự Án" in loai_noi_dung_opt:
        current_post_type = "du-an"
    else:
        current_post_type = "san-pham"

    # Reset trang nếu người dùng đổi loại nội dung
    if st.session_state.get("wp_post_type") != current_post_type:
        st.session_state.wp_post_type = current_post_type
        st.session_state.wp_page_num = 1
        st.session_state.bai_cu_duoc_chon = None
        st.rerun()

    # Tải dữ liệu tương ứng với loại nội dung
    danh_sach_hien_thi_wp = []
    if wp_site_url:
        danh_sach_hien_thi_wp = lay_toan_bo_du_lieu_wp(wp_site_url, royal_api_key, current_post_type, wp_username=wp_username)

    col_audit_left, col_audit_right = st.columns([1.1, 1.9])

    # --------------------------------------------------------------------------
    # CỘT TRÁI: DANH SÁCH CÁC TRANG / BÀI VIẾT TỪ WEBSITE
    # --------------------------------------------------------------------------
    with col_audit_left:
        st.markdown(f"#### 📑 1. Danh sách ({len(danh_sach_hien_thi_wp)} mục):")
        if danh_sach_hien_thi_wp:
            tim_kiem_wp = st.text_input(
                "🔎 Tìm theo tên / từ khóa:",
                placeholder="Nhập tên sản phẩm hoặc bài viết...",
                key="search_old_wp"
            )
            
            danh_sach_loc = danh_sach_hien_thi_wp
            if tim_kiem_wp.strip():
                danh_sach_loc = [p for p in danh_sach_hien_thi_wp if tim_kiem_wp.lower() in p.get("title", {}).get("rendered", "").lower()]

            WP_PER_PAGE = 6
            total_wp = len(danh_sach_loc)
            total_wp_pages = max(1, math.ceil(total_wp / WP_PER_PAGE))
            
            if st.session_state.wp_page_num > total_wp_pages:
                st.session_state.wp_page_num = 1
                
            start_wp = (st.session_state.wp_page_num - 1) * WP_PER_PAGE
            end_wp = start_wp + WP_PER_PAGE
            posts_trang_nay = danh_sach_loc[start_wp : end_wp]

            st.caption(f"Trang {st.session_state.wp_page_num}/{total_wp_pages} (Tìm thấy {total_wp} mục):")
            
            for post in posts_trang_nay:
                pid = post.get("id")
                ptitle = post.get("title", {}).get("rendered", "") or "(Chưa đặt tiêu đề)"
                plink = post.get("link", "")
                pdate = post.get("date", "")[:10]

                is_selected = (st.session_state.bai_cu_duoc_chon and st.session_state.bai_cu_duoc_chon.get("id") == pid)
                card_border = "#3b8632" if is_selected else "#e0e0e0"

                with st.container():
                    st.markdown(f"<div style='border-left: 4px solid {card_border}; padding-left: 8px;'><b>{ptitle}</b></div>", unsafe_allow_html=True)
                    st.caption(f"ID: `{pid}` | Ngày: `{pdate}` | [🔗 Xem web]({plink})")
                    
                    btn_text = "✅ Đang Chọn Mục Này" if is_selected else "⚡ Xem & Chỉnh Sửa"
                    if st.button(btn_text, key=f"btn_pick_{current_post_type}_{pid}", use_container_width=True):
                        try:
                            with st.spinner("Đang tải toàn bộ nội dung từ website..."):
                                headers_get = {
                                    "Authorization": f"Bearer {royal_api_key}",
                                    "X-Royal-MCP-API-Key": royal_api_key
                                } if royal_api_key else {}
                                clean_pass_item = royal_api_key.replace(" ", "").strip() if royal_api_key else ""
                                auth_item = (wp_username.strip(), clean_pass_item) if (wp_username and clean_pass_item) else None
                                r_post = requests.get(
                                    f"{wp_site_url.rstrip('/')}/wp-json/wp/v2/{current_post_type}/{pid}",
                                    auth=auth_item,
                                    headers=headers_get,
                                    timeout=15
                                )
                                if r_post.status_code == 200:
                                    post_full = r_post.json()
                                    full_content = post_full.get("content", {}).get("rendered", "")
                                    st.session_state.bai_cu_duoc_chon = {
                                        "id": pid,
                                        "title": ptitle,
                                        "link": plink,
                                        "content": full_content,
                                        "post_type": current_post_type
                                    }
                                    st.session_state.tieu_de_edit_tay = ptitle
                                    st.session_state.noi_dung_edit_tay = full_content
                                    st.session_state.noi_dung_toi_uu = ""
                                    st.session_state.bao_cao_audit = ""
                                    st.toast(f"Đã mở: {ptitle}", icon="✅")
                                    st.rerun()
                                else:
                                    st.error(f"Không thể tải nội dung (Mã {r_post.status_code})")
                        except Exception as ex_load:
                            st.error(f"Lỗi: {ex_load}")
                    st.markdown("<hr style='margin: 8px 0; border: 0.5px solid #f0f0f0;'>", unsafe_allow_html=True)

            # Nút chuyển trang cho bài viết WordPress
            if total_wp_pages > 1:
                col_wpp_1, col_wpp_2, col_wpp_3 = st.columns([1, 2, 1])
                with col_wpp_1:
                    if st.button("⬅️ Trước", key="btn_wp_prev", disabled=(st.session_state.wp_page_num <= 1), use_container_width=True):
                        st.session_state.wp_page_num -= 1
                        st.rerun()
                with col_wpp_2:
                    st.markdown(f"<div style='text-align: center; padding-top: 6px; font-weight: bold;'>Trang {st.session_state.wp_page_num}/{total_wp_pages}</div>", unsafe_allow_html=True)
                with col_wpp_3:
                    if st.button("Sau ➡️", key="btn_wp_next", disabled=(st.session_state.wp_page_num >= total_wp_pages), use_container_width=True):
                        st.session_state.wp_page_num += 1
                        st.rerun()
        else:
            if current_post_type == "product":
                st.warning("⚠️ Không tìm thấy sản phẩm qua WooCommerce REST API. Hãy chọn **📄 Trang Sản Phẩm / Trang Tĩnh (Pages)** hoặc **📝 Bài Viết Tin Tức (Posts)** ở trên!")
            else:
                st.warning("Website chưa trả về dữ liệu hoặc danh mục này đang trống. Bạn có thể bấm '🔄 Làm mới danh sách' ở trên để quét lại!")

    # --------------------------------------------------------------------------
    # CỘT PHẢI: KHÔNG GIAN XEM & CHỈNH SỬA CHI TIẾT
    # --------------------------------------------------------------------------
    with col_audit_right:
        st.markdown("#### 🛠️ 2. Không gian Xem & Chỉnh Sửa Chi Tiết:")
        
        # Nếu đã chọn 1 trang / bài viết
        if st.session_state.bai_cu_duoc_chon:
            item_dang_chon = st.session_state.bai_cu_duoc_chon
            target_ptype = item_dang_chon.get("post_type", "pages")
            
            c_info1, c_info2 = st.columns([3, 1])
            with c_info1:
                st.info(f"📌 Đang chọn: **{item_dang_chon['title']}** (ID: `{item_dang_chon['id']}` - Loại: `{target_ptype}`)\n\n🔗 Link xem thực tế: [{item_dang_chon['link']}]({item_dang_chon['link']})")
            with c_info2:
                if st.button("❌ Đóng / Chọn mục khác", key="btn_close_pick", use_container_width=True):
                    st.session_state.bai_cu_duoc_chon = None
                    st.rerun()

            tab_manual_edit, tab_ai_audit, tab_original_view = st.tabs([
                "✏️ (A) Soạn Thảo & Chỉnh Sửa Trực Tiếp",
                "🤖 (B) AI Khám & Nâng Cấp Tự Động",
                "👁️ (C) Xem Bản Gốc Đang Có Trên Web"
            ])

            # ==================================================================
            # TAB A: SOẠN THẢO & CHỈNH SỬA TRỰC TIẾP (MANUAL LIVE EDITOR)
            # ==================================================================
            with tab_manual_edit:
                st.markdown("##### ✏️ Trình soạn thảo trực tiếp (Cập nhật thẳng lên website hwood.vn):")
                
                # Ô sửa tiêu đề
                new_manual_title = st.text_input(
                    "📝 Tiêu đề trang / bài viết:",
                    value=st.session_state.get("tieu_de_edit_tay", item_dang_chon["title"]),
                    key="input_manual_edit_title"
                )

                # Khung tiện ích: Mẫu HTML & Tra cứu thông số
                with st.expander("💡 Khung tiện ích: Tra cứu thông số & Mẫu HTML chuẩn HWOOD"):
                    st.caption("Sao chép nhanh các khối thông tin chuẩn nhận diện thương hiệu HWOOD:")
                    c_tool1, c_tool2, c_tool3 = st.columns(3)
                    with c_tool1:
                        st.markdown("**Bảng Báo Giá 2026 (VAT 8%):**")
                        sample_table = '<table class="hwood-table" style="width: 100%; border-collapse: collapse; margin: 18px 0;"><thead><tr style="background-color: #3b8632; color: #fff;"><th style="padding: 10px; border: 1px solid #ddd;">Tên Sản Phẩm</th><th style="padding: 10px; border: 1px solid #ddd;">Quy Cách</th><th style="padding: 10px; border: 1px solid #ddd;">Màu Sắc</th><th style="padding: 10px; border: 1px solid #ddd;">Đơn Giá (VAT 8%)</th></tr></thead><tbody><tr><td style="padding: 9px; border: 1px solid #ddd;">Gỗ nhựa ngoài trời HWOOD</td><td style="padding: 9px; border: 1px solid #ddd;">140 x 25 x 2900 mm</td><td style="padding: 9px; border: 1px solid #ddd;">Wood, Coffee, Dark Grey</td><td style="padding: 9px; border: 1px solid #ddd; font-weight: bold; color: #3b8632;">Liên hệ 0912 565 353</td></tr></tbody></table>'
                        st.code(sample_table, language="html")
                    with c_tool2:
                        st.markdown("**Khung Cam Kết & Hotline HWOOD:**")
                        sample_contact = '<div style="background-color: #f6faf6; border-left: 5px solid #3b8632; padding: 16px; margin: 20px 0; border-radius: 4px;"><h4 style="color: #3b8632; margin-top: 0;">🏢 TỔNG KHO VẬT LIỆU HWOOD VIỆT NAM</h4><p>• Hơn 12 năm nhập khẩu và phân phối vật liệu trang trí cao cấp.</p><p>• Đối tác tin cậy: Landmark 81, Vinpearl Phú Quốc, Novaworld...</p><p>• Kho hàng sẵn trên 500 container phục vụ dự án toàn quốc.</p><p>• <strong>Hotline:</strong> <span style="color: #3b8632; font-size: 1.1em; font-weight: bold;">0912 565 353</span></p></div>'
                        st.code(sample_contact, language="html")
                    with c_tool3:
                        st.markdown("**Khung Hình Ảnh Chuẩn SEO (Alt):**")
                        sample_img = '<figure style="margin: 20px 0; text-align: center;"><img src="https://hwood.vn/duong-dan-anh.jpg" alt="Mô tả sản phẩm HWOOD" style="max-width: 100%; height: auto; border-radius: 6px;" /><figcaption style="font-style: italic; color: #666; font-size: 0.9em; margin-top: 6px;">Hình ảnh: Mô tả sản phẩm thực tế thi công bởi HWOOD</figcaption></figure>'
                        st.code(sample_img, language="html")

                    st.markdown("---")
                    st.markdown("**📚 Tra cứu thông số & giá từ 14 file tri thức HWOOD:**")
                    file_tra_cuu = st.selectbox("Chọn tài liệu vật liệu để xem thông số:", options=ds_file, key="sb_lookup_file_tab2")
                    if file_tra_cuu:
                        try:
                            with open(file_tra_cuu, "r", encoding="utf-8") as f_spec:
                                noi_dung_spec = f_spec.read()
                                st.text_area("Nội dung tài liệu thông số:", value=noi_dung_spec[:2500] + ("..." if len(noi_dung_spec) > 2500 else ""), height=180, key="txt_lookup_view_tab2")
                        except Exception:
                            pass

                # Ô sửa nội dung HTML
                new_manual_content = st.text_area(
                    "📄 Nội dung HTML chi tiết (Chỉnh sửa tùy ý):",
                    value=st.session_state.get("noi_dung_edit_tay", item_dang_chon["content"]),
                    height=450,
                    key="textarea_manual_edit_content"
                )

                # Nút cập nhật và lưu
                c_act_m1, c_act_m2, c_act_m3 = st.columns([2, 1.2, 1.2])
                with c_act_m1:
                    if st.button("💾 CẬP NHẬT TRỰC TIẾP LÊN HWOOD.VN", type="primary", use_container_width=True, help="Lưu ngay tiêu đề và nội dung mới vào trang trên website"):
                        if not ket_noi_wp or not royal_api_key:
                            st.error("Chưa kết nối WordPress hoặc thiếu Royal MCP Key!")
                        else:
                            try:
                                with st.spinner("Đang gửi cập nhật lên website HWOOD..."):
                                    target_id = item_dang_chon["id"]
                                    thanh_cong, ket_qua = cap_nhat_bai_wordpress(
                                        site_url=wp_site_url,
                                        post_id=target_id,
                                        post_type=target_ptype,
                                        title=new_manual_title,
                                        content=new_manual_content,
                                        wp_username=wp_username,
                                        api_key=royal_api_key
                                    )
                                    if thanh_cong:
                                        st.success(f"🎉 Đã cập nhật thành công lên website HWOOD! (ID: {target_id})")
                                        st.markdown(f"👉 [Bấm vào đây để xem ngay trang thực tế vừa sửa]({item_dang_chon['link']})")
                                        st.session_state.bai_cu_duoc_chon["title"] = new_manual_title
                                        st.session_state.bai_cu_duoc_chon["content"] = new_manual_content
                                        st.session_state.tieu_de_edit_tay = new_manual_title
                                        st.session_state.noi_dung_edit_tay = new_manual_content
                                    else:
                                        st.error(f"Lỗi khi cập nhật lên WordPress: {ket_qua}")
                                        if "rest_cannot_create" in str(ket_qua) or "401" in str(ket_qua):
                                            st.warning("⚠️ **WordPress yêu cầu Tên đăng nhập WP + Mật khẩu ứng dụng** ở thanh bên trái để cấp quyền chỉnh sửa.")
                            except Exception as ex_m_up:
                                st.error(f"Lỗi kết nối WordPress: {ex_m_up}")

                with c_act_m2:
                    st.download_button(
                        label="📥 Tải file HTML",
                        data=new_manual_content,
                        file_name=f"trang_{item_dang_chon['id']}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                with c_act_m3:
                    if st.button("💾 Lưu vào Lịch sử", key="btn_save_manual_history", use_container_width=True):
                        luu_bai_viet_lich_su(f"[Chỉnh sửa] {new_manual_title}", new_manual_content)
                        st.toast("Đã lưu vào Thư viện Lịch sử!", icon="💾")

                # Xem trước trực tiếp giao diện
                st.markdown("---")
                st.markdown("##### 👁️ Xem trước giao diện thực tế (Live Preview):")
                preview_html = f"""<div style="font-family: Arial, sans-serif; line-height: 1.7; color: #333; max-width: 900px; margin: 0 auto;">{new_manual_content}</div>"""
                components.html(preview_html, height=800, scrolling=True)

            # ==================================================================
            # TAB B: AI KHÁM & NÂNG CẤP TỰ ĐỘNG (AI SEO REFRESHER)
            # ==================================================================
            with tab_ai_audit:
                st.markdown("##### 🤖 AI Phân tích điểm yếu & Nâng cấp toàn diện:")
                st.markdown("Bạn có thể **copy dán nội dung góp ý** vào ô bên dưới, hoặc **đính kèm file tài liệu / hình ảnh** (ảnh chụp màn hình, bảng giá, file Word `.docx`, PDF, file Text). AI sẽ tự động đọc toàn bộ và viết lại bài hoàn chỉnh!")
                
                col_aud_fb1, col_aud_fb2 = st.columns([1.5, 1])
                with col_aud_fb1:
                    yeu_cau_rieng_ai = st.text_area(
                        "📝 Ghi chú yêu cầu riêng cho AI (Copy qua đây):",
                        placeholder="Ví dụ: Bổ sung bảng quy cách & kích thước, cập nhật bảng giá VAT 8%, nhấn mạnh bảo hành 10 năm...",
                        height=130,
                        key="input_ai_specific_request"
                    )
                with col_aud_fb2:
                    file_audit_tab2 = st.file_uploader(
                        "📎 Đính kèm hình ảnh hoặc tài liệu tham khảo (Tùy chọn):",
                        type=["png", "jpg", "jpeg", "webp", "docx", "pdf", "txt", "md"],
                        key="file_audit_tab2",
                        help="Hỗ trợ ảnh chụp mẫu, file Word .docx, PDF hoặc text"
                    )
                    if file_audit_tab2:
                        f_aud_text, f_aud_summary, f_aud_b64 = doc_noi_dung_file_dinh_kem(file_audit_tab2)
                        st.success(f_aud_summary)
                        if f_aud_b64:
                            st.image(file_audit_tab2, caption=f"🖼️ Ảnh đính kèm: {file_audit_tab2.name}", width=200)

                col_aud_b1, col_aud_b2 = st.columns([1.6, 1.2])
                with col_aud_b1:
                    btn_audit = st.button("🚀 Bắt đầu Phân Tích & Nâng Cấp Toàn Diện Bằng AI", type="primary", use_container_width=True)
                with col_aud_b2:
                    toi_uu_token_tab2 = st.checkbox(
                        "⚡ Tiết Kiệm Token (Giảm ~60%)",
                        value=st.session_state.get("toi_uu_token_tab2", True),
                        key="cb_toi_uu_token_tab2",
                        help="Sử dụng Knowledge Graph tinh gọn để chỉ nạp thông số và bảng giá cần thiết, giảm chi phí token DeepSeek khi kiểm toán."
                    )
                    st.session_state["toi_uu_token_tab2"] = toi_uu_token_tab2
                
                if btn_audit:
                    if not api_key:
                        st.error("Vui lòng nhập DeepSeek API Key!")
                    else:
                        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                        f_aud_content = ""
                        if file_audit_tab2:
                            f_aud_content, _, _ = doc_noi_dung_file_dinh_kem(file_audit_tab2)
                        
                        if toi_uu_token_tab2:
                            tri_thuc_tab2 = lay_tri_thuc_tinh_gon(item_dang_chon['title'])
                            if not tri_thuc_tab2:
                                tri_thuc_tab2 = lay_tri_thuc_phu_hop(item_dang_chon['title'])
                        else:
                            tri_thuc_tab2 = lay_tri_thuc_phu_hop(item_dang_chon['title'])
                        
                        prompt_audit = f"""Bạn là Giám đốc SEO và Chuyên gia Kiểm toán Nội dung cao cấp của HWOOD VIỆT NAM.

DƯỚI ĐÂY LÀ NỘI DUNG ĐANG CÓ TRÊN WEBSITE HWOOD.VN:
Tiêu đề: {item_dang_chon['title']}
Mã HTML hiện tại:
{item_dang_chon['content']}

YÊU CẦU BỔ SUNG CỦA NGƯỜI DÙNG:
{yeu_cau_rieng_ai if yeu_cau_rieng_ai.strip() else 'Không có mô tả chữ riêng (Hãy tự động tối ưu toàn diện)'}

{f_aud_content}

BỘ NÃO TRI THỨC VÀ BÁO GIÁ VẬT LIỆU MỚI NHẤT CỦA HWOOD:
{tri_thuc_tab2 if tri_thuc_tab2 else "Tuân thủ quy chuẩn kỹ thuật và báo giá chính hãng HWOOD Việt Nam (VAT 8%, bảo hành 5 năm, Hotline 0912 565 353)."}

NHIỆM VỤ CỦA BẠN (CONTENT AUDIT & REFRESH THEO CHUẨN 2026):
1. PHẦN 1 - BÁO CÁO KIỂM TOÁN (AUDIT REPORT):
   - Đánh giá ngắn gọn 3-4 gạch đầu dòng: Trang cũ đang thiếu gì? (Thiếu bảng giá VAT 8%, thiếu hình ảnh có alt, thiếu bảng thông số, thiếu nhận diện màu #3b8632, CTA chưa chuẩn).

2. PHẦN 2 - BẢN NÂNG CẤP HOÀN CHỈNH (MÃ HTML MỚI):
   - Giữ nguyên chủ đề cốt lõi để bảo tồn thứ hạng tìm kiếm.
   - Viết lại toàn bộ thành mã HTML chuyên sâu, mạch lạc với thẻ <h2>, <h3> (TUYỆT ĐỐI KHÔNG DÙNG H1).
   - Áp dụng màu thương hiệu #3b8632 cho tiêu đề h2 và các hộp điểm nhấn.
   - Bổ sung bảng thông số kỹ thuật, bảng giá 2026 đã gồm 8% VAT tương ứng với sản phẩm trong bài.
   - Bổ sung các khung ảnh gợi ý kèm thẻ Alt tối ưu SEO.
   - Chèn khung liên hệ & Hotline 0912 565 353 ở cuối trang.
   - KHÔNG bọc mã trong markdown ```html, hãy trả về trực tiếp.

Hãy trình bày phần 1 bên trong thẻ <!-- AUDIT_REPORT -->...<!-- END_AUDIT_REPORT --> và phần 2 là mã HTML bài viết mới."""

                        with st.spinner("🤖 AI đang phân tích bài cũ và tái cấu trúc nội dung chuẩn SEO HWOOD... Vui lòng chờ vài giây!"):
                            try:
                                from modules.ai_engine import goi_chat_completion_an_toan
                                resp_audit = goi_chat_completion_an_toan(
                                    client=client,
                                    model=chon_model,
                                    messages=[{"role": "user", "content": prompt_audit}],
                                    max_tokens=8192,
                                    temperature=0.7
                                )
                                raw_result = resp_audit.choices[0].message.content.strip()
                                
                                # Tách phần Báo cáo Audit và phần HTML mới
                                bao_cao = ""
                                noi_dung_moi = raw_result
                                
                                if "<!-- AUDIT_REPORT -->" in raw_result and "<!-- END_AUDIT_REPORT -->" in raw_result:
                                    parts = raw_result.split("<!-- END_AUDIT_REPORT -->")
                                    bao_cao = parts[0].replace("<!-- AUDIT_REPORT -->", "").strip()
                                    noi_dung_moi = parts[1].strip()
                                
                                if noi_dung_moi.startswith("```"):
                                    lines = noi_dung_moi.splitlines()
                                    if lines[0].startswith("```"): lines = lines[1:]
                                    if lines and lines[-1].strip() == "```": lines = lines[:-1]
                                    noi_dung_moi = "\n".join(lines).strip()

                                st.session_state.bao_cao_audit = bao_cao
                                st.session_state.noi_dung_toi_uu = noi_dung_moi
                                st.success("🎉 Đã phân tích và nâng cấp trang thành công!")
                                st.rerun()

                            except Exception as ex_audit:
                                st.error(f"Lỗi phân tích: {ex_audit}")

                # Hiển thị kết quả tối ưu từ AI
                if st.session_state.noi_dung_toi_uu:
                    st.markdown("---")
                    if st.session_state.bao_cao_audit:
                        st.markdown("#### 📋 Báo cáo Đánh giá Điểm yếu Trang Cũ:")
                        st.markdown(f"""<div class="audit-card">{st.session_state.bao_cao_audit}</div>""", unsafe_allow_html=True)

                    st.markdown("#### ✨ Nội dung sau khi được AI Nâng cấp Mới:")
                    
                    col_opt_act1, col_opt_act2, col_opt_act3, col_opt_act4 = st.columns([1.5, 1.2, 1.2, 1.5])
                    with col_opt_act1:
                        if ket_noi_wp and wp_site_url and royal_api_key:
                            if st.button("🚀 CẬP NHẬT BẢN AI NÀY LÊN WEB", type="primary", use_container_width=True):
                                try:
                                    with st.spinner("Đang cập nhật trực tiếp lên WordPress..."):
                                        target_id = item_dang_chon['id']
                                        thanh_cong, ket_qua = cap_nhat_bai_wordpress(
                                            site_url=wp_site_url,
                                            post_id=target_id,
                                            post_type=target_ptype,
                                            title=None,
                                            content=st.session_state.noi_dung_toi_uu,
                                            wp_username=wp_username,
                                            api_key=royal_api_key
                                        )
                                        if thanh_cong:
                                            st.success(f"🎉 Đã cập nhật thành công trang lên website HWOOD! (ID: {target_id})")
                                            st.markdown(f"👉 [Bấm vào đây để xem thực tế trên web]({item_dang_chon['link']})")
                                            st.session_state.bai_cu_duoc_chon["content"] = st.session_state.noi_dung_toi_uu
                                            st.session_state.noi_dung_edit_tay = st.session_state.noi_dung_toi_uu
                                        else:
                                            st.error(f"Lỗi khi cập nhật lên WordPress: {ket_qua}")
                                            if "rest_cannot_create" in str(ket_qua) or "401" in str(ket_qua):
                                                st.warning("⚠️ **WordPress yêu cầu Tên đăng nhập WP + Mật khẩu ứng dụng** ở thanh bên trái để cấp quyền chỉnh sửa.")
                                except Exception as ex_up:
                                    st.error(f"Lỗi kết nối: {ex_up}")
                    with col_opt_act2:
                        if st.button("➡️ Đưa vào Sửa tay", key="btn_move_to_manual", use_container_width=True, help="Chuyển mã HTML này sang tab (A) để bạn tự tay tinh chỉnh thêm"):
                            st.session_state.noi_dung_edit_tay = st.session_state.noi_dung_toi_uu
                            st.toast("Đã chuyển nội dung sang tab (A) Soạn Thảo Trực Tiếp!", icon="✏️")
                            st.rerun()
                    with col_opt_act3:
                        st.download_button(
                            label="📥 Tải file HTML",
                            data=st.session_state.noi_dung_toi_uu,
                            file_name=f"trang_ai_{item_dang_chon['id']}.html",
                            mime="text/html",
                            use_container_width=True
                        )
                    with col_opt_act4:
                        if st.button("💾 Lưu vào Lịch sử", key="btn_save_audit", use_container_width=True):
                            luu_bai_viet_lich_su(f"[AI Nâng Cấp] {item_dang_chon['title']}", st.session_state.noi_dung_toi_uu)
                            st.toast("Đã lưu vào Thư viện Lịch sử!", icon="💾")

                    tab_opt_code, tab_opt_view = st.tabs(["📋 Mã HTML Mới để Copy", "👁️ Xem Trước Bản Mới"])
                    with tab_opt_code:
                        st.code(st.session_state.noi_dung_toi_uu, language="html")
                    with tab_opt_view:
                        preview_opt = f"""<div style="font-family: Arial, sans-serif; line-height: 1.7; color: #333; max-width: 900px; margin: 0 auto;">{st.session_state.noi_dung_toi_uu}</div>"""
                        components.html(preview_opt, height=1000, scrolling=True)

            # ==================================================================
            # TAB C: XEM BẢN GỐC ĐANG CÓ TRÊN WEB
            # ==================================================================
            with tab_original_view:
                st.markdown(f"##### 👁️ Nội dung nguyên bản đang có trên website: [Xem bài gốc]({item_dang_chon['link']})")
                tab_orig_view, tab_orig_code = st.tabs(["👁️ Hiển Thị Giao Diện Gốc", "📋 Mã HTML Gốc"])
                with tab_orig_view:
                    components.html(f"""<div style="font-family: Arial, sans-serif; line-height: 1.7; color: #333; max-width: 900px; margin: 0 auto;">{item_dang_chon['content']}</div>""", height=800, scrolling=True)
                with tab_orig_code:
                    st.code(item_dang_chon["content"], language="html")

        else:
            st.info("👈 Hãy chọn một **Trang Sản Phẩm (Pages)** hoặc **Bài Viết (Posts)** từ danh sách bên trái để bắt đầu xem và chỉnh sửa!")
            st.markdown("""
            **Các tính năng nổi bật của khu vực này:**
            - 📑 **Xem toàn bộ danh mục website**: Dễ dàng chuyển đổi giữa **Trang Sản Phẩm / Trang Tĩnh (Pages)**, **Bài Viết Tin Tức (Posts)** và **Sản Phẩm Cửa Hàng (WooCommerce)**.
            - ✏️ **Trình Soạn Thảo Trực Tiếp (Live Editor)**: Cho phép bạn sửa tiêu đề, chỉnh sửa trực tiếp mã HTML, bổ sung bảng giá VAT 8%, hotline 0912 565 353 và cập nhật tức thì lên website `hwood.vn`.
            - 🤖 **AI SEO Refresher**: Tự động phân tích điểm yếu (Content Audit) và viết lại trang chuẩn SEO thương hiệu HWOOD 2026.
            - 📚 **Tra cứu kỹ thuật tiện ích**: Tích hợp sẵn 14 bộ tài liệu sản phẩm HWOOD để bạn tra cứu quy cách và báo giá ngay tại chỗ mà không cần mở nhiều cửa sổ.
            """)
