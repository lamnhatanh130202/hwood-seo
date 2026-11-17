import re
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from modules.content_planner import (
    lay_ke_hoach_thang,
    luu_ke_hoach_thang,
    tao_ke_hoach_thang_ai,
    xuat_csv_ke_hoach_thang,
    lay_danh_sach_thang_da_co
)
from modules.ai_engine import tao_bai_viet_hwood_chuan_seo

def render_tab6(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, danh_sach_bai_viet_wp=None, kho_tri_thuc=""):
    """Giao diện Tab 6: Lên Kế Hoạch Nội Dung Tháng (Content Editorial Calendar)"""
    st.markdown("### 📅 Kế Hoạch Biên Tập Nội Dung Tháng (Content Planner)")
    st.markdown("Hệ thống tự động phân bổ bài viết theo từng tuần, kết hợp **5 Topic Cluster** và **27 Định dạng thể loại** của HWOOD để tạo một lộ trình phủ sóng từ khóa dày đặc trên Google. Bạn có thể bấm **'✍️ Viết Ngay'** để chuyển bất kỳ bài nào sang Tab 1 viết ngay lập tức!")

    # 1. KHU VỰC THIẾT LẬP THÁNG & TẠO KẾ HOẠCH
    col_t1, col_t2, col_t3, col_t4 = st.columns([2, 1.5, 2.5, 2])
    
    # Tính tháng năm hiện tại làm mặc định
    now = datetime.now()
    thang_mac_dinh = f"Tháng {now.month:02d}/{now.year}"
    
    with col_t1:
        thang_chon = st.text_input("Kỳ kế hoạch (Tháng/Năm):", value=thang_mac_dinh, key="input_thang_plan")
    with col_t2:
        so_bai_tuan = st.selectbox("Tần suất xuất bản:", options=["3 bài / tuần (~12 bài)", "4 bài / tuần (~16 bài)", "5 bài / tuần (~20 bài)", "2 bài / tuần (~8 bài)"], index=0, key="sb_so_bai_tuan")
    with col_t3:
        ds_trong_tam = [
            "Tất cả 5 cụm chủ đề (Phân bổ đều)",
            "Đẩy mạnh: Bàn ghế sân vườn & Ngoài trời",
            "Đẩy mạnh: Sàn gỗ nhựa hồ bơi & Vỉ ban công",
            "Đẩy mạnh: Tấm ốp ngoài trời WPC & Phủ ASA",
            "Đẩy mạnh: Tấm ốp nano & PVC vân đá",
            "Đẩy mạnh: Báo giá & Hướng dẫn thi công (Commercial/How-to)"
        ]
        chu_de_trong_tam = st.selectbox("Trọng tâm chiến dịch:", options=ds_trong_tam, key="sb_trong_tam_plan")
    with col_t4:
        st.write("")
        st.write("")
        btn_tao_plan = st.button("🚀 AI Lập Kế Hoạch Tháng", type="primary", use_container_width=True)

    # Đọc kế hoạch của tháng được chọn
    danh_sach_bai = lay_ke_hoach_thang(thang_chon)

    # Xử lý khi bấm nút tạo plan bằng AI
    if btn_tao_plan:
        if not api_key:
            st.error("Vui lòng nhập DeepSeek API Key ở thanh điều hướng bên trái!")
        else:
            with st.spinner(f"🤖 DeepSeek đang nghiên cứu ma trận từ khóa website và lập kế hoạch {thang_chon}... Vui lòng chờ vài giây!"):
                try:
                    so_bai_int = 3
                    if "4 bài" in so_bai_tuan:
                        so_bai_int = 4
                    elif "5 bài" in so_bai_tuan:
                        so_bai_int = 5
                    elif "2 bài" in so_bai_tuan:
                        so_bai_int = 2

                    plan_moi = tao_ke_hoach_thang_ai(
                        api_key=api_key,
                        model=chon_model,
                        thang_nam=thang_chon,
                        so_bai_tuan=so_bai_int,
                        chu_de_trong_tam=chu_de_trong_tam,
                        ds_wp=danh_sach_bai_viet_wp,
                        kho_tri_thuc=kho_tri_thuc
                    )
                    luu_ke_hoach_thang(thang_chon, plan_moi)
                    st.success(f"🎉 Đã khởi tạo thành công Kế Hoạch {thang_chon} với {len(plan_moi)} bài viết chuẩn SEO!")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Lỗi khi lập kế hoạch AI: {ex}")

    st.markdown("---")

    # 2. HIỂN THỊ VÀ QUẢN LÝ KẾ HOẠCH NỘI DUNG
    if danh_sach_bai:
        # Thống kê nhanh
        tong_bai = len(danh_sach_bai)
        da_viet = len([b for b in danh_sach_bai if b.get("trang_thai") == "Đã hoàn thành" or "Đã" in b.get("trang_thai", "")])
        chua_viet = tong_bai - da_viet
        tien_do = int((da_viet / tong_bai) * 100) if tong_bai > 0 else 0

        col_st1, col_st2, col_st3, col_st4 = st.columns([2, 1.5, 1.5, 2])
        with col_st1:
            st.markdown(f"**Tiến độ tháng:** `{da_viet}/{tong_bai} bài hoàn thành` ({tien_do}%)")
            st.progress(tien_do / 100)
        with col_st2:
            st.metric("Bài chưa viết", f"{chua_viet} bài")
        with col_st3:
            st.metric("Đã hoàn thành", f"{da_viet} bài")
        with col_st4:
            csv_plan = xuat_csv_ke_hoach_thang(danh_sach_bai)
            st.download_button(
                label="📥 Xuất File Excel Kế Hoạch",
                data=csv_plan,
                file_name=f"ke_hoach_noi_dung_{thang_chon.replace('/', '_')}.csv",
                mime="text/csv",
                use_container_width=True,
                help="Tải về file Excel bảng kế hoạch tháng đầy đủ phân bổ theo tuần và ngày (chuẩn tiếng Việt có dấu)"
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Bộ lọc kế hoạch
        col_f1, col_f2 = st.columns([1.5, 2.5])
        with col_f1:
            ds_tuan = ["Tất Cả Các Tuần"] + sorted(list(set(b.get("tuan", "Tuần 1") for b in danh_sach_bai)))
            loc_tuan = st.selectbox("Lọc theo tuần:", options=ds_tuan, key="sb_filter_plan_week")
        with col_f2:
            tim_kiem_plan = st.text_input("🔎 Tìm kiếm trong kế hoạch:", placeholder="Nhập từ khóa hoặc tiêu đề...", key="input_search_plan")

        # Áp dụng bộ lọc
        ds_hien_thi = danh_sach_bai
        if loc_tuan != "Tất Cả Các Tuần":
            ds_hien_thi = [b for b in ds_hien_thi if b.get("tuan") == loc_tuan]
        if tim_kiem_plan.strip():
            q = tim_kiem_plan.lower()
            ds_hien_thi = [
                b for b in ds_hien_thi 
                if q in b.get("tieu_de", "").lower() 
                or q in b.get("tu_khoa_chinh", "").lower()
                or q in b.get("cum_chu_de", "").lower()
            ]

        # Danh sách bài viết dạng Card tương tác
        for idx, item in enumerate(ds_hien_thi):
            is_done = (item.get("trang_thai") == "Đã hoàn thành" or "Đã" in item.get("trang_thai", ""))
            card_border = "#3b8632" if is_done else "#e2e8f0"
            card_bg = "#f9fcf9" if is_done else "#ffffff"
            badge_status = '<span style="background-color: #3b8632; color: #fff; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">🟢 Đã viết</span>' if is_done else '<span style="background-color: #f59e0b; color: #fff; padding: 3px 8px; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">🟡 Chưa viết</span>'

            sec_kws = item.get("tu_khoa_phu", [])
            sec_tags_html = " ".join([
                f'<span style="background-color: #f1f5f9; color: #334155; padding: 2px 7px; border-radius: 10px; font-size: 0.78rem; border: 1px solid #e2e8f0; margin-right: 4px;">{s}</span>'
                for s in (sec_kws if isinstance(sec_kws, list) else [str(sec_kws)])
            ])

            with st.container():
                st.markdown(
                    f"""<div style="border: 1px solid {card_border}; background-color: {card_bg}; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <div>
                                <span style="background-color: #eff6ff; color: #1d4ed8; font-weight: bold; font-size: 0.82rem; padding: 3px 8px; border-radius: 4px; border: 1px solid #bfdbfe;">📌 {item.get('tuan', '')} - {item.get('thu', '')}</span>
                                <span style="background-color: #f3f4f6; color: #374151; font-size: 0.82rem; padding: 3px 8px; border-radius: 4px; margin-left: 6px;">📂 {item.get('cum_chu_de', '')}</span>
                                <span style="background-color: #fdf2f8; color: #9d174d; font-size: 0.82rem; padding: 3px 8px; border-radius: 4px; margin-left: 6px;">🎯 {item.get('search_intent', '')}</span>
                            </div>
                            <div>{badge_status}</div>
                        </div>
                        <div style="font-size: 1.05rem; font-weight: bold; color: #1e293b; margin: 6px 0;">{item.get('tieu_de', '')}</div>
                        <div style="font-size: 0.9rem; color: #475569; margin-bottom: 6px;">
                            <b>🎯 Focus Keyword:</b> <span style="color: #166534; font-weight: bold; background: #eef7ee; padding: 2px 6px; border-radius: 4px;">{item.get('tu_khoa_chinh', '')}</span>
                            <span style="margin-left: 12px;"><b>📐 Thể loại:</b> <i>{item.get('the_loai', '')}</i></span>
                        </div>
                        <div style="margin-bottom: 6px;">
                            <b>📎 Từ khóa phụ:</b> {sec_tags_html}
                        </div>
                        <div style="font-size: 0.85rem; color: #64748b; font-style: italic; background: #f8fafc; padding: 6px 10px; border-radius: 4px; border-left: 3px solid #3b8632;">
                            💡 <b>Góc nhìn chiến lược:</b> {item.get('ghi_chu', '')}
                        </div>
                    </div>""",
                    unsafe_allow_html=True
                )

                col_btn1, col_btn2, col_btn3 = st.columns([2, 1.2, 1.2])
                with col_btn1:
                    btn_write_now = st.button(
                        f"🚀 Lấy Bài Này Viết Ngay (AI Viết & Mở Tab 1)",
                        key=f"btn_write_plan_{idx}",
                        use_container_width=True,
                        type="primary" if not is_done else "secondary"
                    )
                    if btn_write_now:
                        if not api_key:
                            st.error("⚠️ Vui lòng nhập DeepSeek API Key ở thanh bên trái!")
                        else:
                            kw_bai = item.get("tu_khoa_chinh", "")
                            the_loai_bai = item.get("the_loai", "🤖 Tự động nhận diện theo từ khóa (Mặc định)")
                            with st.status(f"🤖 Đang tạo bài viết: '{kw_bai}'...", expanded=True) as status_box:
                                st.write("⏳ Đang nạp tri thức HWOOD và gửi yêu cầu tới DeepSeek AI...")
                                try:
                                    tieu_de_bai = item.get("tieu_de", "")
                                    tu_khoa_phu = item.get("tu_khoa_phu", [])
                                    ghi_chu_chien_luoc = item.get("ghi_chu", "")
                                    search_intent = item.get("search_intent", "")
                                    cum_chu_de = item.get("cum_chu_de", "")

                                    noi_dung_bai, meta_t, meta_d = tao_bai_viet_hwood_chuan_seo(
                                        tu_khoa=kw_bai,
                                        the_loai_bai=the_loai_bai,
                                        do_dai_bai="Tiêu chuẩn SEO (1.300 - 1.600 từ)",
                                        api_key=api_key,
                                        chon_model=chon_model,
                                        danh_sach_bai_viet_wp=danh_sach_bai_viet_wp,
                                        tieu_de=tieu_de_bai,
                                        tu_khoa_phu=tu_khoa_phu,
                                        ghi_chu_chien_luoc=ghi_chu_chien_luoc,
                                        search_intent=search_intent,
                                        cum_chu_de=cum_chu_de,
                                        toi_uu_token=True
                                    )
                                    st.session_state.noi_dung_bai_viet = noi_dung_bai
                                    st.session_state.tu_khoa_hien_tai = kw_bai
                                    st.session_state.meta_title = meta_t
                                    st.session_state.meta_desc = meta_d
                                    st.session_state.bai_duoc_chuyen_sang_tab1 = tieu_de_bai
                                    st.session_state.ke_hoach_item_dang_viet = item
                                    st.session_state["chuyen_tab_index"] = 0  # Tự động nhảy sang Tab 1

                                    item["trang_thai"] = "Đã hoàn thành"
                                    luu_ke_hoach_thang(thang_chon, danh_sach_bai)
                                    status_box.update(label=f"🎉 Đã viết xong '{kw_bai}'! Đang mở Tab 1...", state="complete")
                                    st.toast(f"🎉 Đã viết xong '{kw_bai}' và chuyển sang Tab 1!", icon="✅")
                                    st.rerun()
                                except Exception as ex_w:
                                    status_box.update(label=f"❌ Lỗi: {ex_w}", state="error")
                                    st.error(f"Lỗi khi viết bài: {ex_w}")

                with col_btn2:
                    new_status = "Đã hoàn thành" if not is_done else "Chưa viết"
                    lbl_btn_toggle = "✅ Đánh dấu hoàn thành" if not is_done else "🔄 Đặt lại chưa viết"
                    if st.button(lbl_btn_toggle, key=f"btn_toggle_status_{idx}", use_container_width=True):
                        item["trang_thai"] = new_status
                        luu_ke_hoach_thang(thang_chon, danh_sach_bai)
                        st.rerun()
                with col_btn3:
                    if st.button("🗑️ Xóa bài này", key=f"btn_del_plan_{idx}", use_container_width=True):
                        if item in danh_sach_bai:
                            danh_sach_bai.remove(item)
                            luu_ke_hoach_thang(thang_chon, danh_sach_bai)
                            st.toast("Đã xóa bài khỏi kế hoạch!", icon="🗑️")
                            st.rerun()

                # Nếu bài này đã viết hoặc đã xong, hiển thị nút mở xem ngay
                if is_done or item.get("trang_thai") == "Đã hoàn thành":
                    c_done_box1, c_done_box2 = st.columns([2.5, 1.5])
                    with c_done_box1:
                        if st.button(f"👉 Mở Tab 1 xem chi tiết bài '{item.get('tu_khoa_chinh')}' & Đăng WP", key=f"btn_open_tab1_{idx}", type="primary", use_container_width=True):
                            st.session_state.tu_khoa_hien_tai = item.get("tu_khoa_chinh", "")
                            st.session_state["chuyen_tab_index"] = 0
                            st.rerun()
                    with c_done_box2:
                        st.caption("✅ Đã có trong Tab 1 & Lịch sử lưu")

                st.write("")

        st.markdown("---")
        # Thêm bài viết thủ công vào kế hoạch
        with st.expander("➕ Thêm Bài Viết Mới Thủ Công Vào Kế Hoạch Này"):
            col_add1, col_add2, col_add3 = st.columns([1.5, 1.5, 3])
            with col_add1:
                tuan_add = st.selectbox("Tuần:", options=["Tuần 1", "Tuần 2", "Tuần 3", "Tuần 4"], key="sb_add_tuan")
            with col_add2:
                thu_add = st.selectbox("Thứ:", options=["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"], key="sb_add_thu")
            with col_add3:
                tieu_de_add = st.text_input("Tiêu đề bài viết đề xuất:", placeholder="Nhập tiêu đề chuẩn SEO...", key="txt_add_tieu_de")

            col_add4, col_add5, col_add6 = st.columns([2, 2, 2])
            with col_add4:
                kw_chinh_add = st.text_input("Từ khóa chính (Focus):", placeholder="Ví dụ: báo giá lam sóng ngoài trời...", key="txt_add_kw_chinh")
            with col_add5:
                kw_phu_add = st.text_input("Từ khóa phụ (cách nhau bởi dấu phẩy):", placeholder="lam sóng asa, giá thi công lam sóng...", key="txt_add_kw_phu")
            with col_add6:
                the_loai_add = st.selectbox("Thể loại:", options=[
                    "💰 Báo Giá (Price) + Bảng HTML kỹ thuật & VAT 8%",
                    "⚖️ So Sánh (Comparison) - 2 hoặc 4 loại vật liệu",
                    "🖼️ Mẫu & Thiết Kế (Gallery / Listicle) - Top mẫu đẹp xu hướng",
                    "🛠️ Hướng Dẫn Kỹ Thuật (How-to) + Checklist thi công",
                    "⭐ Review / Đánh Giá Thực Tế + Giải đáp thắc mắc Q&A",
                    "🎯 Hướng Dẫn Chọn Mua + Kỹ thuật mã hàng",
                    "🏡 Giải Pháp Ứng Dụng & Case Study theo không gian",
                    "📖 Định Nghĩa & Giải Thích (Define) + Báo giá cơ bản"
                ], key="sb_add_the_loai")

            if st.button("➕ Thêm Bài Viết Này Vào Kế Hoạch", key="btn_add_manual_plan", use_container_width=True):
                if tieu_de_add.strip() and kw_chinh_add.strip():
                    secs = [s.strip() for s in kw_phu_add.split(",") if s.strip()]
                    bai_moi = {
                        "tuan": tuan_add,
                        "thu": thu_add,
                        "tieu_de": tieu_de_add.strip(),
                        "tu_khoa_chinh": kw_chinh_add.strip(),
                        "tu_khoa_phu": secs,
                        "the_loai": the_loai_add,
                        "search_intent": "Thương mại & Tư vấn",
                        "cum_chu_de": "HWOOD Vật Liệu",
                        "ghi_chu": "Bài viết được thêm thủ công bởi SEO Specialist",
                        "trang_thai": "Chưa viết"
                    }
                    danh_sach_bai.append(bai_moi)
                    luu_ke_hoach_thang(thang_chon, danh_sach_bai)
                    st.success("Đã thêm bài viết mới vào kế hoạch!")
                    st.rerun()
                else:
                    st.warning("Vui lòng nhập đầy đủ Tiêu đề và Từ khóa chính!")

    else:
        st.info(f"💡 Hiện chưa có kế hoạch nội dung nào cho **{thang_chon}**. Hãy chọn cấu hình ở trên và bấm **'🚀 AI Lập Kế Hoạch Tháng'** để DeepSeek tự động xây dựng lộ trình phủ từ khóa hoàn chỉnh cho bạn nhé!")
