import subprocess
import os

chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
cmd = [
    chrome_path,
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--lang=vi",
    "--dump-dom",
    "https://www.google.com.vn/search?q=tam+op+nano&hl=vi&gl=vn"
]

res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
print("Return code:", res.returncode)
print("Stdout length:", len(res.stdout))
if "hwood.vn" in res.stdout:
    print("SUCCESS: Found hwood.vn in real Google DOM rendered by Chrome!")
else:
    print("hwood.vn not in output. First 300 chars:", res.stdout[:300])
