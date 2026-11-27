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
        dwell_min: int = 60,
        dwell_max: int = 90,
        visit_pages: bool = True,
        deep_browse: bool = True,
        headless: bool = False,
        click_zalo: bool = False,
        delay_between_min: int = 8,
        delay_between_max: int = 15,
        stop_event: Optional[threading.Event] = None,
        steady_pacing: bool = False,
        start_delay: float = 0.0,
        pacing_state: Optional[Dict] = None,
        pacing_lock: Optional[threading.Lock] = None,
    ):
        super().__init__(daemon=True)
        self.config = config
        self.keyword_queue = keyword_queue
        self.result_store = result_store
        self.max_pages = max_pages
        self.dwell_min = dwell_min
        self.dwell_max = dwell_max
        self.visit_pages = visit_pages
        self.deep_browse = deep_browse
        # Tự động chuyển sang Headless nếu chạy trên Linux / Streamlit Cloud không có màn hình
        if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
            headless = True
        self.headless = headless
        self.click_zalo = click_zalo
        self.delay_between_min = delay_between_min
        self.delay_between_max = delay_between_max
        self.stop_event = stop_event or threading.Event()
        self.steady_pacing = steady_pacing
        self.start_delay = start_delay
        self.pacing_state = pacing_state
        self.pacing_lock = pacing_lock
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
        js = r"""
        () => {
            const results = [];
            const seenUrls = new Set();
            const ignoreHosts = ['google.', 'gstatic.', 'youtube.com', 'schema.org', 'w3.org', 'support.google', 'policies.google'];

            function cleanGoogleUrl(raw) {
                if (!raw) return '';
                let u = raw.trim();
                // 1. Giải mã URL mã hóa Protobuf của Google (/goto?url=CAES...)
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
                // 2. Giải mã các tham số chuyển hướng thông thường của Google (/url?q= hoặc /url?url=)
                const m = u.match(/[?&](?:url|q|u|imgrefurl|source_url|ru)=([^&#]+)/i);
                if (m && m[1]) {
                    try { u = decodeURIComponent(m[1]); } catch(e) { u = m[1]; }
                }
                if (u.startsWith('//')) u = 'https:' + u;
                return u.split('?')[0].split('#')[0].replace(/\/$/, '');
            }

            // Hàm kiểm tra domain thực sự có phải hwood.vn không (tránh bắt nhầm đối thủ)
            function isHwoodHost(u) {
                if (!u) return false;
                try {
                    const parsed = new URL(u.startsWith('http') ? u : 'https://' + u.replace(/^\/+/, ''));
                    const host = parsed.hostname.toLowerCase().replace(/^www\./, '');
                    return host === 'hwood.vn' || host.endsWith('.hwood.vn');
                } catch(e) {
                    const m = u.toLowerCase().match(/^(?:https?:\/\/)?(?:www\.)?([^\/:?#]+)/);
                    return m ? (m[1] === 'hwood.vn' || m[1].endsWith('.hwood.vn')) : false;
                }
            }

            // Quét tất cả các khối kết quả xuất hiện trên trang, lọc sạch để tránh trùng lặp giữa card cha và con
            const rawCards = Array.from(document.querySelectorAll('[data-attrid*="overview"], [aria-label*="AI"], .c2xzTb, .xpdopen, div.MjjYud, div.g, div.tF2Cxc'));
            const cards = [];
            rawCards.forEach(c => {
                if (cards.some(other => other.contains(c))) return;
                cards.push(c);
            });

            let pos = 0;
            cards.forEach(card => {
                // Bỏ qua các khối ô tìm kiếm, form nhập liệu, quảng cáo (Sponsored) hoặc People Also Ask
                if (card.querySelector('input, textarea, form, [role="search"]')) return;
                if (card.closest('#tads, #bottomads, [data-text-ad], [aria-label="Ads"]') || card.matches('[data-text-ad]')) return;
                if (card.closest('.related-question-pair, [data-initq]') || card.matches('.related-question-pair')) return;
                const cardTextRaw = (card.innerText || '').trim();
                if (cardTextRaw.startsWith('Bạn nói:') || cardTextRaw.includes('Tìm kiếm có liên quan')) return;
                if (/^(Được tài trợ|Sponsored|Quảng cáo)\b/i.test(cardTextRaw)) return;

                const links = Array.from(card.querySelectorAll('a'));
                if (links.length === 0) return;

                const citeEl = card.querySelector('cite');
                const citeText = (citeEl ? citeEl.innerText : '').toLowerCase();

                // Hàm lọc URL HWOOD chuẩn: phân tách bài viết thật vs trang chủ
                function isRealHwoodArticle(u) {
                    if (!isHwoodHost(u)) return false;
                    const clean = u.replace(/^https?:\/\//i, '').replace(/^www\./i, '').split('?')[0].split('#')[0].replace(/\/+$/, '');
                    return clean !== 'hwood.vn' && clean.length > 'hwood.vn'.length;
                }

                function isBareHwoodHome(u) {
                    if (!isHwoodHost(u)) return false;
                    const clean = u.replace(/^https?:\/\//i, '').replace(/^www\./i, '').split('?')[0].split('#')[0].replace(/\/+$/, '');
                    return clean === 'hwood.vn';
                }

                let articleUrl = '';
                let articleAnchor = null;
                let homeUrl = '';
                let homeAnchor = null;

                // 1. Quét từ tiêu đề h3 hoặc role='heading' (đây là vị trí bài viết thật 100%)
                const headingEl = card.querySelector('h3, [role="heading"]');
                let headingA = null;
                let headingUrl = '';
                if (headingEl) {
                    headingA = headingEl.closest('a') || headingEl.querySelector('a') || (headingEl.parentElement ? headingEl.parentElement.closest('a') : null);
                    if (headingA) {
                        headingUrl = cleanGoogleUrl(headingA.href || headingA.getAttribute('href') || headingA.getAttribute('data-url') || '');
                    }
                }

                if (headingUrl && headingUrl.toLowerCase().includes('hwood.vn')) {
                    if (isRealHwoodArticle(headingUrl)) {
                        articleUrl = headingUrl;
                        articleAnchor = headingA;
                    } else if (isBareHwoodHome(headingUrl)) {
                        homeUrl = 'https://hwood.vn';
                        homeAnchor = headingA;
                    }
                }

                // 2. Quét qua các link khác nếu tiêu đề h3 chưa có link trực tiếp
                if (!articleUrl && !homeUrl) {
                    for (let a of links) {
                        let u = cleanGoogleUrl(a.href || a.getAttribute('href') || a.getAttribute('data-url') || '');
                        if (isRealHwoodArticle(u)) {
                            if (!articleUrl) {
                                articleUrl = u;
                                articleAnchor = a;
                            }
                        } else if (isBareHwoodHome(u)) {
                            if (!homeUrl) {
                                homeUrl = 'https://hwood.vn';
                                homeAnchor = a;
                            }
                        }
                    }
                }

                // Nhận diện HWOOD chính xác theo domain URL hoặc thẻ <cite> (không bắt theo chữ 'hwood' trong văn bản của đối thủ)
                const isCardHwood = Boolean(articleUrl || homeUrl)
                    || /(?:^|[\s\/.])hwood\.vn\b/i.test(citeText);

                let bestLink = null;
                let bestUrl = '';
                let bestIsHwood = false;

                if (isCardHwood) {
                    bestIsHwood = true;
                    if (articleUrl) {
                        bestUrl = articleUrl;
                        bestLink = articleAnchor || (headingEl ? (headingEl.closest('a') || headingEl) : links[0]);
                    } else if (homeUrl) {
                        bestUrl = homeUrl;
                        bestLink = homeAnchor || links[0];
                    } else {
                        // Thử quét lại toàn bộ link thẻ a
                        for (let a of links) {
                            let u = cleanGoogleUrl(a.href || a.getAttribute('href') || a.getAttribute('data-url') || '');
                            if (isHwoodHost(u)) {
                                if (isRealHwoodArticle(u)) {
                                    bestUrl = u;
                                    bestLink = a;
                                    break;
                                } else if (!bestUrl && isBareHwoodHome(u)) {
                                    bestUrl = 'https://hwood.vn';
                                    bestLink = a;
                                }
                            }
                        }
                        // Nếu Google dùng mã hóa link (/goto?url=CAES...) nhưng thẻ chắc chắn là HWOOD:
                        // Tuyệt đối KHÔNG bỏ qua! Gán bestLink vào tiêu đề bài viết và lấy URL từ cite hoặc fallback
                        if (!bestUrl) {
                            bestLink = (headingEl ? (headingEl.closest('a') || headingEl) : null) || links[0];
                            let citeMatch = citeText.match(/hwood\.vn(?:\s*[›>]\s*([a-z0-9-]+))?/i);
                            if (citeMatch && citeMatch[1] && !['website', 'kiểm', 'duyệt', 'kiem-duyet'].some(x => citeMatch[1].includes(x))) {
                                bestUrl = 'https://hwood.vn/' + citeMatch[1] + '/';
                            } else {
                                bestUrl = 'https://hwood.vn';
                            }
                        }
                    }
                } else {
                    for (let a of links) {
                        let u = cleanGoogleUrl(a.href || a.getAttribute('href') || '');
                        if (!u || !u.startsWith('http')) continue;
                        if (ignoreHosts.some(x => u.includes(x))) continue;
                        bestLink = a;
                        bestUrl = u;
                        break;
                    }
                }

                if (!bestUrl) return;
                if (seenUrls.has(bestUrl)) return;
                seenUrls.add(bestUrl);
                pos += 1;

                let sType = 'organic';
                let sLabel = `Top ${pos}`;
                if (card.closest('[data-attrid*="overview"], [aria-label*="AI"]') || card.matches('[data-attrid*="overview"], [aria-label*="AI"]')) {
                    sType = 'ai_overview';
                    sLabel = '🏆 AI Overview';
                } else if (card.closest('.c2xzTb, [data-attrid*="featured"]') || card.matches('.c2xzTb, [data-attrid*="featured"]')) {
                    sType = 'featured_snippet';
                    sLabel = '💎 Top 0 Featured';
                }

                let heading = card.querySelector('h3, [role="heading"]');
                let title = heading ? heading.innerText.trim() : (bestLink && bestLink.innerText ? bestLink.innerText : bestUrl).trim().split('\n')[0];
                if (!title || title.length < 3) title = bestIsHwood ? 'HWOOD Việt Nam' : bestUrl;

                if (bestIsHwood && bestUrl) {
                    card.setAttribute('data-bot-hwood-card', 'true');
                    if (bestLink) {
                        bestLink.setAttribute('data-bot-hwood-target', 'true');
                        bestLink.setAttribute('data-bot-url', bestUrl);
                    }
                    if (heading) {
                        heading.setAttribute('data-bot-hwood-target', 'true');
                        heading.setAttribute('data-bot-url', bestUrl);
                        const headingParentA = heading.closest('a');
                        if (headingParentA) {
                            headingParentA.setAttribute('data-bot-hwood-target', 'true');
                            headingParentA.setAttribute('data-bot-url', bestUrl);
                        }
                    }
                }

                results.push({
                    position: pos,
                    title: title,
                    url: bestUrl,
                    source_type: sType,
                    source_label: sLabel,
                    is_hwood: bestIsHwood
                });
            });

            // 3. Quét dự phòng toàn bộ các liên kết hwood.vn còn lại trên trang (đảm bảo không bao giờ bỏ sót, trừ quảng cáo)
            document.querySelectorAll('a').forEach(a => {
                if (a.closest('#tads, #bottomads, [data-text-ad], [aria-label="Ads"]')) return;
                let u = cleanGoogleUrl(a.href || a.getAttribute('href') || a.getAttribute('data-url') || '');
                if (!isHwoodHost(u)) return;
                if (seenUrls.has(u)) return;
                seenUrls.add(u);
                pos += 1;
                let title = (a.innerText || a.getAttribute('aria-label') || u).trim().split('\n')[0];
                a.setAttribute('data-bot-fallback-link', 'true');
                a.setAttribute('data-bot-url', u);
                results.push({
                    position: pos,
                    title: title || 'HWOOD Việt Nam',
                    url: u,
                    source_type: 'organic',
                    source_label: `Top ${pos}`,
                    is_hwood: true
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
        """Lọc và ưu tiên sắp xếp: Nhận mọi kết quả được xác định là HWOOD."""
        hwood = [r for r in serp if r.get("is_hwood") or TARGET_DOMAIN in r.get("url", "").lower()]
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
            if "sorry/index" in url or "google.com/sorry" in url:
                return True
            title = (page.title() or "").lower()
            if any(x in title for x in ["sorry...", "unusual traffic", "rất tiếc", "robot"]):
                return True
            # Chỉ kiểm tra form captcha nếu có dấu hiệu trang sorry
            if ("sorry" in url or "sorry" in title) and page.locator("form#captcha-form, [action*='Sorry']").count() > 0:
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

    def _wait_for_pacing_slot(self):
        """Giãn nhịp click chung giữa các bot để giữ đều 1–2 lượt nhấp/phút (~32–55s/lượt)."""
        if not self.steady_pacing or self.pacing_lock is None or self.pacing_state is None:
            return
        gap = random.uniform(32.0, 55.0)
        logged = False
        while not self.stop_event.is_set():
            with self.pacing_lock:
                now = time.time()
                last_ts = self.pacing_state.get("last_click_ts", 0.0)
                wait_s = (last_ts + gap) - now
                if wait_s <= 0:
                    self.pacing_state["last_click_ts"] = now
                    return
            if not logged:
                self._log(f"⏱️ [Nhịp đều] Giãn nhịp ~{int(wait_s)}s để giữ đều 1–2 nhấp/phút...")
                self._write_progress("waiting", f"Giãn nhịp đều (~{int(wait_s)}s)")
                logged = True
            time.sleep(min(0.5, max(0.1, wait_s)))

    def _visit_hwood_page(self, page, result: Dict):
        """Click vào kết quả hwood.vn (AI Overview, Cụm hình ảnh, hay Organic) để tăng traffic chuẩn Google."""
        self._wait_for_pacing_slot()
        if self.stop_event.is_set():
            return
        source_type = result.get("source_type", "organic")
        source_label = result.get("source_label", f"Top {result.get('position', '?')}")
        target_url = result.get("url", "")
        if not target_url.startswith("http"):
            target_url = f"https://hwood.vn/{target_url.lstrip('/')}"
        
        # Đảm bảo target_url thuộc domain hwood.vn và không dính badge "kiểm duyệt" của Google
        if TARGET_DOMAIN not in target_url.lower() or any(x in target_url.lower() for x in ["kiểm", "duyệt", "kiem-duyet", "kiemduyet"]):
            target_url = "https://hwood.vn"

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

            # 2. Tìm phần tử HWOOD trên DOM theo độ ưu tiên tuyệt đối:
            target_locator = None
            candidate_selectors = []

            # Ưu tiên số 1: Tìm chính xác phần tử có slug hoặc data-bot-url của bài viết
            if slug:
                candidate_selectors.extend([
                    f"a[data-bot-url*='{slug}']",
                    f"h3[data-bot-url*='{slug}']",
                    f"a[href*='{slug}']:has(h3)",
                    f"h3:has(a[href*='{slug}'])",
                    f"div.MjjYud:has(a[href*='{slug}']) h3",
                    f"div.g:has(a[href*='{slug}']) h3",
                    f"a[href*='{slug}']",
                ])
            else:
                candidate_selectors.extend([
                    "a[data-bot-url='https://hwood.vn']",
                    "h3[data-bot-url='https://hwood.vn']",
                    "a:has(h3)[href*='hwood.vn']",
                    "div.MjjYud:has-text('hwood.vn') a:has(h3)",
                    "div.g:has-text('hwood.vn') a:has(h3)",
                ])

            # Ưu tiên số 2: Các thẻ đã được tag chính xác trong lượt quét
            candidate_selectors.extend([
                f"a[data-bot-url='{target_url}']",
                f"a[href*='{clean_target}']",
                "[data-bot-hwood-target='true']:has(h3)",
                "h3[data-bot-hwood-target='true']",
                "[data-bot-hwood-target='true']",
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

            # 3. Nếu tìm thấy phần tử trên màn hình: Cuộn mượt tới, Highlight nổi bật rồi Click
            if target_locator is not None:
                try:
                    target_locator.scroll_into_view_if_needed(timeout=2500)

                    # Tự động đọc URL thực tế từ thẻ liên kết chuẩn bị click để tránh bị kẹt ở trang chủ
                    try:
                        href_attr = page.evaluate("""(el) => {
                            if (!el) return '';
                            const a = el.closest('a') || el.querySelector('a') || el;
                            let raw = a.href || a.getAttribute('href') || a.getAttribute('data-url') || a.getAttribute('data-bot-url') || '';
                            if (raw.includes('/goto?') || raw.includes('/goto/')) {
                                const gm = raw.match(/[?&]url=([A-Za-z0-9_-]+)/i);
                                if (gm && gm[1]) {
                                    try {
                                        let b64 = gm[1].replace(/-/g, '+').replace(/_/g, '/');
                                        while (b64.length % 4 !== 0) b64 += '=';
                                        const decoded = atob(b64);
                                        const urlMatch = decoded.match(/https?:\\/\\/[^\\s\\x00-\\x1f\\x7f-\\xff]+/i);
                                        if (urlMatch) return urlMatch[0];
                                    } catch(e) {}
                                }
                            }
                            return raw;
                        }""", target_locator.element_handle())
                        if href_attr and TARGET_DOMAIN in href_attr.lower():
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

                    # Bấm chuẩn xác bằng click chuột thật của Playwright trước, fallback sang JS click nếu bị che
                    try:
                        target_locator.click(timeout=3500)
                        clicked = True
                    except Exception:
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
                    # Sử dụng wait_for_timeout để Playwright CDP event loop cập nhật URL và tab mới kịp thời
                    start_wait = time.time()
                    while time.time() - start_wait < 15.0:
                        try:
                            page.wait_for_timeout(400)
                        except Exception:
                            time.sleep(0.4)

                        for p in page.context.pages:
                            p_u = (p.url or "").lower()
                            if TARGET_DOMAIN in p_u and not any(comp in p_u for comp in ["kosmos", "haroma", "anpro", "santot"]):
                                active_page = p
                                try:
                                    active_page.bring_to_front()
                                except Exception:
                                    pass
                                if p != page:
                                    opened_new_tab = True
                                break

                        curr_check = (active_page.url or "").lower()
                        if TARGET_DOMAIN in curr_check:
                            break

                    curr_u = (active_page.url or "").lower()
                    if TARGET_DOMAIN in curr_u:
                        self._log(f"🎉 ĐÃ CLICK THÀNH CÔNG VÀO HWOOD TỪ GOOGLE: {active_page.url[:60]}")
                except Exception as e_click:
                    self._log(f"   ⚠️ Thao tác click DOM ({str(e_click)[:40]}), chuyển sang mở trực tiếp...")
                    clicked = False

            # 4. Fallback an toàn & Đảm bảo giữ nguyên bài viết (TUYỆT ĐỐI CẤM REDIRECT RA TRANG CHỦ)
            try:
                active_page.wait_for_load_state("domcontentloaded", timeout=8000)
            except Exception:
                pass

            curr_url = (active_page.url or "").lower()

            # BẢO VỆ CHẶN ĐỐI THỦ: Nếu mở nhầm trang khác (kosmos, haroma, anpro,...) -> đóng ngay lập tức!
            if any(comp in curr_url for comp in ["kosmos", "haroma", "anpro", "santot"]):
                self._log(f"⛔ Phát hiện mở nhầm trang đối thủ ({curr_url[:35]}), thoát ngay lập tức!")
                try:
                    if opened_new_tab and active_page != page:
                        active_page.close()
                        page.bring_to_front()
                except Exception:
                    pass
                return

            if TARGET_DOMAIN in curr_url:
                # ĐÃ Ở TRONG HWOOD (BÀI VIẾT, SẢN PHẨM HOẶC TRANG MỤC TIÊU):
                # TUYỆT ĐỐI GIỮ NGUYÊN BÀI VIẾT, CẤM GỌI GOTO() HOẶC CHUYỂN HƯỚNG RA TRANG CHỦ!
                self._log(f"✅ Đang đọc đúng bài viết mục tiêu: {active_page.url[:60]}")
            elif TARGET_DOMAIN not in curr_url:
                # Nếu sau 15s vẫn còn kẹt ở Google do click trượt -> mở trực tiếp target_url
                if TARGET_DOMAIN in target_url.lower():
                    self._log(f"   ℹ️ Đang vào trực tiếp bài viết HWOOD: {target_url[:60]}")
                    try:
                        active_page.goto(target_url, timeout=25000)
                        active_page.wait_for_load_state("domcontentloaded", timeout=15000)
                    except Exception:
                        pass
                else:
                    return

        except Exception as e_visit:
            self._log(f"   ❌ Lỗi mở trang hwood: {str(e_visit)[:80]}")
            if TARGET_DOMAIN not in (active_page.url or "").lower():
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
            self._log(f"⏳ Ở lại đọc nội dung & tương tác ~{dwell}s (cuộn chuột, xem sản phẩm như người thật)...")
            elapsed = 0
            explored_next = False

            # Thời điểm chuyển sang xem thêm sản phẩm/menu nav (ở khoảng 35-45% thời gian dwell)
            explore_threshold = int(dwell * random.uniform(0.35, 0.45)) if (self.deep_browse and dwell >= 40) else -1

            while elapsed < dwell and not self.stop_event.is_set():
                chunk = min(random.randint(4, 7), dwell - elapsed)
                time.sleep(chunk)
                elapsed += chunk
                status_label = "Đang xem sản phẩm liên quan" if explored_next else "Đang đọc bài viết"
                self._write_progress("dwelling", f"{status_label}: {elapsed}/{dwell}s (cuộn chuột)")
                if random.random() < 0.65:
                    try:
                        active_page.mouse.wheel(0, random.randint(150, 450))
                    except Exception:
                        pass

                # Khách hàng tương tác sâu: Bấm xem thêm sản phẩm hoặc menu sau khi đọc bài được một lúc
                if self.deep_browse and not explored_next and explore_threshold > 0 and elapsed >= explore_threshold:
                    explored_next = True
                    nav_ok = self._deep_browse_explore(active_page)
                    if nav_ok:
                        self._write_progress("dwelling", f"Đang khám phá sản phẩm: {active_page.url[:40]}")
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

    def _deep_browse_explore(self, active_page) -> bool:
        """
        Mô phỏng hành vi khách hàng thật trên website:
        Sau khi đọc bài viết ban đầu, khách click xem tiếp menu sản phẩm (nav header),
        sản phẩm tương tự/liên quan (related products) hoặc danh mục trên hwood.vn.
        Hành vi này tạo ra multi-page session (>1 pageview), tăng time-on-site và kéo Bounce Rate về 0%.
        """
        try:
            self._log("🛒 [Khách hàng tìm hiểu] Đang tìm menu sản phẩm / sản phẩm liên quan để xem tiếp...")

            # Tìm các link nội bộ hợp lệ trên hwood.vn
            link_info = active_page.evaluate("""() => {
                const currentUrl = window.location.href.split('?')[0].replace(/\\/$/, '');
                const domain = 'hwood.vn';

                const prioritySelectors = [
                    'header a[href*="hwood.vn"]', 'nav a[href*="hwood.vn"]', '.main-nav a', '.menu-item a',
                    '.related a', '.product a', '.products a', '.woocommerce-loop-product__link',
                    '.product-item a', '.box-image a', '.entry-content a[href*="hwood.vn"]'
                ];

                function isValid(a) {
                    if (!a || !a.href) return false;
                    const href = a.href.split('?')[0].replace(/\\/$/, '');
                    if (href === currentUrl) return false;
                    if (!href.includes(domain)) return false;
                    if (href.startsWith('javascript:') || href.startsWith('tel:') || href.startsWith('mailto:')) return false;
                    if (href.includes('#') && href.split('#')[0] === currentUrl) return false;
                    if (/\\.(jpg|jpeg|png|gif|webp|svg|pdf|zip)$/i.test(href)) return false;
                    if (href.includes('wp-admin') || href.includes('wp-login') || href.includes('cart') || href.includes('checkout')) return false;

                    const rect = a.getBoundingClientRect();
                    const style = window.getComputedStyle(a);
                    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                    return (rect.width > 0 && rect.height > 0);
                }

                let candidates = [];
                for (const sel of prioritySelectors) {
                    const els = document.querySelectorAll(sel);
                    for (const el of els) {
                        if (isValid(el)) {
                            const text = (el.innerText || el.getAttribute('title') || '').trim();
                            candidates.push({ href: el.href, text: text.substring(0, 50) });
                        }
                    }
                }

                if (candidates.length === 0) {
                    const allLinks = document.querySelectorAll('a[href*="hwood.vn"]');
                    for (const el of allLinks) {
                        if (isValid(el)) {
                            const text = (el.innerText || el.getAttribute('title') || '').trim();
                            candidates.push({ href: el.href, text: text.substring(0, 50) });
                        }
                    }
                }

                const unique = [];
                const seen = new Set();
                for (const c of candidates) {
                    if (!seen.has(c.href)) {
                        seen.add(c.href);
                        unique.push(c);
                    }
                }
                return unique;
            }""")

            if not link_info or len(link_info) == 0:
                self._log("   ℹ Không tìm thấy link sản phẩm phù hợp khác, tiếp tục tương tác trang hiện tại.")
                return False

            chosen = random.choice(link_info[:8])
            target_href = chosen.get("href", "")
            target_text = chosen.get("text", "") or target_href
            self._log(f"   👉 Bấm xem sản phẩm/trang liên quan: '{target_text[:35]}' ({target_href[:50]})")

            human_sleep(1.0, 2.5)
            try:
                active_page.goto(target_href, timeout=30000, wait_until="domcontentloaded")
                human_sleep(2.0, 3.5)
                random_scroll(active_page, min_scrolls=2, max_scrolls=5)
                return True
            except Exception as eg:
                self._log(f"   ⚠️ Lỗi chuyển trang: {eg}")
                return False
        except Exception as e:
            self._log(f"   ⚠️ Lỗi khi tìm kiếm sản phẩm: {e}")
            return False

    def _click_zalo_conversion(self, active_page):
        """
        Tìm và tương tác nút Zalo OA nếu có trên trang (chỉ bấm nếu mở tab mới hoặc popup,
        tuyệt đối không điều hướng active_page ra khỏi bài viết đang đọc).
        """
        try:
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
                    # Đóng tab zalo mới nếu vừa mở ra
                    if len(active_page.context.pages) > prev_tabs:
                        for p in active_page.context.pages:
                            if p != active_page and "zalo" in (p.url or "").lower():
                                try:
                                    p.close()
                                    active_page.bring_to_front()
                                except Exception:
                                    pass
                                break
                    self._log("   🎉 Đã tương tác Zalo OA thành công mà không rời khỏi bài viết!")
            else:
                self._log("   ℹ️ Trang không có nút Zalo OA trực tiếp, hoàn tất đọc bài tự nhiên.")
        except Exception as e_z:
            self._log(f"   ℹ️ Bỏ qua tương tác Zalo: {str(e_z)[:40]}")

    def run(self):
        from playwright.sync_api import sync_playwright
        import urllib.parse
        self._write_progress("starting", "Khởi động trình duyệt")

        if self.start_delay > 0:
            self._write_progress("waiting", f"Chờ khởi động lệch pha ({int(self.start_delay)}s)")
            self._log(f"⏱️ [Nhịp đều] Khởi động lệch pha sau {int(self.start_delay)}s...")
            waited = 0.0
            while waited < self.start_delay and not self.stop_event.is_set():
                time.sleep(min(0.5, self.start_delay - waited))
                waited += 0.5

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
                        "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
                        "--enforce-webrtc-ip-permission-check",
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
                        # Chống lộ dấu vân tay WebDriver & khóa rò rỉ IP thật qua WebRTC trên toàn bộ tab
                        ctx.add_init_script("""
                            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                            (function() {
                                const OrigRTC = window.RTCPeerConnection || window.webkitRTCPeerConnection || window.mozRTCPeerConnection;
                                if (!OrigRTC) return;
                                const WrappedRTC = function(config, constraints) {
                                    if (config && Array.isArray(config.iceServers)) {
                                        config = Object.assign({}, config, { iceServers: [] });
                                    }
                                    const pc = new OrigRTC(config, constraints);
                                    const origAddEvent = pc.addEventListener.bind(pc);
                                    pc.addEventListener = function(type, listener, options) {
                                        if (type === 'icecandidate' && typeof listener === 'function') {
                                            const wrappedListener = function(ev) {
                                                if (ev && ev.candidate && ev.candidate.candidate &&
                                                    (ev.candidate.candidate.includes('typ host') || ev.candidate.candidate.includes('typ srflx'))) {
                                                    return;
                                                }
                                                return listener.apply(this, arguments);
                                            };
                                            return origAddEvent(type, wrappedListener, options);
                                        }
                                        return origAddEvent(type, listener, options);
                                    };
                                    return pc;
                                };
                                WrappedRTC.prototype = OrigRTC.prototype;
                                window.RTCPeerConnection = WrappedRTC;
                                if (window.webkitRTCPeerConnection) window.webkitRTCPeerConnection = WrappedRTC;
                            })();
                        """)
                        pg = ctx.new_page()
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
                            for page_num in range(1, self.max_pages + 1):
                                self._write_progress("running", f"Đang tìm kiếm '{TARGET_DOMAIN}' trên Google (Trang {page_num})...")

                                # 1. Quét ngay vị trí đầu trang (bắt ngay Top 1, 2, 3, AI Overview, Featured Snippet)
                                serp = self._extract_serp_results(page)
                                hwood_hits = self._find_hwood_results(serp)

                                # 2. Nếu chưa thấy ở ngay đầu trang (Top 1, 2, 3):
                                # Cuộn nhẹ xuống từ từ như người thật để quét tiếp các kết quả bên dưới
                                if not hwood_hits:
                                    for _ in range(4):
                                        page.mouse.wheel(0, random.randint(350, 500))
                                        human_sleep(0.7, 1.3)
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

                                # Nếu chưa thấy: cuộn thêm hoặc bấm chuyển trang nếu có nút Next
                                if page_num < self.max_pages:
                                    try:
                                        page.mouse.wheel(0, 800)
                                        human_sleep(1.0, 1.8)
                                        next_btn = page.locator("#pnnext, a#pnnext, a[aria-label*='Next'], a[aria-label*='Tiếp'], [jsname='TeSSvd']")
                                        if next_btn.count() > 0 and next_btn.first.is_visible():
                                            next_btn.first.scroll_into_view_if_needed(timeout=3000)
                                            human_sleep(0.8, 1.5)
                                            next_btn.first.click(timeout=5000)
                                            human_sleep(2.0, 3.5)
                                            if not self._handle_captcha_if_needed(page, keyword):
                                                break
                                        else:
                                            # Hỗ trợ giao diện cuộn vô tận của Google
                                            page.mouse.wheel(0, 1000)
                                            human_sleep(1.5, 2.5)
                                    except Exception:
                                        pass

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
    dwell_min: int = 60,
    dwell_max: int = 90,
    visit_pages: bool = True,
    deep_browse: bool = True,
    headless: bool = False,
    click_zalo: bool = False,
    delay_between_min: int = 8,
    delay_between_max: int = 15,
    steady_pacing: bool = False,
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
    pacing_lock = threading.Lock()
    pacing_state = {"last_click_ts": 0.0}
    bots = []
    for idx, cfg in enumerate(danh_sach_bot):
        s_delay = (idx * random.uniform(22.0, 35.0)) if (steady_pacing and idx > 0) else 0.0
        bot = BotWorker(
            config=cfg,
            keyword_queue=kw_queue,
            result_store=store,
            max_pages=max_pages,
            dwell_min=dwell_min,
            dwell_max=dwell_max,
            visit_pages=visit_pages,
            deep_browse=deep_browse,
            headless=headless,
            click_zalo=click_zalo,
            delay_between_min=delay_between_min,
            delay_between_max=delay_between_max,
            stop_event=stop_event,
            steady_pacing=steady_pacing,
            start_delay=s_delay,
            pacing_state=pacing_state,
            pacing_lock=pacing_lock,
        )
        bots.append(bot)

    print("=" * 60)
    print(f"🤖 KHỞI CHẠY {len(bots)} BOT | {len(unique_kw)} TỪ KHÓA | Quét tới trang {max_pages}")
    print("=" * 60)
    for b in bots:
        b.start()
        human_sleep(0.5, 1.5)  # Khởi động lệch pha, không mở 5 cửa sổ cùng lúc

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
