# -*- coding: utf-8 -*-
"""
Cầu nối Antigravity (Chế độ không cần API Key trả phí).
Tổng hợp Prompt chuẩn HWOOD, lưu vào ai_requests/latest_prompt.md,
và cung cấp giao diện 1-click Copy / Paste kết quả đồng nhất cho các Tab.
"""
import os
import json
from datetime import datetime
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_REQUESTS_DIR = os.path.join(BASE_DIR, "ai_requests")
LATEST_PROMPT_FILE = os.path.join(AI_REQUESTS_DIR, "latest_prompt.md")
LATEST_TASK_FILE = os.path.join(AI_REQUESTS_DIR, "latest_task.json")


def is_antigravity_mode(api_key: str = "") -> bool:
    """Trả về True nếu người dùng chọn chế độ Antigravity hoặc chưa có API Key."""
    if st.session_state.get("use_antigravity", False):
        return True
    return not bool((api_key or "").strip())


def save_antigravity_prompt(task_type: str, title: str, prompt_text: str, metadata: dict = None) -> str:
    """Lưu prompt mới nhất ra file để có thể gửi hoặc gọi Antigravity xử lý trực tiếp."""
    os.makedirs(AI_REQUESTS_DIR, exist_ok=True)
    header = (
        f"# YÊU CẦU TỪ HWOOD SEO APP ({task_type.upper()})\n"
        f"- **Tiêu đề:** {title}\n"
        f"- **Thời gian:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"---\n\n"
    )
    with open(LATEST_PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write(header + prompt_text)

    task_info = {
        "task_type": task_type,
        "title": title,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {},
    }
    with open(LATEST_TASK_FILE, "w", encoding="utf-8") as f:
        json.dump(task_info, f, ensure_ascii=False, indent=2)

    return LATEST_PROMPT_FILE


def render_antigravity_panel(
    task_key: str,
    title: str,
    prompt_text: str,
    paste_label: str = "📥 Dán kết quả từ Antigravity vào đây:",
    apply_label: str = "✅ Nạp kết quả vào App",
    placeholder: str = "Dán nội dung HTML / Markdown / JSON mà Antigravity vừa trả về...",
):
    """
    Hiển thị hộp Prompt chuẩn cho Antigravity + ô dán kết quả trả về.
    Trả về chuỗi người dùng dán nếu bấm nút Nạp, ngược lại trả về None.
    """
    st.info(
        f"🚀 **Chế độ Antigravity (Miễn phí - Không cần API Key):** {title}\n\n"
        "• **Cách 1:** Bấm nút **Copy** ở góc trên bên phải khung Prompt dưới đây -> dán vào chat Antigravity.\n"
        "• **Cách 2:** Nhắn thẳng cho Antigravity: *\"Xử lý yêu cầu mới nhất trong ai_requests/latest_prompt.md\"*."
    )

    with st.expander("📋 Xem & Copy Prompt chuẩn HWOOD gửi Antigravity", expanded=True):
        st.code(prompt_text, language="markdown")

    pasted = st.text_area(
        paste_label,
        height=240,
        placeholder=placeholder,
        key=f"ag_paste_{task_key}",
    )
    if st.button(apply_label, type="primary", use_container_width=True, key=f"ag_apply_{task_key}"):
        if not pasted.strip():
            st.warning("⚠️ Bạn chưa dán kết quả từ Antigravity vào ô bên trên!")
            return None
        return pasted.strip()
    return None
