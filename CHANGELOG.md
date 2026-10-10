# Changelog

## [1.2.0] - 2026-10-10
### 🇻🇳 Tính năng mới
- Tải **B-variant** (`B36`–`B99`) của skin gốc cho cả **head** và **bust** (trước đây chỉ có splash). Chỉ quét khi skin gốc (skin 0) tồn tại; hero Flowborn (582, 584) không có B-variant nên bị loại khỏi vòng quét.
- Module **đổi tên** riêng (`modules/utils/renamer.py`): đổi file từ ID gốc sang `Hero_{Loại}_{Tên}_{ID}_{Skin}`. Có chế độ xem trước (dry-run), không bao giờ ghi đè, an toàn khi chạy lại. Menu mới: `5. rename` và `6. all+rename`.
- **Tự cập nhật** (`modules/utils/updater.py`): kiểm tra khi mở app và ở menu `7. update`. Cập nhật file `.exe` từ GitHub Releases (xác minh SHA-256 nếu release có file `.sha256`) và cập nhật `hero.json` từ repo (sao lưu bản cũ thành `hero.json.bak`).
- Số phiên bản lấy từ **tag Git** khi build (`build.ps1` hoặc workflow `release.yml`), không còn sửa tay trong `config.py`.
- Tùy chọn `DUPLICATE_CHECK` (`disk` / `url`) để chọn cách kiểm tra file đã tải. Chế độ `url` ghi nhớ URL trong `logs/downloaded_urls.txt`, không phụ thuộc tên file.
- Hiển thị lỗi của các luồng xử lý ở cuối phiên (trước đây bị bỏ qua im lặng).

### 🇻🇳 Sửa lỗi
- Sửa lỗi không tải được `301270_B51`, `301480_B55` (Azzen'Ka, Preyta) và bản `head` tương ứng: tên file lưu trùng với skin 0 nên bị bỏ qua do "Already exists", và chưa có logic tạo ID dạng `...head_B51`.
- Sửa lỗi không tìm thấy `hero.json` khi chạy bản `.exe` đóng gói (nay tìm cạnh file exe, trong file đóng gói kèm, thư mục đang chạy, hoặc theo cấu trúc mã nguồn).
- Bust và Splash kiểm tra "hero có tồn tại" bằng `glob` thay vì cứng đuôi `.jpg`, không còn bỏ sót file `.png` / `.webp`.
- Sửa khóa ghi `download.log` (trước đây tạo lock mới mỗi lần nên không có tác dụng).

### 🇻🇳 Thay đổi
- ⚠️ File tải về giờ lưu theo **ID gốc trên server** (vd `301270head_B51.jpg`); việc đặt tên dễ đọc chuyển sang bước đổi tên. Thư mục đã có file `Hero_*` từ bản cũ có thể bị trùng với file mới — hãy chạy `rename` ở chế độ xem trước để phát hiện xung đột.
- Bỏ `SPECIAL_BUST` và `parse_hero_id_from_special`, thay bằng quét B-variant tự động.
- Không in dòng `Not found` cho các lần quét B (log gọn hơn).

---

### 🇬🇧 Added
- Download **B-variants** (`B36`–`B99`) of the base skin for both **head** and **bust** (previously splash only). Scanned only when the base skin (skin 0) exists; Flowborn heroes (582, 584) have no B-variants and are excluded.
- Separate **rename** module (`modules/utils/renamer.py`): renames files from raw IDs to `Hero_{Type}_{Name}_{ID}_{Skin}`. Includes a dry-run preview, never overwrites, and is safe to re-run. New menu entries: `5. rename` and `6. all+rename`.
- **Auto-update** (`modules/utils/updater.py`): checked on startup and via menu `7. update`. Updates the `.exe` from GitHub Releases (SHA-256 verified when the release has a `.sha256` file) and `hero.json` from the repo (previous copy kept as `hero.json.bak`).
- App version now comes from the **Git tag** at build time (`build.ps1` or the `release.yml` workflow) — no more manual edits in `config.py`.
- `DUPLICATE_CHECK` option (`disk` / `url`) to choose how already-downloaded files are detected. `url` mode remembers URLs in `logs/downloaded_urls.txt`, independent of file names.
- Worker-thread errors are now reported at the end of a run (previously swallowed silently).

### 🇬🇧 Fixed
- Fixed `301270_B51`, `301480_B55` (Azzen'Ka, Preyta) and their `head` counterparts not downloading: the saved filename collided with skin 0 and was skipped as "Already exists", and no logic existed to build `...head_B51` IDs.
- Fixed `hero.json` not being found when running the packaged `.exe` (now looked up next to the exe, in the bundled copy, in the working directory, or in the source layout).
- Bust and Splash now check hero existence with `glob` instead of a hardcoded `.jpg`, no longer missing `.png` / `.webp` files.
- Fixed the `download.log` write lock (a new lock was created on every call, so it had no effect).

### 🇬🇧 Changed
- ⚠️ Downloaded files are now saved by their **original server ID** (e.g. `301270head_B51.jpg`); readable naming moved to the rename step. Folders that already contain `Hero_*` files from older versions may end up with duplicates — run `rename` in preview mode to detect conflicts.
- Removed `SPECIAL_BUST` and `parse_hero_id_from_special`, replaced by automatic B-variant scanning.
- `Not found` lines are no longer printed during B-variant scans (cleaner output).

## [1.1.0] - 2026-06-19
### 🇻🇳 Tính năng mới
- Tự động nhận diện định dạng file thực tế (JPEG/PNG/GIF/WEBP/BMP) dựa trên **magic bytes** của nội dung tải về, thay vì tin tưởng đuôi `.jpg` mặc định.
- `HttpClient.download()` giờ nhận `file_id` (không đuôi) thay vì filename cố định; đuôi file thật được gán **sau khi** tải về.
- Kiểm tra file đã tồn tại dựa trên base name (`{file_id}.*`) thay vì đuôi cố định, đảm bảo không tải trùng dù file cũ có đuôi khác.

### 🇻🇳 Sửa lỗi
- Khắc phục tình trạng một số file tải về có MIME không khớp với đuôi file được gán (ví dụ ảnh PNG bị lưu nhầm đuôi `.jpg`).

### 🇻🇳 Thay đổi
- `BaseAssetDownloader._fetch()` và `process_hero()` cập nhật để tương thích với cơ chế nhận diện đuôi file mới (sử dụng `glob` thay vì giả định cứng `.jpg`).

---

### 🇬🇧 Added
- Auto-detect real file format (JPEG/PNG/GIF/WEBP/BMP) via **magic bytes** of the downloaded content, instead of trusting a fixed `.jpg` extension.
- `HttpClient.download()` now accepts a bare `file_id` (no extension) instead of a fixed filename; the real extension is assigned **after** the content is fetched.
- Existence check now matches by base name (`{file_id}.*`) instead of a fixed extension, preventing duplicate downloads when an existing file has a different extension.

### 🇬🇧 Fixed
- Fixed downloaded files having a MIME type mismatched with their assigned extension (e.g. a PNG image incorrectly saved with a `.jpg` extension).

### 🇬🇧 Changed
- `BaseAssetDownloader._fetch()` and `process_hero()` updated to work with the new extension-detection mechanism (using `glob` instead of a hardcoded `.jpg`).

## [1.0.4] - 2026-04-28
### 🇻🇳 Sửa lỗi
- Sửa lỗi **shared mutable state** khiến `head` và `frame` không thể tải phiên bản EVO5.
- Sửa lỗi logic trong script `main.py` khi cào dữ liệu ảnh.

### 🇬🇧 Fixes
- Fixed **shared mutable state** causing `head` and `frame` EVO5 download failure.
- Corrected crawling logic in `main.py` to ensure stable image data retrieval.