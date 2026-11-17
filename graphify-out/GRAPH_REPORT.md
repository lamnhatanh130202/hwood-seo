# 🧭 BÁO CÁO ĐỒ THỊ TRI THỨC MÃ NGUỒN (CODEBASE KNOWLEDGE GRAPH)

> **Thời gian tạo:** 16/11/2026 08:56:32  
> **Tổng quan:** `33 files` | `10538 dòng code` | `144 hàm` | `6 classes` | `408 liên kết gọi hàm`

---

## 🗂️ 1. Bản Đồ Danh Mục Files & Kiến Trúc

### 📄 `app.py` (426 dòng)
**Các hàm định nghĩa:**
- **`nạp_tri_thuc()`** (dòng 199)

### 📄 `audit_codebase.py` (92 dòng)
**Các hàm định nghĩa:**
- **`check_syntax()`** (dòng 7)
- **`find_undefined_names_ast(filepath)`** (dòng 24) - *Phan tich AST de tim cac bien/ham dung ma khong import hoac khai bao*
- **`check_undefined_variables()`** (dòng 67)

### 📄 `chay_app.py` (59 dòng)
**Các hàm định nghĩa:**
- **`ensure_streamlit_credentials()`** (dòng 5) - *Dam bao khong bi hoi email khi chay Streamlit lan dau tren may moi*
- **`main()`** (dòng 17)

### 📄 `modules/__init__.py` (1 dòng)

### 📄 `modules/ai_engine.py` (522 dòng)
**Các hàm định nghĩa:**
- **`goi_chat_completion_an_toan(client, model)`** (dòng 6) - *Gọi chat completion với cơ chế tương thích thông minh:*
- **`goi_ai_tao_va_noi_bai(client, model, messages, max_tokens, max_loops)`** (dòng 21) - *Gọi AI sinh bài viết với cơ chế TỰ ĐỘNG NỐI TIẾP LIỀN MẠCH (Auto-Continuation) nếu chạm trần token*
- **`viet_tiep_bai_dang_do(noi_dung_dang_do, tu_khoa_bai, api_key, model_name)`** (dòng 72) - *Viết tiếp một bài viết bất kỳ đang bị dừng giữa chừng và nối liền mạch lại với nhau*
- **`kiem_tra_gop_y_toan_dien(yeu_cau_text)`** (dòng 104) - *Tự động phát hiện xem góp ý là danh sách nhiều lỗi (Audit checklist) cần sửa toàn diện bài viết không*
- **`parse_and_apply_patch(original_html, ai_response)`** (dòng 119) - *Bóc tách các khối thay thế <<<THAY_THE>>> để sửa cục bộ với cơ chế so khớp thông minh không phân biệt khoảng trắng*
- **`thuc_hien_tinh_chinh_ai(noi_dung_cu, yeu_cau_text, file_text, tu_khoa_bai, api_key, model_name, img_b64, che_do_sua)`** (dòng 184) - *Gọi AI tinh chỉnh bài viết theo cơ chế thông minh:*
- **`tao_bai_viet_hwood_chuan_seo(tu_khoa, the_loai_bai, do_dai_bai, api_key, chon_model, danh_sach_bai_viet_wp, tieu_de, tu_khoa_phu, ghi_chu_chien_luoc, search_intent, cum_chu_de)`** (dòng 327) - *Hàm tạo bài viết SEO chuẩn toàn diện của HWOOD VIỆT NAM:*

### 📄 `modules/bot_farm.py` (1407 dòng)
**Các hàm định nghĩa:**
- **`append_live_log(log_line)`** (dòng 55) - *Ghi thêm 1 dòng nhật ký vào file live log để giao diện hiển thị realtime.*
- **`doc_live_logs(n, max_lines)`** (dòng 74) - *Đọc n dòng log realtime gần nhất.*
- **`xoa_live_logs()`** (dòng 86)
- **`kiem_tra_proxy_mot_bot(cfg)`** (dòng 166) - *Kiểm tra kết nối và đo độ trễ thực tế của 1 proxy.*
- **`human_sleep(min_s, max_s)`** (dòng 208) - *Ngủ một khoảng ngẫu nhiên để mô phỏng tốc độ đọc/nhìn của người thật.*
- **`random_scroll(page, min_scrolls, max_scrolls)`** (dòng 213) - *Cuộn trang từng đoạn với tốc độ ngẫu nhiên, giống người đọc nội dung.*
- **`type_like_human(page, selector, text)`** (dòng 221) - *Gõ từng ký tự với độ trễ ngẫu nhiên, không dán nguyên khối.*
- **`doc_proxy_config()`** (dòng 231) - *Đọc cấu hình 5 proxy từ file bot_proxies.json (nếu có).*
- **`chay_5_bot(danh_sach_tu_khoa, danh_sach_bot, max_pages, dwell_min, dwell_max, visit_pages, headless, click_zalo, delay_between_min, delay_between_max)`** (dòng 1312) - *Khởi chạy 5 bot song song. Trả về (danh_sach_ket_qua, danh_sach_thread_bot).*
- **`doc_tien_do()`** (dòng 1388) - *Đọc tiến độ các bot từ file an toàn (với retry chống xung đột trên Windows).*
- **`doc_ket_qua()`** (dòng 1400)
- **`proxy_dict(self)`** (dòng 136)
- **`__init__(self)`** (dòng 256)
- **`_load(self)`** (dòng 261)
- **`add(self, record)`** (dòng 269)
- **`all(self)`** (dòng 275)
- **`__init__(self, config, keyword_queue, result_store, max_pages, dwell_min, dwell_max, visit_pages, headless, click_zalo, delay_between_min, delay_between_max, stop_event)`** (dòng 284)
- **`_log(self, msg)`** (dòng 316)
- **`_write_progress(self, status, detail)`** (dòng 322) - *Ghi tiến độ hiện tại an toàn tuyệt đối đa luồng và đa tiến trình (tránh khóa file trên Windows).*
- **`_extract_serp_results(self, page)`** (dòng 348) - *Trích xuất toàn diện kết quả tìm kiếm Google: AI Overview, Featured Snippet, Cụm hình ảnh và Organic (bắt chính xác Top 1, 2, 3).*
- **`_find_hwood_results(self, serp)`** (dòng 528) - *Lọc và ưu tiên sắp xếp: Nhận mọi kết quả được xác định là HWOOD.*
- **`_is_403(self, page)`** (dòng 543) - *Kiểm tra xem trang có bị lỗi 403 Forbidden của Google không (hình robot vặn cờ lê).*
- **`_recover_from_403(self, page, keyword)`** (dòng 560) - *Tự động xử lý khi Google trả về lỗi 403 Forbidden (hình người máy bị hỏng):*
- **`_is_blocked(self, page)`** (dòng 594) - *Kiểm tra chính xác trang có thực sự bị chặn CAPTCHA hoặc 403 bởi Google hay không.*
- **`_handle_captcha_if_needed(self, page, keyword)`** (dòng 612) - *Kiểm tra và xử lý khi gặp CAPTCHA:*
- **`_accept_consent_if_needed(self, page)`** (dòng 700) - *Nhấn nút đồng ý cookie/điều khoản nếu Google hiện lên.*
- **`_visit_hwood_page(self, page, result)`** (dòng 712) - *Click vào kết quả hwood.vn (AI Overview, Cụm hình ảnh, hay Organic) để tăng traffic chuẩn Google.*
- **`_click_zalo_conversion(self, active_page)`** (dòng 941) - *Tìm và click nút Zalo trong bài viết hoặc icon Zalo nổi ở góc dưới bên phải.*
- **`run(self)`** (dòng 1079)
- **`rank_score(item)`** (dòng 534)
- **`_create_browser_session(use_proxy_dict)`** (dòng 1099)

### 📄 `modules/chat_advisor.py` (150 dòng)
**Các hàm định nghĩa:**
- **`doc_quy_chuan_chung()`** (dòng 18) - *Đọc bộ quy chuẩn & lưu ý lỗi sai chung của thương hiệu HWOOD*
- **`luu_quy_chuan_chung(danh_sach_quy_chuan)`** (dòng 32) - *Lưu danh sách quy chuẩn vào file JSON*
- **`lay_noi_dung_quy_chuan_cho_prompt()`** (dòng 42) - *Trả về chuỗi text quy chuẩn chung để gắn vào System Prompt mọi bài viết*
- **`doc_lich_su_chat_advisor()`** (dòng 50) - *Đọc toàn bộ lịch sử tin nhắn trong khung chat chiến lược*
- **`luu_lich_su_chat_advisor(messages)`** (dòng 60) - *Lưu lịch sử chat vào file JSON*
- **`xoa_lich_su_chat_advisor()`** (dòng 69) - *Xóa lịch sử chat để bắt đầu phiên mới*
- **`gui_tin_nhan_advisor(api_key, model, messages, file_context, kho_tri_thuc)`** (dòng 77) - *Gửi tin nhắn trong cuộc trò chuyện chiến lược SEO HWOOD*
- **`ai_trich_xuat_quy_chuan_tu_chat(api_key, model, messages_history)`** (dòng 114) - *AI phân tích cuộc trò chuyện gần nhất để tự động rút ra các nguyên tắc mới cần thêm vào quy chuẩn chung*

### 📄 `modules/content_planner.py` (179 dòng)
**Các hàm định nghĩa:**
- **`khoi_tao_thu_muc_plan()`** (dòng 13)
- **`lay_ten_file_plan(thang_nam)`** (dòng 17) - *Tạo tên file theo định dạng ke_hoach_YYYY_MM.json*
- **`lay_ke_hoach_thang(thang_nam)`** (dòng 23) - *Đọc dữ liệu kế hoạch tháng từ file JSON*
- **`luu_ke_hoach_thang(thang_nam, danh_sach_bai)`** (dòng 34) - *Lưu danh sách bài viết trong kế hoạch tháng vào file JSON*
- **`lay_danh_sach_thang_da_co()`** (dòng 44) - *Lấy danh sách các tháng đã có kế hoạch*
- **`tao_ke_hoach_thang_ai(api_key, model, thang_nam, so_bai_tuan, chu_de_trong_tam, ds_wp, kho_tri_thuc)`** (dòng 54) - *Sử dụng DeepSeek để lập kế hoạch biên tập nội dung thông minh cho cả tháng*
- **`xuat_csv_ke_hoach_thang(danh_sach_bai)`** (dòng 146) - *Xuất danh sách bài viết trong kế hoạch tháng ra chuỗi CSV chuẩn UTF-8 BOM cho Excel*

### 📄 `modules/file_handler.py` (471 dòng)
**Các hàm định nghĩa:**
- **`xoa_dau_tieng_viet(text)`** (dòng 13) - *Chuyển chữ tiếng Việt có dấu thành không dấu để so khớp slug và tiêu đề*
- **`doc_noi_dung_file_dinh_kem(uploaded_file)`** (dòng 22) - *Trích xuất nội dung văn bản và thông tin từ file đính kèm (Word, PDF, Text, Ảnh)*
- **`chuan_hoa_bang_html_hwood(html_str)`** (dòng 98) - *Tự động chuẩn hóa toàn bộ các bảng <table> trong bài viết chuẩn giao diện HWOOD:*
- **`xuat_bang_html_ra_csv(html_str)`** (dòng 184) - *Trích xuất tất cả các bảng dữ liệu trong bài viết sang định dạng CSV/Excel với UTF-8 BOM*
- **`tao_file_word_tu_html(html_str, title, meta_title, meta_desc, focus_kw, them_ke_hoach_media)`** (dòng 209) - *Chuyển đổi bài viết HTML sang tài liệu Word (.docx) chuyên nghiệp:*
- **`_replace_table(match)`** (dòng 109)
- **`_chen_noi_dung_inline(p, html_text, base_font_size, default_color)`** (dòng 237) - *Phân tích và giữ nguyên in đậm (strong/b), in nghiêng (em/i) trong đoạn văn Word*

### 📄 `modules/history_manager.py` (81 dòng)
**Các hàm định nghĩa:**
- **`doc_tu_khoa_tuy_chinh()`** (dòng 13) - *Đọc từ điển từ khóa do người dùng tùy chỉnh hoặc gán riêng cho từng bài viết*
- **`luu_tu_khoa_tuy_chinh(pid_or_slug, tu_khoa_moi)`** (dòng 23) - *Lưu từ khóa tùy chỉnh cho bài viết để hiển thị chính xác theo ý muốn*
- **`luu_bai_viet_lich_su(tu_khoa, noi_dung, meta_title, meta_desc, gop_y_note, file_dinh_kem_name)`** (dòng 34) - *Lưu bài viết vào thư mục lịch sử dạng JSON có kèm danh mục sản phẩm và nhật ký góp ý*
- **`lay_danh_sach_lich_su()`** (dòng 66) - *Lấy danh sách các bài viết đã lưu từ trước tới nay (mới nhất lên đầu) kèm phân loại chủ đề*

### 📄 `modules/keyword_matrix.py` (550 dòng)
**Các hàm định nghĩa:**
- **`kiem_tra_tieu_de_rac(tieu_de, pslug)`** (dòng 21) - *Kiểm tra xem tiêu đề hoặc slug có phải là trang quản trị, bài nháp hoặc trang tiện ích không phải keyword SEO không*
- **`trich_xuat_focus_and_secondary_kw(tieu_de, noi_dung, pslug, pid)`** (dòng 105) - *Bóc tách Từ khóa chính (Focus Keyword) và Các từ khóa phụ đi kèm (Secondary/LSI) từ tiêu đề & nội dung chuẩn Yoast SEO*
- **`trich_xuat_danh_sach_keyword_chuan_hwood(danh_sach_bai_viet_wp, ds_ls, che_do, loc_chuyen_muc)`** (dòng 251) - *Trích xuất danh sách từ khóa thực tế chuẩn SEO (Focus & Secondary/LSI) từ các bài viết & sản phẩm trên hwood.vn.*
- **`lay_ma_tran_toan_bo_keyword(ds_wp, ds_ls)`** (dòng 312) - *Tổng hợp ma trận toàn bộ từ khóa chính và phụ từ Website WordPress và Lịch sử lưu trữ (ĐÃ LỌC SẠCH BÀI NHÁP/ADMIN)*
- **`xuat_csv_ma_tran_keyword(danh_sach_matrix)`** (dòng 413) - *Xuất danh sách ma trận từ khóa thành chuỗi CSV chuẩn UTF-8 BOM cho Excel*
- **`goi_y_goc_nhin_tu_khoa_ve_tinh(tu_khoa_goc, danh_sach_bai_viet_wp)`** (dòng 444) - *Rà soát xem từ khóa gốc đã có bài viết trên website chưa,*

### 📄 `modules/knowledge.py` (102 dòng)
**Các hàm định nghĩa:**
- **`viet_hoa_tieu_de(s)`** (dòng 6) - *Viết hoa đầu mỗi từ tiếng Việt mà không bị lỗi dấu*
- **`phan_loai_chu_de(tu_khoa)`** (dòng 12) - *Tự động phân loại bài viết theo danh mục sản phẩm chính thức của HWOOD*
- **`lay_tri_thuc_phu_hop(tu_khoa, current_dir)`** (dòng 34) - *Trích lọc và ưu tiên các tài liệu tri thức HWOOD có độ liên quan cao nhất với từ khóa bài viết*
- **`doc_kho_tri_thuc(current_dir)`** (dòng 85) - *Đọc toàn bộ các tài liệu tri thức .md hiện có trong thư mục*

### 📄 `modules/media_planner.py` (352 dòng)
**Các hàm định nghĩa:**
- **`xoa_hop_placeholder_anh(html_str)`** (dòng 8) - *Làm sạch toàn bộ các hộp placeholder giả lập và ghi chú gợi ý vị trí ảnh khỏi bài viết để tiết kiệm token và làm sạch HTML*
- **`tao_ke_hoach_media_seo(html_str, tu_khoa_chinh, danh_muc)`** (dòng 25) - *Tự động phân tích cấu trúc bài viết HTML để tạo Bảng Kế Hoạch Hình Ảnh & Video chuẩn SEO:*
- **`xuat_csv_ke_hoach_media(ds_media)`** (dòng 150) - *Xuất danh sách kế hoạch media ra định dạng CSV/Excel UTF-8 BOM để mở tiếng Việt không lỗi font*
- **`tao_bang_html_ke_hoach_media(ds_media)`** (dòng 178) - *Tạo bảng HTML chuẩn giao diện thương hiệu HWOOD (Header nền xanh #237a3b, chữ trắng in đậm)*
- **`tao_preview_co_khung_vi_tri_anh(html_str, ds_media)`** (dòng 227) - *Chỉ dùng riêng cho chế độ xem trước trực quan (Preview):*
- **`chen_anh_that_vao_html(html_str, vi_tri_stt, url_anh, the_alt, caption, ds_media)`** (dòng 284) - *Chèn một thẻ <figure><img> thật vào đúng vị trí tương ứng trong bài viết HTML*

### 📄 `modules/rank_tracker.py` (801 dòng)
**Các hàm định nghĩa:**
- **`doc_lich_su_thu_hang()`** (dòng 16)
- **`luu_lich_su_thu_hang(data)`** (dòng 25)
- **`tim_bai_viet_khop_nhat_wp(keyword, danh_sach_bai_viet_wp)`** (dòng 193) - *Tìm trang hoặc bài viết trên website hwood.vn khớp chính xác nhất với từ khóa tìm kiếm (đặc biệt ưu tiên Landing Page con).*
- **`tao_link_google_search(keyword)`** (dòng 268) - *Tạo đường link mở trực tiếp kết quả tìm kiếm Google Việt Nam đã TẮT CÁ NHÂN HÓA HOÀN TOÀN (pws=0)*
- **`nhap_ket_qua_spineditor(van_ban_paste, danh_sach_bai_viet_wp)`** (dòng 274) - *Phân tích văn bản sao chép từ SpinEditor (spineditor.com) hoặc bảng thứ hạng:*
- **`trich_xuat_urls_tu_dom(text)`** (dòng 397) - *Trích xuất danh sách tất cả các URL organic sạch từ DOM rendered của Google*
- **`quet_google_live_chrome(keyword, start)`** (dòng 416) - *Sử dụng Google Chrome chạy ngầm với anti-detection và profile cô lập*
- **`check_thu_hang_google_keyword(keyword, target_domain, danh_sach_bai_viet_wp, max_pages)`** (dòng 454) - *Kiểm tra thứ hạng từ khóa THỰC TẾ trên Google Việt Nam (Top 20 organic)*
- **`xuat_csv_thu_hang(danh_sach_rank)`** (dòng 520) - *Xuất danh sách thứ hạng từ khóa thành chuỗi CSV chuẩn UTF-8 BOM cho Excel*
- **`doc_database_keywords()`** (dòng 548) - *Đọc toàn bộ cơ sở dữ liệu từ khóa đã tra cứu và theo dõi (Tracked Keywords Database)*
- **`luu_database_keywords(data)`** (dòng 591) - *Lưu toàn bộ cơ sở dữ liệu từ khóa theo dõi*
- **`dong_bo_ket_qua_quet_vao_db(danh_sach_ket_qua, danh_sach_bai_viet_wp)`** (dòng 600) - *Tự động đồng bộ kết quả quét Google / SpinEditor vào Cơ sở dữ liệu từ khóa đã tra cứu*
- **`them_tu_khoa_vao_db(danh_sach_tu_khoa, loai, chuyen_muc, danh_sach_bai_viet_wp)`** (dòng 700) - *Thêm danh sách từ khóa vào Database theo dõi*
- **`xoa_tu_khoa_khoi_db(tu_khoa_key)`** (dòng 749) - *Xóa một từ khóa khỏi cơ sở dữ liệu theo dõi*
- **`xuat_csv_database_keywords(db_dict)`** (dòng 760) - *Xuất toàn bộ Cơ sở dữ liệu từ khóa thành CSV chuẩn UTF-8 BOM để mở trong Excel*

### 📄 `modules/wordpress_api.py` (329 dòng)
**Các hàm định nghĩa:**
- **`lay_toan_bo_du_lieu_wp(site_url, api_key, post_type, wp_username)`** (dòng 6) - *Lấy toàn bộ bài viết (posts), trang tĩnh (pages) hoặc sản phẩm (san-pham / product / WooCommerce) từ WordPress REST API.*
- **`lay_tat_ca_noi_dung_wp(site_url, api_key, wp_username)`** (dòng 144) - *Lấy đồng bộ toàn diện Bài viết (posts), Trang tĩnh (pages) và Sản phẩm (san-pham) từ website WordPress*
- **`dang_bai_len_wordpress(site_url, title, content, status, wp_username, api_key, focus_kw, meta_title, meta_desc, slug)`** (dòng 175) - *Đăng bài viết mới lên WordPress với cơ chế xác thực đa tầng và TỰ ĐỘNG ĐIỀN YOAST SEO / RANK MATH:*
- **`cap_nhat_bai_wordpress(site_url, post_id, post_type, title, content, wp_username, api_key)`** (dòng 279) - *Cập nhật bài viết/trang/sản phẩm trên WordPress với cơ chế xác thực đa tầng*
- **`_fetch_endpoint_all_pages(endpoint_template, is_wc)`** (dòng 24)
- **`_gui_yeu_cau(auth_tuple, headers_dict, query_param)`** (dòng 224)

### 📄 `run_bot_farm.py` (118 dòng)
**Các hàm định nghĩa:**
- **`doc_tu_khoa_tu_file()`** (dòng 33)
- **`doc_cai_dat()`** (dòng 52)

### 📄 `scratch_inspect_serp.py` (19 dòng)

### 📄 `scratch_inspect_serp2.py` (51 dòng)
**Các hàm định nghĩa:**
- **`__init__(self)`** (dòng 13)
- **`handle_starttag(self, tag, attrs)`** (dòng 20)
- **`handle_endtag(self, tag)`** (dòng 27)
- **`handle_data(self, data)`** (dòng 32)

### 📄 `scratch_test_bridge.py` (41 dòng)
**Các hàm định nghĩa:**
- **`do_POST(self)`** (dòng 7)
- **`do_OPTIONS(self)`** (dòng 20)
- **`log_message(self, format)`** (dòng 27)

### 📄 `scratch_test_chrome.py` (21 dòng)

### 📄 `scratch_test_google.py` (20 dòng)

### 📄 `scripts/graphify_engine.py` (447 dòng)
**Các hàm định nghĩa:**
- **`__init__(self, root_dir)`** (dòng 25)
- **`should_ignore(self, path)`** (dòng 44)
- **`scan_codebase(self)`** (dòng 54)
- **`analyze_python_file(self, file_path)`** (dòng 64)
- **`build_call_edges(self)`** (dòng 196) - *Xây dựng liên kết gọi hàm giữa các module (call graph)*
- **`export_graph_json(self, out_dir)`** (dòng 211)
- **`export_graph_report_md(self, out_dir)`** (dòng 223)
- **`export_graph_html(self, out_dir)`** (dòng 262) - *Tạo giao diện mạng lưới đồ thị tương tác HTML5 Canvas / SVG có thể zoom, pan, click xem chi tiết*
- **`run(self)`** (dòng 429)

### 📄 `tabs/__init__.py` (1 dòng)

### 📄 `tabs/tab1_viet_moi.py` (889 dòng)
**Các hàm định nghĩa:**
- **`render_soan_thao_thu_cong(ket_noi_wp, wp_site_url, royal_api_key, wp_username)`** (dòng 34) - *Khu vực tự soạn thảo thủ công, dán mã HTML, xem trước trực quan và lưu vào lịch sử bài viết*
- **`render_tab1(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, danh_sach_bai_viet_wp, wp_username)`** (dòng 315) - *Giao diện Tab 1: Viết bài mới chuẩn SEO, xem trước, sửa nhanh bằng tay & góp ý tinh chỉnh bằng AI*

### 📄 `tabs/tab2_kham_bai.py` (490 dòng)
**Các hàm định nghĩa:**
- **`render_tab2(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, kho_tri_thuc, ds_file, wp_username)`** (dòng 12) - *Giao diện Tab 2: Xem & Chỉnh Sửa Trang Sản Phẩm / Bài Viết Trên Website*

### 📄 `tabs/tab3_kiem_toan.py` (256 dòng)
**Các hàm định nghĩa:**
- **`render_tab3(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, danh_sach_bai_viet_wp, kho_tri_thuc)`** (dòng 8) - *Giao diện Tab 3: Bảng Thống Kê & Ma Trận Keyword Đang Sử Dụng*

### 📄 `tabs/tab4_thu_hang.py` (874 dòng)
**Các hàm định nghĩa:**
- **`modal_serp_debug(row, danh_sach_bai_viet_wp)`** (dòng 34)
- **`render_tab4(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, danh_sach_bai_viet_wp)`** (dòng 137) - *Giao diện Tab 4: Kiểm Tra Thứ Hạng Từ Khóa Google (Rank Tracker) & Quản Lý Data Keyword*

### 📄 `tabs/tab5_lich_su.py` (508 dòng)
**Các hàm định nghĩa:**
- **`render_tab5(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, wp_username)`** (dòng 28) - *Giao diện Tab 5: Thư Viện Lịch Sử Bài Viết (Phân Chia Theo Chủ Đề Sản Phẩm)*

### 📄 `tabs/tab6_ke_hoach_thang.py` (297 dòng)
**Các hàm định nghĩa:**
- **`render_tab6(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, danh_sach_bai_viet_wp, kho_tri_thuc)`** (dòng 14) - *Giao diện Tab 6: Lên Kế Hoạch Nội Dung Tháng (Content Editorial Calendar)*

### 📄 `tabs/tab7_chat_chien_luoc.py` (153 dòng)
**Các hàm định nghĩa:**
- **`render_tab7(api_key, chon_model, ket_noi_wp, wp_site_url, royal_api_key, danh_sach_bai_viet_wp, kho_tri_thuc)`** (dòng 13) - *Giao diện Tab 7: Khung Chat Chiến Lược SEO & Quản Lý Quy Chuẩn Lỗi Sai Chung Cho Toàn Bộ Bài Viết*

### 📄 `tabs/tab8_bot_farm.py` (603 dòng)
**Các hàm định nghĩa:**
- **`ghi_file(path, content)`** (dòng 37)
- **`ghi_cau_hinh(keywords_text, proxies, settings)`** (dòng 42)
- **`dang_chay()`** (dòng 57)
- **`dung_bot()`** (dòng 85)
- **`_render_dashboard_content(is_running)`** (dòng 115)
- **`render_realtime_col_run()`** (dòng 325) - *Bảng điều khiển trực tiếp thời gian thực, không dùng @st.fragment để tránh xung đột DOM với st.tabs.*
- **`render_tab8()`** (dòng 351)

### 📄 `test_proxies.py` (69 dòng)
**Các hàm định nghĩa:**
- **`curl_test(proxy_url, test_url)`** (dòng 14) - *Gọi curl qua proxy, trả về (thanh_cong, noi_dung).*
- **`main()`** (dòng 26)

### 📄 `test_suite.py` (159 dòng)
**Các hàm định nghĩa:**
- **`run_tests()`** (dòng 6)

---

## 🔗 2. Sơ Đồ Mối Quan Hệ Gọi Hàm (Key Function Calls)

| Hàm gọi (Caller) | Hàm được gọi (Callee) | Loại liên kết |
| :--- | :--- | :--- |
| `nạp_tri_thuc` (app.py) | `doc_kho_tri_thuc` (modules/knowledge.py) | `calls` |
| `find_undefined_names_ast` (audit_codebase.py) | `add` (modules/bot_farm.py) | `calls` |
| `find_undefined_names_ast` (audit_codebase.py) | `add` (modules/bot_farm.py) | `calls` |
| `find_undefined_names_ast` (audit_codebase.py) | `add` (modules/bot_farm.py) | `calls` |
| `find_undefined_names_ast` (audit_codebase.py) | `add` (modules/bot_farm.py) | `calls` |
| `check_undefined_variables` (audit_codebase.py) | `find_undefined_names_ast` (audit_codebase.py) | `calls` |
| `main` (chay_app.py) | `ensure_streamlit_credentials` (chay_app.py) | `calls` |
| `main` (chay_app.py) | `run` (scripts/graphify_engine.py) | `calls` |
| `main` (chay_app.py) | `run` (scripts/graphify_engine.py) | `calls` |
| `main` (chay_app.py) | `run` (scripts/graphify_engine.py) | `calls` |
| `main` (chay_app.py) | `run` (scripts/graphify_engine.py) | `calls` |
| `__init__` (scratch_inspect_serp2.py) | `__init__` (scripts/graphify_engine.py) | `calls` |
| `curl_test` (test_proxies.py) | `run` (scripts/graphify_engine.py) | `calls` |
| `main` (test_proxies.py) | `curl_test` (test_proxies.py) | `calls` |
| `main` (test_proxies.py) | `curl_test` (test_proxies.py) | `calls` |
| `run_tests` (test_suite.py) | `lay_ma_tran_toan_bo_keyword` (modules/keyword_matrix.py) | `calls` |
| `run_tests` (test_suite.py) | `trich_xuat_danh_sach_keyword_chuan_hwood` (modules/keyword_matrix.py) | `calls` |
| `run_tests` (test_suite.py) | `phan_loai_chu_de` (modules/knowledge.py) | `calls` |
| `run_tests` (test_suite.py) | `viet_hoa_tieu_de` (modules/knowledge.py) | `calls` |
| `run_tests` (test_suite.py) | `doc_lich_su_thu_hang` (modules/rank_tracker.py) | `calls` |
| `run_tests` (test_suite.py) | `doc_database_keywords` (modules/rank_tracker.py) | `calls` |
| `run_tests` (test_suite.py) | `nhap_ket_qua_spineditor` (modules/rank_tracker.py) | `calls` |
| `run_tests` (test_suite.py) | `tao_link_google_search` (modules/rank_tracker.py) | `calls` |
| `run_tests` (test_suite.py) | `doc_proxy_config` (modules/bot_farm.py) | `calls` |
| `run_tests` (test_suite.py) | `kiem_tra_proxy_mot_bot` (modules/bot_farm.py) | `calls` |
| `run_tests` (test_suite.py) | `doc_live_logs` (modules/bot_farm.py) | `calls` |
| `run_tests` (test_suite.py) | `doc_ket_qua` (modules/bot_farm.py) | `calls` |
| `run_tests` (test_suite.py) | `doc_tien_do` (modules/bot_farm.py) | `calls` |
| `run_tests` (test_suite.py) | `lay_danh_sach_lich_su` (modules/history_manager.py) | `calls` |
| `run_tests` (test_suite.py) | `xoa_dau_tieng_viet` (modules/file_handler.py) | `calls` |
| `goi_ai_tao_va_noi_bai` (modules/ai_engine.py) | `chuan_hoa_bang_html_hwood` (modules/file_handler.py) | `calls` |
| `goi_ai_tao_va_noi_bai` (modules/ai_engine.py) | `goi_chat_completion_an_toan` (modules/ai_engine.py) | `calls` |
| `viet_tiep_bai_dang_do` (modules/ai_engine.py) | `lay_tri_thuc_phu_hop` (modules/knowledge.py) | `calls` |
| `viet_tiep_bai_dang_do` (modules/ai_engine.py) | `goi_ai_tao_va_noi_bai` (modules/ai_engine.py) | `calls` |
| `thuc_hien_tinh_chinh_ai` (modules/ai_engine.py) | `lay_tri_thuc_phu_hop` (modules/knowledge.py) | `calls` |
| `thuc_hien_tinh_chinh_ai` (modules/ai_engine.py) | `lay_noi_dung_quy_chuan_cho_prompt` (modules/chat_advisor.py) | `calls` |
| `thuc_hien_tinh_chinh_ai` (modules/ai_engine.py) | `kiem_tra_gop_y_toan_dien` (modules/ai_engine.py) | `calls` |
| `thuc_hien_tinh_chinh_ai` (modules/ai_engine.py) | `goi_ai_tao_va_noi_bai` (modules/ai_engine.py) | `calls` |
| `thuc_hien_tinh_chinh_ai` (modules/ai_engine.py) | `parse_and_apply_patch` (modules/ai_engine.py) | `calls` |
| `thuc_hien_tinh_chinh_ai` (modules/ai_engine.py) | `xoa_hop_placeholder_anh` (modules/media_planner.py) | `calls` |
| `thuc_hien_tinh_chinh_ai` (modules/ai_engine.py) | `chuan_hoa_bang_html_hwood` (modules/file_handler.py) | `calls` |
| `thuc_hien_tinh_chinh_ai` (modules/ai_engine.py) | `goi_chat_completion_an_toan` (modules/ai_engine.py) | `calls` |
| `thuc_hien_tinh_chinh_ai` (modules/ai_engine.py) | `parse_and_apply_patch` (modules/ai_engine.py) | `calls` |
| `thuc_hien_tinh_chinh_ai` (modules/ai_engine.py) | `chuan_hoa_bang_html_hwood` (modules/file_handler.py) | `calls` |
| `tao_bai_viet_hwood_chuan_seo` (modules/ai_engine.py) | `lay_tri_thuc_phu_hop` (modules/knowledge.py) | `calls` |
| `tao_bai_viet_hwood_chuan_seo` (modules/ai_engine.py) | `lay_noi_dung_quy_chuan_cho_prompt` (modules/chat_advisor.py) | `calls` |
| `tao_bai_viet_hwood_chuan_seo` (modules/ai_engine.py) | `goi_ai_tao_va_noi_bai` (modules/ai_engine.py) | `calls` |
| `tao_bai_viet_hwood_chuan_seo` (modules/ai_engine.py) | `parse_and_apply_patch` (modules/ai_engine.py) | `calls` |
| `tao_bai_viet_hwood_chuan_seo` (modules/ai_engine.py) | `xoa_hop_placeholder_anh` (modules/media_planner.py) | `calls` |
| `tao_bai_viet_hwood_chuan_seo` (modules/ai_engine.py) | `chuan_hoa_bang_html_hwood` (modules/file_handler.py) | `calls` |
| `tao_bai_viet_hwood_chuan_seo` (modules/ai_engine.py) | `luu_bai_viet_lich_su` (modules/history_manager.py) | `calls` |
| `tao_bai_viet_hwood_chuan_seo` (modules/ai_engine.py) | `viet_hoa_tieu_de` (modules/knowledge.py) | `calls` |
| `kiem_tra_proxy_mot_bot` (modules/bot_farm.py) | `proxy_dict` (modules/bot_farm.py) | `calls` |
| `random_scroll` (modules/bot_farm.py) | `human_sleep` (modules/bot_farm.py) | `calls` |
| `type_like_human` (modules/bot_farm.py) | `human_sleep` (modules/bot_farm.py) | `calls` |
| `type_like_human` (modules/bot_farm.py) | `human_sleep` (modules/bot_farm.py) | `calls` |
| `chay_5_bot` (modules/bot_farm.py) | `xoa_live_logs` (modules/bot_farm.py) | `calls` |
| `chay_5_bot` (modules/bot_farm.py) | `append_live_log` (modules/bot_farm.py) | `calls` |
| `chay_5_bot` (modules/bot_farm.py) | `doc_proxy_config` (modules/bot_farm.py) | `calls` |
| `chay_5_bot` (modules/bot_farm.py) | `human_sleep` (modules/bot_farm.py) | `calls` |
| *...và 348 liên kết gọi hàm khác trong graph.json* | | |

---
💡 *Mẹo dành cho AI Agent: Tra cứu file này hoặc `graph.json` trước khi đọc từng file để tiết kiệm token và nắm bắt chuẩn xác điểm ảnh hưởng (blast radius).*