# AoV Image Crawler

<p align="center">
  <img src="icon.ico" width="80" alt="App Icon"/>
</p>

<p align="center">
  <a href="https://github.com/KotexChick00/AovImageCrawler/releases/latest">
    <img src="https://img.shields.io/github/v/release/KotexChick00/AovImageCrawler?style=flat-square" alt="Latest Release"/>
  </a>
  <a href="https://github.com/KotexChick00/AovImageCrawler/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/KotexChick00/AovImageCrawler?style=flat-square" alt="License"/>
  </a>
  <img src="https://img.shields.io/badge/platform-Windows-blue?style=flat-square" alt="Platform"/>
  <img src="https://img.shields.io/badge/python-3.10-blue?style=flat-square" alt="Python"/>
</p>

<p align="center">
  <strong>🌐 Ngôn ngữ / Language:</strong>
  <a href="#-tiếng-việt">Tiếng Việt</a> |
  <a href="#-english">English</a>
</p>

---

## 🇻🇳 Tiếng Việt

Tool tải splash art, head icon và bust của tướng trong **Arena of Valor (AoV)** từ server Garena 傳說對決.

### Tính năng

- Tải **splash art** (ảnh loading) của tất cả tướng và skin
- Tải **head icon** (ảnh đầu tướng) của tất cả tướng và skin
- Tải **bust** (khung avatar) của tất cả tướng và skin
- Bỏ qua file đã tải, không tải lại
- Ghi log mỗi phiên tải vào thư mục `logs/`
- Tự động dừng khi gặp skin không tồn tại (miss limit)
- Đa luồng — tải song song nhiều tướng cùng lúc

### Download

Tải file `.exe` mới nhất tại trang [Releases](https://github.com/KotexChick00/AovImageCrawler/releases/latest) — không cần cài Python.

### Cách dùng

1. Tải `AovImageCrawler.exe` từ trang Releases
2. Đặt file `.exe` vào thư mục bạn muốn lưu ảnh
3. Chạy file, chọn chế độ tải:

```
========================================
  Chọn chế độ tải:
  1. splash  — chỉ tải splash
  2. head    — chỉ tải head
  3. bust   — chỉ tải bust
  4. all     — tải tất cả (mặc định)
========================================
```

4. Ảnh sẽ được lưu vào các thư mục tương ứng:

```
📁 thư mục chạy exe
├── 📁 splash/
│   └── 📁 {hero_id}/
├── 📁 head/
│   └── 📁 {hero_id}/
├── 📁 bust/
│   └── 📁 {hero_id}/
└── 📁 logs/
    ├── download.log
    └── {timestamp}.log
```

### Build từ source

**Yêu cầu:** Python 3.10+

```bash
git clone https://github.com/KotexChick00/AovImageCrawler.git
cd AovImageCrawler
pip install -r requirements.txt
python main.py
```


---

## 🇬🇧 English

Tool to download splash art, head icons and busts of heroes in **Arena of Valor (AoV)** from the Garena 傳說對決 server.

### Features

- Download **splash art** (loading screen images) for all heroes and skins
- Download **head icons** for all heroes and skins
- Download **bust** (avatar borders) for all heroes and skins
- Skips already downloaded files
- Writes a session log to the `logs/` folder after each run
- Automatically stops when missing skins exceed the miss limit
- Multi-threaded — downloads multiple heroes in parallel

### Download

Get the latest `.exe` from the [Releases](https://github.com/KotexChick00/AovImageCrawler/releases/latest) page — no Python installation required.

### Usage

1. Download `AovImageCrawler.exe` from the Releases page
2. Place the `.exe` in the folder where you want images saved
3. Run the file and select a download mode:

```
========================================
  Chọn chế độ tải:
  1. splash  — chỉ tải splash
  2. head    — chỉ tải head
  3. bust   — chỉ tải bust
  4. all     — tải tất cả (mặc định)
========================================
```

4. Images will be saved into the corresponding folders:

```
📁 folder where exe is placed
├── 📁 splash/
│   └── 📁 {hero_id}/
├── 📁 head/
│   └── 📁 {hero_id}/
├── 📁 bust/
│   └── 📁 {hero_id}/
└── 📁 logs/
    ├── download.log
    └── {timestamp}.log
```

### Build from source

**Requirements:** Python 3.10+

```bash
git clone https://github.com/KotexChick00/AovImageCrawler.git
cd AovImageCrawler
pip install -r requirements.txt
python main.py
```

---

## License

[GPL-3.0](LICENSE)
