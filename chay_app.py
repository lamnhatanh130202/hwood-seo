import os
import sys
import subprocess

def ensure_streamlit_credentials():
    """Dam bao khong bi hoi email khi chay Streamlit lan dau tren may moi"""
    try:
        home_dir = os.path.expanduser("~")
        streamlit_dir = os.path.join(home_dir, ".streamlit")
        cred_file = os.path.join(streamlit_dir, "credentials.toml")
        os.makedirs(streamlit_dir, exist_ok=True)
        with open(cred_file, "w", encoding="utf-8") as f:
            f.write('[general]\nemail = ""\n')
    except Exception:
        pass

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    ensure_streamlit_credentials()

    os.environ["STREAMLIT_SERVER_SHOW_EMAIL_PROMPT"] = "false"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    # Kiem tra thu vien can thiet
    missing = []
    for pkg in ["streamlit", "playwright", "bs4", "openai", "docx"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"[HWOOD SEO] Phat hien thieu thu vien: {', '.join(missing)}")
        print("[HWOOD SEO] Dang tu dong cai dat thu vien, vui long doi 1 - 2 phut...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=False)
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("[HWOOD SEO] Dang cai dat Chromium cho 5 Bot Playwright...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)

    print("\n=======================================================")
    print("   HWOOD SEO ASSISTANT DANG KHOI DONG TAI: http://localhost:8501")
    print("   Che do: Cua so Ung dung Doc lap (Native App Mode)")
    print("=======================================================\n")

    # Kiem tra trinh duyet Chrome/Edge de mo che do App Window
    browser = None
    for p in [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]:
        if os.path.exists(p):
            browser = p
            break

    profile_dir = os.path.join(script_dir, ".app_profile")
    os.makedirs(profile_dir, exist_ok=True)

    server_cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.headless", "true",
        "--server.showEmailPrompt", "false",
        "--browser.gatherUsageStats", "false"
    ]

    try:
        server_proc = subprocess.Popen(server_cmd)
        
        # Cho server san sang
        import time, socket
        for _ in range(40):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(('127.0.0.1', 8501)) == 0:
                    break
            time.sleep(0.3)

        if browser:
            app_args = [
                browser,
                "--app=http://localhost:8501",
                f"--user-data-dir={profile_dir}",
                "--window-size=1450,920",
                "--window-position=40,20",
                "--app-id=hwood-seo-assistant"
            ]
            browser_proc = subprocess.Popen(app_args)
            browser_proc.wait()
        else:
            import webbrowser
            webbrowser.open("http://localhost:8501")
            server_proc.wait()

    except KeyboardInterrupt:
        print("\nDa dung ung dung HWOOD SEO.")
    finally:
        try:
            server_proc.terminate()
            server_proc.wait(timeout=2)
        except Exception:
            try:
                server_proc.kill()
            except Exception:
                pass

if __name__ == "__main__":
    main()
