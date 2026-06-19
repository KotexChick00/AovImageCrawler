# Changelog

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