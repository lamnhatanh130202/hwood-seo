# 🚀 HƯỚNG DẪN CÀI ĐẶT & SỬ DỤNG HWOOD SEO TRÊN MÁY TÍNH MỚI

Phần mềm này có thể chạy trên **bất kỳ máy tính Windows nào** (máy ở nhà, máy cơ quan, laptop cá nhân).  
Bạn chỉ cần thực hiện các bước đơn giản dưới đây:

---

## 📌 BƯỚC 1: Cài đặt Python (Nếu máy chưa có)

1. Tải bản Python mới nhất cho Windows tại:  
   👉 **[https://www.python.org/downloads/](https://www.python.org/downloads/)**
2. Mở file cài đặt `.exe` vừa tải về.
3. ⚠️ **LƯU Ý CỰC KỲ QUAN TRỌNG:**  
   Ở màn hình cài đặt đầu tiên, bạn **BẮT BUỘC PHẢI TÍCH CHỌN** vào ô:  
   **`☑ Add Python to PATH`** (hoặc `Add python.exe to PATH`) ở góc dưới cùng màn hình!
4. Nhấn **Install Now** và đợi 30 giây cho đến khi hoàn tất.

---

## 📌 BƯỚC 2: Cài Đặt Môi Trường Tự Động (Chỉ làm 1 lần duy nhất)

1. Mở thư mục phần mềm `aicode`.
2. Tìm và **nhấp đúp chuột vào file**:  
   👉 **`CAI_DAT_LAN_DAU.bat`**
3. Cửa sổ màu đen sẽ tự động:
   - Nâng cấp `pip`.
   - Cài đặt đầy đủ các thư viện trong `requirements.txt` (`streamlit`, `playwright`, `openai`, `requests`,...).
   - Tải và cài đặt trình duyệt Chromium cho tính năng **5 Bot Quét Thứ Hạng**.
4. Khi màn hình hiện thông báo **`CAI DAT HOAN TAT!`**, bạn có thể bấm bất kỳ phím nào để đóng lại.

---

## 📌 BƯỚC 3: Mở Ứng Dụng Hàng Ngày

Mỗi ngày khi muốn sử dụng ứng dụng, bạn chỉ cần:
- **Cách 1 (Khuyên dùng):** Nhấp đúp chuột vào file **`CHAY_APP.bat`**
- **Cách 2:** Nhấp đúp chuột vào file **`chay_app.py`**
- Trình duyệt web sẽ tự động mở trang ứng dụng tại địa chỉ:  
  🌐 **`http://localhost:8501`**

---

## 🛠️ Xử Lý Sự Cố Thường Gặp

| Hiện tượng | Nguyên nhân | Cách khắc phục |
| :--- | :--- | :--- |
| Bấm `CHAY_APP.bat` bị tắt ngay | Máy tính chưa có Python hoặc chưa tích chọn `Add Python to PATH` | Cài lại Python theo Bước 1 và nhớ **tích chọn ô Add Python to PATH**. |
| Báo lỗi `No module named ...` | Chưa cài đặt các thư viện cần thiết | Nhấp đúp vào file `CAI_DAT_LAN_DAU.bat` để hệ thống tự cài lại. |
| Bot quét thứ hạng báo thiếu trình duyệt | Chưa tải Chromium cho Playwright | Bấm chạy `CAI_DAT_LAN_DAU.bat` hoặc mở CMD gõ: `playwright install chromium`. |
