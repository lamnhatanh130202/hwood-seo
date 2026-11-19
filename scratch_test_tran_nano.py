import time
from playwright.sync_api import sync_playwright
from modules.bot_farm import BotWorker, BotConfig, ResultStore

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
    )
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        locale="vi-VN"
    )
    page = ctx.new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    url = "https://www.google.com.vn/search?q=tr%E1%BA%A7n+nh%E1%BB%B1a+nano+gi%E1%BA%ADt+c%E1%BA%A5p&hl=vi&gl=vn"
    page.goto(url, timeout=30000)
    time.sleep(2)
    
    cfg = BotConfig(bot_id="bot1", name="TestBot")
    import queue, threading
    bot = BotWorker(cfg, queue.Queue(), ResultStore(), threading.Event(), 5, False, False, 1, 2, 1, 2)
    
    serp = bot._extract_serp_results(page)
    print("Page Title:", page.title())
    print("Page URL:", page.url)
    print("Total SERP extracted:", len(serp))
    for r in serp:
        print(f"Top {r.get('position')}: [{r.get('is_hwood')}] {r.get('title')} -> {r.get('url')}")
        
    hwood = bot._find_hwood_results(serp)
    print("HWOOD Hits:", len(hwood))
    for h in hwood:
        print("  Hit:", h)
        
    browser.close()
