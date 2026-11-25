# -*- coding: utf-8 -*-
"""
TAB 8 - HỆ THỐNG 5 BOT QUÉT THỨ HẠNG GOOGLE (PROXY/VPN RIÊNG)
File này là MỚI, không đụng vào các tab cũ. Để thêm vào app.py, xem hướng dẫn
cuối file hoặc file README_5_BOT.md.
"""
import os
import sys
import json
import csv
import io
import signal
import subprocess
import streamlit as st
from datetime import datetime

# Thư mục gốc dự án (chứa app.py) - file này nằm trong tabs/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Tái dùng bộ từ khóa mẫu có sẵn của dự án (nếu có)
try:
    from modules.rank_tracker import BO_TU_KHOA_HWOOD_PRESETS
    HAS_PRESETS = True
except Exception:
    BO_TU_KHOA_HWOOD_PRESETS = {}
    HAS_PRESETS = False

from modules.bot_farm import doc_tien_do, doc_ket_qua, doc_live_logs, kiem_tra_proxy_mot_bot

# Lưu tiến trình subprocess đang chạy (module-level, tồn tại qua các lần rerun)
RUNNING_PROC = {"popen": None, "started_at": None}


# ==============================================================================
# TIỆN ÍCH GHI CẤU HÌNH RA FILE
# ==============================================================================
def ghi_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def ghi_cau_hinh(keywords_text: str, proxies: list, settings: dict):
    # 1. Từ khóa
    ghi_file(os.path.join(BASE_DIR, "bot_keywords.txt"), keywords_text)
    # 2. Proxy
    ghi_file(
        os.path.join(BASE_DIR, "bot_proxies.json"),
        json.dumps({"bots": proxies}, ensure_ascii=False, indent=2),
    )
    # 3. Cài đặt
    ghi_file(
        os.path.join(BASE_DIR, "bot_settings.json"),
        json.dumps(settings, ensure_ascii=False, indent=2),
    )


def dang_chay() -> bool:
    p = RUNNING_PROC.get("popen")
    if p is not None:
        if p.poll() is None:
            return True
        else:
            RUNNING_PROC["popen"] = None
            return False
    # Fallback kiểm tra bot_farm_progress.json (chỉ coi là đang chạy nếu cập nhật trong 40s trở lại)
    prog = doc_tien_do()
    summary = prog.get("_summary", {})
    if summary.get("status") == "running":
        now = datetime.now()
        for k, v in prog.items():
            if k == "_summary":
                continue
            if v.get("status") in ["running", "starting", "dwelling", "resting", "waiting_captcha"]:
                up_str = v.get("updated_at")
                if up_str:
                    try:
                        up_dt = datetime.fromisoformat(up_str)
                        if (now - up_dt).total_seconds() < 40:
                            return True
                    except Exception:
                        pass
    return False


def dung_bot():
    p = RUNNING_PROC.get("popen")
    if p and p.poll() is None:
        try:
            p.terminate()
            try:
                p.wait(timeout=3)
            except Exception:
                p.kill()
        except Exception:
            pass
    RUNNING_PROC["popen"] = None
    # Cập nhật status dừng trong file tiến độ
    prog = doc_tien_do()
    if prog:
        prog.setdefault("_summary", {})["status"] = "stopped"
        for k, v in prog.items():
            if k != "_summary" and v.get("status") in ["running", "starting", "dwelling", "resting"]:
                v["status"] = "done"
                v["detail"] = "Đã dừng bởi người dùng"
        try:
            with open(os.path.join(BASE_DIR, "bot_farm_progress.json"), "w", encoding="utf-8") as f:
                json.dump(prog, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


# ==============================================================================
# BẢNG ĐIỀU KHIỂN THỜI GIAN THỰC (REALTIME FRAGMENT - TỰ ĐỘNG CẬP NHẬT MỖI 2S)
# ==============================================================================
def _render_dashboard_content(is_running: bool):
    prog = doc_tien_do()
    summary = prog.get("_summary", {})
    results = doc_ket_qua()

    total_kws = summary.get("total_keywords", 0)
    total_processed = sum(v.get("processed", 0) for k, v in prog.items() if k != "_summary" and isinstance(v, dict))
    total_found = sum(v.get("found", 0) for k, v in prog.items() if k != "_summary" and isinstance(v, dict))
    all_done = (not is_running) and (summary.get("status") == "finished" or (total_kws > 0 and total_processed >= total_kws))

    # 1. Header Trạng Thái Thời Gian Thực & Nút Dừng Nhanh
    if is_running:
        c_stt, c_ref, c_btn = st.columns([2.2, 0.9, 0.9])
        with c_stt:
            st.markdown("""
            <div style="background: linear-gradient(90deg, #ecfdf5 0%, #f0fdf4 100%); border: 1.5px solid #10b981; border-radius: 8px; padding: 10px 14px; display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.3rem;">🟢</span>
                <div>
                    <strong style="color: #065f46; font-size: 0.95rem;">HỆ THỐNG ĐANG QUÉT THỜI GIAN THỰC (REALTIME)</strong>
                    <div style="color: #047857; font-size: 0.78rem;">Màn hình tự động cập nhật • Hoạt động ổn định</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with c_ref:
            if st.button("🔄 Cập nhật", key="btn_refresh_realtime", use_container_width=True, help="Làm mới số liệu ngay lập tức"):
                st.rerun()
        with c_btn:
            if st.button("⏹️ DỪNG QUÉT", type="secondary", use_container_width=True, help="Dừng tất cả bot ngay lập tức"):
                dung_bot()
                st.toast("Đã gửi lệnh dừng tất cả bot!", icon="⏹️")
                st.rerun()
    elif all_done:
        c_done1, c_done2 = st.columns([2.5, 1])
        with c_done1:
            st.markdown("""
            <div style="background: #f0fdf4; border: 1.5px solid #86efac; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">
                <strong style="color: #166534; font-size: 0.95rem;">🎉 TẤT CẢ BOT ĐÃ HOÀN THÀNH QUÉT (100%)!</strong>
                <div style="color: #15803d; font-size: 0.8rem;">Dữ liệu thứ hạng đã được lưu an toàn. Bấm <strong>Làm mới (F5)</strong> để sẵn sàng chạy đợt quét tiếp theo.</div>
            </div>
            """, unsafe_allow_html=True)
        with c_done2:
            if st.button("🔄 Làm mới (F5)", key="btn_refresh_alldone", use_container_width=True, type="primary", help="Làm mới lại giao diện và bảng dữ liệu"):
                st.rerun()
    else:
        c_rdy1, c_rdy2 = st.columns([2.5, 1])
        with c_rdy1:
            st.markdown("""
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 14px; margin-bottom: 8px;">
                <span style="color: #475569; font-size: 0.88rem;">⚪ <strong>Trạng thái:</strong> Hệ thống sẵn sàng. Nhập từ khóa ở cột trái và bấm <strong>Bắt đầu chạy 5 Bot</strong>.</span>
            </div>
            """, unsafe_allow_html=True)
        with c_rdy2:
            if st.button("🔄 Làm mới (F5)", key="btn_refresh_ready", use_container_width=True, help="Tải lại dữ liệu mới nhất"):
                st.rerun()
        sys_log_file = os.path.join(BASE_DIR, "bot_farm_sys.log")
        if os.path.exists(sys_log_file):
            try:
                with open(sys_log_file, "r", encoding="utf-8", errors="replace") as f_err:
                    err_txt = f_err.read()
                if "Traceback" in err_txt:
                    st.error(f"⚠️ Phát hiện lỗi trong lần chạy trước:\n```\n{err_txt[-400:]}\n```")
            except Exception:
                pass

    # Cảnh báo Captcha nổi bật gộp gọn gàng
    captcha_bots = [info.get('name', bot_id) for bot_id, info in prog.items() if bot_id != "_summary" and isinstance(info, dict) and info.get("status") == "waiting_captcha"]
    if captcha_bots:
        st.error(f"🚨 **CẦN GIẢI CAPTCHA ({', '.join(captcha_bots)}):** Cửa sổ trình duyệt đang mở trên màn hình. Anh bấm vào giải (tích chọn hình ảnh), Bot sẽ tự động nhận diện và tiếp tục quét ngay lập tức!")

    # 2. Thanh Tiến Độ Tổng Thể
    if total_kws > 0:
        pct = min(1.0, max(0.0, total_processed / total_kws))
        st.progress(pct, text=f"📊 Tiến độ quét: {total_processed}/{total_kws} từ khóa ({int(pct*100)}%) — Thấy HWOOD: {total_found} lượt")

    # 3. Trạng Thái 5 Bot Live Cards (Trực quan, thời gian thực)
    st.markdown("##### 🤖 Trạng thái 5 Bot thời gian thực:")
    bot_cols = st.columns(5)
    for idx in range(5):
        b_id = f"bot_{idx+1:02d}"
        b_name = f"Bot {idx+1}"
        info = prog.get(b_id, {})
        stt = info.get("status", "idle")
        detail = info.get("detail", "Chưa có nhiệm vụ")
        processed = info.get("processed", 0)
        found = info.get("found", 0)

        if all_done:
            stt = "done"
            if "Nghỉ" in detail or "Đang" in detail:
                detail = f"Đã hoàn thành {processed} từ khóa"

        if stt == "waiting_captcha":
            icon, color, stt_label = "🚨", "#ef4444", "GẶP CAPTCHA"
        elif stt in ["running", "starting"]:
            icon, color, stt_label = "🔍", "#0284c7", "Đang quét"
        elif stt == "dwelling":
            icon, color, stt_label = "📖", "#059669", "Đang đọc bài"
        elif stt == "resting":
            icon, color, stt_label = "⏸️", "#d97706", "Nghỉ an toàn"
        elif stt == "done":
            icon, color, stt_label = "✅", "#16a34a", "Hoàn thành"
        else:
            icon, color, stt_label = "⚪", "#64748b", "Sẵn sàng"

        with bot_cols[idx]:
            st.markdown(f"""
            <div style="background: white; border: 1.5px solid {color}; border-radius: 8px; padding: 7px 9px; min-height: 105px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                        <strong style="font-size: 0.85rem; color: #0f172a;">{b_name}</strong>
                        <span style="font-size: 0.68rem; background: {color}18; color: {color}; padding: 1px 5px; border-radius: 4px; font-weight: 600;">{icon} {stt_label}</span>
                    </div>
                    <div style="font-size: 0.73rem; color: #334155; line-height: 1.25; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
                        {detail}
                    </div>
                </div>
                <div style="border-top: 1px solid #f1f5f9; padding-top: 3px; font-size: 0.7rem; color: #64748b; display: flex; justify-content: space-between;">
                    <span>Đã tra: <strong>{processed}</strong></span>
                    <span style="color: #059669; font-weight: 600;">HWOOD: {found}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # 4. Màn Hình Live Console Stream
    st.markdown("##### 💻 Màn hình theo dõi thực tế (Live Console Stream):")
    recent_logs = doc_live_logs(35)
    log_content = "\n".join(recent_logs) if recent_logs else "Chưa có hoạt động nào..."
    st.markdown(f"""
    <div style="background: #1e293b; color: #e2e8f0; font-family: monospace; font-size: 0.75rem; padding: 10px 14px; border-radius: 8px; height: 180px; overflow-y: auto; white-space: pre-wrap; line-height: 1.4; border: 1px solid #334155;">
{log_content}
    </div>
    """, unsafe_allow_html=True)

    # 5. Thống Kê & Bảng Kết Quả Tức Thời
    st.markdown("##### 📋 Kết quả ghi nhận tức thời:")
    if results:
        top_ai_img = 0
        top1_3 = 0
        top4_10 = 0
        ngoai_top = 0
        loi_count = 0

        for r in results:
            hits = r.get("ket_qua_hwood", [])
            stt = r.get("trang_thai", "")
            if stt == "loi":
                loi_count += 1
            elif hits:
                if any(h.get("source_type") in ["ai_overview", "image_pack"] for h in hits):
                    top_ai_img += 1
                best_pos = min([h.get("position", 999) for h in hits])
                if best_pos <= 3:
                    top1_3 += 1
                elif best_pos <= 10:
                    top4_10 += 1
                else:
                    ngoai_top += 1
            else:
                ngoai_top += 1

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("🏆 Top AI / Ảnh", top_ai_img, help="Số từ khóa HWOOD lọt vào AI Overview hoặc Cụm hình ảnh Google")
        m2.metric("🥇 Top 1 - 3", top1_3)
        m3.metric("🥈 Top 4 - 10", top4_10)
        m4.metric("⚪ Ngoài Top 50", ngoai_top)
        m5.metric("❌ Lỗi kết nối", loi_count)

        rows = []
        for r in reversed(results[-50:]):
            hits = r.get("ket_qua_hwood", [])
            stt = r.get("trang_thai", "")
            
            if stt == "loi":
                err_msg = r.get("loi", "Lỗi kết nối")
                if "ERR_CONNECTION_RESET" in err_msg or "ERR_PROXY" in err_msg:
                    rank_str = "❌ Lỗi Proxy (Port đóng/Reset)"
                elif "Timeout" in err_msg:
                    rank_str = "⏱️ Hết thời gian chờ (Timeout mạng)"
                else:
                    rank_str = f"❌ Lỗi: {err_msg[:30]}"
                urls = "-"
                status_badge = "❌ Lỗi Proxy / Mạng"
            elif stt == "bi_chan_captcha":
                rank_str = "🚨 Chờ giải Captcha trên màn hình"
                urls = "-"
                status_badge = "🚨 Gặp Captcha"
            elif hits:
                hit_labels = []
                for h in hits[:2]:
                    lbl = h.get("source_label") or f"Top {h['position']}"
                    hit_labels.append(f"{lbl} (trang {h.get('trang_google', 1)})")
                rank_str = ", ".join(hit_labels)
                urls = "; ".join([h["url"].replace("https://", "").replace("http://", "")[:50] for h in hits[:2]])

                if any(h.get("source_type") == "ai_overview" for h in hits):
                    status_badge = "🏆 AI Overview"
                elif any(h.get("source_type") == "image_pack" for h in hits):
                    status_badge = "🖼️ Cụm Hình Ảnh"
                elif any(h.get("source_type") == "featured_snippet" for h in hits):
                    status_badge = "💎 Top 0 Featured"
                else:
                    status_badge = "✅ Thấy HWOOD"
            else:
                rank_str = "⚪ Ngoài Top 50"
                urls = "-"
                status_badge = "⚪ Ngoài Top 50"

            rows.append({
                "Từ khóa": r.get("tu_khoa", ""),
                "Bot": r.get("bot_name", ""),
                "Thứ hạng & Nguồn": rank_str,
                "URL": urls,
                "Trạng thái": status_badge,
                "Thời gian": r.get("thoi_gian", ""),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("Chưa có kết quả nào. Kết quả sẽ tự động nhảy vào bảng này ngay khi bot tra xong.")


def render_realtime_col_run():
    """Bảng điều khiển trực tiếp thời gian thực, không dùng @st.fragment để tránh xung đột DOM với st.tabs."""
    try:
        is_running = dang_chay()
        _render_dashboard_content(is_running=is_running)

        # Nếu bot đang chạy: Tự động bấm cập nhật nhẹ nhàng qua client-side JavaScript sau mỗi 4 giây (không chặn Python thread)
        if is_running:
            import streamlit.components.v1 as components
            components.html("""
            <script>
            setTimeout(function() {
                const btn = window.parent.document.querySelector('button[key="btn_refresh_realtime"]') 
                         || Array.from(window.parent.document.querySelectorAll('button')).find(el => el.innerText && el.innerText.includes('Cập nhật tiến độ'));
                if (btn) {
                    btn.click();
                }
            }, 3800);
            </script>
            """, height=0)
    except Exception as e_dash:
        st.error(f"⚠️ Lỗi hiển thị bảng điều khiển: {e_dash}")

# ==============================================================================
# HÀM RENDER TAB (gọi từ app.py)
# ==============================================================================
def render_tab8():
    st.markdown("### 🤖 Hệ Thống 5 Bot Quét Thứ Hạng Google (Proxy/VPN Riêng)")
    st.caption(
        "5 bot chạy độc lập, mỗi bot 1 IP riêng, chia sẻ chung danh sách từ khóa "
        "(lấy ngẫu nhiên đến khi hết). Quét trang 1→5, ghi nhận thứ hạng bài/sản phẩm "
        "hwood.vn, nếu thấy thì vào trang đọc nội dung và ở lại tự nhiên như người thật."
    )

    if sys.platform.startswith("linux"):
        st.info("💡 **Gợi ý từ chuyên gia:** Bạn đang xem ứng dụng trên **Streamlit Cloud (Máy chủ quốc tế)**. 5 Bot cày thứ hạng & đẩy traffic hoạt động tốt nhất trên **máy tính văn phòng/nhà (IP Việt Nam dân cư)** bằng file `CHAY_APP.bat` để không bao giờ bị Google chặn Captcha. Kết quả quét từ máy tính sẽ được đồng bộ lên đây để bạn xem trên điện thoại bất cứ lúc nào!")

    # ---------- CỘT TRÁI: CẤU HÌNH | CỘT PHẢI: TIẾN ĐỘ + KẾT QUẢ ----------
    col_cfg, col_run = st.columns([1, 1.4])

    with col_cfg:
        st.markdown("#### 1️⃣ Danh sách từ khóa (5 bot dùng chung)")

        def on_preset_change():
            chosen = st.session_state.get("sel_bot_preset")
            if chosen and chosen != "Nhập tay" and chosen in BO_TU_KHOA_HWOOD_PRESETS:
                st.session_state["bot_farm_keywords_input"] = "\n".join(BO_TU_KHOA_HWOOD_PRESETS[chosen])

        if "bot_farm_keywords_input" not in st.session_state:
            st.session_state["bot_farm_keywords_input"] = "gỗ nhựa ngoài trời\ntấm nhựa ốp tường\ntrần nano"

        if HAS_PRESETS:
            st.selectbox(
                "Chọn bộ từ khóa mẫu:",
                options=["Nhập tay"] + list(BO_TU_KHOA_HWOOD_PRESETS.keys()),
                key="sel_bot_preset",
                on_change=on_preset_change,
                help="Chọn bộ mẫu để tự động nạp vào ô bên dưới, rồi bạn có thể sửa thêm.",
            )

        keywords_text = st.text_area(
            "Mỗi dòng 1 từ khóa:",
            key="bot_farm_keywords_input",
            height=160,
            placeholder="gỗ nhựa ngoài trời\ntấm nhựa ốp tường\ntrần nano\n...",
        )

        st.markdown("#### 2️⃣ Cấu hình Proxy/VPN cho Bot")
        st.caption(
            "💡 **Hỗ trợ mọi định dạng:** Bạn có thể dán thẳng chuỗi `IP:PORT:USER:PASS` (VD: `160.187.120.113:19883:cLNHhR:tJbThm`) "
            "vào ô Server, hệ thống sẽ tự động tách IP, Cổng, User và Password chuẩn xác 100%!\n\n"
            "- Để trống thì Bot đó sẽ dùng IP trực tiếp của máy tính.\n"
            "- Nếu chỉ có 1 Proxy, bạn có thể chỉnh số lượng Bot = 1 hoặc cho các bot dùng chung."
        )

        col_n_bot, col_share = st.columns([1, 1])
        with col_n_bot:
            so_bot = st.number_input("Số lượng Bot muốn chạy song song (1 - 5):", min_value=1, max_value=5, value=5)
        with col_share:
            dung_chung_p1 = st.checkbox("Áp dụng Proxy của Bot 1 cho tất cả các bot", value=False, help="Tiện lợi khi bạn chỉ có 1 proxy và muốn các bot khác cùng dùng chung proxy đó.")

        st.caption("💡 **Mẹo chống Captcha:** Nếu không có Proxy riêng (dùng IP trực tiếp của máy tính), bạn nên chỉnh **Số lượng Bot = 1 hoặc 2** để Google không nghi ngờ và tránh bị chặn Captcha liên tục.")

        # Tự động nạp danh sách proxy đã lưu từ bot_proxies.json (nếu có)
        saved_proxies_file = os.path.join(BASE_DIR, "bot_proxies.json")
        saved_bots = []
        if os.path.exists(saved_proxies_file):
            try:
                with open(saved_proxies_file, "r", encoding="utf-8") as f:
                    saved_bots = json.load(f).get("bots", [])
            except Exception:
                saved_bots = []

        proxies = []
        for i in range(int(so_bot)):
            def_srv = saved_bots[i].get("proxy_server", "") if i < len(saved_bots) else ""
            def_usr = saved_bots[i].get("proxy_username", "") if i < len(saved_bots) else ""
            def_pwd = saved_bots[i].get("proxy_password", "") if i < len(saved_bots) else ""

            with st.expander(f"🤖 Bot {i+1} — Cấu hình IP", expanded=(i == 0)):
                c1, c2 = st.columns(2)
                with c1:
                    name = st.text_input(f"Tên bot {i+1}:", value=f"Bot {i+1}", key=f"botname_{i}")
                    server_val = def_srv
                    if i > 0 and dung_chung_p1 and "proxy_0" in st.session_state:
                        server_val = st.session_state.get("proxy_0", def_srv)
                    server = st.text_input(
                        f"Proxy server {i+1}:",
                        value=server_val,
                        placeholder="160.187.120.113:19883:cLNHhR:tJbThm hoặc http://ip:port",
                        key=f"proxy_{i}",
                        help="Dán thẳng IP:PORT:USER:PASS hoặc để trống = dùng IP máy tính."
                    )
                with c2:
                    user_val = def_usr
                    pwd_val = def_pwd
                    if i > 0 and dung_chung_p1:
                        user_val = st.session_state.get("puser_0", def_usr)
                        pwd_val = st.session_state.get("ppass_0", def_pwd)
                    user = st.text_input(f"Username proxy {i+1}:", value=user_val, key=f"puser_{i}")
                    pwd = st.text_input(f"Password proxy {i+1}:", value=pwd_val, type="password", key=f"ppass_{i}")

                # Tự động tách nếu dán IP:PORT:USER:PASS vào server
                final_server = server.strip()
                final_user = user.strip()
                final_pwd = pwd.strip()
                if final_server and ":" in final_server and not final_server.startswith("http"):
                    parts = final_server.split(":")
                    if len(parts) == 4:
                        final_server = f"http://{parts[0]}:{parts[1]}"
                        if not final_user:
                            final_user = parts[2]
                        if not final_pwd:
                            final_pwd = parts[3]

                proxies.append({
                    "bot_id": f"bot_{i+1:02d}",
                    "name": name,
                    "proxy_server": final_server,
                    "proxy_username": final_user,
                    "proxy_password": final_pwd,
                })

        if st.button("🔍 Kiểm tra kết nối IP / Proxy của các Bot", use_container_width=True, help="Kiểm tra xem từng Proxy có kết nối được không và đo tốc độ Ping"):
            with st.spinner("Đang kiểm tra kết nối từng IP/Proxy..."):
                from modules.bot_farm import BotConfig
                for p_item in proxies:
                    cfg_test = BotConfig(
                        bot_id=p_item["bot_id"],
                        name=p_item["name"],
                        proxy_server=p_item["proxy_server"],
                        proxy_username=p_item["proxy_username"],
                        proxy_password=p_item["proxy_password"],
                    )
                    res = kiem_tra_proxy_mot_bot(cfg_test)
                    if res["status"] == "ok":
                        st.success(f"✅ **{p_item['name']}:** {res['msg']}")
                    elif res["status"] == "direct":
                        st.info(f"⚪ **{p_item['name']}:** {res['msg']}")
                    else:
                        st.error(f"❌ **{p_item['name']}:** {res['msg']}")

        st.markdown("#### 3️⃣ Cài đặt hoạt động")
        fast_mode = st.checkbox(
            "⚡ Chế độ kiểm tra nhanh (Có kết quả ngay trong 5-8s, không chờ đọc trang)",
            value=False,
            help="Bật tùy chọn này khi anh muốn kiểm tra thứ hạng nhanh 1 hoặc vài từ khóa mà không cần ở lại trang web 45-90s.",
        )
        if fast_mode:
            st.info("💡 **Chế độ kiểm tra nhanh đang BẬT:** Bot quét lấy thứ hạng ngay (5-8s/từ), không giữ dwell time lâu.")
            def_dwell_min, def_dwell_max = 2, 4
            def_delay_min, def_delay_max = 2, 4
            def_visit = False
            def_pages = 3
        else:
            def_dwell_min, def_dwell_max = 60, 90
            def_delay_min, def_delay_max = 8, 15
            def_visit = True
            def_pages = 5

        c1, c2 = st.columns(2)
        with c1:
            max_pages = st.slider("Quét tới trang Google:", 1, 5, def_pages)
            delay_min = st.number_input("Nghỉ tối thiểu giữa các từ (giây):", min_value=1, max_value=60, value=def_delay_min, help="Dừng ngẫu nhiên giữa các từ để Google không nghi ngờ")
            delay_max = st.number_input("Nghỉ tối đa giữa các từ (giây):", min_value=2, max_value=120, value=def_delay_max, help="Dừng ngẫu nhiên giữa các từ để Google không nghi ngờ")
        with c2:
            dwell_min = st.number_input("Thời gian đọc trang tối thiểu (giây):", 1, 300, def_dwell_min)
            dwell_max = st.number_input("Thời gian đọc trang tối đa (giây):", 2, 600, def_dwell_max)
            visit_pages = st.checkbox("Vào trang hwood.vn đọc nội dung khi thấy", value=def_visit)
            click_zalo = st.checkbox("💬 Bấm nút/icon Zalo OA sau khi đọc bài (Tăng traffic Zalo)", value=False, help="Sau khi đọc bài xong đủ thời gian dwell time, bot sẽ tìm nút Zalo trong bài viết hoặc icon Zalo nổi ở góc phải để bấm vào, giúp tăng chuyển đổi và traffic Zalo OA.")
            headless = st.checkbox("Chạy ẩn (Bỏ chọn để hiện cửa sổ trình duyệt trên màn hình)", value=False)

        settings = {
            "max_pages": int(max_pages),
            "delay_min": int(delay_min),
            "delay_max": int(delay_max),
            "dwell_min": int(dwell_min),
            "dwell_max": int(dwell_max),
            "visit_pages": bool(visit_pages),
            "click_zalo": bool(click_zalo),
            "headless": bool(headless),
        }

        st.markdown("---")
        if not dang_chay():
            col_b1, col_b2 = st.columns([2.2, 1])
            with col_b1:
                btn_txt = "⚡ Bắt đầu quét nhanh (5-8s)" if fast_mode else "🚀 Bắt đầu chạy 5 Bot"
                run_clicked = st.button(btn_txt, type="primary", use_container_width=True)
            with col_b2:
                if st.button("🔄 Làm mới (F5)", key="btn_f5_col_cfg", use_container_width=True, help="Làm mới lại trang (F5)"):
                    st.rerun()

            if run_clicked:
                if not keywords_text.strip():
                    st.error("❌ Chưa có từ khóa! Hãy nhập ít nhất 1 từ khóa.")
                else:
                    ghi_cau_hinh(keywords_text, proxies, settings)
                    runner = os.path.join(BASE_DIR, "run_bot_farm.py")
                    try:
                        log_sys_path = os.path.join(BASE_DIR, "bot_farm_sys.log")
                        log_sys = open(log_sys_path, "w", encoding="utf-8")
                        env = os.environ.copy()
                        env["PYTHONIOENCODING"] = "utf-8"
                        env["PYTHONUTF8"] = "1"
                        proc = subprocess.Popen(
                            [sys.executable or "python", runner],
                            cwd=BASE_DIR,
                            stdout=log_sys,
                            stderr=subprocess.STDOUT,
                            env=env,
                        )
                        RUNNING_PROC["popen"] = proc
                        RUNNING_PROC["started_at"] = datetime.now().strftime("%H:%M:%S")
                        st.toast(f"✅ Đã khởi động 5 bot lúc {RUNNING_PROC['started_at']}!", icon="🚀")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Lỗi khởi động: {e}")
        else:
            st.warning(f"⏳ 5 bot đang quét realtime (bắt đầu lúc {RUNNING_PROC.get('started_at', 'vừa xong')})...")
            if st.button("⏹️ Dừng tất cả bot", use_container_width=True):
                dung_bot()
                st.success("Đã gửi lệnh dừng.")
                st.rerun()

    with col_run:
        render_realtime_col_run()

        # Nút xuất CSV
        results = doc_ket_qua()
        if results:
            csv_buf = io.StringIO()
            writer = csv.writer(csv_buf)
            writer.writerow(["tu_khoa", "bot", "thoi_gian", "trang_thai", "vi_tri", "url", "tieu_de"])
            for r in results:
                hits = r.get("ket_qua_hwood", [])
                if hits:
                    for h in hits:
                        writer.writerow([
                            r.get("tu_khoa", ""), r.get("bot_name", ""), r.get("thoi_gian", ""),
                            "found", h.get("position", ""), h.get("url", ""), h.get("title", ""),
                        ])
                else:
                    writer.writerow([
                        r.get("tu_khoa", ""), r.get("bot_name", ""), r.get("thoi_gian", ""),
                        r.get("trang_thai", "not_found"), "", "", "",
                    ])
            st.download_button(
                "⬇️ Tải kết quả CSV",
                data=csv_buf.getvalue().encode("utf-8-sig"),
                file_name=f"ket_qua_5bot_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    st.markdown("---")
    st.caption(
        "⚠️ Lưu ý: Công cụ này dùng để KIỂM TRA THỨ HẠNG và XÁC MINH NỘI DUNG. "
        "Việc click + ở lại trang ở quy mô lớn có thể bị Google xem là thao túng CTR "
        "và gây rủi ro cho website. Nên dùng proxy residential (IP nhà dân) và chạy vừa phải."
    )


# ==============================================================================
# HƯỚNG DẪN THÊM TAB NÀY VÀO app.py (CHỈ THÊM, KHÔNG SỬA FILE CŨ)
# ==============================================================================
# Trong file app.py của bạn, thêm 3 dòng sau:
#
#   1. Ở phần import tab (gần các dòng 'from tabs.tab7_... import ...'), thêm:
#        from tabs.tab8_bot_farm import render_tab8
#
#   2. Trong hàm st.tabs([...]), thêm tên tab mới vào CUỐI DANH SÁCH:
#        "🤖 5 Bot Quét Thứ Hạng"
#
#   3. Thêm khối with tab_moi: render_tab8()
#
# Xem file README_5_BOT.md để biết chi tiết + cài đặt Playwright + proxy.
