import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
}
try:
    r = requests.get('https://www.google.com.vn/search?q=tam+op+nano&hl=vi&gl=vn', headers=headers, timeout=10)
    print('Status:', r.status_code, 'Length:', len(r.text))
    matches = re.findall(r'https?://[^\s"\'<>]*hwood\.vn[^\s"\'<>]*', r.text)
    print('hwood matches:', len(matches))
    for m in set(matches):
        print(' -', m)
    # Check if there is captcha or blocked
    if 'sorry' in r.url or 'captcha' in r.text.lower():
        print('CAPTCHA DETECTED!')
except Exception as e:
    print('Error:', e)
