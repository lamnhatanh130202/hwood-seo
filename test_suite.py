import os
import sys
import json
import traceback

def run_tests():
    print("==================================================")
    print("      BAT DAU KIEM TRA TOAN BO CHUC NANG          ")
    print("==================================================")
    
    passed = 0
    failed = 0

    # 1. Test Keyword Matrix & Presets
    print("\n[TEST 1] Kiem tra module keyword_matrix & knowledge...")
    try:
        from modules.keyword_matrix import lay_ma_tran_toan_bo_keyword, trich_xuat_danh_sach_keyword_chuan_hwood
        from modules.knowledge import phan_loai_chu_de, viet_hoa_tieu_de
        
        sample_wp = [
            {"id": 1, "title": {"rendered": "Go nhua ngoai troi Hwood"}, "link": "https://hwood.vn/go-nhua", "slug": "go-nhua"}
        ]
        matrix = lay_ma_tran_toan_bo_keyword(sample_wp, [])
        assert len(matrix) > 0, "Matrix rong"
        kws = trich_xuat_danh_sach_keyword_chuan_hwood()
        assert len(kws) > 0, "Danh sach keyword rong"
        chu_de = phan_loai_chu_de("tam op nano")
        assert chu_de != "", "Phan loai chu de loi"
        title_norm = viet_hoa_tieu_de("tam op nano hwood")
        print(f"  --> OK (Tong cong {len(kws)} tu khoa trong Ma tran, Matrix: {len(matrix)} muc)")
        passed += 1
    except Exception as e:
        print(f"  --> THAT BAI: {e}")
        traceback.print_exc()
        failed += 1

    # 2. Test Rank Tracker
    print("\n[TEST 2] Kiem tra module rank_tracker...")
    try:
        from modules.rank_tracker import (
            doc_lich_su_thu_hang, 
            doc_database_keywords, 
            nhap_ket_qua_spineditor,
            tim_bai_viet_khop_nhat_wp,
            tao_link_google_search
        )
        history = doc_lich_su_thu_hang()
        db = doc_database_keywords()
        parsed = nhap_ket_qua_spineditor("tam op nano\t1\t1\thttps://hwood.vn/tam-op")
        assert len(parsed) == 1, "Parse SpinEditor that bai"
        assert parsed[0]["rank"] == 1, "Rank parse sai"
        link_search = tao_link_google_search("tam op nano")
        assert "google.com" in link_search, "Tao link search sai"
        print(f"  --> OK (Doc DB: {len(db)} tu khoa, Lich su: {len(history)} ban ghi)")
        passed += 1
    except Exception as e:
        print(f"  --> THAT BAI: {e}")
        traceback.print_exc()
        failed += 1

    # 3. Test Bot Farm
    print("\n[TEST 3] Kiem tra module bot_farm (5 Bot Quet Thu Hang)...")
    try:
        from modules.bot_farm import (
            doc_proxy_config, 
            doc_tien_do, 
            doc_ket_qua, 
            doc_live_logs,
            kiem_tra_proxy_mot_bot,
            BotConfig
        )
        configs = doc_proxy_config()
        assert len(configs) == 5, f"So luong bot khong phai 5 (co {len(configs)})"
        
        # Test kiem tra proxy voi IP truc tiep khong crash
        cfg_test = BotConfig(
            bot_id="1",
            name="Bot 1",
            proxy_server="",
            proxy_username="",
            proxy_password=""
        )
        res_proxy = kiem_tra_proxy_mot_bot(cfg_test)
        assert "status" in res_proxy, "Kiem tra proxy loi tra ve"
        
        logs = doc_live_logs(n=20)
        results = doc_ket_qua()
        progress = doc_tien_do()
        print(f"  --> OK (Cau hinh 5 bot chuan xac, Live logs OK, Ket qua doc tot)")
        passed += 1
    except Exception as e:
        print(f"  --> THAT BAI: {e}")
        traceback.print_exc()
        failed += 1

    # 4. Test History Manager
    print("\n[TEST 4] Kiem tra module history_manager...")
    try:
        from modules.history_manager import lay_danh_sach_lich_su
        hist = lay_danh_sach_lich_su()
        print(f"  --> OK (Lich su bai viet: {len(hist)} bai)")
        passed += 1
    except Exception as e:
        print(f"  --> THAT BAI: {e}")
        traceback.print_exc()
        failed += 1

    # 5. Test File Handler
    print("\n[TEST 5] Kiem tra module file_handler...")
    try:
        from modules.file_handler import xoa_dau_tieng_viet
        clean_text = xoa_dau_tieng_viet("Tấm ốp Nano Hwood Việt Nam")
        assert "tam op nano hwood viet nam" in clean_text.lower(), "Xoa dau tieng Viet sai"
        print(f"  --> OK (Xoa dau thanh cong: '{clean_text}')")
        passed += 1
    except Exception as e:
        print(f"  --> THAT BAI: {e}")
        traceback.print_exc()
        failed += 1

    # 6. Test Import and Interface of all Tabs
    print("\n[TEST 6] Kiem tra import & giao dien cac Tab...")
    try:
        import tabs.tab1_viet_moi as t1
        import tabs.tab2_kham_bai as t2
        import tabs.tab3_kiem_toan as t3
        import tabs.tab4_thu_hang as t4
        import tabs.tab5_lich_su as t5
        import tabs.tab6_ke_hoach_thang as t6
        import tabs.tab7_chat_chien_luoc as t7
        import tabs.tab8_bot_farm as t8
        import tabs.tab9_traffic_analytics as t9
        
        assert hasattr(t1, "render_tab1"), "Tab 1 thieu render_tab1"
        assert hasattr(t2, "render_tab2"), "Tab 2 thieu render_tab2"
        assert hasattr(t3, "render_tab3"), "Tab 3 thieu render_tab3"
        assert hasattr(t4, "render_tab4"), "Tab 4 thieu render_tab4"
        assert hasattr(t5, "render_tab5"), "Tab 5 thieu render_tab5"
        assert hasattr(t6, "render_tab6"), "Tab 6 thieu render_tab6"
        assert hasattr(t7, "render_tab7"), "Tab 7 thieu render_tab7"
        assert hasattr(t8, "render_tab8"), "Tab 8 thieu render_tab8"
        assert hasattr(t9, "render_tab9"), "Tab 9 thieu render_tab9"
        print("  --> OK (Tat ca 9 Tab deu day du ham render)")
        passed += 1
    except Exception as e:
        print(f"  --> THAT BAI: {e}")
        traceback.print_exc()
        failed += 1

    # 7. Test Rank Optimizer (Chiến lược đột phá Top 1-5)
    print("\n[TEST 7] Kiem tra module rank_optimizer (Chien luoc dot pha Top 1-5)...")
    try:
        from modules.rank_optimizer import (
            chan_doan_tu_khoa_ngoai_top,
            lay_toan_bo_chan_doan_ngoai_top,
            dua_vao_ke_hoach_thang_nhanh,
            dua_vao_bot_farm_queue
        )
        sample_kw = {
            "tu_khoa": "Báo Giá Gỗ Nhựa Ngoài Trời",
            "rank_hien_tai": 6,
            "url_dich": "https://hwood.vn/bao-gia-san-go-nhua-ngoai-troi",
            "tieu_de_bai": "Báo Giá Sàn Gỗ",
            "chuyen_muc": "Gỗ Nhựa Ngoài Trời"
        }
        diag = chan_doan_tu_khoa_ngoai_top(sample_kw)
        assert diag["tier"] == 1, "Tier phan loai sai"
        assert len(diag["phuong_an_de_xuat"]) > 0, "De xuat rong"
        assert "Quick Answer" in "".join(diag["phuong_an_de_xuat"]) or "Quick Answer" in "".join(diag["loi_phat_hien"]), "Thieu de xuat Quick Answer"
        
        all_diag = lay_toan_bo_chan_doan_ngoai_top()
        assert all_diag["tong_so_ngoai_top"] > 0, "Tong so ngoai top bang 0"
        print(f"  --> OK (Chan doan tot: {all_diag['tong_so_ngoai_top']} tu khoa ngoai Top 5, Tier 1: {all_diag['dem_tier1']}, Tier 2: {all_diag['dem_tier2']}, Tier 3: {all_diag['dem_tier3']})")
        passed += 1
    except Exception as e:
        print(f"  --> THAT BAI: {e}")
        traceback.print_exc()
        failed += 1

    # 8. Test Google Analytics GA4 & Google Search Console
    print("\n[TEST 8] Kiem tra module google_analytics_gsc (GA4 & Search Console)...")
    try:
        from modules.google_analytics_gsc import (
            lay_toan_bo_du_lieu_traffic,
            tao_du_lieu_snapshot_thuc_te,
            kiem_tra_credentials
        )
        # Test 28 ngay qua
        data_28d, _, _ = lay_toan_bo_du_lieu_traffic("28 ngày qua (Chuẩn)")
        assert data_28d["ga4"]["active_users_str"] == "5,3 N", "28d GA4 users sai"
        assert data_28d["gsc"]["clicks"] > 0, "28d GSC clicks phai lon hon 0"
        assert len(data_28d["gsc"]["top_queries"]) > 0, "28d GSC top_queries rong"

        # Test 7 ngay qua
        data_7d, _, _ = lay_toan_bo_du_lieu_traffic("7 ngày qua")
        assert data_7d["gsc"]["clicks"] > 0, "7d GSC clicks phai lon hon 0"
        assert len(data_7d["gsc"]["chart_clicks"]) > 0, "7d chart series length sai"

        # Test 24 gio qua
        data_24h, _, _ = lay_toan_bo_du_lieu_traffic("24 giờ qua (Realtime)")
        assert data_24h["ga4"]["realtime_users_30m"] == 22, "24h realtime users sai"
        assert data_24h["gsc"]["clicks"] == 303, "24h GSC clicks sai"
        assert data_24h["gsc"]["impressions"] == 12000, "24h GSC impressions sai"

        # Test 3 thang qua
        data_3m, _, _ = lay_toan_bo_du_lieu_traffic("3 tháng qua")
        assert data_3m["ga4"]["active_users_str"] == "15,8 N", "3m GA4 users sai"
        assert data_3m["gsc"]["clicks"] == 13800, "3m GSC clicks sai"

        print(f"  --> OK (28d: {data_28d['ga4']['active_users_str']} users | 7d: {data_7d['ga4']['active_users_str']} users, {data_7d['gsc']['clicks_str']} clicks | 24h: {data_24h['gsc']['clicks']} clicks, {data_24h['gsc']['impressions_str']} imps)")
        passed += 1
    except Exception as e:
        print(f"  --> THAT BAI: {e}")
        traceback.print_exc()
        failed += 1

    print("\n==================================================")
    print(f"TONG KET: {passed} PASSED / {passed + failed} TOTAL")
    if failed == 0:
        print(">>> TAT CA CAC CHUC NANG HOAT DONG HOAN HAO KHONG CO LOI! <<<")
    else:
        print(">>> CO CHUC NANG BI LOI! <<<")
    print("==================================================")
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
