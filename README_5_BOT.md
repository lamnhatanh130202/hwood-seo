# 🤖 HƯỚNG DẪN CÀI ĐẶT HỆ THỐNG 5 BOT QUÉT THỨ HẠNG GOOGLE

> **Tất cả file trong gói này đều là FILE MỚI — không ghi đè, không thay thế file cũ nào của dự án aicode.**
> Bạn chỉ cần copy các file vào đúng vị trí và thêm 3 dòng vào `app.py`.

---

## 📦 Các file mới cần copy vào thư mục `aicode/`

| File | Copy vào vị trí |
|---|---|
| `modules/bot_farm.py` | `aicode/modules/bot_farm.py` |
| `tabs/tab8_bot_farm.py` | `aicode/tabs/tab8_bot_farm.py` |
| `run_bot_farm.py` | `aicode/run_bot_farm.py` |
| `bot_proxies.json.example` | `aicode/bot_proxies.json.example` (file mẫu) |
| `README_5_BOT.md` | `aicode/README_5_BOT.md` (tài liệu này) |

---

## 1️⃣ Cài đặt thư viện (chạy 1 lần trong Terminal/CMD)

```bash
pip install playwright playwright-stealth
playwright install chromium
```

> Nếu lỗi `playwright` không tìm thấy, dùng: `python -m playwright install chromium`

---

## 2️⃣ Thêm Tab mới vào `app.py` (chỉ THÊM, không sửa dòng cũ)

Mở `app.py`, thực hiện đúng 3 bước sau:

**Bước A — Thêm import (tìm chỗ các dòng `from tabs.tab7_... import ...`, thêm dòng này bên dưới):**
```python
from tabs.tab8_bot_farm import render_tab8
```

**Bước B — Thêm tên tab vào danh sách `st.tabs([...])`:**
Tìm đoạn:
```python
tab_viet_moi, tab_kham_bai_cu, tab_ma_tran_kw, tab_rank_tracker, tab_ke_hoach_thang, tab_chat_advisor, tab_lich_su = st.tabs([
    "✍️ Viết Bài Mới", 
    "🔍 Sửa Bài Cũ / WP", 
    "📊 Ma Trận Keyword", 
    "🎯 Thứ Hạng Google", 
    "📅 Kế Hoạch Tháng", 
    "💬 Cố Vấn & Lỗi Sai", 
    "📚 Lịch Sử Bài Lưu"
])
```
Thêm biến và tên tab mới thành:
```python
tab_viet_moi, tab_kham_bai_cu, tab_ma_tran_kw, tab_rank_tracker, tab_ke_hoach_thang, tab_chat_advisor, tab_lich_su, tab_bot_farm = st.tabs([
    "✍️ Viết Bài Mới", 
    "🔍 Sửa Bài Cũ / WP", 
    "📊 Ma Trận Keyword", 
    "🎯 Thứ Hạng Google", 
    "📅 Kế Hoạch Tháng", 
    "💬 Cố Vấn & Lỗi Sai", 
    "📚 Lịch Sử Bài Lưu",
    "🤖 5 Bot Quét Thứ Hạng"
])
```

**Bước C — Thêm khối render tab (thêm ở cuối, sau khối `with tab_lich_su:`):**
```python
with tab_bot_farm:
    render_tab8()
```

Xong! Chạy lại `streamlit run app.py` sẽ thấy tab **🤖 5 Bot Quét Thứ Hạng** ở cuối.

---

## 3️⃣ Tư vấn Proxy/VPN (quan trọng — bạn hỏi "chưa rõ, cần tư vấn")

### ❌ Cách KHÔNG hoạt động:
- Cài 5 phần mềm VPN khác nhau trên 1 máy → Hệ điều hành chỉ route toàn bộ traffic qua **1 card mạng mặc định**, nên 5 bot vẫn dùng chung 1 IP. Google vẫn thấy 1 người dùng.

### ✅ Cách ĐÚNG & RẺ NHẤT: Dùng PROXY từ tài khoản VPN bạn đã có
Hầu hết nhà cung cấp VPN (**NordVPN, Surfshark, ExpressVPN**...) đều cho phép dùng **SOCKS5/HTTP proxy** với nhiều server khác nhau. Bạn chỉ cần **1 tài khoản VPN** → lấy được **5 địa chỉ proxy với 5 IP khác nhau** (chọn 5 server ở các tỉnh/thành VN khác nhau: Hà Nội, Đà Nẵng, TP.HCM, Cần Thơ, Hải Phòng).

**Ví dụ với Surfshark:**
1. Vào tài khoản Surfshark → mục **VPN Setup** → **Manual setup** → **Proxy**.
2. Lấy thông tin: `host` (vd: `vn-hai.prod.surfshark.com`), `port` (vd: `1080`), `username` & `password` proxy (khác mật khẩu tài khoản).
3. Chọn 5 server khác nhau → điền vào tab **🤖 5 Bot** ở mục `Proxy server` dạng:
   `socks5://vn-hai.prod.surfshark.com:1080` (kèm username/password).

**Ví dụ với NordVPN:** Tương tự, server proxy dạng `socks5://amsterdam.nl.socks.nordhold.net:1080`.

### 💎 Cách tốt nhất (chống phát hiện cao nhất): Residential Proxy
- Nhà cung cấp: **BrightData, Oxylabs, Smartproxy, Proxy-Seller** (có gói VN).
- IP là nhà dân thật → Google gần như không phát hiện bot.
- Mua 5 endpoint (hoặc 1 endpoint có xoay IP tự động) → điền vào cấu hình.

> Nếu chưa có proxy, bạn vẫn chạy được: để trống `Proxy server` → 5 bot dùng chung IP máy (chậm hơn, dễ bị Google chặn captcha hơn). Nên mua proxy để chạy ổn định.

---

## 4️⃣ Cách dùng

### Cách A — Qua giao diện Streamlit (khuyến nghị):
1. Mở tab **🤖 5 Bot Quét Thứ Hạng**.
2. Chọn bộ từ khóa mẫu (Bộ 32/50 từ khóa HWOOD) hoặc nhập tay.
3. Điền 5 proxy (hoặc để trống).
4. Chỉnh cài đặt: quét tới trang 5, thời gian đọc trang 45-90s.
5. Nhấn **🚀 Bắt đầu chạy 5 Bot** → nhấn **🔄 Làm mới tiến độ** để xem.
6. Kết quả hiển thị bảng + tải được file CSV.

### Cách B — Chạy không cần Streamlit (CLI):
1. Tạo file `bot_keywords.txt` (mỗi dòng 1 từ khóa) trong thư mục `aicode/`.
2. Tạo file `bot_proxies.json` (copy từ `bot_proxies.json.example`, điền proxy).
3. Chạy: `python run_bot_farm.py`
4. Kết quả: `lich_su_bot_farm.json`, tiến độ: `bot_farm_progress.json`.

---

## 5️⃣ Cách hệ thống hoạt động (đúng yêu cầu của bạn)

- ✅ 5 bot chạy **độc lập song song**, mỗi bot 1 trình duyệt + 1 IP riêng.
- ✅ Danh sách từ khóa **dùng chung**, xáo trộn ngẫu nhiên, mỗi bot lấy 1 từ khóa → tra → lấy tiếp, **đến khi hết** thì dừng.
- ✅ Mỗi lần tra: gõ từ khóa như người thật (trễ giữa các phím), quét **trang 1 → trang 5** (tối đa 50 kết quả).
- ✅ Tìm URL chứa `hwood.vn` (bài viết, trang sản phẩm) → ghi nhận **vị trí Top mấy + trang mấy**.
- ✅ Nếu thấy → **click vào kết quả cao nhất**, cuộn trang đọc nội dung, **ở lại 45-90 giây ngẫu nhiên** (có cuộn xen kẽ), rồi quay lại tra tiếp.
- ✅ Nếu không thấy đến trang 5 → đánh dấu **"Ngoài Top 50"**, bỏ qua, tra từ khóa tiếp theo.
- ✅ Hành vi ngẫu nhiên (delay, scroll, gõ phím, viewport, user-agent khác nhau mỗi bot) → giảm nguy cơ Google phát hiện.

---

## ⚠️ Lưu ý quan trọng (đọc kỹ)

1. **Rủi ro thao túng CTR:** Việc click + ở lại trang (dwell time) ở quy mô bot lớn có thể bị Google xem là gian lận nhấp chuột và **phạt website (hạ hạng hoặc xóa khỏi index)**. Công cụ này được xây dựng CHÍNH để **KIỂM TRA THỨ HẠNG và XÁC MINH NỘI DUNG**. Hãy chạy vừa phải, ưu tiên proxy residential.
2. **Captcha:** Nếu Google hiện captcha, bot đó tự dừng và báo "Bị chặn" → bạn cần đổi proxy khác (IP sạch hơn).
3. **Tốc độ:** Mỗi từ khóa mất ~2-4 phút (gồm thời gian đọc trang). 50 từ khóa / 5 bot ≈ 20-40 phút. Đừng vội tắt giữa chừng — kết quả được ghi liên tục ra file.
4. **Chrome cũ của dự án:** Tab này dùng **Playwright + Chromium** (không dùng Chrome `--dump-dom` cũ) để có thể click, scroll, ở lại trang như người thật. Cả 2 hệ thống song song, không xung đột.

---

## 🛠️ Khắc phục lỗi thường gặp

| Lỗi | Cách xử lý |
|---|---|
| `ModuleNotFoundError: playwright` | Chạy lại: `pip install playwright && playwright install chromium` |
| Bot chạy xong nhưng không có kết quả | Kiểm tra proxy có hoạt động không; thử `headless=False` để xem trình duyệt hiển thị gì |
| Google hiện captcha liên tục | Đổi proxy (IP đã bị gắn cờ); dùng residential proxy |
| `Permission denied` khi ghi file | Chạy Terminal/CMD với quyền Administrator |
