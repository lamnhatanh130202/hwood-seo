# HWOOD SEO Assistant - WordPress REST API Sync Enabled
import os
import streamlit as st
import streamlit.components.v1 as components

# Import các module chức năng từ thư mục modules/
from modules.knowledge import doc_kho_tri_thuc
from modules.wordpress_api import lay_toan_bo_du_lieu_wp, lay_tat_ca_noi_dung_wp

# Import giao diện từng Tab từ thư mục tabs/
from tabs.tab1_viet_moi import render_tab1
from tabs.tab2_kham_bai import render_tab2
from tabs.tab3_kiem_toan import render_tab3
from tabs.tab4_thu_hang import render_tab4
from tabs.tab5_lich_su import render_tab5
from tabs.tab6_ke_hoach_thang import render_tab6
from tabs.tab7_chat_chien_luoc import render_tab7
from tabs.tab8_bot_farm import render_tab8
from tabs.tab9_traffic_analytics import render_tab9

# ==============================================================================
# 1. CẤU HÌNH GIAO DIỆN TRANG WEB STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="HWOOD VIỆT NAM - SEO AI Assistant",
    page_icon=os.path.join(os.path.dirname(__file__), "hwood_app_icon.png") if os.path.exists(os.path.join(os.path.dirname(__file__), "hwood_app_icon.png")) else "🪵",
    layout="wide"
)

# Tùy chỉnh CSS giao diện theo tông màu chuẩn thương hiệu HWOOD (#3b8632)
st.markdown("""
<style>
    .main-title {
        color: #3b8632;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #555;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        background-color: #3b8632;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.6rem 1.5rem;
        border: none;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #2e6927;
        color: white;
    }
    .metric-box {
        background-color: #f7faf6;
        border: 1px solid #c2e0be;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: bold;
        color: #3b8632;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #666;
    }
    .audit-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-left: 5px solid #3b8632;
        border-radius: 6px;
        padding: 14px;
        margin-bottom: 12px;
    }

    /* =========================================================================
       THANH MENU HEADER BAR CHUYÊN NGHIỆP (TOP NAVIGATION NAVBAR)
       ========================================================================= */
    div[data-baseweb="tab-list"] {
        display: flex !important;
        flex-wrap: wrap !important;
        gap: 6px !important;
        background: #f8fafc !important;
        padding: 6px 8px !important;
        border-radius: 10px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        margin-top: 6px !important;
        margin-bottom: 20px !important;
        overflow: visible !important;
    }

    /* Nút Menu Từng Tab */
    button[data-baseweb="tab"] {
        flex: 1 1 auto !important;
        min-width: 120px !important;
        text-align: center !important;
        background-color: #ffffff !important;
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        padding: 8px 12px !important;
        border-radius: 7px !important;
        border: 1px solid #e2e8f0 !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        white-space: nowrap !important;
        cursor: pointer !important;
    }

    /* Hiệu ứng rê chuột */
    button[data-baseweb="tab"]:hover {
        background-color: #eef7ee !important;
        color: #3b8632 !important;
        border-color: #a3d99e !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 5px rgba(59, 134, 50, 0.15) !important;
    }

    /* Nút Menu Active (Đang được chọn) */
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #3b8632 !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border-color: #3b8632 !important;
        border-radius: 7px !important;
        box-shadow: 0 3px 8px rgba(59, 134, 50, 0.35) !important;
        transform: translateY(-1px) !important;
    }

    /* Ẩn hoàn toàn gạch chân đỏ mặc định của Streamlit */
    div[data-baseweb="tab-highlight"],
    div[data-baseweb="tab-border"] {
        display: none !important;
    }

    /* Ẩn các nút mũi tên cuộn scroll mặc định của Streamlit tab nếu có */
    div[data-baseweb="tab-list"] > button[aria-label="Previous tab"],
    div[data-baseweb="tab-list"] > button[aria-label="Next tab"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# 2. KHỞI TẠO SESSION STATE
# ==============================================================================
if "noi_dung_bai_viet" not in st.session_state:
    st.session_state.noi_dung_bai_viet = ""
if "tu_khoa_hien_tai" not in st.session_state:
    st.session_state.tu_khoa_hien_tai = ""
if "meta_title" not in st.session_state:
    st.session_state.meta_title = ""
if "meta_desc" not in st.session_state:
    st.session_state.meta_desc = ""

# Session state cho tính năng Tối ưu bài cũ & Xem chỉnh sửa trang sản phẩm
if "wp_post_type" not in st.session_state:
    st.session_state.wp_post_type = "pages"
if "bai_cu_duoc_chon" not in st.session_state:
    st.session_state.bai_cu_duoc_chon = None
if "tieu_de_edit_tay" not in st.session_state:
    st.session_state.tieu_de_edit_tay = ""
if "noi_dung_edit_tay" not in st.session_state:
    st.session_state.noi_dung_edit_tay = ""
if "noi_dung_toi_uu" not in st.session_state:
    st.session_state.noi_dung_toi_uu = ""
if "bao_cao_audit" not in st.session_state:
    st.session_state.bao_cao_audit = ""
if "wp_page_num" not in st.session_state:
    st.session_state.wp_page_num = 1
if "history_page_num" not in st.session_state:
    st.session_state.history_page_num = 1
if "kw_matrix_page_num" not in st.session_state:
    st.session_state.kw_matrix_page_num = 1
if "kw_ai_suggestions" not in st.session_state:
    st.session_state.kw_ai_suggestions = ""
if "rank_check_results" not in st.session_state:
    st.session_state.rank_check_results = []
if "rank_selected_preset" not in st.session_state:
    st.session_state.rank_selected_preset = "🎯 Dựa vào keyword hiện có trong bài viết (Tự động nạp)"
if "rank_custom_keywords" not in st.session_state:
    st.session_state.rank_custom_keywords = ""
if "the_loai_duoc_chon" not in st.session_state:
    st.session_state.the_loai_duoc_chon = "🤖 Tự động nhận diện theo từ khóa (Mặc định)"
if "bai_duoc_chuyen_sang_tab1" not in st.session_state:
    st.session_state.bai_duoc_chuyen_sang_tab1 = ""


# ==============================================================================
# 3. NẠP KHO TRI THỨC SẢN PHẨM HWOOD
# ==============================================================================
@st.cache_data
def nạp_tri_thuc():
    return doc_kho_tri_thuc()

KHO_TRI_THUC, so_luong_file, ds_file = nạp_tri_thuc()


# ==============================================================================
# 4. THANH ĐIỀU HƯỚNG BÊN TRÁI (SIDEBAR)
# ==============================================================================
with st.sidebar:
    logo_path = os.path.join(os.path.dirname(__file__), "hwood_app_icon.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=70)
    else:
        st.image("https://img.icons8.com/fluency/96/wood.png", width=60)
    st.title("HWOOD SEO Control")

    if st.button("🔄 Làm mới trang (F5)", key="sidebar_btn_f5", use_container_width=True, help="Tải lại toàn bộ ứng dụng và dữ liệu mới nhất (như phím F5 hoặc Ctrl+R)"):
        st.rerun()

    # 1. Chọn nguồn AI: Antigravity (Miễn phí) hoặc DeepSeek API Key
    DEEPSEEK_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deepseek_key.txt")
    loaded_api_key = ""
    if os.path.exists(DEEPSEEK_KEY_FILE):
        try:
            with open(DEEPSEEK_KEY_FILE, "r", encoding="utf-8") as f:
                loaded_api_key = f.read().strip()
        except Exception:
            pass
    if not loaded_api_key:
        loaded_api_key = os.environ.get("DEEPSEEK_API_KEY", "")

    ai_mode = st.radio(
        "🤖 Nguồn xử lý AI:",
        options=["🚀 Dùng Antigravity (Miễn phí - Không cần API)", "🔑 Dùng DeepSeek API Key"],
        index=0,
        help="• Dùng Antigravity: Không tốn phí API! App tự gom Tri thức HWOOD & dữ liệu thành Prompt chuẩn để gửi Antigravity xử lý.\n• Dùng DeepSeek API Key: Gọi tự động qua key DeepSeek trả phí."
    )
    use_antigravity = ai_mode.startswith("🚀")
    st.session_state["use_antigravity"] = use_antigravity

    if use_antigravity:
        api_key = ""
        chon_model = "antigravity"
        st.success("✅ Đang dùng **Antigravity** (Miễn phí 100%, không cần API Key). Bấm nút ở các Tab để lấy Prompt chuẩn HWOOD!")
    else:
        api_key = st.text_input(
            "DeepSeek API Key:",
            value=loaded_api_key,
            type="password",
            placeholder="sk-...",
            help="Nhập API Key DeepSeek của bạn. Key được lưu an toàn cục bộ trên máy và không bao giờ đồng bộ lên GitHub."
        )
        if api_key and api_key != loaded_api_key:
            try:
                with open(DEEPSEEK_KEY_FILE, "w", encoding="utf-8") as f:
                    f.write(api_key.strip())
            except Exception:
                pass

        chon_model = st.selectbox(
            "Chọn Model DeepSeek:",
            options=["deepseek-flash", "deepseek-chat", "deepseek-reasoner"],
            index=0,
            help="• deepseek-flash: Model RẺ NHẤT HIỆN NAY (DeepSeek-V3 siêu tốc độ, tối ưu chi phí ~0.14$/1M token, viết bài SEO cực mượt).\n• deepseek-chat: Model tiêu chuẩn.\n• deepseek-reasoner: Suy luận phản biện chuyên sâu (R1)."
        )

    st.markdown("---")

    # 2. Kết nối WordPress (Royal MCP)
    st.subheader("🌐 Kết nối WordPress")
    ket_noi_wp = st.checkbox("Bật đồng bộ WordPress", value=True)
    
    wp_site_url = "https://hwood.vn"
    DEFAULT_APP_PASS = "Wh7M rPPJ Dp4j UxP5 52HR LEU0"
    royal_api_key = st.session_state.get("wp_app_pass", DEFAULT_APP_PASS)
    DEFAULT_WP_USER = "hwoodhplus@gmail.com"
    wp_username = st.session_state.get("wp_username", DEFAULT_WP_USER)
    danh_sach_bai_viet_wp = []
    
    if ket_noi_wp:
        DEFAULT_WP_URL = "https://hwood.vn"
        wp_site_url = st.text_input(
            "Website WordPress:",
            value=DEFAULT_WP_URL
        ).strip().rstrip("/")
        
        col_wpu1, col_wpu2 = st.columns(2)
        with col_wpu1:
            wp_username = st.text_input(
                "Tên đăng nhập WP:",
                value=st.session_state.get("wp_username", DEFAULT_WP_USER),
                placeholder="vd: hwoodhplus@gmail.com",
                help="Tên tài khoản quản trị viên hoặc biên tập viên trên WordPress (dùng để xác thực quyền đăng bài)."
            ).strip()
            if wp_username:
                st.session_state.wp_username = wp_username
                
        with col_wpu2:
            royal_api_key = st.text_input(
                "Mật khẩu ứng dụng / Key:",
                value=st.session_state.get("wp_app_pass", DEFAULT_APP_PASS),
                type="password",
                help="Mật khẩu ứng dụng (Application Password) lấy tại: WP Admin > Thành viên > Hồ sơ > Mật khẩu ứng dụng, hoặc Khóa API."
            ).strip()
            if royal_api_key:
                st.session_state.wp_app_pass = royal_api_key
        
        if wp_site_url:
            try:
                danh_sach_bai_viet_wp = lay_tat_ca_noi_dung_wp(wp_site_url, royal_api_key, wp_username=wp_username)
            except TypeError:
                danh_sach_bai_viet_wp = lay_tat_ca_noi_dung_wp(wp_site_url, royal_api_key)
            if danh_sach_bai_viet_wp:
                st.success(f"Đã đồng bộ đủ **{len(danh_sach_bai_viet_wp)} trang & bài** từ hwood.vn!")
                if st.button("🔄 Quét lại bài mới từ WP", key="btn_refresh_wp"):
                    wp_cache_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wp_content_cache.json")
                    if os.path.exists(wp_cache_file):
                        try:
                            os.remove(wp_cache_file)
                        except Exception:
                            pass
                    st.cache_data.clear()
                    st.rerun()
            else:
                st.warning("Đang kết nối tới hwood.vn...")

    st.markdown("---")
    
    # 3. Trạng thái Bộ não tri thức
    st.subheader("🧠 Tri thức HWOOD")
    if so_luong_file > 0:
        st.success(f"Đã nạp **{so_luong_file}** file `.md` ({len(KHO_TRI_THUC):,} ký tự)")
        with st.expander("Xem danh sách tài liệu"):
            for f in ds_file:
                st.write(f"- 📄 `{f}`")
    else:
        st.warning("Chưa có file `.md` nào!")

    if st.button("🔄 Cập nhật lại kho tri thức"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.caption("Thương hiệu HWOOD VIỆT NAM\nHotline: 0912 565 353")


# ==============================================================================
# 5. GIAO DIỆN CHÍNH - 5 TABS CHỨC NĂNG
# ==============================================================================
st.markdown("""
<div style="display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%); border: 1px solid #dcfce7; border-radius: 12px; padding: 16px 22px; margin-bottom: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.03);">
    <div>
        <div style="font-size: 1.7rem; font-weight: 800; color: #2e6927; display: flex; align-items: center; gap: 8px;">
            🪵 HWOOD - TRỢ LÝ VIẾT BÀI & TỐI ƯU SEO WEBSITE
        </div>
        <div style="color: #4b5563; font-size: 0.92rem; margin-top: 4px;">
            Hệ thống AI tự động hóa sáng tạo bài viết mới, kiểm toán và nâng cấp bài viết cũ chuẩn SEO thương hiệu HWOOD.
        </div>
    </div>
    <div style="text-align: right; font-size: 0.85rem; color: #166534; font-weight: 600; background: #eef7ee; padding: 6px 12px; border-radius: 8px; border: 1px solid #bbf7d0;">
        📞 Hotline: 0912 565 353<br>
        🌐 hwood.vn | Topic Cluster 2026
    </div>
</div>
""", unsafe_allow_html=True)

# Tự động chuyển tab nếu có yêu cầu (chuyển sang Tab 1 khi viết bài từ Kế Hoạch)
if "chuyen_tab_index" in st.session_state:
    tab_target = st.session_state.pop("chuyen_tab_index")
    components.html(f"""
    <script>
        setTimeout(() => {{
            try {{
                const doc = window.parent ? window.parent.document : document;
                const tabs = doc.querySelectorAll('button[data-baseweb="tab"]');
                if (tabs && tabs[{tab_target}]) {{
                    tabs[{tab_target}].click();
                }}
            }} catch(e) {{
                console.warn('Tab switch iframe error:', e);
            }}
        }}, 120);
    </script>
    """, height=0)

tab_viet_moi, tab_kham_bai_cu, tab_ma_tran_kw, tab_rank_tracker, tab_ke_hoach_thang, tab_chat_advisor, tab_lich_su, tab_bot_farm, tab_traffic_analytics = st.tabs([
    "✍️ Viết Bài Mới", 
    "🔍 Sửa Bài Cũ / WP", 
    "📊 Ma Trận Keyword", 
    "🎯 Thứ Hạng Google", 
    "📅 Kế Hoạch Tháng", 
    "💬 Cố Vấn & Lỗi Sai", 
    "📚 Lịch Sử Bài Lưu",
    "🤖 5 Bot Quét Thứ Hạng",
    "📈 Hiệu Suất GA4 & Search Console"
])

with tab_viet_moi:
    render_tab1(
        api_key=api_key,
        chon_model=chon_model,
        ket_noi_wp=ket_noi_wp,
        wp_site_url=wp_site_url,
        royal_api_key=royal_api_key,
        danh_sach_bai_viet_wp=danh_sach_bai_viet_wp,
        wp_username=wp_username
    )

with tab_kham_bai_cu:
    render_tab2(
        api_key=api_key,
        chon_model=chon_model,
        ket_noi_wp=ket_noi_wp,
        wp_site_url=wp_site_url,
        royal_api_key=royal_api_key,
        kho_tri_thuc=KHO_TRI_THUC,
        ds_file=ds_file,
        wp_username=wp_username
    )

with tab_ma_tran_kw:
    render_tab3(
        api_key=api_key,
        chon_model=chon_model,
        ket_noi_wp=ket_noi_wp,
        wp_site_url=wp_site_url,
        royal_api_key=royal_api_key,
        danh_sach_bai_viet_wp=danh_sach_bai_viet_wp,
        kho_tri_thuc=KHO_TRI_THUC
    )

with tab_rank_tracker:
    render_tab4(
        api_key=api_key,
        chon_model=chon_model,
        ket_noi_wp=ket_noi_wp,
        wp_site_url=wp_site_url,
        royal_api_key=royal_api_key,
        danh_sach_bai_viet_wp=danh_sach_bai_viet_wp
    )

with tab_ke_hoach_thang:
    render_tab6(
        api_key=api_key,
        chon_model=chon_model,
        ket_noi_wp=ket_noi_wp,
        wp_site_url=wp_site_url,
        royal_api_key=royal_api_key,
        danh_sach_bai_viet_wp=danh_sach_bai_viet_wp,
        kho_tri_thuc=KHO_TRI_THUC
    )

with tab_chat_advisor:
    render_tab7(
        api_key=api_key,
        chon_model=chon_model,
        ket_noi_wp=ket_noi_wp,
        wp_site_url=wp_site_url,
        royal_api_key=royal_api_key,
        danh_sach_bai_viet_wp=danh_sach_bai_viet_wp,
        kho_tri_thuc=KHO_TRI_THUC
    )

with tab_lich_su:
    render_tab5(
        api_key=api_key,
        chon_model=chon_model,
        ket_noi_wp=ket_noi_wp,
        wp_site_url=wp_site_url,
        royal_api_key=royal_api_key,
        wp_username=wp_username
    )

with tab_bot_farm:
    render_tab8()

with tab_traffic_analytics:
    render_tab9()

