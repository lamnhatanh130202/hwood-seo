from playwright.sync_api import sync_playwright

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
    
    url = "https://www.google.com.vn/search?q=t%E1%BA%A5m+pvc+v%C3%A2n+%C4%91%C3%A1&hl=vi&gl=vn"
    page.goto(url, timeout=30000)
    page.wait_for_timeout(2000)
    
    info = page.evaluate("""() => {
        return {
            title: document.title,
            url: window.location.href,
            h3_count: document.querySelectorAll('h3').length,
            search_h3: document.querySelectorAll('#search h3').length,
            rso_h3: document.querySelectorAll('#rso h3').length,
            role_heading: document.querySelectorAll('[role="heading"]').length,
            all_a: document.querySelectorAll('a').length,
            rso_exists: Boolean(document.querySelector('#rso')),
            search_exists: Boolean(document.querySelector('#search')),
            body_snippet: (document.body ? document.body.innerText : '').slice(0, 300)
        };
    }""")
    print("Page debug info:")
    for k, v in info.items():
        print(f"  {k}: {v}")
        
    browser.close()
