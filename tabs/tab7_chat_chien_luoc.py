import streamlit as st
from modules.file_handler import doc_noi_dung_file_dinh_kem
from modules.chat_advisor import (
    doc_quy_chuan_chung,
    luu_quy_chuan_chung,
    doc_lich_su_chat_advisor,
    luu_lich_su_chat_advisor,
    xoa_lich_su_chat_advisor,
    gui_tin_nhan_advisor,
    ai_trich_xuat_quy_chuan_tu_chat
)

def render_tab7(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, danh_sach_bai_viet_wp=None, kho_tri_thuc=""):
    """Giao diện Tab 7: Khung Chat Chiến Lược SEO & Quản Lý Quy Chuẩn Lỗi Sai Chung Cho Toàn Bộ Bài Viết"""
    st.markdown("### 💬 Cố Vấn Chiến Lược SEO & Bộ Nhớ Quy Chuẩn Lỗi Sai Chung")
    st.markdown("Thay vì phải nhắc đi nhắc lại từng lỗi sai ở từng bài viết riêng lẻ, bạn có thể **trao đổi định hướng chung tại đây**. Mọi nguyên tắc, lưu ý về kỹ thuật vật liệu, giá cả hay tone giọng thương hiệu sẽ được **lưu vĩnh viễn vào Bộ Nhớ Hệ Thống** và áp dụng tự động cho 100% bài viết!")

    col_chat, col_rules = st.columns([1.6, 1.4])

    # ==============================================================================
    # CỘT PHẢI: BỘ NHỚ QUY CHUẨN & LỖI SAI CHUNG (GLOBAL GUIDELINES)
    # ==============================================================================
    with col_rules:
        st.markdown("#### 📋 Bộ Quy Chuẩn & Lỗi Sai Cần Tránh Chung")
        st.caption("⚡ *Các quy chuẩn này được tự động nạp vào trí nhớ của AI khi tạo bài mới ở Tab 1 hoặc tinh chỉnh bài viết.*")

        danh_sach_qc = doc_quy_chuan_chung()

        # Hiển thị danh sách dạng bullet points đẹp mắt
        for i, qc in enumerate(danh_sach_qc, 1):
            st.markdown(
                f"""<div style="background-color: #f8fafc; border-left: 4px solid #3b8632; border-radius: 4px; padding: 10px 14px; margin-bottom: 8px; font-size: 0.88rem; color: #1e293b; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
                    <b>{i}.</b> {qc}
                </div>""",
                unsafe_allow_html=True
            )

        # Chỉnh sửa bộ quy chuẩn
        with st.expander("✏️ Thêm / Chỉnh Sửa Quy Chuẩn Hệ Thống Bằng Tay", expanded=False):
            st.markdown("Nhập các nguyên tắc (mỗi nguyên tắc trên 1 dòng):")
            text_qc_hien_tai = "\n".join(danh_sach_qc)
            new_text_qc = st.text_area(
                "Nội dung quy chuẩn:",
                value=text_qc_hien_tai,
                height=220,
                key="txt_area_rules_edit"
            )
            col_rc1, col_rc2 = st.columns(2)
            with col_rc1:
                if st.button("💾 Lưu Bộ Quy Chuẩn Này", key="btn_save_rules_manual", use_container_width=True, type="primary"):
                    lines = [l.strip() for l in new_text_qc.split("\n") if l.strip()]
                    luu_quy_chuan_chung(lines)
                    st.success("🎉 Đã lưu thành công bộ quy chuẩn vào toàn hệ thống!")
                    st.rerun()
            with col_rc2:
                if st.button("🔄 Khôi phục mặc định", key="btn_reset_rules_default", use_container_width=True):
                    from modules.chat_advisor import DEFAULT_QUY_CHUAN
                    luu_quy_chuan_chung(DEFAULT_QUY_CHUAN)
                    st.info("Đã khôi phục bộ quy chuẩn ban đầu!")
                    st.rerun()

        # AI tự động rút ra quy chuẩn từ cuộc hội thoại
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🤖 AI Tự Động Rút Nguyên Tắc Mới Từ Cuộc Chat", key="btn_ai_extract_rules", use_container_width=True):
            if not api_key:
                st.error("Vui lòng nhập DeepSeek API Key ở thanh bên trái!")
            else:
                lich_su_hien_tai = doc_lich_su_chat_advisor()
                if not lich_su_hien_tai:
                    st.warning("Chưa có đoạn chat nào để phân tích. Hãy trao đổi với AI ở khung chat bên trái trước nhé!")
                else:
                    with st.spinner("🤖 AI đang tổng hợp các lỗi sai & nguyên tắc mới từ cuộc trò chuyện..."):
                        try:
                            nt_moi = ai_trich_xuat_quy_chuan_tu_chat(api_key, chon_model, lich_su_hien_tai)
                            if nt_moi:
                                danh_sach_qc.extend(nt_moi)
                                luu_quy_chuan_chung(danh_sach_qc)
                                st.success(f"🎉 Đã tự động thêm **{len(nt_moi)} nguyên tắc mới** vào bộ nhớ chung!")
                                st.rerun()
                            else:
                                st.info("Không tìm thấy nguyên tắc kỹ thuật mới nổi bật trong các tin nhắn gần đây.")
                        except Exception as ex_nt:
                            st.error(f"Lỗi rút trích nguyên tắc: {ex_nt}")

    # ==============================================================================
    # CỘT TRÁI: KHUNG CHAT TRAO ĐỔI VỚI CỐ VẤN AI (MULTI-TURN CHAT)
    # ==============================================================================
    with col_chat:
        st.markdown("#### 💬 Khung Chat Trao Đổi Định Hướng & Góp Ý Lỗi Sai")
        
        # Đọc lịch sử chat
        chat_history = doc_lich_su_chat_advisor()

        # Khung hiển thị tin nhắn có thanh cuộn
        chat_container = st.container(height=420)
        with chat_container:
            if not chat_history:
                st.info("👋 Chào bạn! Tôi là Cố vấn Chiến lược SEO của HWOOD VIỆT NAM.\n\nBạn có thể trao đổi với tôi về:\n- 🎯 Định hướng bài viết tháng tới nên tập trung vào sản phẩm gì?\n- ⚠️ Các lỗi sai chung mà AI hay mắc phải (bảng giá, VAT, bảo hành, khung đà, keo dán...).\n- 💡 Ý tưởng triển khai bài viết, cách tối ưu tỷ lệ chuyển đổi cho website.\n\nHãy nhắn tin cho tôi ở khung bên dưới nhé!")
            else:
                for msg in chat_history:
                    avatar_icon = "🧑‍💻" if msg["role"] == "user" else "🪵"
                    with st.chat_message(msg["role"], avatar=avatar_icon):
                        st.markdown(msg["content"])

        # Đính kèm file / hình ảnh tham khảo trong cuộc chat
        with st.expander("📎 Đính kèm hình ảnh hoặc tài liệu góp ý chung (Tùy chọn)"):
            file_chat = st.file_uploader(
                "Tải lên ảnh chụp màn hình lỗi, file quy chuẩn hoặc tài liệu tham khảo:",
                type=["png", "jpg", "jpeg", "webp", "docx", "pdf", "txt"],
                key="uploader_chat_advisor"
            )
            if file_chat:
                st.caption(f"Đã chọn: `{file_chat.name}` ({file_chat.size / 1024:.1f} KB)")

        # Nút xóa lịch sử chat
        col_act1, col_act2 = st.columns([3, 1.2])
        with col_act2:
            if st.button("🧹 Bắt đầu phiên mới", key="btn_clear_chat_advisor", use_container_width=True):
                xoa_lich_su_chat_advisor()
                st.toast("Đã làm mới khung chat!", icon="🧹")
                st.rerun()

        # Ô nhập tin nhắn
        user_msg = st.chat_input("Nhập câu hỏi chiến lược hoặc lỗi sai cần lưu ý chung...")
        if user_msg:
            if not api_key:
                st.error("Vui lòng nhập DeepSeek API Key ở thanh bên trái!")
            else:
                # Đọc nội dung file đính kèm nếu có
                file_context = ""
                if file_chat:
                    text_extracted, summary = doc_noi_dung_file_dinh_kem(file_chat)
                    file_context = f"{summary}\n{text_extracted}"

                # Thêm tin nhắn user vào lịch sử
                chat_history.append({"role": "user", "content": user_msg})
                luu_lich_su_chat_advisor(chat_history)

                # Gọi AI phản hồi
                with st.spinner("🤖 Cố vấn SEO đang phân tích và trả lời..."):
                    try:
                        ai_reply = gui_tin_nhan_advisor(
                            api_key=api_key,
                            model=chon_model,
                            messages=chat_history,
                            file_context=file_context,
                            kho_tri_thuc=kho_tri_thuc
                        )
                        chat_history.append({"role": "assistant", "content": ai_reply})
                        luu_lich_su_chat_advisor(chat_history)
                        st.rerun()
                    except Exception as ex_chat:
                        st.error(f"Lỗi phản hồi AI: {ex_chat}")
