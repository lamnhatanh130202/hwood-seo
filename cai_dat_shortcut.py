# -*- coding: utf-8 -*-
"""
HWOOD SEO ASSISTANT - TẠO PHÍM TẮT DESKTOP & START MENU
Tự động tạo shortcut dạng Ứng dụng Desktop (.lnk) kèm Icon thương hiệu HWOOD.
"""
import os
import sys
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "hwood_app_icon.ico")
LAUNCHER_PATH = os.path.join(BASE_DIR, "app_launcher.pyw")
PYTHON_DIR = os.path.dirname(sys.executable)
PYTHONW_PATH = os.path.join(PYTHON_DIR, "pythonw.exe")

if not os.path.exists(PYTHONW_PATH):
    PYTHONW_PATH = sys.executable


def tao_shortcut(target_lnk_path, name="HWOOD SEO AI"):
    """Tạo file shortcut Windows (.lnk) bằng PowerShell WScript.Shell"""
    ps_script = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{target_lnk_path}')
$Shortcut.TargetPath = '{PYTHONW_PATH}'
$Shortcut.Arguments = '"{LAUNCHER_PATH}"'
$Shortcut.WorkingDirectory = '{BASE_DIR}'
$Shortcut.IconLocation = '{ICON_PATH}, 0'
$Shortcut.Description = 'HWOOD VIET NAM - Tro Ly Content SEO & Ky Thuat AI'
$Shortcut.WindowStyle = 7
$Shortcut.Save()
"""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except Exception as e:
        print(f"Lỗi tạo shortcut {target_lnk_path}: {e}")
        return False


def main():
    print("=" * 60)
    print("   HWOOD VIET NAM - SETUP UNG DUNG DESKTOP")
    print("=" * 60)

    # 1. Tạo shortcut ngay trong thư mục dự án
    project_lnk = os.path.join(BASE_DIR, "HWOOD SEO AI.lnk")
    if tao_shortcut(project_lnk):
        print(f"[+] Da tao shortcut trong thu muc: {project_lnk}")

    # 2. Tạo shortcut tren Desktop
    user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
    desktop_dir = os.path.join(user_profile, "Desktop")
    if os.path.exists(desktop_dir):
        desktop_lnk = os.path.join(desktop_dir, "HWOOD SEO AI.lnk")
        if tao_shortcut(desktop_lnk):
            print(f"[+] Da tao icon tren Man hinh chinh (Desktop): {desktop_lnk}")

    # 3. Tạo shortcut trong Start Menu Programs
    appdata = os.environ.get("APPDATA")
    if appdata:
        start_menu = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs")
        if os.path.exists(start_menu):
            start_lnk = os.path.join(start_menu, "HWOOD SEO AI.lnk")
            if tao_shortcut(start_lnk):
                print(f"[+] Da tao icon trong Start Menu: {start_lnk}")

    print("\n>>> HOAN TAT! Ban co the nhap dup chuot vao icon 'HWOOD SEO AI' tren Desktop de chay app nhu mot phan mem doc lap.")


if __name__ == "__main__":
    main()
