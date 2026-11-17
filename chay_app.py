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
    print("   Luu y: Giu nguyen cua so nay trong khi su dung.")
    print("=======================================================\n")

    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.headless", "false",
        "--server.showEmailPrompt", "false",
        "--browser.gatherUsageStats", "false"
    ]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nDa dung ung dung HWOOD SEO.")

if __name__ == "__main__":
    main()
