import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
}
r = requests.get('https://www.google.com.vn/search?q=tam+op+nano&hl=vi&gl=vn', headers=headers, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')
links = []
for a in soup.find_all('a', href=True):
    href = a['href']
    if 'http' in href and not any(x in href for x in ['google', 'gstatic', 'schema']):
        links.append((href, a.get_text().strip()))

print('Found total non-google links:', len(links))
for idx, (l, t) in enumerate(links[:15], 1):
    print(f'{idx}. {l} | {t[:40]}')
