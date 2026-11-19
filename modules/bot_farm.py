# -*- coding: utf-8 -*-
"""
HWOOD - HỆ THỐNG 5 BOT QUÉT THỨ HẠNG GOOGLE ĐỘC LẬP (PROXY/VPN RIÊNG)
=====================================================================
Mỗi bot chạy trên 1 luồng (thread) độc lập, dùng 1 địa chỉ proxy/VPN riêng,
trình duyệt thật (Chromium) có chống phát hiện. 5 bot chia sẻ chung 1 hàng đợi
từ khóa đã xáo trộn ngẫu nhiên, lấy từ khóa đến khi hết. Với mỗi từ khóa:
  1. Mở Google, gõ từ khóa như người thật (trễ ngẫu nhiên giữa các phím).
  2. Quét trang 1 -> trang 5 (tối đa 50 kết quả organic), tìm URL chứa hwood.vn,
     ghi nhận vị trí + tiêu đề.
  3. Nếu thấy bài/sản phẩm hwood.vn: click vào kết quả cao nhất, cuộn trang đọc
     nội dung, ở lại một khoảng thời gian ngẫu nhiên (mặc định 45-90s) rồi quay lại.
  4. Nếu không thấy đến trang 5: đánh dấu "Ngoài Top 50", bỏ qua, tiếp tục từ khóa sau.
  5. Ghi kết quả ra file JSON/CSV ngay lập tức (không mất dữ liệu khi dừng giữa chừng).

LƯU Ý QUAN TRỌNG (đọc trước khi chạy):
  - Hành vi click + ở lại trang (dwell time) ở quy mô bot có thể bị Google xem là
    thao túng CTR và gây rủi ro phạt website. Công cụ này được xây dựng CHÍNH để
    KIỂM TRA THỨ HẠNG và XÁC MINH NỘI DUNG trang. Hãy dùng ở mức độ vừa phải,
    ưu tiên proxy residential (IP nhà dân) để tránh bị chặn.
  - Cần cài: pip install playwright  ->  playwright install chromium
  - Tùy chọn chống phát hiện tốt hơn: pip install playwright-stealth
"""
import sys
import os
import re
import json
import time
import random
import queue
import requests
import threading
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Thư mục gốc dự án (chứa app.py) - file này nằm trong modules/
CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_FILE = os.path.join(CURRENT_DIR, "lich_su_bot_farm.json")
PROGRESS_FILE = os.path.join(CURRENT_DIR, "bot_farm_progress.json")
PROXY_CONFIG_FILE = os.path.join(CURRENT_DIR, "bot_proxies.json")
LIVE_LOG_FILE = os.path.join(CURRENT_DIR, "bot_farm_live.log")
LOG_LOCK = threading.Lock()
PROGRESS_LOCK = threading.Lock()
CAPTCHA_ACTIVE_EVENT = threading.Event()
CAPTCHA_ACTIVE_EVENT.set()

def append_live_log(log_line: str):
    """Ghi thêm 1 dòng nhật ký vào file live log để giao diện hiển thị realtime."""
    try:
        with LOG_LOCK:
            lines = []
            if os.path.exists(LIVE_LOG_FILE):
                try:
                    with open(LIVE_LOG_FILE, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                except Exception:
                    lines = []
            lines.append(log_line.rstrip() + "\n")
            if len(lines) > 80:
                lines = lines[-80:]
            with open(LIVE_LOG_FILE, "w", encoding="utf-8") as f:
                f.writelines(lines)
    except Exception:
        pass

def doc_live_logs(n: int = 40, max_lines: Optional[int] = None) -> List[str]:
    """Đọc n dòng log realtime gần nhất."""
    limit = max_lines if max_lines is not None else n
    if not os.path.exists(LIVE_LOG_FILE):
        return []
    try:
        with open(LIVE_LOG_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        return lines[-limit:]
    except Exception:
        return []

def xoa_live_logs():
    try:
        if os.path.exists(LIVE_LOG_FILE):
            os.remove(LIVE_LOG_FILE)
    except Exception:
        pass

# Miền mục tiêu cần tìm trong kết quả Google
TARGET_DOMAIN = "hwood.vn"

def is_strict_hwood_url(url: str) -> bool:
    """
    Kiểm tra nghiêm ngặt 100%: URL phải thực sự thuộc domain chính hãng hwood.vn.
    Loại trừ tuyệt đối tất cả đại lý (hoangangroup.com,...), sàn TMĐT, đối thủ (kosmos, haroma,...)
    và các URL nội bộ của Google.
    """
    if not url:
        return False
    try:
        from urllib.parse import urlparse, unquote
        u = unquote(str(url)).strip()
        # Nếu url là redirect của Google chứa domain hwood.vn
        if ("google." in u.lower() or u.startswith("/url")) and "hwood.vn" in u.lower():
            import re
            m = re.search(r"https?://(?:www\.)?hwood\.vn[^\s\"'&<>)]*", u, re.I)
            if m:
                return True
        if not u.startswith(("http://", "https://")):
            u = "https://" + u.lstrip("/")
        parsed = urlparse(u)
        host = (parsed.hostname or "").lower()
        return host == "hwood.vn" or host == "www.hwood.vn" or host.endswith(".hwood.vn")
    except Exception:
        clean = str(url).lower().replace("https://", "").replace("http://", "").replace("www.", "")
        return clean.startswith("hwood.vn/") or clean == "hwood.vn"

# Pool User-Agent thật (Chrome trên Windows) - mỗi bot chọn ngẫu nhiên 1 cái
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]

# Kích thước màn hình phổ biến (mỗi bot dùng 1 viewport riêng)
VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1280, "height": 720},
]

# Thử import playwright-stealth (chống phát hiện tốt hơn) - nếu không có thì bỏ qua
try:
    from playwright_stealth import stealth_sync
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False


# ==============================================================================
# 1. CẤU HÌNH MỖI BOT
# ==============================================================================
@dataclass
class BotConfig:
    bot_id: str
    name: str
    proxy_server: str = ""          # ví dụ: http://1.2.3.4:8080  hoặc socks5://...
    proxy_username: str = ""
    proxy_password: str = ""
    user_agent: str = field(default_factory=lambda: random.choice(USER_AGENTS))
    viewport: Dict = field(default_factory=lambda: random.choice(VIEWPORTS))

    def proxy_dict(self) -> Optional[Dict]:
        if not self.proxy_server:
            return None
        raw_server = self.proxy_server.strip()
        user = self.proxy_username.strip()
        pwd = self.proxy_password.strip()

        # Tự động nhận diện định dạng dán liền IP:PORT:USER:PASS
        if not (raw_server.startswith("http://") or raw_server.startswith("https://") or raw_server.startswith("socks5://")):
            parts = raw_server.split(":")
            if len(parts) == 4:
                # ip:port:user:pass
                raw_server = f"http://{parts[0]}:{parts[1]}"
                if not user:
                    user = parts[2]
                if not pwd:
                    pwd = parts[3]
            elif len(parts) == 2:
                # ip:port
                raw_server = f"http://{parts[0]}:{parts[1]}"
            else:
                raw_server = f"http://{raw_server}"

        p = {"server": raw_server}
        if user:
            p["username"] = user
            p["password"] = pwd
        return p


def kiem_tra_proxy_mot_bot(cfg: BotConfig) -> Dict:
    """Kiểm tra kết nối và đo độ trễ thực tế của 1 proxy."""
    import requests
    p_dict = cfg.proxy_dict()
    if not p_dict:
        return {"status": "direct", "ip": "IP máy tính", "latency": 0, "msg": "Dùng trực tiếp IP máy tính (không qua proxy)"}
    server = p_dict.get("server", "")
    user = p_dict.get("username", "")
    pwd = p_dict.get("password", "")
    
    if user and pwd:
        clean_srv = server.replace("http://", "").replace("https://", "").replace("socks5://", "")
        proxy_url = f"http://{user}:{pwd}@{clean_srv}"
    else:
        proxy_url = server

    proxies = {"http": proxy_url, "https": proxy_url}
    start = time.time()
    try:
        resp = requests.get("http://api.ipify.org?format=json", proxies=proxies, timeout=8)
        latency = int((time.time() - start) * 1000)
        if resp.status_code == 200:
            ip_val = resp.json().get("ip", "OK")
            return {"status": "ok", "ip": ip_val, "latency": latency, "msg": f"Kết nối tốt (IP: {ip_val} • {latency}ms)"}
        else:
            return {"status": "error", "ip": "", "latency": latency, "msg": f"Mã HTTP: {resp.status_code}"}
    except Exception as e:
        err_s = str(e)
        if "407" in err_s or "Authentication" in err_s:
            msg = "Sai Username hoặc Password"
        elif "Timeout" in err_s or "timed out" in err_s:
            msg = "Hết thời gian chờ (Proxy mất mạng hoặc quá chậm)"
        elif "refused" in err_s or "Failed to connect" in err_s:
            msg = "Không thể kết nối (Port đóng hoặc sai IP)"
        else:
            msg = f"Lỗi kết nối ({err_s[:30]})"
        return {"status": "error", "ip": "", "latency": 0, "msg": msg}


# ==============================================================================
# 2. HÀM TIỆN ÍCH - HÀNH VI NGƯỜI THẬT
# ==============================================================================
def human_sleep(min_s: float = 2.0, max_s: float = 5.0):
    """Ngủ một khoảng ngẫu nhiên để mô phỏng tốc độ đọc/nhìn của người thật."""
    time.sleep(random.uniform(min_s, max_s))


def random_scroll(page, min_scrolls: int = 3, max_scrolls: int = 8):
    """Cuộn trang từng đoạn với tốc độ ngẫu nhiên, giống người đọc nội dung."""
    for _ in range(random.randint(min_scrolls, max_scrolls)):
        delta = random.randint(200, 600)
        page.mouse.wheel(0, delta)
        human_sleep(0.5, 1.8)


def type_like_human(page, selector: str, text: str):
    """Gõ từng ký tự với độ trễ ngẫu nhiên, không dán nguyên khối."""
    page.click(selector)
    human_sleep(0.3, 0.8)
    for ch in text:
        page.keyboard.type(ch, delay=random.randint(40, 140))
    human_sleep(0.4, 1.0)
    page.keyboard.press("Enter")


def doc_proxy_config() -> List[BotConfig]:
    """Đọc cấu hình 5 proxy từ file bot_proxies.json (nếu có)."""
    if not os.path.exists(PROXY_CONFIG_FILE):
        return [BotConfig(bot_id=f"bot_{i+1:02d}", name=f"Bot {i+1}") for i in range(5)]
    try:
        with open(PROXY_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        bots = []
        for i, item in enumerate(data.get("bots", [])):
            bots.append(BotConfig(
                bot_id=item.get("bot_id", f"bot_{i+1:02d}"),
                name=item.get("name", f"Bot {i+1}"),
                proxy_server=item.get("proxy_server", ""),
                proxy_username=item.get("proxy_username", ""),
                proxy_password=item.get("proxy_password", ""),
            ))
        return bots
    except Exception:
        return [BotConfig(bot_id=f"bot_{i+1:02d}", name=f"Bot {i+1}") for i in range(5)]


# ==============================================================================
# 3. KẾT QUẢ - AN TOÀN ĐA LUỒNG
# ==============================================================================
class ResultStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.results: List[Dict] = []
        self._load()

    def _load(self):
        if os.path.exists(RESULTS_FILE):
            try:
                with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                    self.results = json.load(f)
            except Exception:
                self.results = []

    def add(self, record: Dict):
        with self.lock:
            self.results.append(record)
            with open(RESULTS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)

    def all(self) -> List[Dict]:
        with self.lock:
            return list(self.results)


# ==============================================================================
# 4. LUỒNG CÔNG VIỆC CỦA MỘT BOT
# ==============================================================================
class BotWorker(threading.Thread):
    def __init__(
        self,
        config: BotConfig,
        keyword_queue: queue.Queue,
        result_store: ResultStore,
        max_pages: int = 5,
        dwell_min: int = 45,
        dwell_max: int = 90,
        visit_pages: bool = True,
        headless: bool = False,
        click_zalo: bool = False,
        delay_between_min: int = 8,
        delay_between_max: int = 15,
        stop_event: Optional[threading.Event] = None,
    ):
        super().__init__(daemon=True)
        self.config = config
        self.keyword_queue = keyword_queue
        self.result_store = result_store
        self.max_pages = max_pages
        self.dwell_min = dwell_min
        self.dwell_max = dwell_max
        self.visit_pages = visit_pages
        # Tự động chuyển sang Headless nếu chạy trên Linux / Streamlit Cloud không có màn hình
        if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
            headless = True
        self.headless = headless
        self.click_zalo = click_zalo
        self.delay_between_min = delay_between_min
        self.delay_between_max = delay_between_max
        self.stop_event = stop_event or threading.Event()
        self.processed = 0
        self.found_count = 0
        self.errors = []

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        full_line = f"[{ts}] [{self.config.name}] {msg}"
        print(full_line, flush=True)
        append_live_log(full_line)

    def _write_progress(self, status: str, detail: str = ""):
        """Ghi tiến độ hiện tại an toàn tuyệt đối đa luồng và đa tiến trình (tránh khóa file trên Windows)."""
        with PROGRESS_LOCK:
            for _ in range(5):
                try:
                    prog = {}
                    if os.path.exists(PROGRESS_FILE):
                        try:
                            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                                prog = json.load(f)
                        except Exception:
                            prog = {}
                    prog[self.config.bot_id] = {
                        "name": self.config.name,
                        "status": status,
                        "detail": detail,
                        "processed": self.processed,
                        "found": self.found_count,
                        "updated_at": datetime.now().isoformat(),
                    }
                    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                        json.dump(prog, f, ensure_ascii=False, indent=2)
                    break
                except Exception:
                    time.sleep(0.05)

    def _extract_serp_results(self, page) -> List[Dict]:
        """Trích xuất toàn diện kết quả tìm kiếm Google: AI Overview, Featured Snippet, Cụm hình ảnh và Organic (bắt chính xác Top 1, 2, 3)."""
        try:
            curr_u = (page.url or "").lower()
            if not any(g in curr_u for g in ["google.", "/search"]):
                return []
        except Exception:
            return []

        js = r"""
        () => {
            const results = [];
            const seenUrls = new Set();
            const seenElements = new Set();
            const ignoreHosts = ['google.', 'gstatic.', 'youtube.com', 'schema.org', 'w3.org', 'support.google', 'policies.google'];

            // Đảm bảo chỉ quét trên vùng kết quả tìm kiếm của Google
            const searchContainer = document.querySelector('#search, #rso, #center_col');
            if (!searchContainer) return [];

            function cleanGoogleUrl(raw) {
                if (!raw) return '';
                let u = raw.trim();
                try { u = decodeURIComponent(u); } catch(e) {}
                
                // 1. Nếu raw chứa URL hwood.vn chính thức, bóc tách ra ngay lập tức
                const mHwood = u.match(/https?:\/\/(?:www\.)?hwood\.vn[^\s"'&<>)]*/i);
                if (mHwood) {
                    return mHwood[0].split('?')[0].split('#')[0].replace(/\/+$/, '');
                }

                // 2. Giải mã URL mã hóa Protobuf của Google (/goto?url=CAES...)
                if (u.includes('/goto?') || u.includes('/goto/')) {
                    const gm = u.match(/[?&]url=([A-Za-z0-9_-]+)/i);
                    if (gm && gm[1]) {
                        try {
                            let b64 = gm[1].replace(/-/g, '+').replace(/_/g, '/');
                            while (b64.length % 4 !== 0) b64 += '=';
                            const decoded = atob(b64);
                            const urlMatch = decoded.match(/https?:\/\/[^\s\x00-\x1f\x7f-\xff]+/i);
                            if (urlMatch) return urlMatch[0].split('?')[0].split('#')[0].replace(/\/$/, '');
                        } catch(e) {}
                    }
                }

                // 3. Giải mã các tham số chuyển hướng thông thường của Google (/url?)
                if (u.includes('/url?') || u.includes('/url/')) {
                    try {
                        let parsedGoogle = new URL(u.startsWith('http') ? u : ('https://www.google.com' + (u.startsWith('/') ? '' : '/') + u));
                        let targetParam = parsedGoogle.searchParams.get('url') 
                                       || parsedGoogle.searchParams.get('ru') 
                                       || parsedGoogle.searchParams.get('imgrefurl') 
                                       || parsedGoogle.searchParams.get('source_url');
                        if (!targetParam) {
                            let qVal = parsedGoogle.searchParams.get('q');
                            if (qVal && (qVal.startsWith('http://') || qVal.startsWith('https://'))) {
                                targetParam = qVal;
                            }
                        }
                        if (targetParam) u = targetParam;
                    } catch(e) {}
                }
                if (u.startsWith('//')) u = 'https:' + u;
                return u.split('?')[0].split('#')[0].replace(/\/+$/, '');
            }

            function isStrictHwood(u) {
                if (!u) return false;
                try {
                    let full = u.startsWith('http') ? u : ('https://' + u.replace(/^\/+/, ''));
                    let parsed = new URL(full, 'https://www.google.com');
                    let h = parsed.hostname.toLowerCase();
                    return h === 'hwood.vn' || h === 'www.hwood.vn' || h.endsWith('.hwood.vn');
                } catch(e) {
                    let clean = u.toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '');
                    return clean.startsWith('hwood.vn/') || clean === 'hwood.vn';
                }
            }

            // Quét trực tiếp qua tất cả các tiêu đề h3 của kết quả tìm kiếm trên Google
            const headings = Array.from(searchContainer.querySelectorAll('h3, [role="heading"]'));
            let pos = 0;

            headings.forEach(heading => {
                let title = (heading.innerText || '').trim().split('\n')[0];
                if (!title || title.length < 3) return;
                if (title.startsWith('Bạn nói:') || title.includes('Tìm kiếm có liên quan') || title.includes('Mọi người cũng hỏi')) return;

                if (seenElements.has(heading)) return;
                seenElements.add(heading);

                const card = heading.closest('div.MjjYud, div.g, div.tF2Cxc, [data-attrid*="overview"], .N54PNb, .c2xzTb, .xpdopen') || heading.parentElement;
                const headingA = heading.closest('a') || (heading.parentElement ? heading.parentElement.querySelector('a') : null);

                // Thu thập tất cả các thẻ a trong card/heading để bóc tách liên kết
                let allA = [];
                if (headingA) allA.push(headingA);
                if (card) {
                    card.querySelectorAll('a').forEach(a => {
                        if (!allA.includes(a)) allA.push(a);
                    });
                }

                let bestUrl = '';
                let bestA = null;
                let isHwood = false;

                // Tìm tất cả các ứng viên domain hwood.vn trong card này
                let hwoodCandidates = [];
                for (let a of allA) {
                    let raw = a.href || a.getAttribute('href') || a.getAttribute('data-url') || a.getAttribute('ping') || '';
                    let u = cleanGoogleUrl(raw);
                    if (isStrictHwood(u)) {
                        let path = '';
                        try {
                            path = new URL(u).pathname.replace(/^\/+/, '').replace(/\/+$/, '');
                        } catch(e) {}
                        hwoodCandidates.push({ a: a, url: u, path: path });
                    }
                }

                if (hwoodCandidates.length > 0) {
                    // ƯU TIÊN TUYỆT ĐỐI LINK BÀI VIẾT CHI TIẾT (path != '') TRƯỚC TRANG CHỦ (path == '')
                    let deepArticles = hwoodCandidates.filter(x => x.path && x.path.length > 1);
                    if (deepArticles.length > 0) {
                        bestUrl = deepArticles[0].url;
                        bestA = deepArticles[0].a;
                    } else {
                        bestUrl = hwoodCandidates[0].url;
                        bestA = hwoodCandidates[0].a;
                    }
                    isHwood = true;
                } else {
                    // Không phải HWOOD
                    let raw = headingA ? (headingA.href || headingA.getAttribute('href') || '') : '';
                    let u = cleanGoogleUrl(raw);
                    if (u && u.startsWith('http') && !ignoreHosts.some(x => u.includes(x))) {
                        bestUrl = u;
                    }
                    bestA = headingA;
                    isHwood = false;
                }

                if (!bestUrl) return;
                if (seenUrls.has(bestUrl)) return;
                seenUrls.add(bestUrl);
                pos += 1;

                let sType = 'organic';
                let sLabel = `Top ${pos}`;
                if (card && (card.closest('[data-attrid*="overview"], [aria-label*="AI"]') || card.matches('[data-attrid*="overview"], [aria-label*="AI"]'))) {
                    sType = 'ai_overview';
                    sLabel = '🏆 AI Overview';
                } else if (card && (card.closest('.c2xzTb, [data-attrid*="featured"]') || card.matches('.c2xzTb, [data-attrid*="featured"]'))) {
                    sType = 'featured_snippet';
                    sLabel = '💎 Top 0 Featured';
                }

                // CHỈ gắn cờ target nếu thực sự là hwood.vn
                if (isHwood && bestA) {
                    if (card) card.setAttribute('data-bot-hwood-card', 'true');
                    bestA.setAttribute('data-bot-hwood-link', 'true');
                    bestA.setAttribute('data-bot-target-url', bestUrl);
                    heading.setAttribute('data-bot-hwood-target', 'true');
                    heading.setAttribute('data-bot-url', bestUrl);
                }

                results.push({
                    position: pos,
                    title: title,
                    url: bestUrl,
                    source_type: sType,
                    source_label: sLabel,
                    is_hwood: isHwood
                });
            });

            return results;
        }
        """
        try:
            return page.evaluate(js)
        except Exception:
            return []

    def _find_hwood_results(self, serp: List[Dict]) -> List[Dict]:
        """
        Lọc và ưu tiên sắp xếp: CHỈ nhận các kết quả có domain thực sự là hwood.vn (100% chính hãng).
        Loại bỏ tuyệt đối tất cả các trang web đại lý (hoangangroup.com,...), sàn TMĐT hoặc đối thủ.
        """
        hwood = []
        for r in serp:
            url = r.get("url", "")
            if is_strict_hwood_url(url):
                r["is_hwood"] = True
                hwood.append(r)
            else:
                r["is_hwood"] = False

        if not hwood:
            return []

        def rank_score(item):
            raw_url = item.get("url", "").lower().rstrip("/")
            is_bare_home = raw_url in ["https://hwood.vn", "http://hwood.vn", "https://www.hwood.vn"]
            home_penalty = 1 if is_bare_home else 0
            return (home_penalty, item.get("position", 999))

        hwood.sort(key=rank_score)
        return hwood

    def _is_403(self, page) -> bool:
        """Kiểm tra xem trang có bị lỗi 403 Forbidden của Google không (hình robot vặn cờ lê)."""
        try:
            title = (page.title() or "").lower()
            if "403" in title or "forbidden" in title:
                return True
            body_text = ""
            try:
                body_text = (page.locator("body").inner_text(timeout=800) or "").lower()
            except Exception:
                pass
            if "403. that's an error" in body_text or "does not have permission to get url" in body_text:
                return True
            return False
        except Exception:
            return False

    def _recover_from_403(self, page, keyword: str) -> bool:
        """
        Tự động xử lý khi Google trả về lỗi 403 Forbidden (hình người máy bị hỏng):
        Chuyển hướng vào trang chủ google.com, gõ từ khóa vào ô tìm kiếm như người thật để vượt chặn 403.
        """
        self._log(f"⚠️ Phát hiện Google chặn 403 (Forbidden), tự động chuyển qua trang chủ Google để tra cứu lại...")
        try:
            try:
                page.context.clear_cookies()
            except Exception:
                pass
            page.goto("https://www.google.com.vn", timeout=25000)
            human_sleep(1.5, 2.5)
            self._accept_consent_if_needed(page)

            # Tìm ô tìm kiếm của Google
            search_box = page.locator("textarea[name='q'], input[name='q']").first
            if search_box.count() > 0 and search_box.is_visible():
                search_box.click()
                search_box.fill("")
                type_like_human(page, "textarea[name='q'], input[name='q']", keyword)
                human_sleep(0.5, 1.2)
                page.keyboard.press("Enter")
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                human_sleep(1.5, 2.5)
                if not self._is_403(page):
                    self._log(f"✅ Vượt qua 403 thành công! Đã nạp trang kết quả tìm kiếm cho '{keyword}'")
                    return True

            # Thử phương án 2: google.com quốc tế
            import urllib.parse
            page.goto(f"https://www.google.com/search?q={urllib.parse.quote_plus(keyword)}&pws=0", timeout=25000)
            human_sleep(2.0, 3.0)
            return not self._is_403(page)
        except Exception as e_rec:
            self._log(f"   ⚠️ Thao tác vượt 403: {str(e_rec)[:50]}")
            return False

    def _is_blocked(self, page) -> bool:
        """Kiểm tra chính xác trang có thực sự bị chặn CAPTCHA hoặc 403 bởi Google hay không."""
        try:
            if self._is_403(page):
                return True
            url = (page.url or "").lower()
            if "sorry" in url or "recaptcha" in url:
                return True
            title = (page.title() or "").lower()
            if any(x in title for x in ["sorry", "unusual traffic", "rất tiếc", "robot"]):
                return True
            # Bất kể URL nào, nếu có form captcha hoặc recaptcha xuất hiện trên DOM thì chắc chắn đang bị chặn
            if page.locator("form#captcha-form, [action*='Sorry'], div#recaptcha, iframe[src*='recaptcha']").count() > 0:
                return True
            return False
        except Exception:
            return False

    def _handle_captcha_if_needed(self, page, keyword: str) -> bool:
        """
        Kiểm tra và xử lý khi gặp CAPTCHA:
        Tạm dừng, đưa cửa sổ trình duyệt lên màn hình để người dùng tự tay giải,
        chờ tối đa 10 phút (600s). Tự động nhận diện khi người dùng giải xong (hoặc tự submit form),
        sau đó tải lại đúng kết quả tìm kiếm và đảm bảo kết quả SERP đã nạp đầy đủ.
        """
        if not self._is_blocked(page):
            return True

        # Nếu là lỗi 403 Forbidden, thử tự động vượt qua bằng cách gõ từ khóa từ trang chủ google.com
        if self._is_403(page):
            if self._recover_from_403(page, keyword):
                return True

        # Đánh dấu tạm khóa các bot khác dùng chung IP để tránh Google block liên tục
        CAPTCHA_ACTIVE_EVENT.clear()
        self._log(f"⚠️ [PHÁT HIỆN CAPTCHA] Vui lòng giải CAPTCHA trên cửa sổ trình duyệt của {self.config.name}...")
        self._write_progress("waiting_captcha", f"⚠️ CẦN GIẢI CAPTCHA trên màn hình cho {self.config.name}!")
        try:
            page.bring_to_front()
        except Exception:
            pass

        start_wait = time.time()
        try:
            while time.time() - start_wait < 600 and not self.stop_event.is_set():
                time.sleep(1.5)
                try:
                    if page.is_closed():
                        self._log(f"⚠️ Cửa sổ {self.config.name} bị đóng trong lúc chờ giải Captcha.")
                        return False
                except Exception:
                    pass

                # Hỗ trợ tự động submit form nếu người dùng đã tích chọn reCAPTCHA xong
                try:
                    has_solved_token = page.evaluate("""() => {
                        const el = document.querySelector('[name="g-recaptcha-response"], textarea#g-recaptcha-response');
                        return el && el.value && el.value.trim().length > 10;
                    }""")
                    if has_solved_token:
                        submit_btn = page.locator("form#captcha-form input[type='submit'], form#captcha-form button, input[type='submit']")
                        if submit_btn.count() > 0:
                            submit_btn.first.click(timeout=1500)
                except Exception:
                    pass

                # Kiểm tra xem trang đã thoát khỏi trạng thái chặn sorry chưa
                if not self._is_blocked(page):
                    self._log(f"🎉 ĐÃ GIẢI XONG CAPTCHA trên {self.config.name}! Đang tải kết quả tìm kiếm cho '{keyword}'...")
                    self._write_progress("running", f"Đã giải Captcha! Đang nạp kết quả: {keyword}")
                    human_sleep(2.0, 3.5)

                    import urllib.parse
                    search_url = f"https://www.google.com.vn/search?q={urllib.parse.quote_plus(keyword)}&hl=vi&gl=vn"

                    # Kiểm tra xem trang đã nạp kết quả tìm kiếm chưa
                    curr_url = (page.url or "").lower()
                    has_results = False
                    try:
                        if page.locator("#search, #rso, div.g, div.MjjYud").count() > 0:
                            has_results = True
                    except Exception:
                        pass

                    if not has_results or "search" not in curr_url or "sorry" in curr_url:
                        self._log(f"🔄 Mở lại trang kết quả Google cho '{keyword}'...")
                        try:
                            page.goto(search_url, timeout=30000)
                            page.wait_for_load_state("domcontentloaded", timeout=15000)
                        except Exception:
                            pass

                    # BẮT BUỘC ĐỢI PHẦN TỬ KẾT QUẢ XUẤT HIỆN TRÊN MÀN HÌNH ĐỂ TRÁNH BỎ QUA BÀI VIẾT:
                    try:
                        page.wait_for_selector("#search, #rso, div.g, div.MjjYud, [data-attrid*='overview']", timeout=15000)
                    except Exception:
                        pass
                    human_sleep(1.2, 2.0)
                    return True
        finally:
            # Mở khóa cho các bot khác tiếp tục hoạt động
            CAPTCHA_ACTIVE_EVENT.set()

        self._log(f"⏱️ Quá hạn 10 phút chờ giải Captcha trên {self.config.name}")
        return False

    def _accept_consent_if_needed(self, page):
        """Nhấn nút đồng ý cookie/điều khoản nếu Google hiện lên."""
        for btn_text in ["Tôi đồng ý", "Đồng ý", "Accept all", "Accept", "Tôi chấp nhận"]:
            try:
                btn = page.get_by_role("button", name=re.compile(btn_text, re.IGNORECASE))
                if btn.count() > 0:
                    btn.first.click(timeout=2000)
                    human_sleep(1, 2)
                    return
            except Exception:
                continue

    def _visit_hwood_page(self, page, result: Dict):
        """Click vào kết quả hwood.vn (AI Overview, Cụm hình ảnh, hay Organic) để tăng traffic chuẩn Google."""
        source_type = result.get("source_type", "organic")
        source_label = result.get("source_label", f"Top {result.get('position', '?')}")
        target_url = result.get("url", "")
        if not target_url.startswith("http"):
            target_url = f"https://hwood.vn/{target_url.lstrip('/')}"
        
        # BẢO VỆ CẤP 1: Xác thực nghiêm ngặt 100% domain hwood.vn
        if not is_strict_hwood_url(target_url):
            self._log(f"🛡️ Từ chối truy cập URL không thuộc hwood.vn: {target_url[:60]}")
            return

        clean_target = target_url.replace("https://", "").replace("http://", "").split("?")[0].rstrip("/")
        
        # Trích xuất đường dẫn chi tiết của bài viết/sản phẩm (slug)
        from urllib.parse import urlparse
        parsed = urlparse(target_url)
        slug = parsed.path.strip("/")
        if any(x in slug.lower() for x in ["kiểm", "duyệt", "kiem-duyet", "kiemduyet"]):
            slug = ""

        self._log(f"👉 Vào bài viết: {target_url[:65]} ({source_label})")
        active_page = page
        opened_new_tab = False

        try:
            # 1. Bỏ thuộc tính target='_blank' trên toàn trang để khi bấm sẽ mở trực tiếp trên tab hiện tại
            try:
                page.evaluate("""() => {
                    document.querySelectorAll('a[target]').forEach(a => a.removeAttribute('target'));
                }""")
            except Exception:
                pass

            # 2. Tìm phần tử HWOOD trên DOM theo độ ưu tiên tuyệt đối (CHỈ CHỌN PHẦN TỬ THỰC SỰ TRỎ ĐẾN HWOOD):
            target_locator = None
            candidate_selectors = [
                f"a[data-bot-target-url='{target_url}']",
                f"a[data-bot-url='{target_url}']",
                f"h3[data-bot-url='{target_url}']",
                "a[data-bot-hwood-link='true']",
            ]

            if slug:
                candidate_selectors.extend([
                    f"a[data-bot-target-url*='{slug}']",
                    f"a[data-bot-url*='{slug}']",
                    f"h3[data-bot-url*='{slug}']",
                    f"a[href*='hwood.vn'][href*='{slug}']",
                    f"a[href*='hwood.vn']:has(h3)",
                ])
            else:
                candidate_selectors.extend([
                    "a[data-bot-target-url='https://hwood.vn']",
                    "a[data-bot-url='https://hwood.vn']",
                    "h3[data-bot-url='https://hwood.vn']",
                    "a[href*='hwood.vn']:has(h3)",
                ])

            candidate_selectors.extend([
                f"a[href*='{clean_target}']",
                "a[data-bot-hwood-target='true'][href*='hwood.vn']",
                "h3[data-bot-hwood-target='true']",
                "[data-bot-fallback-link='true']",
            ])

            for sel in candidate_selectors:
                try:
                    loc = page.locator(sel).first
                    if loc.count() > 0:
                        target_locator = loc
                        break
                except Exception:
                    continue

            clicked = False

            # 3. Nếu tìm thấy phần tử: Xác thực an toàn trước khi bấm để TUYỆT ĐỐI KHÔNG CLICK NHẦM ĐỐI THỦ
            if target_locator is not None:
                try:
                    # Kiểm tra thẻ a có thực sự chứa domain hwood.vn hay không
                    is_safe = page.evaluate("""(el) => {
                        if (!el) return false;
                        const a = el.closest('a') || el.querySelector('a') || el;
                        let raw = a.href || a.getAttribute('href') || a.getAttribute('data-url') || a.getAttribute('data-bot-target-url') || a.getAttribute('data-bot-url') || '';
                        let u = raw.toLowerCase();
                        if (u.includes('hwood.vn')) return true;
                        if (a.getAttribute('data-bot-hwood-link') === 'true' || a.getAttribute('data-bot-hwood-target') === 'true') return true;
                        // Kiểm tra không phải domain khác chứa từ khóa hwood trong slug (ví dụ: hoangangroup.com/...hwood...)
                        try {
                            let parsed = new URL(raw, 'https://www.google.com');
                            let host = parsed.hostname.toLowerCase();
                            if (host !== 'hwood.vn' && host !== 'www.hwood.vn' && !host.endsWith('.hwood.vn') && !host.includes('google.')) {
                                return false;
                            }
                        } catch(e) {}
                        return true;
                    }""", target_locator.element_handle())

                    if not is_safe:
                        self._log(f"🛡️ Phần tử không chứa domain hwood.vn, ngăn click nhầm vào đối thủ/đại lý!")
                        target_locator = None
                except Exception:
                    pass

            if target_locator is not None:
                try:
                    target_locator.scroll_into_view_if_needed(timeout=2500)

                    # Tự động đọc URL thực tế từ thẻ liên kết chuẩn bị click
                    try:
                        href_attr = page.evaluate("""(el) => {
                            if (!el) return '';
                            const a = el.closest('a') || el.querySelector('a') || el;
                            let raw = a.href || a.getAttribute('href') || a.getAttribute('data-url') || a.getAttribute('data-bot-url') || '';
                            return raw;
                        }""", target_locator.element_handle())
                        if href_attr and "hwood.vn" in href_attr.lower():
                            clean_href = href_attr.split('?')[0].split('#')[0].rstrip('/')
                            parsed_h = urlparse(clean_href)
                            if parsed_h.path.strip('/'):
                                target_url = clean_href
                                slug = parsed_h.path.strip('/')
                    except Exception:
                        pass

                    try:
                        page.evaluate("""(el) => {
                            if (!el) return;
                            el.scrollIntoView({behavior: 'smooth', block: 'center'});
                            el.style.outline = '4px solid #ff0055';
                            el.style.backgroundColor = '#fff3cd';
                            el.style.boxShadow = '0 0 20px rgba(255, 0, 85, 0.9)';
                            el.style.transition = 'all 0.5s ease';
                        }""", target_locator.element_handle())
                    except Exception:
                        pass

                    self._log(f"🎯 Đã khóa vị trí bài viết HWOOD ({source_label}), chuẩn bị click vào trang...")
                    human_sleep(1.2, 2.0)

                    # Bấm chuẩn xác vào thẻ <a> liên kết (hoặc chính nó)
                    try:
                        page.evaluate("""(el) => {
                            if (!el) return;
                            const a = el.closest('a') || el.querySelector('a') || el;
                            a.click();
                        }""", target_locator.element_handle())
                        clicked = True
                    except Exception:
                        try:
                            target_locator.click(force=True, timeout=2500)
                            clicked = True
                        except Exception:
                            clicked = False

                    # Chờ hoàn tất chuyển hướng sang domain hwood.vn
                    start_wait = time.time()
                    while time.time() - start_wait < 15.0:
                        try:
                            page.wait_for_timeout(400)
                        except Exception:
                            time.sleep(0.4)

                        for p in page.context.pages:
                            p_u = p.url or ""
                            if is_strict_hwood_url(p_u):
                                active_page = p
                                try:
                                    active_page.bring_to_front()
                                except Exception:
                                    pass
                                if p != page:
                                    opened_new_tab = True
                                break

                        if is_strict_hwood_url(active_page.url or ""):
                            break

                    if is_strict_hwood_url(active_page.url or ""):
                        self._log(f"🎉 ĐÃ CLICK THÀNH CÔNG VÀO HWOOD TỪ GOOGLE: {active_page.url[:60]}")
                except Exception as e_click:
                    self._log(f"   ⚠️ Thao tác click DOM ({str(e_click)[:40]}), chuyển sang mở trực tiếp...")
                    clicked = False

            # BẢO VỆ CHỐNG NHẦM TRANG 100%: Đóng ngay bất kỳ tab nào không thuộc hwood.vn và Google
            for p in list(page.context.pages):
                p_url = p.url or ""
                if not is_strict_hwood_url(p_url) and not any(g in p_url.lower() for g in ["google.", "gstatic."]):
                    try:
                        self._log(f"🛡️ Đóng ngay tab bên ngoài không thuộc hwood.vn: {p_url[:50]}")
                        p.close()
                    except Exception:
                        pass

            # 4. Fallback an toàn & Đảm bảo giữ nguyên bài viết (TUYỆT ĐỐI CẤM REDIRECT RA TRANG CHỦ)
            try:
                active_page.wait_for_load_state("domcontentloaded", timeout=8000)
            except Exception:
                pass

            curr_url = (active_page.url or "").rstrip("/")
            is_bare_home = curr_url in ["https://hwood.vn", "http://hwood.vn", "https://www.hwood.vn"]

            if is_strict_hwood_url(curr_url) and not (slug and is_bare_home):
                self._log(f"✅ Đang đọc đúng bài viết mục tiêu: {active_page.url[:60]}")
            else:
                self._log(f"   ℹ️ Đang vào trực tiếp bài viết HWOOD: {target_url[:60]}")
                try:
                    active_page.goto(target_url, timeout=25000)
                    active_page.wait_for_load_state("domcontentloaded", timeout=15000)
                except Exception:
                    pass

        except Exception as e_visit:
            self._log(f"   ❌ Lỗi mở trang hwood: {str(e_visit)[:80]}")
            if not is_strict_hwood_url(active_page.url or ""):
                try:
                    active_page.goto(target_url, timeout=30000)
                except Exception:
                    pass

        # 5. Đọc nội dung bài viết và tương tác cuộn tự nhiên như người thật trên hwood.vn
        try:
            self._log(f"📖 Đã vào trang HWOOD: {active_page.url[:60]}")
            self._write_progress("dwelling", f"Đang đọc: {active_page.url[:40]}")
            human_sleep(2, 4)

            # Cuộn xem nội dung bài viết tự nhiên
            random_scroll(active_page, min_scrolls=4, max_scrolls=8)

            # Ở lại trang (dwell) trong khoảng dwell_min -> dwell_max giây để Google tính chuẩn traffic
            dwell = random.randint(self.dwell_min, self.dwell_max)
            self._log(f"⏳ Ở lại đọc nội dung ~{dwell}s (cuộn chuột tương tác tăng time-on-site)...")
            elapsed = 0
            while elapsed < dwell and not self.stop_event.is_set():
                chunk = min(random.randint(4, 7), dwell - elapsed)
                time.sleep(chunk)
                elapsed += chunk
                self._write_progress("dwelling", f"Đang đọc bài viết: {elapsed}/{dwell}s (cuộn chuột)")
                if random.random() < 0.65:
                    try:
                        active_page.evaluate(f"window.scrollBy({{ top: {random.randint(180, 420)}, behavior: 'smooth' }});")
                    except Exception:
                        pass
        except Exception:
            pass

        # 5.5. Tương tác nút Zalo OA (trong bài viết hoặc icon nổi góc phải) sau khi đọc xong bài
        if self.click_zalo and not self.stop_event.is_set():
            self._click_zalo_conversion(active_page)

        # 6. Dọn dẹp: Đảm bảo giữ nguyên tab bài viết active_page trên màn hình cho người dùng xem
        try:
            active_page.bring_to_front()
            human_sleep(1.0, 2.0)
        except Exception:
            pass

    def _click_zalo_conversion(self, active_page):
        """
        Tìm và tương tác nút Zalo OA nếu có trên trang (chỉ bấm nếu trang hiện tại thuộc hwood.vn,
        tuyệt đối không điều hướng active_page ra khỏi bài viết đang đọc).
        """
        try:
            if not is_strict_hwood_url(active_page.url or ""):
                self._log("🛡️ Không phải trang hwood.vn, hủy tương tác Zalo!")
                return

            self._log("💬 [ZALO TRAFFIC] Đang tìm nút liên hệ Zalo OA...")
            # Chỉ tìm các link chứa zalo.me hoặc oa.zalo.me thật, tuyệt đối không bấm link nội bộ
            cand_zalo = active_page.locator("a[href*='zalo.me'], a[href*='oa.zalo.me']").first
            if cand_zalo.count() > 0 and cand_zalo.is_visible():
                href = cand_zalo.get_attribute("href") or ""
                if "zalo.me" in href.lower():
                    self._log("   🎯 Đã phát hiện nút Zalo OA chính thức, tương tác click...")
                    cand_zalo.scroll_into_view_if_needed(timeout=2000)
                    human_sleep(0.8, 1.5)
                    # Mở trong tab mới nếu chưa có target='_blank' để bảo vệ bài viết
                    active_page.evaluate("""(el) => {
                        el.setAttribute('target', '_blank');
                    }""", cand_zalo.element_handle())
                    prev_tabs = len(active_page.context.pages)
                    cand_zalo.click(timeout=2500)
                    human_sleep(2.0, 3.5)

                    # Tự động đóng tab Zalo mới mở sau khi gửi tương tác để trả lại không gian cho người dùng
                    for p in list(active_page.context.pages):
                        p_u = (p.url or "").lower()
                        if p != active_page and ("zalo" in p_u or "chat.zalo.me" in p_u):
                            try:
                                p.close()
                            except Exception:
                                pass
                    try:
                        active_page.bring_to_front()
                    except Exception:
                        pass
                    self._log("   🎉 Đã tương tác Zalo OA thành công và đóng tab phụ an toàn!")
            else:
                self._log("   ℹ️ Trang không có nút Zalo OA trực tiếp, hoàn tất đọc bài tự nhiên.")
        except Exception as e_z:
            self._log(f"   ℹ️ Bỏ qua tương tác Zalo: {str(e_z)[:40]}")

    def run(self):
        from playwright.sync_api import sync_playwright
        import urllib.parse
        self._write_progress("starting", "Khởi động trình duyệt")

        while not self.stop_event.is_set() and not self.keyword_queue.empty():
            try:
                with sync_playwright() as p:
                    proxy = self.config.proxy_dict()
                    launch_args = [
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--start-maximized",
                        "--disable-http2",
                        "--disable-quic",
                        "--disable-ipv6",
                        "--ignore-certificate-errors",
                    ]

                    def _create_browser_session(use_proxy_dict):
                        try:
                            br = p.chromium.launch(
                                headless=self.headless,
                                proxy=use_proxy_dict,
                                args=launch_args,
                            )
                        except Exception as e_br:
                            if "executable doesn't exist" in str(e_br).lower() or "playwright install" in str(e_br).lower():
                                import subprocess
                                self._log("⏳ Đang cài đặt bộ Chromium Playwright cho máy chủ...")
                                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
                                br = p.chromium.launch(
                                    headless=self.headless,
                                    proxy=use_proxy_dict,
                                    args=launch_args,
                                )
                            else:
                                raise e_br
                        ctx = br.new_context(
                            user_agent=self.config.user_agent,
                            viewport=self.config.viewport,
                            locale="vi-VN",
                            timezone_id="Asia/Ho_Chi_Minh",
                            proxy=use_proxy_dict,
                        )
                        if HAS_STEALTH:
                            stealth_sync(ctx)
                        pg = ctx.new_page()
                        pg.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                        return br, ctx, pg

                    try:
                        browser, context, page = _create_browser_session(proxy)
                    except Exception as e_init:
                        err_str = str(e_init)
                        if proxy and any(x in err_str for x in ["ERR_CONNECTION_RESET", "ERR_PROXY", "Timeout", "ERR_CONNECTION_REFUSED"]):
                            self._log(f"⚠️ Proxy không phản hồi. Tự động chuyển sang IP máy trực tiếp!")
                            try:
                                browser.close()
                            except Exception:
                                pass
                            proxy = None
                            browser, context, page = _create_browser_session(None)
                        else:
                            raise e_init

                    self._write_progress("running", "Sẵn sàng, lấy từ khóa...")

                    while not self.stop_event.is_set():
                        try:
                            keyword = self.keyword_queue.get_nowait()
                        except queue.Empty:
                            break

                        self.processed += 1
                        self._log(f"🔍 Tra từ khóa [{self.processed}]: {keyword}")
                        self._write_progress("running", f"Đang tra: {keyword}")

                        record = {
                            "tu_khoa": keyword,
                            "bot_id": self.config.bot_id,
                            "bot_name": self.config.name,
                            "thoi_gian": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            "ket_qua_hwood": [],
                            "trang_thai": "ok",
                        }

                        try:
                            # Đảm bảo cửa sổ trình duyệt luôn sống
                            try:
                                if page.is_closed() or not browser.is_connected():
                                    self._log("⚠️ Cửa sổ trình duyệt bị gián đoạn, tự động mở lại...")
                                    browser, context, page = _create_browser_session(proxy)
                            except Exception:
                                browser, context, page = _create_browser_session(proxy)

                            # Bước 1: Mở thẳng trang tìm kiếm của từ khóa (chính xác 100%, không bị kẹt ở ô gõ)
                            search_url = f"https://www.google.com.vn/search?q={urllib.parse.quote_plus(keyword)}&hl=vi&gl=vn"
                            try:
                                page.goto(search_url, timeout=30000)
                            except Exception as e_step1:
                                err_s = str(e_step1)
                                if "closed" in err_s.lower():
                                    self._log("⚠️ Cửa sổ bị đóng, khởi động lại...")
                                    browser, context, page = _create_browser_session(proxy)
                                    page.goto(search_url, timeout=30000)
                                elif proxy and any(x in err_s for x in ["ERR_CONNECTION_RESET", "ERR_PROXY", "Timeout"]):
                                    self._log(f"⚠️ Proxy bị đứt kết nối ({err_s[:35]}). Chuyển sang kết nối trực tiếp...")
                                    try:
                                        browser.close()
                                    except Exception:
                                        pass
                                    proxy = None
                                    browser, context, page = _create_browser_session(None)
                                    page.goto(search_url, timeout=30000)
                                else:
                                    raise e_step1

                            # Chờ nếu đang có bot khác đang giải Captcha (tránh cùng IP bị Google chặn liên tục)
                            if not CAPTCHA_ACTIVE_EVENT.is_set():
                                self._write_progress("resting", "Tạm dừng chờ bot khác giải Captcha...")
                                CAPTCHA_ACTIVE_EVENT.wait(timeout=300)

                            human_sleep(1.2, 2.0)
                            self._accept_consent_if_needed(page)

                            # Tự động phát hiện và vượt qua lỗi 403 Forbidden của Google
                            if self._is_403(page):
                                ok_403 = self._recover_from_403(page, keyword)
                                if not ok_403 and self._is_403(page):
                                    record["trang_thai"] = "bi_chan_403"
                                    self.errors.append(f"Google 403 Forbidden tại '{keyword}'")
                                    self.result_store.add(record)
                                    self._log(f"⚠️ Google chặn 403 cho từ '{keyword}', chuyển tiếp từ khóa sau...")
                                    if not self.keyword_queue.empty() and not self.stop_event.is_set():
                                        pause_s = round(random.uniform(self.delay_between_min, self.delay_between_max), 1)
                                        self._write_progress("resting", f"Nghỉ {pause_s}s trước từ tiếp theo")
                                        time.sleep(pause_s)
                                    continue

                            # Kiểm tra và chờ người dùng tự giải Captcha nếu Google chặn
                            if not self._handle_captcha_if_needed(page, keyword):
                                record["trang_thai"] = "bi_chan_captcha"
                                self.errors.append(f"Quá hạn giải Captcha tại '{keyword}'")
                                self.result_store.add(record)
                                self._log(f"⚠️ Bỏ qua từ '{keyword}' do chưa giải Captcha kịp, tiếp tục từ tiếp theo...")
                                if not self.keyword_queue.empty() and not self.stop_event.is_set():
                                    pause_s = round(random.uniform(self.delay_between_min, self.delay_between_max), 1)
                                    self._write_progress("resting", f"Nghỉ {pause_s}s trước từ tiếp theo")
                                    time.sleep(pause_s)
                                continue

                            # Đảm bảo phần tử kết quả tìm kiếm đã thực sự xuất hiện trên màn hình
                            try:
                                page.wait_for_selector("#search, #rso, div.g, div.MjjYud, [data-attrid*='overview']", timeout=12000)
                            except Exception:
                                pass
                            human_sleep(1.0, 1.8)

                            # Bước 2: Quét tìm kiếm trên trang kết quả Google (bắt ngay Top 1, 2, 3)
                            all_hwood = []
                            captcha_failed = False
                            for page_num in range(1, self.max_pages + 1):
                                self._write_progress("running", f"Đang tìm kiếm '{TARGET_DOMAIN}' trên Google (Trang {page_num})...")

                                # Kiểm tra bảo vệ nếu trang bị chặn Captcha giữa chừng
                                if self._is_blocked(page):
                                    if not self._handle_captcha_if_needed(page, keyword):
                                        record["trang_thai"] = "bi_chan_captcha"
                                        self.errors.append(f"Google chặn Captcha tại '{keyword}'")
                                        captcha_failed = True
                                        break

                                # 1. Cuộn mượt nhẹ để kích hoạt Google nạp đầy đủ (lazy-load) toàn bộ 10 kết quả trang
                                for _ in range(2):
                                    try:
                                        page.evaluate("window.scrollBy({ top: 550, behavior: 'smooth' });")
                                    except Exception:
                                        pass
                                    human_sleep(0.4, 0.7)

                                # Quét bắt ngay các kết quả
                                serp = self._extract_serp_results(page)

                                # Nếu không bắt được kết quả nào (do mạng lag hoặc vừa dính Captcha)
                                if len(serp) == 0 and self._is_blocked(page):
                                    if not self._handle_captcha_if_needed(page, keyword):
                                        record["trang_thai"] = "bi_chan_captcha"
                                        self.errors.append(f"Google chặn Captcha tại '{keyword}'")
                                        captcha_failed = True
                                        break
                                    serp = self._extract_serp_results(page)

                                hwood_hits = self._find_hwood_results(serp)

                                # 2. Nếu chưa thấy ở nửa trên: Cuộn tiếp xuống sâu hơn để tìm tiếp
                                if not hwood_hits:
                                    for _ in range(3):
                                        try:
                                            page.evaluate("window.scrollBy({ top: 750, behavior: 'smooth' });")
                                        except Exception:
                                            pass
                                        human_sleep(0.5, 0.9)
                                        serp = self._extract_serp_results(page)
                                        hwood_hits = self._find_hwood_results(serp)
                                        if hwood_hits:
                                            break

                                for h in hwood_hits:
                                    h["trang_google"] = page_num
                                all_hwood.extend(hwood_hits)
                                if hwood_hits:
                                    self._log(f"   ✅ Trang {page_num}: thấy {len(hwood_hits)} kết quả hwood.vn")
                                    break

                                # Nếu chưa thấy: cuộn thêm hoặc chuyển sang trang tiếp theo của Google
                                if page_num < self.max_pages:
                                    next_page = page_num + 1
                                    self._log(f"   ➡️ Không thấy ở trang {page_num}, chuyển sang trang {next_page}...")
                                    navigated_next = False
                                    
                                    # Phương án 1: Tìm và click nút Next / "Xem thêm kết quả"
                                    try:
                                        page.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
                                        human_sleep(1.0, 1.8)
                                        next_btn = page.locator("#pnnext, a#pnnext, a[aria-label*='Next'], a[aria-label*='Tiếp'], a[aria-label*='Trang tiếp'], button:has-text('Xem thêm kết quả'), a:has-text('Xem thêm kết quả'), [jsname='tJHJ8b'], [jsname='TeSSvd']").first
                                        if next_btn.count() > 0 and next_btn.is_visible():
                                            next_btn.scroll_into_view_if_needed(timeout=2500)
                                            human_sleep(0.5, 1.0)
                                            next_btn.click(timeout=4000)
                                            human_sleep(2.0, 3.5)
                                            if not self._is_blocked(page):
                                                navigated_next = True
                                    except Exception:
                                        navigated_next = False

                                    # Phương án 2: Dùng tham số chuẩn start= của Google (100% chuẩn xác không phụ thuộc giao diện)
                                    if not navigated_next:
                                        start_idx = page_num * 10
                                        next_url = f"https://www.google.com.vn/search?q={urllib.parse.quote_plus(keyword)}&start={start_idx}&hl=vi&gl=vn"
                                        try:
                                            page.goto(next_url, timeout=25000)
                                            page.wait_for_load_state("domcontentloaded", timeout=15000)
                                            human_sleep(1.5, 2.5)
                                        except Exception:
                                            pass

                                    if not self._handle_captcha_if_needed(page, keyword):
                                        break

                            if captcha_failed:
                                self.result_store.add(record)
                                continue

                            record["ket_qua_hwood"] = all_hwood
                            if all_hwood:
                                self.found_count += len(all_hwood)
                                def _hit_score(item):
                                    raw_u = item.get("url", "").lower().rstrip("/")
                                    is_home = raw_u in ["https://hwood.vn", "http://hwood.vn", "https://www.hwood.vn"]
                                    # Ưu tiên bài viết chi tiết (is_home = 0) trước trang chủ (is_home = 1)
                                    return (1 if is_home else 0, item.get("position", 999))

                                top_hit = min(all_hwood, key=_hit_score)
                                self._log(f"🎯 TÌM THẤY {len(all_hwood)} KẾT QUẢ HWOOD! Thứ hạng: TOP {top_hit['position']} ({top_hit['url'][:55]})")
                                if self.visit_pages:
                                    self._visit_hwood_page(page, top_hit)
                            else:
                                record["trang_thai"] = "ngoai_top_50"
                                self._log(f"⚪ Không thấy hwood.vn trong Top {self.max_pages*10} cho '{keyword}'")

                        except Exception as e:
                            record["trang_thai"] = "loi"
                            record["loi"] = str(e)[:200]
                            self.errors.append(f"{keyword}: {str(e)[:80]}")
                            self._log(f"   ❌ Lỗi: {str(e)[:100]}")

                        self.result_store.add(record)

                        # Chỉ nghỉ ngẫu nhiên nếu trong hàng đợi VẪN CÒN TỪ KHÓA!
                        if not self.keyword_queue.empty() and not self.stop_event.is_set():
                            pause_s = round(random.uniform(self.delay_between_min, self.delay_between_max), 1)
                            self._log(f"⏸️ Nghỉ an toàn {pause_s}s trước từ tiếp theo để tránh Google quét...")
                            self._write_progress("resting", f"Nghỉ an toàn {pause_s}s trước từ tiếp theo")
                            time.sleep(pause_s)

                    try:
                        browser.close()
                    except Exception:
                        pass

            except Exception as e:
                err_msg = str(e)
                if any(x in err_msg.lower() for x in ["connection closed", "browser has been closed", "target page"]):
                    self._log(f"🔄 Phiên trình duyệt bị gián đoạn ({err_msg[:40]}). Tự động mở phiên mới tiếp tục...")
                    human_sleep(2, 3)
                    continue
                else:
                    self._write_progress("error", err_msg[:100])
                    self._log(f"💥 Lỗi trình duyệt: {err_msg[:100]}")
                    break

        self._write_progress("done", f"Hoàn thành {self.processed} từ khóa")
        self._log(f"🏁 Kết thúc. Đã tra {self.processed} từ khóa, thấy {self.found_count} lượt hwood.vn")


# ==============================================================================
# 5. HÀM CHẠY TOÀN BỘ 5 BOT (DÙNG CHO CLI VÀ STREAMLIT)
# ==============================================================================
def chay_5_bot(
    danh_sach_tu_khoa: List[str],
    danh_sach_bot: Optional[List[BotConfig]] = None,
    max_pages: int = 5,
    dwell_min: int = 45,
    dwell_max: int = 90,
    visit_pages: bool = True,
    headless: bool = False,
    click_zalo: bool = False,
    delay_between_min: int = 8,
    delay_between_max: int = 15,
) -> Tuple[List[Dict], List[BotWorker]]:
    """
    Khởi chạy 5 bot song song. Trả về (danh_sach_ket_qua, danh_sach_thread_bot).
    Giao diện Streamlit có thể theo dõi tiến độ qua file bot_farm_progress.json.
    """
    # Xáo trộn từ khóa ngẫu nhiên, bỏ trùng lặp
    unique_kw = list(dict.fromkeys([k.strip() for k in danh_sach_tu_khoa if k and k.strip()]))
    random.shuffle(unique_kw)
    kw_queue: queue.Queue = queue.Queue()
    for kw in unique_kw:
        kw_queue.put(kw)

    if danh_sach_bot is None:
        danh_sach_bot = doc_proxy_config()

    # Xóa file tiến độ cũ và khởi tạo nhật ký mới
    xoa_live_logs()
    append_live_log(f"[{datetime.now().strftime('%H:%M:%S')}] [HỆ THỐNG] 🚀 Khởi chạy {len(danh_sach_bot)} Bot quét {len(unique_kw)} từ khóa (Quét tới trang {max_pages})")
    
    prog_init = {
        "_summary": {
            "total_keywords": len(unique_kw),
            "started_at": datetime.now().strftime("%H:%M:%S"),
            "status": "running",
        }
    }
    with PROGRESS_LOCK:
        try:
            tmp_init = f"{PROGRESS_FILE}.tmp_init"
            with open(tmp_init, "w", encoding="utf-8") as f:
                json.dump(prog_init, f, ensure_ascii=False, indent=2)
            os.replace(tmp_init, PROGRESS_FILE)
        except Exception:
            pass

    store = ResultStore()
    stop_event = threading.Event()
    bots = []
    for cfg in danh_sach_bot:
        bot = BotWorker(
            config=cfg,
            keyword_queue=kw_queue,
            result_store=store,
            max_pages=max_pages,
            dwell_min=dwell_min,
            dwell_max=dwell_max,
            visit_pages=visit_pages,
            headless=headless,
            click_zalo=click_zalo,
            delay_between_min=delay_between_min,
            delay_between_max=delay_between_max,
            stop_event=stop_event,
        )
        bots.append(bot)

    print("=" * 60)
    print(f"🤖 KHỞI CHẠY {len(bots)} BOT | {len(unique_kw)} TỪ KHÓA | Quét tới trang {max_pages}")
    print("=" * 60)
    has_empty_proxy = any(not (b.config.proxy_server or "").strip() for b in bots)
    for b in bots:
        b.start()
        # Khởi động lệch pha: nếu dùng chung IP máy thật thì giãn cách 2.5 - 4s để tránh Google quét cùng lúc
        if has_empty_proxy:
            human_sleep(2.0, 3.5)
        else:
            human_sleep(0.8, 1.6)

    return store.all(), bots


def doc_tien_do() -> Dict:
    """Đọc tiến độ các bot từ file an toàn (với retry chống xung đột trên Windows)."""
    if os.path.exists(PROGRESS_FILE):
        for _ in range(5):
            try:
                with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                time.sleep(0.04)
    return {}


def doc_ket_qua() -> List[Dict]:
    if os.path.exists(RESULTS_FILE):
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []
