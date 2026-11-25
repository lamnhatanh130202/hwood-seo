import math
import streamlit as st
from openai import OpenAI

from modules.history_manager import lay_danh_sach_lich_su, luu_tu_khoa_tuy_chinh
from modules.keyword_matrix import lay_ma_tran_toan_bo_keyword, xuat_csv_ma_tran_keyword

def render_tab3(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, danh_sach_bai_viet_wp=None, kho_tri_thuc=""):
    """Giao diện Tab 3: Bảng Thống Kê & Ma Trận Keyword Đang Sử Dụng"""
    st.markdown("### 📊 Bảng Thống Kê & Ma Trận Keyword Đang Sử Dụng")
    st.markdown("Hệ thống tự động quét và bóc tách **Từ Khóa Chính (Focus Keywords)** và **Các Từ Khóa Phụ Đi Kèm (Secondary/LSI Keywords)** từ toàn bộ các bài viết đã có trên website HWOOD (`hwood.vn`) và kho lưu trữ máy tính. Giúp bạn kiểm soát cấu trúc Topic Cluster và phát hiện nguy cơ **Ăn thịt từ khóa (Keyword Cannibalization)**!")

    # Lấy dữ liệu ma trận từ khóa
    ds_lich_su_all = lay_danh_sach_lich_su()
    ma_tran_all = lay_ma_tran_toan_bo_keyword(danh_sach_bai_viet_wp, ds_lich_su_all)

    if ma_tran_all:
        # Tính toán các chỉ số thống kê
        tong_so_bai = len(ma_tran_all)
        unique_focus = set(x["tu_khoa_chinh"].lower() for x in ma_tran_all)
        tong_so_focus = len(unique_focus)
        
        all_secondary = []
        for x in ma_tran_all:
            all_secondary.extend(x["tu_khoa_phu"])
        tong_so_secondary = len(set(s.lower() for s in all_secondary))
        
        trung_lap_items = [x for x in ma_tran_all if x.get("trung_lap")]
        unique_trung_lap_keys = set(x["tu_khoa_chinh"].lower() for x in trung_lap_items)

        # 1. KHỐI THỐNG KÊ TỔNG QUAN (KPI CARDS)
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        with col_kpi1:
            st.markdown(f'<div style="background-color: #f8faf8; border: 1px solid #d4e7d4; border-radius: 8px; padding: 14px; text-align: center;"><div style="color: #666; font-size: 0.9em; font-weight: bold;">📑 Tổng Bài Viết Đã Quét</div><div style="color: #3b8632; font-size: 1.8em; font-weight: bold; margin-top: 4px;">{tong_so_bai:,}</div><div style="color: #888; font-size: 0.8em;">Website & Thư viện máy</div></div>', unsafe_allow_html=True)
        with col_kpi2:
            st.markdown(f'<div style="background-color: #f8faf8; border: 1px solid #d4e7d4; border-radius: 8px; padding: 14px; text-align: center;"><div style="color: #666; font-size: 0.9em; font-weight: bold;">🎯 Từ Khóa Chính (Focus)</div><div style="color: #1e6b15; font-size: 1.8em; font-weight: bold; margin-top: 4px;">{tong_so_focus:,}</div><div style="color: #888; font-size: 0.8em;">Từ khóa cốt lõi độc nhất</div></div>', unsafe_allow_html=True)
        with col_kpi3:
            st.markdown(f'<div style="background-color: #f8faf8; border: 1px solid #d4e7d4; border-radius: 8px; padding: 14px; text-align: center;"><div style="color: #666; font-size: 0.9em; font-weight: bold;">📎 Từ Khóa Phụ Đi Kèm</div><div style="color: #2e6628; font-size: 1.8em; font-weight: bold; margin-top: 4px;">{tong_so_secondary:,}</div><div style="color: #888; font-size: 0.8em;">Secondary & LSI Keywords</div></div>', unsafe_allow_html=True)
        with col_kpi4:
            bg_trung = "#fff5f5" if len(unique_trung_lap_keys) > 0 else "#f8faf8"
            border_trung = "#f5c6cb" if len(unique_trung_lap_keys) > 0 else "#d4e7d4"
            color_trung = "#d9534f" if len(unique_trung_lap_keys) > 0 else "#3b8632"
            st.markdown(f'<div style="background-color: {bg_trung}; border: 1px solid {border_trung}; border-radius: 8px; padding: 14px; text-align: center;"><div style="color: #666; font-size: 0.9em; font-weight: bold;">⚠️ Nguy Cơ Ăn Thịt Từ Khóa</div><div style="color: {color_trung}; font-size: 1.8em; font-weight: bold; margin-top: 4px;">{len(unique_trung_lap_keys)}</div><div style="color: #888; font-size: 0.8em;">{len(trung_lap_items)} bài viết bị trùng lặp</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. BỘ LỌC VÀ CÔNG CỤ TÌM KIẾM
        col_fil1, col_fil2, col_fil3, col_fil4 = st.columns([2, 2, 1.2, 1.2])
        
        ds_chu_de_co_san = ["Tất Cả Cụm Chủ Đề"] + sorted(list(set(x["danh_muc"] for x in ma_tran_all)))
        with col_fil1:
            loc_chu_de_kw = st.selectbox("📂 Lọc theo Cụm Chủ Đề:", options=ds_chu_de_co_san, key="sb_loc_chu_de_kw")
        with col_fil2:
            tim_kiem_kw_text = st.text_input("🔎 Tìm kiếm từ khóa hoặc tiêu đề:", placeholder="Nhập từ khóa cần lọc...", key="input_search_kw_matrix")
        with col_fil3:
            so_dong_tren_trang = st.selectbox("Số dòng/trang:", options=[10, 15, 25, 50, 100], index=1, key="sb_rows_per_page_kw")
        with col_fil4:
            st.write("")
            csv_content = xuat_csv_ma_tran_keyword(ma_tran_all)
            st.download_button(
                label="📥 Xuất File Excel / CSV",
                data=csv_content,
                file_name="bang_thong_ke_keyword_hwood.csv",
                mime="text/csv",
                use_container_width=True,
                help="Tải về file Excel bảng thống kê đầy đủ toàn bộ từ khóa chính và từ khóa phụ (chuẩn tiếng Việt có dấu)"
            )

        col_chk1, col_chk2 = st.columns([2, 1])
        with col_chk1:
            chi_hien_cannibal = st.checkbox("⚠️ Chỉ hiển thị các từ khóa đang bị trùng lặp (Cannibalization)", value=False, key="chk_filter_cannibal")

        with st.expander("✏️ Sửa / Đồng bộ riêng Focus Keyword cho từng bài (Khớp 100% Yoast SEO)", expanded=False):
            st.markdown("Hệ thống đã tự động bóc tách từ khóa chuẩn xác theo URL Slug và Tiêu đề. Nếu bạn muốn điều chỉnh riêng cho bất kỳ bài viết nào để khớp tuyệt đối với cụm từ khóa đặt trong Yoast SEO Premium, bạn có thể chỉnh và lưu tại đây:")
            col_ov1, col_ov2, col_ov3 = st.columns([3, 2, 1])
            with col_ov1:
                ds_bai_options = {f"[{item['id']}] {item['tieu_de'][:55]}...": item for item in ma_tran_all}
                bai_duoc_chon_str = st.selectbox("Chọn bài viết cần kiểm tra / sửa từ khóa:", options=list(ds_bai_options.keys()), key="sb_override_post")
                selected_post_obj = ds_bai_options[bai_duoc_chon_str]
            with col_ov2:
                kw_moi = st.text_input("Cụm từ khóa chính (Focus Keyword):", value=selected_post_obj["tu_khoa_chinh"], key="input_override_kw")
            with col_ov3:
                st.write("")
                if st.button("💾 Lưu Keyword", key="btn_save_override_kw", use_container_width=True):
                    if kw_moi.strip():
                        val = kw_moi.strip()
                        luu_tu_khoa_tuy_chinh(selected_post_obj["id"], val)
                        if selected_post_obj.get("slug"):
                            luu_tu_khoa_tuy_chinh(selected_post_obj["slug"], val)
                        if selected_post_obj.get("tieu_de"):
                            luu_tu_khoa_tuy_chinh(selected_post_obj["tieu_de"], val)
                        st.success(f"🎉 Đã cập nhật cụm từ khóa chính: '{val}' cho bài viết [{selected_post_obj['id']}]!")
                        st.rerun()

        # Áp dụng bộ lọc
        ds_hien_thi_matrix = ma_tran_all
        if loc_chu_de_kw != "Tất Cả Cụm Chủ Đề":
            ds_hien_thi_matrix = [x for x in ds_hien_thi_matrix if x["danh_muc"] == loc_chu_de_kw]
        if tim_kiem_kw_text.strip():
            kw_query = tim_kiem_kw_text.lower()
            ds_hien_thi_matrix = [
                x for x in ds_hien_thi_matrix 
                if kw_query in x["tieu_de"].lower() 
                or kw_query in x["tu_khoa_chinh"].lower() 
                or any(kw_query in s.lower() for s in x["tu_khoa_phu"])
            ]
        if chi_hien_cannibal:
            ds_hien_thi_matrix = [x for x in ds_hien_thi_matrix if x.get("trung_lap")]

        # 3. BẢNG THỐNG KÊ MA TRẬN KEYWORD (BẢNG TRỰC QUAN)
        st.markdown(f"#### 📋 Danh sách chi tiết ({len(ds_hien_thi_matrix)} bài viết phù hợp):")

        # Phân trang
        total_rows = len(ds_hien_thi_matrix)
        total_kw_pages = max(1, math.ceil(total_rows / so_dong_tren_trang))
        if st.session_state.kw_matrix_page_num > total_kw_pages:
            st.session_state.kw_matrix_page_num = 1

        start_kw = (st.session_state.kw_matrix_page_num - 1) * so_dong_tren_trang
        end_kw = start_kw + so_dong_tren_trang
        rows_trang_nay = ds_hien_thi_matrix[start_kw : end_kw]

        st.caption(f"Đang hiển thị Trang {st.session_state.kw_matrix_page_num}/{total_kw_pages} (Từ dòng {start_kw + 1} đến {min(end_kw, total_rows)} trên tổng số {total_rows}):")

        # Tạo bảng hiển thị đẹp mắt
        html_table_rows = []
        for idx, row in enumerate(rows_trang_nay, start_kw + 1):
            badge_color = "#3b8632"
            badge_bg = "#eef7ee"
            badge_alert = ""
            if row.get("trung_lap"):
                badge_color = "#d9534f"
                badge_bg = "#fff0f0"
                badge_alert = f'<span style="background-color: #d9534f; color: #fff; font-size: 0.75em; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">⚠️ Trùng {row["tan_suat"]} bài</span>'

            sec_tags_html = "".join([
                f'<span style="display: inline-block; background-color: #f1f5f9; color: #334155; padding: 3px 8px; border-radius: 12px; margin: 2px 4px 2px 0; font-size: 0.82em; border: 1px solid #e2e8f0;">{s}</span>'
                for s in row["tu_khoa_phu"]
            ])

            link_html = f'<a href="{row["link"]}" target="_blank" style="color: #3b8632; text-decoration: none; font-weight: bold;">🔗 Xem web</a>' if row.get("link") else f'<code>ID: {row["id"]}</code>'

            row_html = (
                f'<tr style="border-bottom: 1px solid #eee;">'
                f'<td style="padding: 10px 8px; text-align: center; color: #666; font-size: 0.9em;">{idx}</td>'
                f'<td style="padding: 10px 8px;">'
                f'<div style="font-weight: 600; color: #1e293b; font-size: 0.95em;">{row["tieu_de"]}</div>'
                f'<div style="color: #64748b; font-size: 0.8em; margin-top: 2px;">{row["danh_muc"]} | {row["nguon"]} | {link_html}</div>'
                f'</td>'
                f'<td style="padding: 10px 8px; min-width: 180px;">'
                f'<div style="display: inline-block; background-color: {badge_bg}; color: {badge_color}; border: 1px solid {badge_color}; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.9em;">🎯 {row["tu_khoa_chinh"]}</div>'
                f'{badge_alert}'
                f'</td>'
                f'<td style="padding: 10px 8px; min-width: 320px;">{sec_tags_html if sec_tags_html else "<span style=\'color: #94a3b8; font-style: italic;\'>Đang cập nhật...</span>"}</td>'
                f'</tr>'
            )
            html_table_rows.append(row_html)

        full_table_html = (
            '<div style="overflow-x: auto; margin-top: 10px; border: 1px solid #e2e8f0; border-radius: 8px;">'
            '<table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; background-color: #fff;">'
            '<thead><tr style="background-color: #f8fafc; border-bottom: 2px solid #e2e8f0; text-align: left; color: #475569; font-size: 0.88em; text-transform: uppercase; letter-spacing: 0.03em;">'
            '<th style="padding: 12px 8px; width: 50px; text-align: center;">STT</th>'
            '<th style="padding: 12px 8px; width: 35%;">Tiêu Đề Bài Viết & Cụm Chủ Đề</th>'
            '<th style="padding: 12px 8px; width: 25%;">Từ Khóa Chính (Focus Keyword)</th>'
            '<th style="padding: 12px 8px; width: 40%;">Các Từ Khóa Phụ Đi Kèm (Secondary / LSI)</th>'
            '</tr></thead><tbody>'
            + "".join(html_table_rows)
            + '</tbody></table></div>'
        )
        st.markdown(full_table_html, unsafe_allow_html=True)

        # Nút chuyển trang cho bảng ma trận
        if total_kw_pages > 1:
            col_kwn1, col_kwn2, col_kwn3 = st.columns([1, 2, 1])
            with col_kwn1:
                if st.button("⬅️ Trang Trước", key="btn_kw_matrix_prev", disabled=(st.session_state.kw_matrix_page_num <= 1), use_container_width=True):
                    st.session_state.kw_matrix_page_num -= 1
                    st.rerun()
            with col_kwn2:
                st.markdown(f"<div style='text-align: center; padding-top: 8px; font-weight: bold;'>Trang {st.session_state.kw_matrix_page_num} / {total_kw_pages}</div>", unsafe_allow_html=True)
            with col_kwn3:
                if st.button("Trang Sau ➡️", key="btn_kw_matrix_next", disabled=(st.session_state.kw_matrix_page_num >= total_kw_pages), use_container_width=True):
                    st.session_state.kw_matrix_page_num += 1
                    st.rerun()

        st.markdown("---")

        # 4. KHU VỰC CẢNH BÁO CHI TIẾT ĂN THỊT TỪ KHÓA (CANNIBALIZATION AUDIT)
        with st.expander("⚠️ Chi Tiết Cảnh Báo Ăn Thịt Từ Khóa (Keyword Cannibalization Audit)"):
            if unique_trung_lap_keys:
                st.warning(f"Phát hiện **{len(unique_trung_lap_keys)} từ khóa chính** đang được sử dụng ở nhiều bài viết khác nhau. Việc này khiến các bài viết cùng tranh giành thứ hạng trên Google, làm giảm sức mạnh SEO.")
                for kw_dup in sorted(unique_trung_lap_keys):
                    bai_trung = [x for x in ma_tran_all if x["tu_khoa_chinh"].lower() == kw_dup]
                    st.markdown(f"**🎯 Từ khóa: `{kw_dup.title()}`** ({len(bai_trung)} bài viết cùng nhắm mục tiêu):")
                    for b in bai_trung:
                        link_info = f"[🔗 Xem bài]({b['link']})" if b.get("link") else f"ID: `{b['id']}`"
                        st.markdown(f"- 📄 **{b['tieu_de']}** ({b['nguon']}) — {link_info}")
                    st.info(f"💡 **Giải pháp SEO đề xuất:** Hãy phân tách mục đích tìm kiếm (Search Intent) giữa các bài viết trên. Ví dụ: 1 bài tập trung vào **Báo Giá Chi Tiết**, 1 bài về **Hướng Dẫn Kỹ Thuật Thi Công**, 1 bài về **Mẫu Thiết Kế Thực Tế**.")
                    st.write("")
            else:
                st.success("🎉 Rất tốt! Không phát hiện hiện tượng ăn thịt từ khóa nghiêm trọng nào trong hệ thống bài viết hiện tại.")

        # 5. KHU VỰC AI GỢI Ý MỞ RỘNG TỪ KHÓA MỚI (KEYWORD GAP ANALYSIS)
        with st.expander("🤖 AI Phân Tích & Gợi Ý Mở Rộng Từ Khóa Mới Còn Thiếu (Keyword Gap)"):
            st.markdown("AI DeepSeek sẽ đối chiếu toàn bộ các từ khóa hiện có của website với Bộ não 5 Topic Cluster của HWOOD để tìm ra những **từ khóa phụ tiềm năng cao** và **từ khóa ngách (long-tail)** mà website chưa khai thác!")
            
            btn_run_kw_gap = st.button("🚀 Bắt Đầu Quét Lỗ Hổng Từ Khóa Bằng DeepSeek", type="primary", use_container_width=True)
            if btn_run_kw_gap:
                sample_covered_keys = sorted(list(unique_focus))[:60]
                prompt_gap = f"""Bạn là Chuyên gia Chiến lược SEO hàng đầu của thương hiệu HWOOD VIỆT NAM.

DANH SÁCH CÁC TỪ KHÓA CHÍNH HIỆN ĐANG ĐƯỢC PHỦ TRÊN WEBSITE HWOOD.VN:
{sample_covered_keys}

BỘ NÃO TRI THỨC VÀ 5 TRỤ CỘT TOPIC CLUSTER HWOOD:
{kho_tri_thuc}

NHIỆM VỤ CỦA BẠN (KEYWORD GAP ANALYSIS & EXPANSION CHO NĂM 2026):
1. Đánh giá ngắn gọn: HWOOD đang phủ tốt những mảng từ khóa nào và còn thiếu những góc nhìn nào?
2. Lập danh sách 15-20 TỪ KHÓA MỚI TIỀM NĂNG CAO (Gồm Từ khóa chính và 2-3 Từ khóa phụ đi kèm) thuộc 5 cụm sản phẩm:
   - Gỗ nhựa ngoài trời WPC / ASA
   - Tấm nhựa ốp tường PVC vân đá & Nano
   - Trần nhựa nano giật cấp
   - Sàn gỗ nhựa hồ bơi & ban công
   - Bàn ghế sân vườn polywood & phụ kiện
3. Với mỗi từ khóa mới, nêu rõ: Mục đích tìm kiếm (Search Intent: Mua hàng / So sánh / Kỹ thuật) và Tiêu đề bài viết gợi ý chuẩn SEO.

Hãy trình bày rõ ràng, súc tích bằng markdown."""

                from modules.antigravity_bridge import is_antigravity_mode, save_antigravity_prompt
                if is_antigravity_mode(api_key):
                    save_antigravity_prompt("keyword_gap", "Phân tích lỗ hổng từ khóa HWOOD", prompt_gap)
                    st.session_state["ag_tab3_prompt"] = prompt_gap
                else:
                    client_kw = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

                    with st.spinner("🤖 DeepSeek đang phân tích khoảng trống từ khóa (Keyword Gap)... Vui lòng chờ vài giây!"):
                        try:
                            from modules.ai_engine import goi_chat_completion_an_toan
                            resp_gap = goi_chat_completion_an_toan(
                                client=client_kw,
                                model=chon_model,
                                messages=[{"role": "user", "content": prompt_gap}],
                                max_tokens=3000,
                                temperature=0.7
                            )
                            st.session_state.kw_ai_suggestions = resp_gap.choices[0].message.content.strip()
                            st.success("🎉 Đã phân tích xong khoảng trống từ khóa!")
                        except Exception as ex_gap:
                            st.error(f"Lỗi phân tích AI: {ex_gap}")

            if st.session_state.get("ag_tab3_prompt"):
                from modules.antigravity_bridge import render_antigravity_panel
                pasted_gap = render_antigravity_panel(
                    task_key="tab3_gap",
                    title="Phân tích lỗ hổng từ khóa (Keyword Gap)",
                    prompt_text=st.session_state["ag_tab3_prompt"],
                    paste_label="📥 Dán kết quả phân tích từ khóa từ Antigravity vào đây:",
                    apply_label="✅ Hiển thị kết quả phân tích",
                )
                if pasted_gap:
                    st.session_state.kw_ai_suggestions = pasted_gap
                    st.session_state["ag_tab3_prompt"] = ""
                    st.rerun()

            if st.session_state.kw_ai_suggestions:
                st.markdown("---")
                st.markdown("#### 💡 Kết quả Đề xuất Mở rộng Từ khóa Mới từ DeepSeek:")
                st.markdown(st.session_state.kw_ai_suggestions)

    else:
        st.info("Chưa tìm thấy bài viết nào để phân tích ma trận từ khóa. Hãy kết nối website WordPress hoặc viết bài mới ở Tab 1!")
