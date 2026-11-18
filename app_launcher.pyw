# -*- coding: utf-8 -*-
"""
HWOOD SEO ASSISTANT - NATIVE DESKTOP APP LAUNCHER
Khởi động hệ thống Streamlit hoàn toàn ngầm (không hiện cửa sổ đen CMD).
Tự động mở cửa sổ ứng dụng độc lập (Chrome/Edge App Mode) như phần mềm cài đặt chuyên nghiệp.
Tự động dọn dẹp tiến trình nền khi đóng cửa sổ để tiết kiệm tài nguyên máy.
"""
import os
import sys
import time
import socket
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8501
URL = f"http://localhost:{PORT}"
PROFILE_DIR = os.path.join(BASE_DIR, ".app_profile")


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0


def find_browser():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def ensure_streamlit_config():
    """Đảm bảo cấu hình không bao giờ hiện prompt hỏi email hoặc thu thập dữ liệu"""
    try:
        home_dir = os.path.expanduser("~")
        streamlit_dir = os.path.join(home_dir, ".streamlit")
        cred_file = os.path.join(streamlit_dir, "credentials.toml")
        os.makedirs(streamlit_dir, exist_ok=True)
        with open(cred_file, "w", encoding="utf-8") as f:
            f.write('[general]\nemail = ""\n')
    except Exception:
        pass


def start_streamlit_server():
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable

    ensure_streamlit_config()

    env = os.environ.copy()
    env["STREAMLIT_SERVER_SHOW_EMAIL_PROMPT"] = "false"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["STREAMLIT_SERVER_HEADLESS"] = "true"

    cmd = [
        pythonw, "-m", "streamlit", "run", "app.py",
        "--server.port", str(PORT),
        "--server.headless", "true",
        "--server.showEmailPrompt", "false",
        "--browser.gatherUsageStats", "false"
    ]

    creationflags = 0
    if os.name == 'nt':
        creationflags = 0x08000000  # CREATE_NO_WINDOW (không hiện cửa sổ cmd)

    proc = subprocess.Popen(
        cmd,
        cwd=BASE_DIR,
        env=env,
        creationflags=creationflags,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return proc


def wait_for_server(timeout=25):
    start = time.time()
    while time.time() - start < timeout:
        if is_port_in_use(PORT):
            return True
        time.sleep(0.4)
    return False


def main():
    os.chdir(BASE_DIR)
    
    server_proc = None
    if not is_port_in_use(PORT):
        server_proc = start_streamlit_server()
        ready = wait_for_server(25)
        if not ready:
            sys.exit(1)

    browser = find_browser()
    if browser:
        os.makedirs(PROFILE_DIR, exist_ok=True)
        app_args = [
            browser,
            f"--app={URL}",
            f"--user-data-dir={PROFILE_DIR}",
            "--window-size=1450,920",
            "--window-position=40,20",
            "--app-id=hwood-seo-assistant"
        ]
        p_browser = subprocess.Popen(app_args)
        p_browser.wait()
    else:
        import webbrowser
        webbrowser.open(URL)
        return

    # Khi người dùng tắt cửa sổ app, tự động dừng server ngầm nếu do launcher này bật
    if server_proc:
        try:
            server_proc.terminate()
            server_proc.wait(timeout=3)
        except Exception:
            try:
                server_proc.kill()
            except Exception:
                pass


if __name__ == "__main__":
    main()
