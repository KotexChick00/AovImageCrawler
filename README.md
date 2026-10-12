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
- Tải cả các phiên bản **B** (`B36`–`B99`) của skin gốc cho splash, head và bust
- **Đổi tên hàng loạt** file đã tải sang tên dễ đọc (tách riêng khỏi bước tải)
- **Tự kiểm tra và cập nhật** app (`.exe`) và `hero.json` từ GitHub
- Bỏ qua file đã tải, không tải lại
- Ghi log mỗi phiên tải vào thư mục `logs/`
- Tự động dừng khi gặp skin không tồn tại (miss limit)
- Đa luồng — tải song song nhiều tướng cùng lúc

### Download

Tải file `.exe` mới nhất tại trang [Releases](https://github.com/KotexChick00/AovImageCrawler/releases/latest) — không cần cài Python.

### Cách dùng

1. Tải file `.exe` từ trang Releases
2. Đặt file `.exe` vào thư mục bạn muốn lưu ảnh, cùng với file `hero.json` (danh sách tên tướng, xem [hero.json](#herojson))
3. Chạy file, chọn chế độ:

```
========================================
  AoV Image Crawler vx.x.x
  Chọn chế độ:
  1. splash      — chỉ tải splash
  2. head        — chỉ tải head
  3. bust        — chỉ tải bust
  4. all         — tải tất cả (mặc định)
  5. rename      — đổi tên file đã tải
  6. all+rename  — tải tất cả rồi đổi tên
  7. update      — kiểm tra cập nhật (app + hero.json)
========================================
```

Sau mỗi lần chạy, app hỏi có muốn chạy chế độ khác không và chờ bạn nhấn Enter trước khi đóng, nên cửa sổ không tự thoát.

4. Ảnh sẽ được lưu vào các thư mục tương ứng:

```
📁 thư mục chạy exe
├── 📄 hero.json
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

### Tên file và đổi tên

Khi tải, file được lưu theo **ID gốc trên server**. Dùng chế độ `5. rename` (hoặc `6. all+rename`) để đổi sang tên dễ đọc theo mẫu `Hero_{Loại}_{Tên}_{ID}_{Skin}`:

| Khi tải về | Sau khi đổi tên |
|---|---|
| `12700.jpg` | `Hero_Splash_{Tên}_127_0.jpg` |
| `301271head.jpg` | `Hero_Head_{Tên}_127_1.jpg` |
| `301270_B51.jpg` | `Hero_Bust_{Tên}_127_0_B51.jpg` |
| `3011620_2.jpg` | `Hero_Bust_{Tên}_116_20_2.jpg` |

- `_2` là bản **EVO5**, `_B{n}` là **B-variant**; Flowborn dùng `m` / `f` thay cho số skin.
- Chế độ `rename` cho **xem trước** trước khi đổi thật, **không ghi đè** file có sẵn (báo xung đột) và an toàn khi chạy lại.
- Tên lấy từ `hero.json`; hero không có trong file sẽ được giữ nguyên tên gốc và báo lại.

> ⚠️ Mặc định app xác định "đã tải" bằng cách tìm file theo tên gốc trên đĩa. Sau khi đổi tên, file sẽ không còn khớp và **chạy lại chế độ tải sẽ tải lại chúng**. Hãy tải xong rồi mới đổi tên, hoặc build với `DUPLICATE_CHECK = "url"` (xem [Cấu hình](#cấu-hình)).

### hero.json

`hero.json` là danh sách `{"id": ..., "name": ...}` dùng để đặt tên khi đổi tên. App tìm file theo thứ tự: cạnh file `.exe` → file đóng gói kèm → thư mục đang chạy. Khi có hero mới, chọn `7. update` để tải bản mới nhất từ repo (bản cũ được lưu thành `hero.json.bak`).

### Cập nhật tự động

- App kiểm tra bản mới khi mở và ở mục `7. update`.
- **File `.exe`:** tải từ [Releases](https://github.com/KotexChick00/AovImageCrawler/releases/latest), xác minh SHA-256 (nếu release có file `.sha256`), rồi tự thay file và mở lại. Chỉ hỗ trợ Windows.
- **hero.json:** so với bản trên nhánh `main`, hiển thị hero mới / đổi tên / bị xóa rồi hỏi xác nhận.
- Chạy từ mã nguồn thì dùng `git pull` thay cho cập nhật `.exe`.

### Cấu hình

Các tùy chọn nằm trong `modules/core/config.py` (áp dụng khi chạy từ mã nguồn hoặc tự build):

| Tùy chọn | Ý nghĩa |
|---|---|
| `DUPLICATE_CHECK` | `"disk"` (mặc định): file còn trên đĩa là đã tải, xóa file sẽ tự tải lại, nhưng file đã đổi tên bị coi là chưa tải. `"url"`: ghi nhớ URL trong `logs/downloaded_urls.txt`, đổi tên thoải mái nhưng xóa file sẽ không tự tải lại. |
| `B_SUFFIX_RANGE` | Dải B-variant được quét (mặc định `B36`–`B99`). |
| `MISS_LIMIT` | Số lần miss liên tiếp trước khi dừng quét skin của một hero. |
| `UPDATE_CHECK_ON_START` | Tự kiểm tra cập nhật khi mở app. |

### Build từ source

**Yêu cầu:** Python 3.10+

```bash
git clone https://github.com/KotexChick00/AovImageCrawler.git
cd AovImageCrawler
pip install -r requirements.txt
python main.py
```


### Lưu ý pháp lý

AoV Image Crawler là công cụ độc lập, **không liên kết, không được tài trợ hay chứng nhận bởi Garena, Level Infinite, Tencent, TIMi Studio Group** hoặc bất kỳ chủ sở hữu nào của Arena of Valor. Tên game, tên tướng và hình ảnh thuộc về chủ sở hữu của chúng. Repo này **không chứa sẵn tài nguyên game**: ảnh chỉ được tải về máy của bạn khi bạn chạy công cụ. Hãy tôn trọng điều khoản sử dụng của game và chỉ dùng ảnh cho mục đích cá nhân hợp lệ.

### Chính sách ký mã (Code signing policy)

Free code signing provided by [SignPath.io](https://about.signpath.io), certificate by [SignPath Foundation](https://signpath.org).

**Vai trò trong nhóm**
- Tác giả, người commit và người review: [KotexChick00](https://github.com/KotexChick00)
- Người phê duyệt (Approver): [KotexChick00](https://github.com/KotexChick00)

Đây là dự án một người duy trì nên một người giữ mọi vai trò. Xác thực hai lớp (MFA) được bật cho GitHub và SignPath.

**Những gì được ký:** chỉ file `AoV.Image.Crawler.exe` do workflow GitHub Actions [`release.yml`](.github/workflows/release.yml) build từ các commit có gắn tag của repo này. Mỗi bản phát hành đều được phê duyệt thủ công trước khi ký.

**Chính sách quyền riêng tư:** chương trình không thu thập, lưu trữ hay gửi dữ liệu cá nhân. Nó chỉ kết nối đến:
1. Máy chủ CDN công khai của Garena (`dl.ops.kgtw.garenanow.com`) để tải ảnh, khi bạn bắt đầu một lượt tải.
2. GitHub, để kiểm tra bản mới của app và `hero.json` (khi mở app và ở mục `7. update`). Yêu cầu này chỉ gồm thông tin mà mọi yêu cầu HTTP đều gửi (địa chỉ IP, user agent). App luôn hỏi xác nhận trước khi cài bản cập nhật. Muốn tắt kiểm tra khi mở app, đặt `UPDATE_CHECK_ON_START = False` trong `modules/core/config.py` rồi tự build.

Chính sách quyền riêng tư của các dịch vụ này áp dụng cho các kết nối trên, ví dụ [GitHub](https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement). Log tải chỉ được ghi trong thư mục `logs/` trên máy bạn.

**Cài đặt và gỡ cài đặt:** app là một file `.exe` chạy trực tiếp, không thay đổi cấu hình hệ thống. Để gỡ, xóa file `.exe` cùng các thư mục `splash`, `head`, `bust`, `logs` và file `hero.json` do app tạo ra.

### Giấy phép của thành phần bên thứ ba

| Thành phần | Giấy phép |
|---|---|
| [requests](https://github.com/psf/requests) | Apache-2.0 |
| [urllib3](https://github.com/urllib3/urllib3) | MIT |
| [idna](https://github.com/kjd/idna) | BSD-3-Clause |
| [charset-normalizer](https://github.com/jawah/charset_normalizer) | MIT |
| [certifi](https://github.com/certifi/python-certifi) | MPL-2.0 |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) (công cụ build) | GPL-2.0-or-later với ngoại lệ cho bootloader |


---

## 🇬🇧 English

Tool to download splash art, head icons and busts of heroes in **Arena of Valor (AoV)** from the Garena 傳說對決 server.

### Features

- Download **splash art** (loading screen images) for all heroes and skins
- Download **head icons** for all heroes and skins
- Download **bust** (avatar borders) for all heroes and skins
- Also fetches **B-variants** (`B36`–`B99`) of the base skin for splash, head and bust
- **Bulk rename** of downloaded files to readable names (separate from the download step)
- **Self-update** for the app (`.exe`) and `hero.json` from GitHub
- Skips already downloaded files
- Writes a session log to the `logs/` folder after each run
- Automatically stops when missing skins exceed the miss limit
- Multi-threaded — downloads multiple heroes in parallel

### Download

Get the latest `.exe` from the [Releases](https://github.com/KotexChick00/AovImageCrawler/releases/latest) page — no Python installation required.

### Usage

1. Download the `.exe` from the Releases page
2. Place the `.exe` in the folder where you want images saved, together with `hero.json` (the hero name list, see [hero.json](#herojson-1))
3. Run the file and select a mode:

```
========================================
  AoV Image Crawler vx.x.x
  Chọn chế độ:
  1. splash      — chỉ tải splash
  2. head        — chỉ tải head
  3. bust        — chỉ tải bust
  4. all         — tải tất cả (mặc định)
  5. rename      — đổi tên file đã tải
  6. all+rename  — tải tất cả rồi đổi tên
  7. update      — kiểm tra cập nhật (app + hero.json)
========================================
```

*(Menu text is in Vietnamese: 1–3 download a single type, 4 downloads everything, 5 renames, 6 downloads then renames, 7 checks for updates.)*

After each run the app asks whether to run another mode and waits for Enter before closing, so the window does not exit on its own.

4. Images will be saved into the corresponding folders:

```
📁 folder where exe is placed
├── 📄 hero.json
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

### File names and renaming

Files are saved by their **original server ID** when downloaded. Use mode `5. rename` (or `6. all+rename`) to rename them to readable names following `Hero_{Type}_{Name}_{ID}_{Skin}`:

| As downloaded | After renaming |
|---|---|
| `12700.jpg` | `Hero_Splash_{Name}_127_0.jpg` |
| `301271head.jpg` | `Hero_Head_{Name}_127_1.jpg` |
| `301270_B51.jpg` | `Hero_Bust_{Name}_127_0_B51.jpg` |
| `3011620_2.jpg` | `Hero_Bust_{Name}_116_20_2.jpg` |

- `_2` marks an **EVO5** variant and `_B{n}` a **B-variant**; Flowborn heroes use `m` / `f` in place of the skin number.
- `rename` offers a **preview** before changing anything, **never overwrites** existing files (conflicts are reported) and is safe to re-run.
- Names come from `hero.json`; heroes missing from it keep their original file names and are reported.

> ⚠️ By default the app decides a file is "already downloaded" by looking for its original name on disk. After renaming, files no longer match, so **running the download again will fetch them again**. Download first and rename afterwards, or build with `DUPLICATE_CHECK = "url"` (see [Configuration](#configuration)).

### hero.json

`hero.json` is a list of `{"id": ..., "name": ...}` entries used for naming during rename. The app looks for it next to the `.exe` → in the bundled copy → in the working directory. When new heroes are released, choose `7. update` to fetch the latest version from the repo (the previous copy is kept as `hero.json.bak`).

### Auto-update

- The app checks for new versions on startup and via `7. update`.
- **`.exe`:** downloaded from [Releases](https://github.com/KotexChick00/AovImageCrawler/releases/latest), SHA-256 verified (when the release has a `.sha256` file), then swapped in and relaunched automatically. Windows only.
- **hero.json:** compared with the copy on the `main` branch; new / renamed / removed heroes are listed and you are asked to confirm.
- When running from source, use `git pull` instead of the `.exe` update.

### Configuration

Options live in `modules/core/config.py` (apply when running from source or building your own):

| Option | Meaning |
|---|---|
| `DUPLICATE_CHECK` | `"disk"` (default): a file still on disk counts as downloaded, so deleting it re-downloads it, but renamed files count as missing. `"url"`: remembers URLs in `logs/downloaded_urls.txt`, so you can rename freely, but deleting a file will not re-download it. |
| `B_SUFFIX_RANGE` | Range of B-variants to scan (default `B36`–`B99`). |
| `MISS_LIMIT` | Consecutive misses before skin scanning stops for a hero. |
| `UPDATE_CHECK_ON_START` | Check for updates when the app starts. |

### Build from source

**Requirements:** Python 3.10+

```bash
git clone https://github.com/KotexChick00/AovImageCrawler.git
cd AovImageCrawler
pip install -r requirements.txt
python main.py
```


### Legal notice

AoV Image Crawler is an independent tool and is **not affiliated with, sponsored by or endorsed by Garena, Level Infinite, Tencent, TIMi Studio Group** or any owner of Arena of Valor. Game names, hero names and images belong to their respective owners. This repository **does not contain any game assets**: images are only downloaded to your own machine when you run the tool. Please respect the game's terms of use and use downloaded images for legitimate personal purposes only.

### Code signing policy

Free code signing provided by [SignPath.io](https://about.signpath.io), certificate by [SignPath Foundation](https://signpath.org).

**Team roles**
- Authors, committers and reviewers: [KotexChick00](https://github.com/KotexChick00)
- Approvers: [KotexChick00](https://github.com/KotexChick00)

This is a single-maintainer project, so one person holds all roles. Multi-factor authentication is enabled on GitHub and SignPath.

**What is signed:** only `AoV.Image.Crawler.exe`, built by the GitHub Actions workflow [`release.yml`](.github/workflows/release.yml) from tagged commits of this repository. Every release is approved manually before signing.

**Privacy policy:** this program does not collect, store or transmit personal data. It only connects to:
1. Garena's public CDN (`dl.ops.kgtw.garenanow.com`) to download images, when you start a download.
2. GitHub, to check for new versions of the app and `hero.json` (at startup and via `7. update`). The request contains only what any HTTP request sends (IP address, user agent). The app always asks for confirmation before installing an update. To disable the startup check, set `UPDATE_CHECK_ON_START = False` in `modules/core/config.py` and build your own copy.

The privacy policies of these services apply to those connections, for example [GitHub](https://docs.github.com/site-policy/privacy-policies/github-general-privacy-statement). Download logs are written only to the `logs/` folder on your machine.

**Installation and removal:** the app is a portable single `.exe` and makes no changes to system configuration. To uninstall, delete the `.exe` and the `splash`, `head`, `bust` and `logs` folders and the `hero.json` file created by the app.

### Third-party licenses

| Component | License |
|---|---|
| [requests](https://github.com/psf/requests) | Apache-2.0 |
| [urllib3](https://github.com/urllib3/urllib3) | MIT |
| [idna](https://github.com/kjd/idna) | BSD-3-Clause |
| [charset-normalizer](https://github.com/jawah/charset_normalizer) | MIT |
| [certifi](https://github.com/certifi/python-certifi) | MPL-2.0 |
| [PyInstaller](https://github.com/pyinstaller/pyinstaller) (build tool) | GPL-2.0-or-later with bootloader exception |


---

## License

[GPL-3.0](LICENSE)