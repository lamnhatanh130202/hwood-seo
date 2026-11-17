# -*- coding: utf-8 -*-
"""
MODULE TỰ ĐỘNG ĐỒNG BỘ CODE LÊN GITHUB KHÔNG CẦN CÀI GIT
Sử dụng GitHub REST API v3 chính thức để đẩy file trực tiếp vào kho lamnhatanh130202/hwood-seo
"""

import os
import sys
import base64
import json
import hashlib
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(BASE_DIR, "github_token.txt")
REPO_NAME = "lamnhatanh130202/hwood-seo"
BRANCH = "main"

EXCLUDE_DIRS = {'.git', '__pycache__', '.user_uploaded', 'chrome_user_data', '.system_generated', 'hwood_chrome_extension'}
EXCLUDE_EXTS = {'.pyc', '.mp4', '.zip', '.log', '.tmp'}


def doc_github_token():
    """Đọc GitHub Personal Access Token từ file github_token.txt hoặc biến môi trường"""
    token = os.environ.get("GITHUB_TOKEN")
    if not token and os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                token = f.read().strip()
        except Exception:
            token = ""
    return token


def luu_github_token(token):
    """Lưu GitHub Token vào file để dùng lâu dài"""
    try:
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(token.strip())
        return True
    except Exception:
        return False


def lay_danh_sach_file_hien_tai_github(token, repo=REPO_NAME, branch=BRANCH):
    """Lấy danh sách các file và mã băm SHA hiện có trên GitHub để tránh upload trùng"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            tree = r.json().get("tree", [])
            return {item["path"]: item["sha"] for item in tree if item.get("type") == "blob"}
    except Exception:
        pass
    return {}


def day_mot_file_len_github(token, relative_path, local_full_path, repo=REPO_NAME, branch=BRANCH, existing_sha=None):
    """Upload một file cụ thể lên GitHub repo bằng REST API"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        with open(local_full_path, "rb") as f:
            content_bytes = f.read()
    except Exception as e:
        return False, f"Không đọc được file: {e}"

    # Kiểm tra xem nội dung file có thay đổi so với GitHub không
    git_blob_header = f"blob {len(content_bytes)}\0".encode("utf-8")
    local_sha = hashlib.sha1(git_blob_header + content_bytes).hexdigest()
    if existing_sha and local_sha == existing_sha:
        return True, "Không đổi"

    b64_content = base64.b64encode(content_bytes).decode("utf-8")
    api_url = f"https://api.github.com/repos/{repo}/contents/{relative_path}"
    
    # Chuẩn bị payload commit
    payload = {
        "message": f"Update {relative_path} from HWOOD Local PC",
        "content": b64_content,
        "branch": branch
    }
    if existing_sha:
        payload["sha"] = existing_sha

    try:
        r = requests.put(api_url, headers=headers, json=payload, timeout=20)
        if r.status_code in [200, 201]:
            return True, "Thành công"
        else:
            err = r.json().get("message", r.text)
            return False, f"Mã lỗi {r.status_code}: {err}"
    except Exception as ex:
        return False, f"Lỗi kết nối: {ex}"


def dong_bo_toan_bo_du_an(token=None, repo=REPO_NAME, branch=BRANCH):
    """Quét toàn bộ thư mục và đẩy các file mới/đã sửa lên GitHub"""
    if not token:
        token = doc_github_token()
        
    if not token:
        return False, "Chưa cấu hình mã GitHub Token! Vui lòng lưu token vào file github_token.txt."

    print(f"[*] Đang kết nối tới repository: {repo} (Nhánh {branch})...")
    remote_files = lay_danh_sach_file_hien_tai_github(token, repo, branch)
    
    files_to_sync = []
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXCLUDE_EXTS or file in ["github_token.txt", "google_credentials.json", "hwood_seo_cloud_package.zip"]:
                continue
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, BASE_DIR).replace("\\", "/")
            files_to_sync.append((rel_path, full_path))

    total = len(files_to_sync)
    print(f"[*] Tìm thấy {total} file trong dự án. Đang đồng bộ lên GitHub...")
    
    success_count = 0
    fail_count = 0
    
    for rel_path, full_path in files_to_sync:
        existing_sha = remote_files.get(rel_path)
        ok, msg = day_mot_file_len_github(token, rel_path, full_path, repo, branch, existing_sha)
        if ok:
            success_count += 1
            print(f"  [+] Đã đồng bộ: {rel_path}")
        else:
            fail_count += 1
            print(f"  [-] Lỗi file {rel_path}: {msg}")

    return True, f"Hoàn tất đồng bộ: Thành công {success_count}/{total} files."


if __name__ == "__main__":
    t = doc_github_token()
    if len(sys.argv) > 1:
        t = sys.argv[1].strip()
        luu_github_token(t)
        
    if not t:
        print("[!] Vui lòng truyền mã token hoặc dán vào file github_token.txt!")
        sys.exit(1)
        
    ok, msg = dong_bo_toan_bo_du_an(t)
    print(msg)
