import requests
import re
from html.parser import HTMLParser

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
}
r = requests.get('https://www.google.com.vn/search?q=tam+op+nano&hl=vi&gl=vn', headers=headers, timeout=10)

class MyParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current_tag = None
        self.current_href = None
        self.current_text = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            d = dict(attrs)
            if 'href' in d:
                self.current_href = d['href']
                self.current_text = []

    def handle_endtag(self, tag):
        if tag == 'a' and self.current_href:
            self.links.append((self.current_href, ''.join(self.current_text).strip()))
            self.current_href = None

    def handle_data(self, data):
        if self.current_href:
            self.current_text.append(data)

parser = MyParser()
parser.feed(r.text)

print(f'Total links: {len(parser.links)}')
clean = []
for h, t in parser.links:
    if any(x in h.lower() for x in ['google.com', 'google.com.vn', 'gstatic.com', 'schema.org']):
        continue
    clean.append((h, t))

print(f'Non-google links: {len(clean)}')
for idx, (h, t) in enumerate(clean[:15], 1):
    print(f'{idx}. {h} | {t[:40]}')

with open('raw_google.html', 'w', encoding='utf-8') as f:
    f.write(r.text)
