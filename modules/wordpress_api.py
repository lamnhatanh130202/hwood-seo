import os
import json
import re
import requests
import streamlit as st

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WP_CACHE_FILE = os.path.join(CURRENT_DIR, "wp_content_cache.json")

@st.cache_data(ttl=3600, show_spinner=False)
def lay_toan_bo_du_lieu_wp(site_url, api_key, post_type="posts", wp_username="", *args, **kwargs):
    """
    Lấy toàn bộ bài viết (posts), trang tĩnh (pages) hoặc sản phẩm (san-pham / product / WooCommerce) từ WordPress REST API.
    Tự động thử các nguồn sản phẩm: WooCommerce (/wp-json/wc/v3/products), CPT san-pham, CPT product.
    """
    if not site_url:
        return []
    wp_username = wp_username or kwargs.get("wp_username", "")
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Royal-MCP-API-Key": api_key
    } if api_key else {}
    
    clean_pass = api_key.replace(" ", "").strip() if api_key else ""
    auth_tuple = (wp_username.strip(), clean_pass) if (wp_username and clean_pass) else None

    # Hàm trợ giúp lấy toàn bộ trang theo 1 endpoint
    def _fetch_endpoint_all_pages(endpoint_template, is_wc=False):
        results = []
        page = 1
        while page <= 25:
            url = endpoint_template.format(page=page)
            try:
                r = requests.get(url, auth=auth_tuple, headers=headers, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    if not data or not isinstance(data, list):
                        break
                    if is_wc:
                        for it in data:
                            if isinstance(it, dict):
                                if "name" in it and "title" not in it:
                                    it["title"] = {"rendered": it["name"]}
                                if "permalink" in it and "link" not in it:
                                    it["link"] = it["permalink"]
                                if "date_created" in it and "date" not in it:
                                    it["date"] = it["date_created"]
                    results.extend(data)
                    total_pages = int(r.headers.get("X-WP-TotalPages", 1))
                    if page >= total_pages or len(data) < 100:
                        break
                    page += 1
                else:
                    break
            except Exception:
                break
        return results

    # Nếu người dùng muốn lấy sản phẩm (san-pham, product, woocommerce)
    if post_type in ["san-pham", "product", "woocommerce", "products"]:
        candidates = []
        base = site_url.rstrip('/')
        
        # 1. Thử WooCommerce REST API (/wp-json/wc/v3/products)
        wc_url = f"{base}/wp-json/wc/v3/products?per_page=100&page={{page}}"
        wc_items = _fetch_endpoint_all_pages(wc_url, is_wc=True)
        if wc_items:
            candidates.append(wc_items)
            
        # 2. Thử CPT san-pham (/wp-json/wp/v2/san-pham)
        sp_url = f"{base}/wp-json/wp/v2/san-pham?per_page=100&page={{page}}&_fields=id,title,link,date,slug,meta,yoast_head_json"
        sp_items = _fetch_endpoint_all_pages(sp_url)
        if not sp_items:
            sp_url_simple = f"{base}/wp-json/wp/v2/san-pham?per_page=100&page={{page}}&_fields=id,title,link,date,slug"
            sp_items = _fetch_endpoint_all_pages(sp_url_simple)
        if sp_items:
            candidates.append(sp_items)
            
        # 3. Thử CPT product (/wp-json/wp/v2/product)
        prod_url = f"{base}/wp-json/wp/v2/product?per_page=100&page={{page}}&_fields=id,title,link,date,slug,meta,yoast_head_json"
        prod_items = _fetch_endpoint_all_pages(prod_url)
        if not prod_items:
            prod_url_simple = f"{base}/wp-json/wp/v2/product?per_page=100&page={{page}}&_fields=id,title,link,date,slug"
            prod_items = _fetch_endpoint_all_pages(prod_url_simple)
        if prod_items:
            candidates.append(prod_items)

        # 4. Thử CPT san_pham (/wp-json/wp/v2/san_pham)
        sp2_url = f"{base}/wp-json/wp/v2/san_pham?per_page=100&page={{page}}&_fields=id,title,link,date,slug"
        sp2_items = _fetch_endpoint_all_pages(sp2_url)
        if sp2_items:
            candidates.append(sp2_items)

        if candidates:
            # Chọn danh sách có nhiều sản phẩm nhất (ví dụ: WooCommerce 172 sản phẩm)
            best_list = max(candidates, key=len)
            return best_list
        return []

    # Với các post_type khác (posts, pages, du-an)
    target_post_type = post_type
    tat_ca = []
    page = 1
    base = site_url.rstrip('/')
    while page <= 25:
        try:
            r = requests.get(
                f"{base}/wp-json/wp/v2/{target_post_type}?per_page=100&page={page}&_fields=id,title,link,date,slug,meta,yoast_head_json",
                auth=auth_tuple,
                headers=headers,
                timeout=15
            )
            if r.status_code == 200:
                data = r.json()
                if not data or not isinstance(data, list):
                    break
                tat_ca.extend(data)
                total_pages = int(r.headers.get("X-WP-TotalPages", 1))
                if page >= total_pages or len(data) < 100:
                    break
                page += 1
            else:
                # Fallback bỏ _fields
                r_fallback = requests.get(
                    f"{base}/wp-json/wp/v2/{target_post_type}?per_page=100&page={page}&_fields=id,title,link,date,slug",
                    auth=auth_tuple,
                    headers=headers,
                    timeout=15
                )
                if r_fallback.status_code == 200:
                    data = r_fallback.json()
                    if not data or not isinstance(data, list):
                        break
                    tat_ca.extend(data)
                    total_pages = int(r_fallback.headers.get("X-WP-TotalPages", 1))
                    if page >= total_pages or len(data) < 100:
                        break
                    page += 1
                else:
                    break
        except Exception:
            break
            
    return tat_ca


@st.cache_data(ttl=3600, show_spinner=False)
def lay_tat_ca_noi_dung_wp(site_url, api_key, wp_username="", *args, **kwargs):
    """Lấy đồng bộ toàn diện Bài viết (posts), Trang tĩnh (pages) và Sản phẩm (san-pham) từ website WordPress (Lưu cache đĩa để app không bao giờ bị đơ)"""
    if not site_url:
        return []
    wp_username = wp_username or kwargs.get("wp_username", "")

    # Tối ưu siêu tốc: Nạp tức thì từ cache file đĩa local nếu đã có, không lặp lại 12 HTTP request làm đơ ứng dụng
    force_refresh = kwargs.get("force_refresh", False)
    if not force_refresh and os.path.exists(WP_CACHE_FILE):
        try:
            with open(WP_CACHE_FILE, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                if cached_data and isinstance(cached_data, list) and len(cached_data) > 0:
                    return cached_data
        except Exception:
            pass
        
    ds_posts = lay_toan_bo_du_lieu_wp(site_url, api_key, "posts", wp_username) or []
    for item in ds_posts:
        item["loai_noi_dung"] = "Bài viết (Post)"

    ds_pages = lay_toan_bo_du_lieu_wp(site_url, api_key, "pages", wp_username) or []
    for item in ds_pages:
        item["loai_noi_dung"] = "Trang tĩnh (Page)"

    ds_products = lay_toan_bo_du_lieu_wp(site_url, api_key, "san-pham", wp_username) or []
    for item in ds_products:
        item["loai_noi_dung"] = "Sản phẩm (san-pham)"

    seen_ids = set()
    tat_ca = []
    for item in ds_posts + ds_pages + ds_products:
        item_id = item.get("id")
        if item_id and item_id not in seen_ids:
            seen_ids.add(item_id)
            tat_ca.append(item)
        elif not item_id:
            tat_ca.append(item)

    # Lưu đệm xuống đĩa để các lần bấm nút, xóa bài, chuyển tab sau đó chạy mượt mà ngay lập tức
    if tat_ca:
        try:
            with open(WP_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(tat_ca, f, ensure_ascii=False)
        except Exception:
            pass

    return tat_ca


def dang_bai_len_wordpress(site_url, title, content, status="draft", wp_username="", api_key="", focus_kw="", meta_title="", meta_desc="", slug=""):
    """
    Đăng bài viết mới lên WordPress với cơ chế xác thực đa tầng và TỰ ĐỘNG ĐIỀN YOAST SEO / RANK MATH:
    1. HTTP Basic Auth chuẩn WordPress Core (Username + Application Password)
    2. Bearer Token & X-API-KEY (Nếu dùng plugin xác thực JWT/API Key)
    3. Tự động điền Focus Keyphrase, SEO Title, Meta Description, Slug vào Yoast SEO & Rank Math
    4. Tự động chuẩn hóa toàn bộ bảng HTML theo phong cách Forest Green HWOOD (Hình 2)
    Trả về: (thanh_cong: bool, du_lieu_hoac_loi: dict/str)
    """
    if not site_url:
        return False, "Chưa nhập địa chỉ website WordPress!"
        
    # Tự động chuẩn hóa toàn bộ bảng trong bài viết trước khi đẩy lên web
    from modules.file_handler import chuan_hoa_bang_html_hwood, xoa_dau_tieng_viet
    content = chuan_hoa_bang_html_hwood(content)
    
    url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
    
    # Tạo slug tự động nếu chưa có
    if not slug and (focus_kw or title):
        raw_slug = xoa_dau_tieng_viet(focus_kw or title)
        slug = re.sub(r'[^a-z0-9\-]+', '-', raw_slug).strip('-')

    payload = {
        "title": title,
        "content": content,
        "status": status
    }
    if slug:
        payload["slug"] = slug

    # TỰ ĐỘNG ĐIỀN YOAST SEO VÀ RANK MATH
    meta_dict = {}
    if focus_kw:
        meta_dict["_yoast_wpseo_focuskw"] = focus_kw
        meta_dict["rank_math_focus_keyword"] = focus_kw
    if meta_title:
        meta_dict["_yoast_wpseo_title"] = meta_title
        meta_dict["rank_math_title"] = meta_title
    if meta_desc:
        meta_dict["_yoast_wpseo_metadesc"] = meta_desc
        meta_dict["rank_math_description"] = meta_desc

    if meta_dict:
        payload["meta"] = meta_dict
    
    last_err = ""

    # Hàm thực hiện gửi request thử cả có meta lẫn fallback không meta
    def _gui_yeu_cau(auth_tuple=None, headers_dict=None, query_param=None):
        target_url = f"{url}?{query_param}" if query_param else url
        req_headers = headers_dict or {"Content-Type": "application/json"}
        
        # Thử 1: Đẩy đầy đủ cả nội dung và meta SEO
        try:
            r = requests.post(target_url, auth=auth_tuple, headers=req_headers, json=payload, timeout=15)
            if r.status_code in [200, 201]:
                return True, r.json(), ""
            # Nếu lỗi do server chặn meta, thử lại lần 2 bỏ trường meta
            if r.status_code == 400 and "meta" in payload:
                p_fallback = {k: v for k, v in payload.items() if k != "meta"}
                r_fb = requests.post(target_url, auth=auth_tuple, headers=req_headers, json=p_fallback, timeout=15)
                if r_fb.status_code in [200, 201]:
                    return True, r_fb.json(), ""
            return False, None, r.text
        except Exception as ex:
            return False, None, str(ex)

    # 1. Thử xác thực chuẩn Application Passwords nếu có wp_username
    if wp_username and api_key:
        ok, res, err = _gui_yeu_cau(auth_tuple=(wp_username.strip(), api_key.strip()))
        if ok:
            return True, res
        last_err = err

        clean_pass = api_key.replace(" ", "").strip()
        if clean_pass != api_key.strip():
            ok, res, err = _gui_yeu_cau(auth_tuple=(wp_username.strip(), clean_pass))
            if ok:
                return True, res
            last_err = err

    # 2. Thử xác thực với Bearer & Custom Headers
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-API-KEY"] = api_key
        headers["X-Royal-MCP-API-Key"] = api_key
        
    ok, res, err = _gui_yeu_cau(headers_dict=headers)
    if ok:
        return True, res
    last_err = err

    # 3. Thử với query param
    if api_key:
        ok, res, err = _gui_yeu_cau(query_param=f"api_key={api_key}")
        if ok:
            return True, res
        last_err = err

    return False, last_err


def cap_nhat_bai_wordpress(site_url, post_id, post_type="posts", title=None, content=None, wp_username="", api_key=""):
    """Cập nhật bài viết/trang/sản phẩm trên WordPress với cơ chế xác thực đa tầng"""
    if not site_url or not post_id:
        return False, "Thiếu URL website hoặc ID bài viết!"
        
    url = f"{site_url.rstrip('/')}/wp-json/wp/v2/{post_type}/{post_id}"
    payload = {}
    if title is not None:
        payload["title"] = title
    if content is not None:
        payload["content"] = content
        
    last_err = ""

    # 1. Thử xác thực chuẩn Application Passwords nếu có wp_username
    if wp_username and api_key:
        try:
            r = requests.post(url, auth=(wp_username.strip(), api_key.strip()), json=payload, timeout=15)
            if r.status_code == 200:
                return True, r.json()
            else:
                last_err = r.text
        except Exception as ex:
            last_err = str(ex)

        clean_pass = api_key.replace(" ", "").strip()
        if clean_pass != api_key.strip():
            try:
                r_clean = requests.post(url, auth=(wp_username.strip(), clean_pass), json=payload, timeout=15)
                if r_clean.status_code == 200:
                    return True, r_clean.json()
            except Exception:
                pass

    # 2. Thử xác thực với Headers
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["X-API-KEY"] = api_key
        headers["X-Royal-MCP-API-Key"] = api_key
        
    try:
        r2 = requests.post(url, headers=headers, json=payload, timeout=15)
        if r2.status_code == 200:
            return True, r2.json()
        else:
            last_err = r2.text
    except Exception as ex2:
        last_err = str(ex2)

    return False, last_err
