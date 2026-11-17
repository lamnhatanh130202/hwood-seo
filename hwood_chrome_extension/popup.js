document.addEventListener("DOMContentLoaded", () => {
  const domainInput = document.getElementById("domainInput");
  const kwInput = document.getElementById("kwInput");
  const btnStartScan = document.getElementById("btnStartScan");
  const btnLoadPresets = document.getElementById("btnLoadPresets");
  const progressText = document.getElementById("progressText");
  const resultsBox = document.getElementById("resultsBox");
  const resultsList = document.getElementById("resultsList");
  const syncBox = document.getElementById("syncBox");
  const btnDownloadJson = document.getElementById("btnDownloadJson");

  let scanResults = {};

  btnLoadPresets.addEventListener("click", () => {
    kwInput.value = [
      "tấm ốp nano",
      "tấm pvc vân đá",
      "giá tấm nano ốp",
      "tấm ốp asa",
      "gỗ nhựa ngoài trời",
      "sàn gỗ nhựa ngoài trời",
      "báo giá sàn gỗ nhựa ngoài trời"
    ].join("\n");
  });

  btnStartScan.addEventListener("click", async () => {
    const domain = domainInput.value.trim().toLowerCase().replace("https://", "").replace("http://", "").replace(/\/$/, "");
    const rawKws = kwInput.value.split("\n").map(k => k.trim()).filter(k => k.length > 0);

    if (rawKws.length === 0) {
      alert("Vui lòng nhập ít nhất một từ khóa!");
      return;
    }

    btnStartScan.disabled = true;
    btnStartScan.innerText = "⏳ Đang quét Google...";
    progressText.style.display = "block";
    resultsBox.style.display = "block";
    resultsList.innerHTML = "";
    syncBox.style.display = "none";
    scanResults = {};

    const total = rawKws.length;

    for (let i = 0; i < total; i++) {
      const kw = rawKws[i];
      progressText.innerText = `Đang quét từ khóa (${i + 1}/${total}): "${kw}" trên Google...`;

      try {
        const res = await checkKeywordGoogle(kw, domain);
        scanResults[kw.toLowerCase()] = res;

        // Hiển thị ra danh sách
        const itemDiv = document.createElement("div");
        itemDiv.className = "res-item";

        const badgeHtml = res.rank 
          ? `<span class="badge-top">Top ${res.rank}</span>` 
          : `<span class="badge-na">Ngoài Top 50</span>`;

        const linkHtml = res.link 
          ? `<a href="${res.link}" target="_blank" style="color: #166534; font-size: 0.76rem; text-decoration: none;">🔗 ${res.link.slice(0, 32)}...</a>`
          : "";

        itemDiv.innerHTML = `
          <div>
            <strong style="font-size: 0.85rem;">${kw}</strong>
            <div style="margin-top: 2px;">${linkHtml}</div>
          </div>
          <div>${badgeHtml}</div>
        `;
        resultsList.appendChild(itemDiv);

      } catch (err) {
        console.error("Lỗi quét từ khóa:", kw, err);
      }

      // Giãn cách 1.5 giây giữa các lượt quét
      await new Promise(r => setTimeout(r, 1500));
    }

    progressText.innerText = `✅ Đã quét xong toàn bộ ${total} từ khóa!`;
    btnStartScan.disabled = false;
    btnStartScan.innerText = "🚀 BẮT ĐẦU QUÉT TỰ ĐỘNG BẰNG CHROME";
    syncBox.style.display = "block";
  });

  // Hàm quét trực tiếp Google SERP (ĐÃ TẮT CÁ NHÂN HÓA HOÀN TOÀN)
  async function checkKeywordGoogle(keyword, targetDomain) {
    const encoded = encodeURIComponent(keyword);
    // Tham số pws=0 (Personalized Web Search = 0) yêu cầu Google tắt toàn bộ lịch sử cá nhân hóa
    const searchUrl = `https://www.google.com.vn/search?q=${encoded}&num=50&hl=vi&gl=vn&pws=0`;

    const response = await fetch(searchUrl, {
      method: "GET",
      credentials: "omit", // BẮT BUỘC: Không gửi cookies đăng nhập tài khoản Google để tránh bias cá nhân
      headers: {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
      }
    });

    const htmlText = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlText, "text/html");

    // Lấy tất cả các kết quả tìm kiếm tự nhiên
    const links = Array.from(doc.querySelectorAll("a[href]"));
    let organicRank = 0;
    let foundRank = null;
    let foundLink = "";
    let foundTitle = "";

    const seenUrls = new Set();

    for (const a of links) {
      let href = a.getAttribute("href") || "";
      if (href.startsWith("/url?q=")) {
        href = decodeURIComponent(href.split("/url?q=")[1].split("&")[0]);
      }

      if (!href.startsWith("http")) continue;
      if (href.includes("google.com") || href.includes("google.com.vn") || href.includes("youtube.com") || href.includes("facebook.com")) continue;

      const cleanUrl = href.split("#")[0].replace(/\/$/, "");
      if (seenUrls.has(cleanUrl)) continue;
      seenUrls.add(cleanUrl);

      organicRank++;

      if (cleanUrl.toLowerCase().includes(targetDomain)) {
        foundRank = organicRank;
        foundLink = cleanUrl + "/";
        foundTitle = a.innerText.trim() || `${keyword} - HWOOD`;
        break; // Lấy vị trí cao nhất của website
      }

      if (organicRank >= 50) break;
    }

    const todayStr = new Date().toLocaleDateString("vi-VN");
    return {
      rank: foundRank,
      rank_best: foundRank,
      diff: foundRank,
      link: foundLink,
      title: foundTitle,
      thoi_gian: todayStr
    };
  }

  // Tải file JSON về máy để tự động đồng bộ vào aicode
  btnDownloadJson.addEventListener("click", () => {
    const jsonStr = JSON.stringify(scanResults, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "lich_su_thu_hang.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    alert("🎉 Đã tải file 'lich_su_thu_hang.json'! Bạn hãy lưu đè vào thư mục dự án aicode để hệ thống tự nhận diện ngay lập tức!");
  });
});
