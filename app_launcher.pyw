# -*- coding: utf-8 -*-
"""
HWOOD SEO ASSISTANT - NATIVE DESKTOP APP LAUNCHER
Khởi động hệ thống Streamlit ngầm và mở cửa sổ ứng dụng độc lập (Chrome/Edge App Mode).
Nếu có lỗi phát sinh, tự động hiện hộp thoại thông báo trực quan cho người dùng.
"""
import os
import sys
import time
import socket
import subprocess
import traceback
import ctypes

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8501
URL = f"http://localhost:{PORT}"
LOG_FILE = os.path.join(BASE_DIR, "launcher.log")


def show_error(title, message):
    """Hiện thông báo lỗi trực quan trên Windows nếu gặp sự cố"""
    try:
        ctypes.windll.user32.MessageBoxW(0, str(message), str(title), 0x10)
    except Exception:
        pass


def log(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


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


def start_streamlit_server():
    python_dir = os.path.dirname(sys.executable)
    pythonw = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable

    log(f"Starting Streamlit using: {pythonw}")

    env = os.environ.copy()
    env["STREAMLIT_SERVER_PORT"] = str(PORT)
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_SERVER_SHOW_EMAIL_PROMPT"] = "false"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    cmd = [
        pythonw, "-m", "streamlit", "run", "app.py",
        "--server.port", str(PORT),
        "--server.headless", "true"
    ]

    # Cờ Detached trên Windows: DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    creationflags = 0x00000008 | 0x00000200 | 0x08000000

    server_log = os.path.join(BASE_DIR, "streamlit_server.log")
    f_log = open(server_log, "a", encoding="utf-8")

    proc = subprocess.Popen(
        cmd,
        cwd=BASE_DIR,
        env=env,
        creationflags=creationflags,
        stdout=f_log,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        close_fds=True
    )
    log(f"Spawned Streamlit server PID: {proc.pid}")
    return proc


def wait_for_server(timeout=25):
    start = time.time()
    while time.time() - start < timeout:
        if is_port_in_use(PORT):
            log(f"Port {PORT} is ready after {time.time() - start:.1f}s")
            return True
        time.sleep(0.3)
    log(f"Timeout waiting for port {PORT}")
    return False


def main():
    try:
        os.chdir(BASE_DIR)
        log("=== LAUNCHER CLICKED ===")

        # 1. Khởi động server ngầm nếu chưa chạy
        if not is_port_in_use(PORT):
            start_streamlit_server()
            if not wait_for_server(25):
                show_error(
                    "Lỗi Khởi Động HWOOD SEO AI",
                    "Không thể kết nối đến máy chủ Streamlit sau 25 giây.\n"
                    "Vui lòng kiểm tra lại file log: streamlit_server.log hoặc chạy CHAY_APP.bat để xem chi tiết."
                )
                sys.exit(1)
        else:
            log(f"Port {PORT} already active.")

        # 2. Mở cửa sổ giao diện ứng dụng (Chrome / Edge App Mode)
        browser = find_browser()
        profile_dir = os.path.join(BASE_DIR, ".app_profile")
        os.makedirs(profile_dir, exist_ok=True)

        if browser:
            log(f"Opening browser App Mode: {browser}")
            app_args = [
                browser,
                f"--app={URL}",
                f"--user-data-dir={profile_dir}",
                "--window-size=1450,920",
                "--window-position=40,20",
                "--app-id=hwood-seo-assistant"
            ]
            # Không dùng cờ DETACHED_PROCESS cho trình duyệt để đảm bảo cửa sổ luôn nổi lên trên cùng (foreground)
            subprocess.Popen(app_args, close_fds=True)
            log("Browser launched.")
        else:
            log("Opening default browser...")
            import webbrowser
            webbrowser.open(URL)

        log("=== LAUNCHER SUCCESS ===")
    except Exception as e:
        err = traceback.format_exc()
        log(f"EXCEPTION: {err}")
        show_error("Lỗi Khởi Động", f"Đã xảy ra lỗi:\n{e}\n\nXem chi tiết tại launcher.log")


if __name__ == "__main__":
    main()
