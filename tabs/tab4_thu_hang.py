import os
import time
from datetime import datetime
import streamlit as st

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from modules.history_manager import lay_danh_sach_lich_su
from modules.keyword_matrix import (
    lay_ma_tran_toan_bo_keyword,
    trich_xuat_danh_sach_keyword_chuan_hwood
)
from modules.rank_tracker import (
    doc_lich_su_thu_hang, 
    luu_lich_su_thu_hang, 
    check_thu_hang_google_keyword, 
    xuat_csv_thu_hang, 
    BO_TU_KHOA_HWOOD_PRESETS,
    tim_bai_viet_khop_nhat_wp,
    tao_link_google_search,
    nhap_ket_qua_spineditor,
    doc_database_keywords,
    luu_database_keywords,
    dong_bo_ket_qua_quet_vao_db,
    them_tu_khoa_vao_db,
    xoa_tu_khoa_khoi_db,
    xuat_csv_database_keywords
)
from modules.rank_optimizer import (
    lay_toan_bo_chan_doan_ngoai_top,
    dua_vao_ke_hoach_thang_nhanh,
    dua_vao_bot_farm_queue,
    chan_doan_tu_khoa_ngoai_top
)

# ==============================================================================
# MODAL POPUP: DEBUG HTML LỊCH SỬ CHECK (GIỐNG HỆT GIAO DIỆN SPINDITOR)
# ==============================================================================
@st.dialog("Chi Tiết Thứ Hạng & Bằng Chứng SERP Google", width="large")
def modal_serp_debug(row, danh_sach_bai_viet_wp=None):
    kw = row.get("tu_khoa", "")
    rank = row.get("rank")
    link = row.get("link", "")
    title = row.get("title", "")
    thoi_gian = row.get("thoi_gian", datetime.now().strftime("%d/%m/%Y"))
    
    if not link or not title:
        matched = tim_bai_viet_khop_nhat_wp(kw, danh_sach_bai_viet_wp)
        if matched:
            if not link:
                link = matched.get("link", "")
            if not title:
                title = matched.get("title", "")
                
    if not title:
        title = f"{kw.title()}: Vật liệu trang trí HWOOD"
        
    google_url = tao_link_google_search(kw)
    
    st.markdown(f"**Từ khóa kiểm tra:** `{kw}` &nbsp;|&nbsp; **Cập nhật:** `{thoi_gian}` &nbsp;|&nbsp; **Website mục tiêu:** `hwood.vn`")
    
    if rank:
        st.markdown(f"""
        <div style="background-color: #f0fdf4; border: 2px solid #22c55e; border-radius: 8px; padding: 18px; margin: 12px 0;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <span style="background: #15803d; color: white; font-size: 0.85em; font-weight: bold; padding: 3px 10px; border-radius: 4px;">
                    🏆 Vị trí thực tế trên Google: Top {rank}
                </span>
                <span style="font-size: 0.82em; color: #15803d; font-weight: bold;">HWOOD VIỆT NAM (XÁC THỰC SERP)</span>
            </div>
            <a href="{link}" target="_blank" style="color: #1a0dab; font-size: 1.2em; font-weight: 600; text-decoration: none; display: block; margin-bottom: 6px;">
                {title}
            </a>
            <div style="color: #4b5563; font-size: 0.88em; word-break: break-all; margin-bottom: 8px;">
                🔗 {link or 'Đang cập nhật liên kết...'}
            </div>
            <div style="color: #374151; font-size: 0.85em; background: #fff; padding: 10px; border-radius: 6px; border: 1px solid #d1d5db;">
                💡 <em>Kết quả này được trích xuất trực tiếp từ trang kết quả tìm kiếm Google Việt Nam không cá nhân hóa. Bấm nút bên dưới để mở Google kiểm tra lại bằng mắt thường.</em>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: #f8fafc; border: 1px dashed #94a3b8; border-radius: 8px; padding: 18px; margin: 12px 0; text-align: center;">
            <div style="color: #475569; font-size: 1.1em; font-weight: bold; margin-bottom: 8px;">
                ⚪ Từ khóa '{kw}' chưa xuất hiện trong top kết quả đã quét
            </div>
            <p style="color: #64748b; font-size: 0.88em; margin-bottom: 12px;">
                Google hiện chưa ghi nhận đường dẫn hwood.vn trong top 20 vị trí đầu tiên của trang tìm kiếm.
            </p>
            <div style="color: #334155; font-size: 0.85em; text-align: left; background: #fff; padding: 10px; border-radius: 6px; border: 1px solid #e2e8f0;">
                📌 <strong>Liên kết bài viết liên quan nhất trên website:</strong><br>
                <a href="{link}" target="_blank" style="color: #1d4ed8;">{link or 'Chưa có bài viết tương ứng'}</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    col_d1, col_d2 = st.columns([1.6, 1])
    with col_d1:
        st.link_button(f"🌐 Mở Google Tìm Kiếm Trực Tiếp ({kw}) ↗", google_url, type="primary", use_container_width=True)
    with col_d2:
        if st.button("❌ Đóng Cửa Sổ Bằng Chứng", key=f"btn_close_dlg_{kw}", use_container_width=True):
            st.rerun()
            
    with st.expander("✏️ Cập nhật nhanh thứ hạng hoặc liên kết này"):
        c_k1, c_k2 = st.columns([1, 2])
        with c_k1:
            new_r = st.number_input("Vị trí Top mới:", min_value=1, max_value=100, value=rank if rank else 2, step=1, key=f"dlg_r_{kw}")
        with c_k2:
            new_u = st.text_input("URL bài viết:", value=link, key=f"dlg_u_{kw}")
        if st.button("💾 Xác nhận lưu", key=f"dlg_save_{kw}"):
            rank_history_data = doc_lich_su_thu_hang()
            k_clean = kw.lower().strip()
            rank_history_data[k_clean] = {
                "rank": int(new_r),
                "link": new_u,
                "title": title,
                "thoi_gian": thoi_gian
            }
            luu_lich_su_thu_hang(rank_history_data)
            
            # Đồng bộ ngay vào Cơ sở dữ liệu từ khóa
            dong_bo_ket_qua_quet_vao_db([{
                "tu_khoa": kw,
                "rank": int(new_r),
                "rank_best": int(new_r),
                "link": new_u,
                "title": title,
                "thoi_gian": thoi_gian
            }], danh_sach_bai_viet_wp)

            for r in st.session_state.rank_check_results:
                if r["tu_khoa"].lower().strip() == k_clean:
                    r["rank"] = int(new_r)
                    r["rank_str"] = f"Top {int(new_r)}"
                    r["link"] = new_u
                    r["bien_dong_str"] = "✏️ Đã xác thực"
                    break
            st.success("Đã cập nhật và lưu vào Cơ sở dữ liệu!")
            st.rerun()


def render_tab4(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, danh_sach_bai_viet_wp=None):
    """Giao diện Tab 4: Kiểm Tra Thứ Hạng Từ Khóa Google (Rank Tracker) & Quản Lý Data Keyword"""
    import os
    import time
    st.markdown("### 🎯 Thứ Hạng Từ Khóa Google (Rank Tracker kiểu SpinEditor)")
    st.markdown("Hệ thống tự động bóc tách **Từ khóa chính (Focus)** và **Từ khóa phụ (Secondary / LSI)** từ website `hwood.vn`, theo dõi thứ hạng thực tế trên Google Việt Nam và lưu trữ bền vững vào **Cơ sở dữ liệu Từ khóa**.")

    # Tự động nạp lại lịch sử thứ hạng đã lưu nếu phiên làm việc chưa có hoặc nếu vừa bị lỗi bot scan toàn bộ n/a
    cur_res = st.session_state.get("rank_check_results")
    is_all_na = cur_res and len(cur_res) > 0 and all(r.get("rank") is None for r in cur_res)
    if not cur_res or is_all_na:
        saved_history = doc_lich_su_thu_hang()
        if saved_history:
            restored = []
            for idx, (kw, val) in enumerate(saved_history.items(), 1):
                if not kw or any(x in kw.lower() for x in ["thủ công", "bản nháp", "giới thiệu", "liên hệ"]):
                    continue
                rk_val = val.get("rank")
                restored.append({
                    "stt": idx,
                    "tu_khoa": kw,
                    "rank": rk_val,
                    "rank_best": val.get("rank_best") or rk_val,
                    "rank_str": f"Top {rk_val}" if rk_val else "n/a",
                    "bien_dong_str": f"⬆️ {val.get('diff', rk_val)}" if rk_val else "⚪ n/a",
                    "link": val.get("link", ""),
                    "title": val.get("title", ""),
                    "thoi_gian": val.get("thoi_gian", "12/11/2026")
                })
            st.session_state.rank_check_results = restored

    # 1. CẤU HÌNH NGUỒN TỪ KHÓA
    col_rk_cfg1, col_rk_cfg2 = st.columns([2.5, 1.2])
    with col_rk_cfg1:
        nguon_rank_opt = st.radio(
            "📂 Chọn nguồn từ khóa cần kiểm tra thứ hạng:",
            options=[
                "🎯 Tự động nạp từ khóa chuẩn SEO từ bài viết hwood.vn",
                "💾 Nạp từ Cơ Sở Dữ Liệu Đã Tra Cứu (Saved Database)",
                "🔥 Chọn bộ từ khóa tổng hợp ngành HWOOD (Mẫu có sẵn)",
                "✏️ Tự gõ / Dán danh sách từ khóa riêng"
            ],
            horizontal=True,
            key="radio_rank_source_choice"
        )
    with col_rk_cfg2:
        target_domain_check = st.text_input(
            "🌐 Tên miền website kiểm tra:",
            value="hwood.vn",
            key="input_target_domain_check",
            help="Mặc định là hwood.vn. Bạn cũng có thể điền tên miền đối thủ để so sánh!"
        )

    # Chuẩn bị danh sách từ khóa mặc định tương ứng với lựa chọn
    default_keywords_str = ""
    
    # Kiểm tra xem có yêu cầu nạp cưỡng bức từ nút 1-click của Database không
    if st.session_state.get("forced_rank_keywords"):
        default_keywords_str = st.session_state["forced_rank_keywords"]
        del st.session_state["forced_rank_keywords"]
        
    elif "Tự động nạp từ khóa chuẩn SEO" in nguon_rank_opt:
        col_sub_m, col_sub_c = st.columns([1.6, 1.2])
        with col_sub_m:
            che_do_nap_opt = st.radio(
                "Phân loại từ khóa cần nạp:",
                options=[
                    "🟢 Chỉ lấy Từ khóa chính (Focus Keywords)",
                    "🔵 Lấy cả Từ khóa chính & Từ khóa phụ liên quan",
                    "🟡 Chỉ lấy Từ khóa phụ (LSI / Long-tail Keywords)"
                ],
                horizontal=True,
                key="radio_che_do_nap_kw"
            )
        with col_sub_c:
            loc_chuyen_muc_opt = st.selectbox(
                "Lọc theo nhóm ngành hàng:",
                options=[
                    "Tất cả chuyên mục",
                    "Bàn Ghế Sân Vườn & Ngoài Trời",
                    "Gỗ Nhựa Ngoài Trời & Sàn Vỉ",
                    "Tấm Ốp Nano & Trần Giật Cấp",
                    "Tấm PVC Vân Đá Cẩm Thạch",
                    "Tấm Ốp Lam Sóng",
                    "Thanh Lam Hộp & Trụ Pergola",
                    "Thanh Đa Năng & Cổng Rào"
                ],
                key="sb_loc_chuyen_muc_kw"
            )
            
        mode_code = "chinh"
        if "cả Từ khóa chính & Từ khóa phụ" in che_do_nap_opt:
            mode_code = "all"
        elif "Chỉ lấy Từ khóa phụ" in che_do_nap_opt:
            mode_code = "phu"

        ds_kws_chuan = trich_xuat_danh_sach_keyword_chuan_hwood(
            danh_sach_bai_viet_wp, 
            ds_ls=lay_danh_sach_lich_su(), 
            che_do=mode_code, 
            loc_chuyen_muc=loc_chuyen_muc_opt
        )
        default_keywords_str = "\n".join(ds_kws_chuan[:50])
        st.info(f"💡 Đã lọc sạch bài nháp/admin! Tự động nạp **{len(ds_kws_chuan[:50])} từ khóa** chuẩn SEO từ các bài viết & sản phẩm trên website hwood.vn!")
        
    elif "Cơ Sở Dữ Liệu Đã Tra Cứu" in nguon_rank_opt:
        db_all = doc_database_keywords()
        col_db_f1, col_db_f2 = st.columns([1.5, 1.2])
        with col_db_f1:
            loc_db_type = st.radio(
                "Lọc theo loại từ khóa trong DB:",
                options=["Tất cả", "Chỉ Từ khóa chính", "Chỉ Từ khóa phụ"],
                horizontal=True,
                key="radio_loc_db_type"
            )
        with col_db_f2:
            loc_db_rank = st.selectbox(
                "Lọc theo thứ hạng đã lưu:",
                options=["Tất cả trạng thái", "Đang Top 1 - 10", "Chưa lên Top / Ngoài 50"],
                key="sb_loc_db_rank"
            )
        
        matched_db_kws = []
        for k_key, v_info in db_all.items():
            kw_display = v_info.get("tu_khoa", k_key)
            loai_kw = v_info.get("loai", "Chính")
            rk_cur = v_info.get("rank_hien_tai")
            
            if loc_db_type == "Chỉ Từ khóa chính" and loai_kw != "Chính":
                continue
            if loc_db_type == "Chỉ Từ khóa phụ" and loai_kw == "Chính":
                continue
                
            if loc_db_rank == "Đang Top 1 - 10" and (not rk_cur or rk_cur > 10):
                continue
            if loc_db_rank == "Chưa lên Top / Ngoài 50" and rk_cur and rk_cur <= 50:
                continue
                
            matched_db_kws.append(kw_display)
            
        default_keywords_str = "\n".join(matched_db_kws)
        st.success(f"💾 Đang nạp **{len(matched_db_kws)} từ khóa** từ Cơ sở dữ liệu đã tra cứu (Tổng cộng có {len(db_all)} từ khóa đang lưu trữ)!")
        
    elif "bộ từ khóa tổng hợp" in nguon_rank_opt:
        col_sel_p1, col_sel_p2 = st.columns([2, 1])
        with col_sel_p1:
            ten_preset_duoc_chon = st.selectbox(
                "Chọn nhóm từ khóa ngành hàng HWOOD:",
                options=list(BO_TU_KHOA_HWOOD_PRESETS.keys()),
                key="sb_preset_choice"
            )
        default_keywords_str = "\n".join(BO_TU_KHOA_HWOOD_PRESETS.get(ten_preset_duoc_chon, []))
        st.success(f"💡 Đang nạp **{len(BO_TU_KHOA_HWOOD_PRESETS.get(ten_preset_duoc_chon, []))} từ khóa hot** thuộc nhóm: `{ten_preset_duoc_chon}`")

    # Ô nhập / xem danh sách từ khóa
    kw_input_area = st.text_area(
        "📝 Danh sách từ khóa sẽ kiểm tra trên Google (Mỗi từ khóa 1 dòng):",
        value=default_keywords_str,
        height=140,
        key="txt_rank_keywords_area"
    )

    list_kws_to_check = [k.strip() for k in kw_input_area.splitlines() if k.strip()]
    st.caption(f"Đang có **{len(list_kws_to_check)} từ khóa** sẵn sàng để quét thứ hạng.")

    # 2. KHU VỰC THAO TÁC: QUÉT TỰ ĐỘNG BẰNG TIỆN ÍCH CHROME (CHUẨN SPINDITOR)
    col_act1, col_act2 = st.columns([1.5, 1.2])
    with col_act1:
        btn_start_rank_scan = st.button("🚀 BẮT ĐẦU QUÉT THỨ HẠNG TRÊN GOOGLE (TOP 50)", type="primary", use_container_width=True)
    with col_act2:
        if st.button("🔄 Nạp Lại Dữ Liệu Từ Lịch Sử Thứ Hạng", use_container_width=True):
            st.cache_data.clear()
            saved_history = doc_lich_su_thu_hang()
            if saved_history:
                restored = []
                for idx, (kw, val) in enumerate(saved_history.items(), 1):
                    if not kw or any(x in kw.lower() for x in ["thủ công", "bản nháp", "giới thiệu", "liên hệ"]):
                        continue
                    rk_val = val.get("rank")
                    restored.append({
                        "stt": idx,
                        "tu_khoa": kw,
                        "rank": rk_val,
                        "rank_best": val.get("rank_best") or rk_val,
                        "rank_str": f"Top {rk_val}" if rk_val else "n/a",
                        "bien_dong_str": f"⬆️ {val.get('diff', rk_val)}" if rk_val else "⚪ n/a",
                        "link": val.get("link", ""),
                        "title": val.get("title", ""),
                        "thoi_gian": val.get("thoi_gian", "12/11/2026")
                    })
                st.session_state.rank_check_results = restored
                st.toast("Đã đồng bộ lại lịch sử thứ hạng mới nhất!", icon="✅")
                st.rerun()

    # KHU VỰC TIỆN ÍCH CHROME EXTENSION (CHUẨN CÔNG NGHỆ SCHECKPRO CỦA SPINDITOR)
    st.markdown("""
    <div style="background-color: #f0fdf4; border: 1.5px solid #86efac; border-radius: 8px; padding: 14px 18px; margin: 12px 0 16px 0;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.6rem;">🧩</span>
                <div>
                    <h4 style="margin: 0; color: #166534; font-size: 1.05rem;">Tiện Ích Mở Rộng Chrome: HWOOD SCheck (Công nghệ giống SCheckPro của SpinEditor)</h4>
                    <p style="margin: 3px 0 0 0; color: #475569; font-size: 0.85rem;">
                        Tương tự như SpinEditor dùng extension <strong>SCheckPro</strong> để người dùng quét trực tiếp từ Chrome mà không bị Google chặn Captcha, hệ thống đã xây dựng sẵn tiện ích <strong>HWOOD SCheck</strong> trong thư mục <code>hwood_chrome_extension</code>.
                    </p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📖 Hướng Dẫn Bật Extension HWOOD SCheck Trên Chrome (Cài đặt 1 lần duy nhất - 30 giây)"):
        ext_folder = os.path.join(CURRENT_DIR, "hwood_chrome_extension")
        st.markdown(f"""
        **Để trình duyệt Chrome tự động quét thứ hạng ngầm như SpinEditor:**
        1. Mở trình duyệt Google Chrome, truy cập vào đường dẫn: `chrome://extensions/`
        2. Bật công tắc **Chế độ dành cho nhà phát triển (Developer mode)** ở góc trên cùng bên phải.
        3. Nhấn vào nút **Tải tiện ích đã giải nén (Load unpacked)** ở góc trái.
        4. Chọn đúng thư mục extension trong máy của bạn:
           `{ext_folder}`
        5. Bấm vào biểu tượng mảnh ghép (Extensions) trên thanh công cụ Chrome và ghim **HWOOD SCheck**.
        
        👉 **Cách sử dụng:** Bấm vào biểu tượng HWOOD trên Chrome ➔ Bấm **`🚀 BẮT ĐẦU QUÉT TỰ ĐỘNG BẰNG CHROME`**. Extension sẽ tự động lấy thứ hạng thật trên Google qua IP của bạn, không bao giờ bị dính Captcha và tự động cập nhật bảng này!
        """)

    with st.expander("✏️ Hiệu chỉnh nhanh thứ hạng nếu cần"):
        c_ed1, c_ed2, c_ed3, c_ed4 = st.columns([2, 1, 2.5, 1.2])
        with c_ed1:
            edit_kw = st.text_input("Từ khóa:", value="tấm ốp nano", key="edit_kw_input")
        with c_ed2:
            edit_rank = st.number_input("Thứ hạng (Top):", min_value=1, max_value=100, value=2, step=1, key="edit_rank_input")
        with c_ed3:
            suggested_p = tim_bai_viet_khop_nhat_wp(edit_kw, danh_sach_bai_viet_wp)
            suggested_url = suggested_p["link"] if suggested_p else "https://hwood.vn/"
            edit_url = st.text_input("URL bài viết / Landing Page:", value=suggested_url, key="edit_url_input")
        with c_ed4:
            st.write("")
            if st.button("💾 Lưu Thứ Hạng", key="btn_save_manual_rank"):
                if edit_kw.strip():
                    now_str = datetime.now().strftime("%d/%m/%Y")
                    rank_history_data = doc_lich_su_thu_hang()
                    k_clean = edit_kw.lower().strip()
                    p_title = suggested_p.get("title", "") if suggested_p else ""
                    rank_history_data[k_clean] = {
                        "rank": int(edit_rank),
                        "rank_best": int(edit_rank),
                        "diff": int(edit_rank),
                        "link": edit_url,
                        "title": p_title,
                        "thoi_gian": now_str
                    }
                    luu_lich_su_thu_hang(rank_history_data)
                    
                    # Đồng bộ vào Cơ sở dữ liệu từ khóa
                    dong_bo_ket_qua_quet_vao_db([{
                        "tu_khoa": edit_kw.strip(),
                        "rank": int(edit_rank),
                        "rank_best": int(edit_rank),
                        "link": edit_url,
                        "title": p_title,
                        "thoi_gian": now_str
                    }], danh_sach_bai_viet_wp)
                    
                    cur_results = st.session_state.get("rank_check_results") or []
                    updated = False
                    for r in cur_results:
                        if r["tu_khoa"].lower().strip() == k_clean:
                            r["rank"] = int(edit_rank)
                            r["rank_str"] = f"Top {int(edit_rank)}"
                            r["bien_dong_str"] = "✏️ Cập nhật"
                            r["link"] = edit_url
                            r["title"] = p_title
                            r["thoi_gian"] = now_str
                            updated = True
                            break
                    if not updated:
                        cur_results.append({
                            "stt": len(cur_results) + 1,
                            "tu_khoa": edit_kw.strip(),
                            "rank": int(edit_rank),
                            "rank_best": int(edit_rank),
                            "rank_str": f"Top {int(edit_rank)}",
                            "bien_dong_str": "✏️ Cập nhật",
                            "link": edit_url,
                            "title": p_title,
                            "thoi_gian": now_str
                        })
                    st.session_state.rank_check_results = cur_results
                    st.success(f"✅ Đã lưu: `{edit_kw}` ➔ **Top {edit_rank}** ({edit_url}) vào cả Lịch sử và Cơ sở dữ liệu!")
                    st.rerun()

    # KHU VỰC NHẬP DỮ LIỆU TỪ SPINEDITOR HOẶC SERP TOOL KHÁC
    with st.expander("📋 Nhập Nhanh Kết Quả (Dán từ SpinEditor / SERP Checker)"):
        st.caption("Sao chép toàn bộ bảng kết quả từ SpinEditor hoặc dán danh sách dạng `Từ khóa [Tab] Thứ hạng [Tab] Link`, hệ thống sẽ tự động phân tích và lưu vào Database.")
        spineditor_paste_text = st.text_area(
            "Dán văn bản kết quả vào đây:",
            placeholder="Ví dụ:\n1\ttấm ốp nano\t2\t2\t2\t12/11/2026\thttps://hwood.vn/tam-op-nano/\nhoặc:\ntấm ốp nano: Top 2",
            height=100,
            key="txt_spineditor_paste"
        )
        if st.button("📥 Phân Tích & Đồng Bộ Vào Database", key="btn_parse_spineditor"):
            if spineditor_paste_text.strip():
                parsed = nhap_ket_qua_spineditor(spineditor_paste_text, danh_sach_bai_viet_wp)
                if parsed:
                    st.session_state.rank_check_results = parsed
                    # Đồng bộ vào lịch sử và DB
                    rank_history_data = doc_lich_su_thu_hang()
                    for p_item in parsed:
                        k_clean = p_item["tu_khoa"].lower().strip()
                        if p_item.get("rank") is not None:
                            rank_history_data[k_clean] = {
                                "rank": p_item["rank"],
                                "rank_best": p_item.get("rank_best") or p_item["rank"],
                                "diff": p_item["rank"],
                                "link": p_item.get("link", ""),
                                "title": p_item.get("title", ""),
                                "thoi_gian": p_item.get("thoi_gian", datetime.now().strftime("%d/%m/%Y"))
                            }
                    luu_lich_su_thu_hang(rank_history_data)
                    dong_bo_ket_qua_quet_vao_db(parsed, danh_sach_bai_viet_wp)
                    st.success(f"🎉 Đã nhập thành công **{len(parsed)} từ khóa** và lưu vào Database!")
                    st.rerun()
                else:
                    st.warning("Không nhận diện được định dạng kết quả. Vui lòng kiểm tra lại văn bản dán vào.")

    # THỰC THI QUÉT THỨ HẠNG GOOGLE
    if btn_start_rank_scan:
        if not list_kws_to_check:
            st.warning("Vui lòng nhập ít nhất một từ khóa để kiểm tra!")
        else:
            rank_history_data = doc_lich_su_thu_hang()
            results = []
            
            prog_bar = st.progress(0)
            status_text = st.empty()
            
            total_kws = len(list_kws_to_check)
            
            for idx, kw in enumerate(list_kws_to_check, 1):
                status_text.markdown(f"⏳ **Đang kiểm tra từ khóa ({idx}/{total_kws}):** `{kw}` trên Google...")
                
                matched_p = tim_bai_viet_khop_nhat_wp(kw, danh_sach_bai_viet_wp)
                page_title = matched_p.get("title", "") if matched_p else ""
                
                found_rank, found_link, status_code = check_thu_hang_google_keyword(
                    kw, 
                    target_domain=target_domain_check,
                    danh_sach_bai_viet_wp=danh_sach_bai_viet_wp
                )
                
                if not found_link and matched_p:
                    found_link = matched_p.get("link", "")
                
                kw_key = kw.lower().strip()
                old_info = rank_history_data.get(kw_key, {})
                old_rank = old_info.get("rank")
                old_link = old_info.get("link")
                
                if status_code == "captcha":
                    if old_rank is not None:
                        final_rank = old_rank
                        final_link = old_link or found_link
                        bien_dong_str = f"➡️ Top {old_rank} (Lưu trữ)"
                    else:
                        final_rank = None
                        final_link = found_link
                        bien_dong_str = "⚠️ Google Chặn Bot (Captcha)"
                elif found_rank is not None:
                    final_rank = found_rank
                    final_link = found_link
                    if old_rank is not None:
                        diff = old_rank - found_rank
                        if diff > 0:
                            bien_dong_str = f"⬆️ {diff}"
                        elif diff < 0:
                            bien_dong_str = f"⬇️ {diff}"
                        else:
                            bien_dong_str = "➡️ 0"
                    else:
                        bien_dong_str = f"🆕 Top {found_rank}"
                else:
                    final_rank = None
                    final_link = found_link
                    bien_dong_str = "⚪ Ngoài Top 20"

                rank_str = f"Top {final_rank}" if final_rank else ("Captcha" if status_code == "captcha" else "n/a")
                now_str = datetime.now().strftime("%d/%m/%Y")

                item_res = {
                    "stt": idx,
                    "tu_khoa": kw,
                    "rank": final_rank,
                    "rank_best": final_rank,
                    "rank_str": rank_str,
                    "bien_dong_str": bien_dong_str,
                    "link": final_link or "",
                    "title": page_title,
                    "thoi_gian": now_str
                }
                results.append(item_res)

                if final_rank is not None:
                    rank_history_data[kw_key] = {
                        "rank": final_rank,
                        "rank_best": final_rank,
                        "diff": final_rank,
                        "link": final_link,
                        "title": page_title,
                        "thoi_gian": now_str
                    }

                prog_bar.progress(idx / total_kws)
                time.sleep(1.8)

            luu_lich_su_thu_hang(rank_history_data)
            
            # TỰ ĐỘNG LƯU TRỮ VÀO CƠ SỞ DỮ LIỆU TỪ KHÓA
            dong_bo_ket_qua_quet_vao_db(results, danh_sach_bai_viet_wp)
            
            st.session_state.rank_check_results = results
            status_text.markdown("✅ **Đã hoàn thành kiểm tra và tự động cập nhật Cơ sở dữ liệu từ khóa!**")
            st.toast("🎉 Đã quét xong thứ hạng Google & lưu vào Data Keyword!", icon="✅")
            st.rerun()

    # 3. HIỂN THỊ BẢNG KẾT QUẢ THỨ HẠNG KIỂU SPINDITOR
    if st.session_state.get("rank_check_results"):
        st.markdown("---")
        st.markdown("#### 📊 Thứ Hạng Từ Khóa Vừa Quét (Bấm vào Vị trí để mở Debug SERP):")
        
        cur_results = st.session_state.rank_check_results
        
        top1_3 = len([r for r in cur_results if r.get("rank") and r["rank"] <= 3])
        top4_10 = len([r for r in cur_results if r.get("rank") and 4 <= r["rank"] <= 10])
        top11_30 = len([r for r in cur_results if r.get("rank") and 11 <= r["rank"] <= 30])
        ngoai_top = len([r for r in cur_results if not r.get("rank")])

        c_rk1, c_rk2, c_rk3, c_rk4 = st.columns(4)
        with c_rk1:
            st.markdown(f'<div style="background-color: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 12px; text-align: center;"><div style="color: #166534; font-size: 0.9em; font-weight: bold;">🥇 Top 1 - 3 (Thống Trị)</div><div style="color: #15803d; font-size: 1.8em; font-weight: bold; margin-top: 4px;">{top1_3}</div></div>', unsafe_allow_html=True)
        with c_rk2:
            st.markdown(f'<div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 12px; text-align: center;"><div style="color: #166534; font-size: 0.9em; font-weight: bold;">🥈 Top 4 - 10 (Trang 1)</div><div style="color: #22c55e; font-size: 1.8em; font-weight: bold; margin-top: 4px;">{top4_10}</div></div>', unsafe_allow_html=True)
        with c_rk3:
            st.markdown(f'<div style="background-color: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 12px; text-align: center;"><div style="color: #92400e; font-size: 0.9em; font-weight: bold;">🥉 Top 11 - 30 (Trang 2-3)</div><div style="color: #d97706; font-size: 1.8em; font-weight: bold; margin-top: 4px;">{top11_30}</div></div>', unsafe_allow_html=True)
        with c_rk4:
            st.markdown(f'<div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;"><div style="color: #64748b; font-size: 0.9em; font-weight: bold;">⚪ Ngoài Top 50 (n/a)</div><div style="color: #94a3b8; font-size: 1.8em; font-weight: bold; margin-top: 4px;">{ngoai_top}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Bộ lọc bảng kết quả & Nút xuất file Excel
        col_rf1, col_rf2, col_rf3 = st.columns([2, 1.5, 1.2])
        with col_rf1:
            tim_kiem_rk = st.text_input("🔎 Tìm kiếm từ khóa:", placeholder="Nhập từ khóa...", key="txt_search_rank_res")
        with col_rf2:
            loc_tang_top = st.selectbox(
                "Lọc phân tầng thứ hạng:",
                options=["Tất Cả Thứ Hạng", "Chỉ Top 1 - 10 (Trang 1)", "Chỉ Top 1 - 3", "Chỉ Ngoài Top 50"],
                key="sb_filter_rank_tier"
            )
        with col_rf3:
            st.write("")
            csv_rank_content = xuat_csv_thu_hang(cur_results)
            st.download_button(
                label="📥 Xuất ra Excel / CSV",
                data=csv_rank_content,
                file_name=f"thu_hang_google_spineditor_{target_domain_check}.csv",
                mime="text/csv",
                use_container_width=True
            )

        ds_rk_hien_thi = cur_results
        if tim_kiem_rk.strip():
            ds_rk_hien_thi = [r for r in ds_rk_hien_thi if tim_kiem_rk.lower() in r["tu_khoa"].lower()]
        if loc_tang_top == "Chỉ Top 1 - 10 (Trang 1)":
            ds_rk_hien_thi = [r for r in ds_rk_hien_thi if r.get("rank") and r["rank"] <= 10]
        elif loc_tang_top == "Chỉ Top 1 - 3":
            ds_rk_hien_thi = [r for r in ds_rk_hien_thi if r.get("rank") and r["rank"] <= 3]
        elif loc_tang_top == "Chỉ Ngoài Top 50":
            ds_rk_hien_thi = [r for r in ds_rk_hien_thi if not r.get("rank")]

        # TIÊU ĐỀ BẢNG THỨ HẠNG KIỂU SPINDITOR
        st.markdown("""
        <div style="background-color: #f1f5f9; padding: 10px 12px; border-radius: 6px; font-weight: bold; color: #334155; font-size: 0.88em; border: 1px solid #cbd5e1; margin-bottom: 8px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 5%; text-align: center;">STT</div>
                <div style="width: 25%;">TỪ KHÓA</div>
                <div style="width: 14%; text-align: center;">VỊ TRÍ (DEBUG)</div>
                <div style="width: 12%; text-align: center;">TỐT NHẤT</div>
                <div style="width: 12%; text-align: center;">CẬP NHẬT</div>
                <div style="width: 24%;">LIÊN KẾT THỰC TẾ</div>
                <div style="width: 8%; text-align: center;">TRA CỨU</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for idx, row in enumerate(ds_rk_hien_thi, 1):
            rk_val = row.get("rank")
            kw_name = row["tu_khoa"]
            google_search_url = tao_link_google_search(kw_name)
            best_val = row.get("rank_best") or rk_val or "-"
            date_val = row.get("thoi_gian", "12/11/2026")
            link_url = row.get("link", "")
            title_page = row.get("title", "")

            # Nhãn nút vị trí có icon và màu nổi bật
            if rk_val and rk_val <= 3:
                btn_pos_label = f"🟢 ↑ {rk_val}"
            elif rk_val and rk_val <= 10:
                btn_pos_label = f"🔵 ↑ {rk_val}"
            elif rk_val:
                btn_pos_label = f"🟠 Top {rk_val}"
            else:
                btn_pos_label = "⚪ n/a"

            c0, c1, c2, c3, c4, c5, c6 = st.columns([0.5, 2.5, 1.4, 1.2, 1.2, 2.4, 0.8])
            
            with c0:
                st.markdown(f"<div style='text-align: center; color: #64748b; font-size: 0.9em; padding-top: 6px;'>{idx}</div>", unsafe_allow_html=True)
            with c1:
                st.markdown(f"<div style='font-weight: 600; color: #0f172a; font-size: 0.95em; padding-top: 6px;'>{kw_name}</div>", unsafe_allow_html=True)
            with c2:
                if st.button(btn_pos_label, key=f"btn_pos_{idx}_{kw_name}", help=f"Bấm để xem Debug SERP cho '{kw_name}'"):
                    modal_serp_debug(row, danh_sach_bai_viet_wp)
            with c3:
                st.markdown(f"<div style='text-align: center; font-weight: 600; color: #334155; padding-top: 6px;'>{best_val}</div>", unsafe_allow_html=True)
            with c4:
                st.markdown(f"<div style='text-align: center; color: #64748b; font-size: 0.85em; padding-top: 6px;'>{date_val}</div>", unsafe_allow_html=True)
            with c5:
                if link_url:
                    title_tip = f" title='{title_page}'" if title_page else ""
                    st.markdown(f"<div style='padding-top: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'><a href='{link_url}' target='_blank' style='color: #2563eb; text-decoration: none; font-size: 0.84em;'{title_tip}>🔗 {link_url}</a></div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='color: #94a3b8; font-style: italic; font-size: 0.85em; padding-top: 6px;'>-</div>", unsafe_allow_html=True)
            with c6:
                st.link_button("🌐", google_search_url, help=f"Mở Google tìm kiếm '{kw_name}'")

            st.markdown("<div style='border-bottom: 1px solid #f1f5f9; margin-bottom: 4px;'></div>", unsafe_allow_html=True)

    # ==============================================================================
    # 4. CHIẾN LƯỢC ĐỘT PHÁ TOP 1 - 5: CHẨN ĐOÁN & XỬ LÝ 1-CLICK TỪ KHÓA NGOÀI TOP 5
    # ==============================================================================
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fef2f2 0%, #fff 100%); border: 1.5px solid #fca5a5; border-radius: 10px; padding: 16px 20px; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 2rem;">🚀</span>
                <div>
                    <h3 style="margin: 0; color: #991b1b; font-size: 1.25rem;">Chiến Lược Đột Phá Top 1 - 5 (Chẩn Đoán & Xử Lý 1-Click Từ Khóa Ngoài Top 5)</h3>
                    <p style="margin: 4px 0 0 0; color: #4b5563; font-size: 0.9rem;">
                        Tự động rà soát toàn bộ từ khóa của <b>HWOOD VIỆT NAM</b> đang nằm ngoài Top 5 Google, phát hiện gốc rễ nguyên nhân (Ăn thịt từ khóa, Lệch Intent, Thiếu Bảng Giá, v.v.) và cung cấp <b>4 nút bấm 1-Click</b> để giải quyết ngay lập tức.
                    </p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    db_tracked_all = doc_database_keywords()
    diag_res = lay_toan_bo_chan_doan_ngoai_top(db_tracked_all, danh_sach_bai_viet_wp)
    
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    with col_t1:
        st.markdown(f"""
        <div style="background-color: #fef2f2; border: 1.5px solid #fecaca; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="color: #991b1b; font-size: 0.88rem; font-weight: bold;">⚡ Cận Top (Top 6 - 10)</div>
            <div style="color: #dc2626; font-size: 1.8rem; font-weight: bold; margin-top: 2px;">{diag_res['dem_tier1']} từ</div>
            <div style="color: #7f1d1d; font-size: 0.78rem;">Ưu tiên số 1: Tối ưu Onpage lên Top 1-3</div>
        </div>
        """, unsafe_allow_html=True)
    with col_t2:
        st.markdown(f"""
        <div style="background-color: #fffbeb; border: 1.5px solid #fde68a; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="color: #92400e; font-size: 0.88rem; font-weight: bold;">🔄 Lệch Intent (Top 11 - 20)</div>
            <div style="color: #d97706; font-size: 1.8rem; font-weight: bold; margin-top: 2px;">{diag_res['dem_tier2']} từ</div>
            <div style="color: #78350f; font-size: 0.78rem;">Sửa URL & Internal Link vệ tinh</div>
        </div>
        """, unsafe_allow_html=True)
    with col_t3:
        st.markdown(f"""
        <div style="background-color: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="color: #475569; font-size: 0.88rem; font-weight: bold;">🎯 Ngoài Top 20 / Chưa Rank</div>
            <div style="color: #64748b; font-size: 1.8rem; font-weight: bold; margin-top: 2px;">{diag_res['dem_tier3']} từ</div>
            <div style="color: #334155; font-size: 0.78rem;">Khoảng trống: Viết bài mới / Plan tháng</div>
        </div>
        """, unsafe_allow_html=True)
    with col_t4:
        st.markdown(f"""
        <div style="background-color: #f0fdf4; border: 1.5px solid #bbf7d0; border-radius: 8px; padding: 12px; text-align: center;">
            <div style="color: #166534; font-size: 0.88rem; font-weight: bold;">📊 Tổng Từ Khóa Cần Đột Phá</div>
            <div style="color: #15803d; font-size: 1.8rem; font-weight: bold; margin-top: 2px;">{diag_res['tong_so_ngoai_top']} từ</div>
            <div style="color: #14532d; font-size: 0.78rem;">Đang ngoài Top 5 / Cần hành động</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Bộ lọc nhóm và tìm kiếm
    c_f1, c_f2 = st.columns([2.2, 1.8])
    with c_f1:
        tab_tier_filter = st.radio(
            "Phân loại từ khóa cần xử lý:",
            options=[
                f"⚡ Tier 1: Cận Top 6 - 10 ({diag_res['dem_tier1']})",
                f"🔄 Tier 2: Lệch Intent 11 - 20 ({diag_res['dem_tier2']})",
                f"🎯 Tier 3: Ngoài Top 20 / n/a ({diag_res['dem_tier3']})",
                f"📋 Tất Cả ({diag_res['tong_so_ngoai_top']})"
            ],
            horizontal=True,
            key="radio_filter_diag_tier"
        )
    with c_f2:
        search_diag_txt = st.text_input("🔎 Tìm kiếm từ khóa ngoài Top:", placeholder="Ví dụ: báo giá, sàn gỗ, bàn ghế, pergola...", key="txt_search_diag")

    # Chọn danh sách tương ứng
    if "Tier 1" in tab_tier_filter:
        ds_diag_view = diag_res["tier1"]
    elif "Tier 2" in tab_tier_filter:
        ds_diag_view = diag_res["tier2"]
    elif "Tier 3" in tab_tier_filter:
        ds_diag_view = diag_res["tier3"]
    else:
        ds_diag_view = diag_res["tier1"] + diag_res["tier2"] + diag_res["tier3"]

    if search_diag_txt.strip():
        q_diag = search_diag_txt.lower().strip()
        ds_diag_view = [d for d in ds_diag_view if q_diag in d["tu_khoa"].lower() or q_diag in d["chuyen_muc"].lower()]

    st.caption(f"Đang hiển thị **{len(ds_diag_view)} từ khóa** cần tối ưu:")

    for idx_d, diag_item in enumerate(ds_diag_view, 1):
        kw_d = diag_item["tu_khoa"]
        rank_d = diag_item["rank"]
        t_d = diag_item["tier"]
        url_d = diag_item["url_dich"]
        nguyen_nhan_d = diag_item["nguyen_nhan"]
        loi_tags = diag_item["loi_phat_hien"]
        de_xuat_steps = diag_item["phuong_an_de_xuat"]
        tieu_de_sug = diag_item["tieu_de_de_xuat"]
        the_loai_sug = diag_item["the_loai_de_xuat"]
        ghi_chu_sug = diag_item["ghi_chu_chien_luoc"]
        cat_d = diag_item["chuyen_muc"]

        # Màu sắc viền và nhãn rank
        if t_d == 1:
            card_bdr = "#f87171"
            badge_bg = "#fee2e2"
            badge_color = "#991b1b"
            rank_label = f"🥈 Vị trí: Top {rank_d} (Cận Top)"
        elif t_d == 2:
            card_bdr = "#fbbf24"
            badge_bg = "#fef3c7"
            badge_color = "#92400e"
            rank_label = f"🥉 Vị trí: Top {rank_d} (Trang 2)"
        else:
            card_bdr = "#cbd5e1"
            badge_bg = "#f1f5f9"
            badge_color = "#475569"
            rank_label = "⚪ Vị trí: Ngoài Top 20 (Chưa Rank)"

        tags_html = " ".join([
            f"<span style='background-color: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; font-weight: 600; border: 1px solid #fca5a5; margin-right: 4px;'>{tag}</span>"
            for tag in loi_tags
        ])

        steps_html = "".join([
            f"<li style='margin-bottom: 4px;'>{step}</li>"
            for step in de_xuat_steps
        ])

        url_link_html = f"<a href='{url_d}' target='_blank' style='color: #2563eb; font-size: 0.83rem; text-decoration: none;'>🔗 {url_d}</a>" if url_d else "<span style='color: #94a3b8; font-style: italic; font-size: 0.83rem;'>Chưa có đường dẫn đích</span>"

        with st.container():
            st.markdown(f"""
            <div style="background-color: #ffffff; border: 1.5px solid {card_bdr}; border-radius: 10px; padding: 14px 18px; margin-bottom: 10px; box-shadow: 0 1px 4px rgba(0,0,0,0.03);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <span style="font-size: 1.12rem; font-weight: 800; color: #0f172a;">{kw_d}</span>
                        <span style="background-color: {badge_bg}; color: {badge_color}; font-weight: bold; font-size: 0.82rem; padding: 3px 8px; border-radius: 5px;">
                            {rank_label}
                        </span>
                        <span style="background-color: #f8fafc; color: #334155; font-size: 0.78rem; padding: 2px 7px; border-radius: 4px; border: 1px solid #e2e8f0;">
                            📂 {cat_d}
                        </span>
                    </div>
                    <div>
                        {url_link_html}
                    </div>
                </div>

                <div style="margin-bottom: 8px;">
                    {tags_html}
                </div>

                <div style="background-color: #fff7ed; border-left: 3.5px solid #f97316; padding: 7px 12px; border-radius: 4px; margin-bottom: 8px; font-size: 0.86rem; color: #9a3412;">
                    <b>⚠️ Nguyên nhân rớt Top:</b> {nguyen_nhan_d}
                </div>

                <div style="background-color: #f0fdf4; border-left: 3.5px solid #22c55e; padding: 8px 12px; border-radius: 4px; margin-bottom: 8px; font-size: 0.86rem; color: #166534;">
                    <b>💡 Phương án bứt phá Top 1 - 5 (Chuẩn HWOOD):</b>
                    <ul style="margin: 3px 0 0 16px; padding: 0;">
                        {steps_html}
                    </ul>
                    <div style="margin-top: 6px; font-size: 0.83rem; color: #15803d; border-top: 1px dashed #bbf7d0; padding-top: 4px;">
                        <b>📝 Tiêu đề đề xuất:</b> <i>{tieu_de_sug}</i> &nbsp;|&nbsp; <b>Định dạng:</b> <code>{the_loai_sug}</code>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 4 Nút hành động 1-Click
            col_b1, col_b2, col_b3, col_b4 = st.columns([1.3, 1.4, 1.4, 1.1])
            
            with col_b1:
                if st.button("🔧 Sửa & Tối Ưu (Tab 2)", key=f"btn_d_tab2_{idx_d}_{kw_d}", use_container_width=True, help=f"Mở bài viết của '{kw_d}' tại Tab 2 để kiểm toán & cập nhật"):
                    matched_wp = tim_bai_viet_khop_nhat_wp(kw_d, danh_sach_bai_viet_wp)
                    if matched_wp:
                        st.session_state.bai_cu_duoc_chon = {
                            "id": matched_wp.get("id"),
                            "title": matched_wp.get("title"),
                            "link": matched_wp.get("link"),
                            "content": matched_wp.get("content", ""),
                            "post_type": matched_wp.get("type", "pages")
                        }
                        st.session_state.tieu_de_edit_tay = matched_wp.get("title", "")
                        st.session_state.noi_dung_edit_tay = matched_wp.get("content", "")
                    else:
                        st.session_state.tieu_de_edit_tay = tieu_de_sug
                        st.session_state.noi_dung_edit_tay = f"<h3>{tieu_de_sug}</h3><p>Từ khóa mục tiêu: <b>{kw_d}</b></p><p>Trang đích mong muốn: {url_d}</p>"
                        st.session_state.bai_cu_duoc_chon = {
                            "id": 0,
                            "title": tieu_de_sug,
                            "link": url_d,
                            "content": st.session_state.noi_dung_edit_tay,
                            "post_type": "pages"
                        }
                    st.session_state.noi_dung_toi_uu = ""
                    st.session_state.bao_cao_audit = ""
                    st.session_state["chuyen_tab_index"] = 1
                    st.toast(f"Đang mở '{kw_d}' tại Tab 2...", icon="🔧")
                    st.rerun()

            with col_b2:
                btn_type_t1 = "primary" if t_d == 3 else "secondary"
                if st.button("✍️ Viết Bài Mới (Tab 1)", key=f"btn_d_tab1_{idx_d}_{kw_d}", type=btn_type_t1, use_container_width=True, help=f"Chuyển từ khóa '{kw_d}' sang Tab 1 để AI viết bài chuẩn SEO mới"):
                    st.session_state.tu_khoa_hien_tai = kw_d
                    st.session_state.the_loai_duoc_chon = the_loai_sug
                    st.session_state.bai_duoc_chuyen_sang_tab1 = tieu_de_sug
                    st.session_state["chuyen_tab_index"] = 0
                    st.toast(f"Đã chuyển '{kw_d}' sang Tab 1 để tạo bài mới!", icon="✍️")
                    st.rerun()

            with col_b3:
                if st.button("📅 Đưa Vào Plan Tháng (Tab 5)", key=f"btn_d_plan_{idx_d}_{kw_d}", use_container_width=True, help=f"Thêm bài viết này vào Kế hoạch biên tập nội dung tháng"):
                    ok_p, msg_p = dua_vao_ke_hoach_thang_nhanh(
                        kw=kw_d,
                        tieu_de=tieu_de_sug,
                        the_loai=the_loai_sug,
                        ghi_chu=ghi_chu_sug,
                        cum_chu_de=cat_d
                    )
                    if ok_p:
                        st.toast(msg_p, icon="✅")
                        st.success(f"{msg_p} (Bạn có thể chuyển qua **Tab 5: Kế Hoạch Tháng** để kiểm tra lịch xuất bản).")
                    else:
                        st.warning(msg_p)

            with col_b4:
                if st.button("🤖 Quét 5 Bot (Tab 8)", key=f"btn_d_bot_{idx_d}_{kw_d}", use_container_width=True, help=f"Thêm '{kw_d}' vào hàng đợi 5 Bot để quét và đẩy tương tác"):
                    ok_b, msg_b = dua_vao_bot_farm_queue(kw_d)
                    st.session_state["chuyen_tab_index"] = 7
                    st.toast(msg_b, icon="🤖")
                    st.rerun()

            st.markdown("<hr style='margin: 12px 0 16px 0; border: 0.5px solid #f1f5f9;'>", unsafe_allow_html=True)

    # ==============================================================================
    # 5. CƠ SỞ DỮ LIỆU TỪ KHÓA ĐÃ THEO DÕI (TRACKED KEYWORDS DATABASE)
    # ==============================================================================
    st.markdown("---")
    st.markdown("### 🗄️ Cơ Sở Dữ Liệu Từ Khóa Đã Tra Cứu (Tracked Keywords Database)")
    st.markdown("Toàn bộ từ khóa chính & phụ đã từng kiểm tra, lịch sử biến động thứ hạng, liên kết bài viết tương ứng trên **`hwood.vn`**.")

    db_tracked = db_tracked_all
    total_db = len(db_tracked)

    db_top1_3 = len([v for v in db_tracked.values() if v.get("rank_hien_tai") and v["rank_hien_tai"] <= 3])
    db_top4_10 = len([v for v in db_tracked.values() if v.get("rank_hien_tai") and 4 <= v["rank_hien_tai"] <= 10])
    db_top11_30 = len([v for v in db_tracked.values() if v.get("rank_hien_tai") and 11 <= v["rank_hien_tai"] <= 30])
    db_ngoai_top = len([v for v in db_tracked.values() if not v.get("rank_hien_tai")])

    m_c1, m_c2, m_c3, m_c4, m_c5 = st.columns(5)
    with m_c1:
        st.metric("Tổng Từ Khóa Đang Lưu", f"{total_db} từ")
    with m_c2:
        st.metric("🥇 Top 1 - 3", f"{db_top1_3}")
    with m_c3:
        st.metric("🥈 Top 4 - 10", f"{db_top4_10}")
    with m_c4:
        st.metric("🥉 Top 11 - 30", f"{db_top11_30}")
    with m_c5:
        st.metric("⚪ Chưa Top / Ngoài 50", f"{db_ngoai_top}")

    # Thanh điều khiển & Tìm kiếm Database
    c_db_act1, c_db_act2, c_db_act3, c_db_act4 = st.columns([1.8, 1.2, 1.3, 1.4])
    with c_db_act1:
        search_db_txt = st.text_input("🔍 Tìm kiếm trong DB:", placeholder="Nhập tên từ khóa...", key="txt_search_db_view")
    with c_db_act2:
        filter_db_type = st.selectbox(
            "Loại từ khóa:",
            options=["Tất cả", "Chính (Focus)", "Phụ (Secondary)"],
            key="sb_view_db_type"
        )
    with c_db_act3:
        filter_db_cat = st.selectbox(
            "Chuyên mục:",
            options=[
                "Tất cả chuyên mục",
                "Bàn Ghế Sân Vườn",
                "Gỗ Nhựa Ngoài Trời",
                "Tấm Ốp Nano",
                "Tấm PVC Vân Đá",
                "Lam Sóng",
                "Pergola",
                "Cổng Rào"
            ],
            key="sb_view_db_cat"
        )
    with c_db_act4:
        filter_db_rank_tier = st.selectbox(
            "Thứ hạng:",
            options=["Tất cả thứ hạng", "Đang Top 1-10", "Đang Top 1-3", "Chưa lên Top"],
            key="sb_view_db_rank_tier"
        )

    # Nút thao tác: Nạp vào quét lại & Xuất file CSV
    col_btn_db1, col_btn_db2, col_btn_db3 = st.columns([1.5, 1.5, 1.5])
    with col_btn_db1:
        if st.button("🔄 Nạp Toàn Bộ Danh Sách Này Để Quét Lại", type="primary", use_container_width=True):
            # Lấy toàn bộ từ khóa khớp bộ lọc
            filtered_kws_to_push = []
            for k_key, v in db_tracked.items():
                kw_name = v.get("tu_khoa", k_key)
                filtered_kws_to_push.append(kw_name)
            st.session_state["forced_rank_keywords"] = "\n".join(filtered_kws_to_push)
            st.toast(f"Đã nạp {len(filtered_kws_to_push)} từ khóa vào ô kiểm tra!", icon="✅")
            st.rerun()
            
    with col_btn_db2:
        csv_db_data = xuat_csv_database_keywords(db_tracked)
        st.download_button(
            label="📥 Tải Toàn Bộ Data Keyword (.csv)",
            data=csv_db_data,
            file_name=f"database_keywords_hwood_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
    with col_btn_db3:
        st.write("")

    # Lọc danh sách hiển thị
    items_to_display = []
    for k_key, v in db_tracked.items():
        kw_name = v.get("tu_khoa", k_key)
        loai = v.get("loai", "Chính")
        cat = v.get("chuyen_muc", "")
        rk = v.get("rank_hien_tai")
        
        if search_db_txt.strip() and search_db_txt.lower() not in kw_name.lower():
            continue
        if filter_db_type == "Chính (Focus)" and loai != "Chính":
            continue
        if filter_db_type == "Phụ (Secondary)" and loai == "Chính":
            continue
        if filter_db_cat != "Tất cả chuyên mục" and filter_db_cat.lower() not in cat.lower():
            continue
        if filter_db_rank_tier == "Đang Top 1-10" and (not rk or rk > 10):
            continue
        if filter_db_rank_tier == "Đang Top 1-3" and (not rk or rk > 3):
            continue
        if filter_db_rank_tier == "Chưa lên Top" and rk and rk <= 50:
            continue
            
        items_to_display.append((k_key, v))

    st.markdown(f"**Đang hiển thị {len(items_to_display)}/{total_db} từ khóa trong Database:**")

    # Header bảng Database
    st.markdown("""
    <div style="background-color: #f1f5f9; padding: 10px 12px; border-radius: 6px; font-weight: bold; color: #334155; font-size: 0.88em; border: 1px solid #cbd5e1; margin-bottom: 8px;">
        <div style="display: flex; align-items: center;">
            <div style="width: 5%; text-align: center;">STT</div>
            <div style="width: 25%;">TỪ KHÓA ĐÃ THEO DÕI</div>
            <div style="width: 12%; text-align: center;">PHÂN LOẠI</div>
            <div style="width: 14%; text-align: center;">THỨ HẠNG</div>
            <div style="width: 10%; text-align: center;">TỐT NHẤT</div>
            <div style="width: 12%; text-align: center;">BIẾN ĐỘNG</div>
            <div style="width: 16%;">BÀI VIẾT ĐÍCH</div>
            <div style="width: 6%; text-align: center;">XÓA</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    for idx, (k_key, val) in enumerate(items_to_display, 1):
        kw_display = val.get("tu_khoa", k_key)
        loai_badge = "🟢 Chính" if val.get("loai") == "Chính" else "🔵 Phụ"
        rk = val.get("rank_hien_tai")
        rk_str = f"Top {rk}" if rk else "Ngoài Top 50"
        rk_best = val.get("rank_tot_nhat") or "-"
        bien_dong = val.get("bien_dong", "-")
        url_dich = val.get("url_dich", "")
        title_bai = val.get("tieu_de_bai", "")
        
        # Màu thứ hạng
        rk_color = "#15803d" if rk and rk <= 3 else ("#22c55e" if rk and rk <= 10 else ("#d97706" if rk else "#94a3b8"))
        
        d0, d1, d2, d3, d4, d5, d6, d7 = st.columns([0.5, 2.5, 1.2, 1.4, 1.0, 1.2, 1.6, 0.6])
        with d0:
            st.markdown(f"<div style='text-align: center; color: #64748b; font-size: 0.88em; padding-top: 5px;'>{idx}</div>", unsafe_allow_html=True)
        with d1:
            st.markdown(f"<div style='font-weight: 600; color: #0f172a; font-size: 0.92em; padding-top: 5px;'>{kw_display}</div>", unsafe_allow_html=True)
        with d2:
            st.markdown(f"<div style='text-align: center; font-size: 0.82em; padding-top: 5px;'>{loai_badge}</div>", unsafe_allow_html=True)
        with d3:
            st.markdown(f"<div style='text-align: center; font-weight: bold; color: {rk_color}; font-size: 0.9em; padding-top: 5px;'>{rk_str}</div>", unsafe_allow_html=True)
        with d4:
            st.markdown(f"<div style='text-align: center; font-size: 0.88em; color: #475569; padding-top: 5px;'>{rk_best}</div>", unsafe_allow_html=True)
        with d5:
            st.markdown(f"<div style='text-align: center; font-size: 0.84em; color: #64748b; padding-top: 5px;'>{bien_dong}</div>", unsafe_allow_html=True)
        with d6:
            if url_dich:
                st.markdown(f"<div style='overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding-top: 5px;'><a href='{url_dich}' target='_blank' style='color: #2563eb; font-size: 0.82em;'>🔗 {url_dich}</a></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='color: #94a3b8; font-size: 0.82em; padding-top: 5px;'>-</div>", unsafe_allow_html=True)
        with d7:
            if st.button("🗑️", key=f"btn_del_db_{k_key}", help=f"Xóa từ khóa '{kw_display}' khỏi Database"):
                xoa_tu_khoa_khoi_db(k_key)
                st.toast(f"Đã xóa '{kw_display}' khỏi Database!", icon="🗑️")
                st.rerun()

        st.markdown("<div style='border-bottom: 1px solid #f8fafc; margin-bottom: 3px;'></div>", unsafe_allow_html=True)

    # Thêm từ khóa thủ công vào Database
    with st.expander("➕ Thêm Từ Khóa Mới Vào Cơ Sở Dữ Liệu Theo Dõi"):
        col_ad1, col_ad2, col_ad3 = st.columns([2, 1, 1.2])
        with col_ad1:
            raw_new_kws = st.text_area("Nhập danh sách từ khóa muốn thêm (Mỗi từ khóa 1 dòng):", height=90, key="txt_add_new_db_kws")
        with col_ad2:
            new_kw_type = st.radio("Loại từ khóa:", options=["Chính", "Phụ"], horizontal=True, key="radio_new_kw_type")
        with col_ad3:
            new_kw_cat = st.selectbox(
                "Chuyên mục:",
                options=[
                    "Bàn Ghế Sân Vườn & Ngoài Trời",
                    "Gỗ Nhựa Ngoài Trời & Sàn Vỉ",
                    "Tấm Ốp Nano & Trần Giật Cấp",
                    "Tấm PVC Vân Đá Cẩm Thạch",
                    "Tấm Ốp Lam Sóng",
                    "Thanh Lam Hộp & Trụ Pergola",
                    "Thanh Đa Năng & Cổng Rào",
                    "Tổng hợp"
                ],
                key="sb_new_kw_cat"
            )
            
        if st.button("💾 Xác Nhận Thêm Vào Database", type="primary", key="btn_save_new_db_kws"):
            lines_new = [l.strip() for l in raw_new_kws.splitlines() if l.strip()]
            if lines_new:
                added = them_tu_khoa_vao_db(
                    lines_new, 
                    loai=new_kw_type, 
                    chuyen_muc=new_kw_cat, 
                    danh_sach_bai_viet_wp=danh_sach_bai_viet_wp
                )
                st.success(f"✅ Đã thêm mới thành công **{added} từ khóa** vào Database theo dõi!")
                st.rerun()
            else:
                st.warning("Vui lòng nhập ít nhất một từ khóa!")
