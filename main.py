import requests
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Configuration
SPLASH_URL = "https://dl.ops.kgtw.garenanow.com/CHT/HeroTrainingLoadingNew_B36/"
HEAD_URL = "https://dl.ops.kgtw.garenanow.com/CHT/HeroHeadPath/"
HEAD_REQUIRED_PREFIX = "30"
HEAD_ICON_REQUIRED_SUFFIX = "head"
SUFFIX_RANGE = range(100)        # skin index 00 to 99
B_SUFFIX_RANGE = range(36, 100)  # B36 to B99 (splash only)
OUTPUT_DIR = "."
EVO5_ALT_SUFFIX = "_2"
# Lưu dưới dạng (hero_id, skin_index) để dùng chung cho splash, head, frame
# Splash dùng :02 padding, head/frame không dùng padding — tách rõ ở đây
EVO5_SKIN_LIST: list[tuple[int, int]] = [
    (116, 20),   # splash: 11620,   head/frame: 3011620
    (133, 11),   # splash: 13311,   head/frame: 3013311
    (167,  7),   # splash: 16707,   head/frame: 301677
]
MISS_LIMIT = 15                  # dừng vòng lặp skin sau N miss liên tiếp

FLOWBORN_SPECIAL_HERO_ID = [582,584] # 582 là pháp sư, 584 là xạ thủ
FLOWBORN_UNIQUE_SUFFIX_ID = "00"
FLOWBORN_GENDER_SUFFIX_FRAME =["m","f"] # giả sử có 2 giới tính, nếu có thể xác định thì sẽ dùng suffix tương ứng thay vì loop cả 2
SPECIAL_FRAME = ["301270_B51"]

SPLASH_DIR = os.path.join(OUTPUT_DIR, "splash")
HEAD_DIR = os.path.join(OUTPUT_DIR, "head")
FRAME_DIR = os.path.join(OUTPUT_DIR, "frame")
LOG_DIR = os.path.join(OUTPUT_DIR, "logs")

# Thread-safe session tracking
_session_lock = threading.Lock()
_session_downloads = []


def _record_session(file_path):
    with _session_lock:
        _session_downloads.append(file_path)


def write_session_log(finished_at: datetime):
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    timestamp = finished_at.strftime("%Y%m%d%H%M%S")
    log_filename = os.path.join(LOG_DIR, f"{timestamp}.log")
    with open(log_filename, "w", encoding="utf-8") as f:
        f.write(f"=== Session log — {finished_at.strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        f.write(f"Total new files downloaded: {len(_session_downloads)}\n\n")
        for path in sorted(_session_downloads):
            f.write(f"{os.path.basename(path)}\n")
    print(f"\nSession log saved: {log_filename} ({len(_session_downloads)} new file(s))")


def select_mode():
    print("=" * 40)
    print("  Chọn chế độ tải:")
    print("  1. splash  — chỉ tải splash")
    print("  2. head    — chỉ tải head")
    print("  3. frame   — chỉ tải frame")
    print("  4. all     — tải tất cả (mặc định)")
    print("=" * 40)
    choice = input("Nhập lựa chọn [1/2/3/4], Enter để chọn all: ").strip()
    if choice == "1":
        print("→ Chế độ: splash\n")
        return "splash"
    elif choice == "2":
        print("→ Chế độ: head\n")
        return "head"
    elif choice == "3":
        print("→ Chế độ: frame\n")
        return "frame"
    else:
        print("→ Chế độ: all\n")
        return "all"


def fetch_hero_ids():
    return list(range(105, 800))


def _append_persistent_log(file_path):
    with _session_lock:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(os.path.join(LOG_DIR, "download.log"), "a") as logf:
            logf.write(f"{file_path}\n")


# ── Miss counter (shared per hero across splash + head) ───────────────────────

class MissCounter:
    """Thread-safe counter tracking consecutive missing skin IDs for one hero."""
    def __init__(self, limit):
        self._lock = threading.Lock()
        self._count = 0
        self.limit = limit
        self.stopped = False

    def hit(self):
        """A file was found — reset the streak."""
        with self._lock:
            self._count = 0

    def miss(self):
        """A file was not found — increment streak, return True if limit reached."""
        with self._lock:
            self._count += 1
            if self._count >= self.limit:
                self.stopped = True
            return self.stopped


# ── ID builders ───────────────────────────────────────────────────────────────

def is_evo5_skin(hero_id, skin_index):
    return (hero_id, skin_index) in EVO5_SKIN_LIST

def build_splash_id(hero_id, skin_index, evo5=False):
    """
    Splash skin ID: {hero_id}{skin_index:02}[_2]
    e.g. hero=196, skin=2        → 19602
         hero=196, skin=2, evo5  → 19602_2
    """
    base = f"{hero_id}{skin_index:02}"
    return f"{base}{EVO5_ALT_SUFFIX}" if evo5 else base


def build_head_id(hero_id, skin_index, evo5=False):
    """
    Head skin ID: 30{hero_id}{skin_index}[_2]head
    Skin index has NO zero-padding for head.
    e.g. hero=196, skin=0        → 301960head
         hero=196, skin=2        → 301962head
         hero=196, skin=2, evo5  → 301962_2head
    """
    skin_part = str(skin_index) if skin_index != 0 else "0"
    evo_part = EVO5_ALT_SUFFIX if evo5 else ""
    return f"{HEAD_REQUIRED_PREFIX}{hero_id}{skin_part}{evo_part}{HEAD_ICON_REQUIRED_SUFFIX}"


# ── Generic download util ─────────────────────────────────────────────────────

def _download(url, save_dir, filename):
    """Download url → save_dir/filename if not already on disk.
    Returns 'downloaded', 'exists', or 'missing'."""
    file_path = os.path.join(save_dir, filename)
    if os.path.exists(file_path):
        print(f"Already exists: {file_path}")
        return "exists"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            os.makedirs(save_dir, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded: {file_path}")
            _append_persistent_log(file_path)
            _record_session(file_path)
            return "downloaded"
        else:
            print(f"Not found: {url}")
            return "missing"
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return "missing"


# ── Splash ────────────────────────────────────────────────────────────────────

def process_splash_downloads(hero_id, miss_counter):
    hero_dir = os.path.join(SPLASH_DIR, str(hero_id))
    base_id = build_splash_id(hero_id, 0)
    result = _download(f"{SPLASH_URL}{base_id}.jpg", hero_dir, f"{base_id}.jpg")

    base_path = os.path.join(hero_dir, f"{base_id}.jpg")
    if result == "missing" and not os.path.exists(base_path):
        return

    # Run skin variants sequentially to respect miss_counter ordering
    for skin_index in SUFFIX_RANGE:
        if skin_index == 0:
            continue
        if miss_counter.stopped:
            print(f"[splash] Hero {hero_id}: miss limit reached, stopping skin loop.")
            break
        _splash_variant(hero_id, hero_dir, skin_index, miss_counter)

    # B_suffix runs independently — not affected by miss counter
    with ThreadPoolExecutor(max_workers=5) as sub:
        for b_suffix in B_SUFFIX_RANGE:
            sub.submit(_splash_b_variant, hero_id, hero_dir, b_suffix)


def _splash_variant(hero_id, hero_dir, skin_index, miss_counter):
    file_id = build_splash_id(hero_id, skin_index)
    result = _download(f"{SPLASH_URL}{file_id}.jpg", hero_dir, f"{file_id}.jpg")

    if result == "missing":
        miss_counter.miss()
    else:
        miss_counter.hit()
        # EVO5 variant — check by skin ID (e.g. 11620 = hero 116, skin 20)
        if is_evo5_skin(hero_id, skin_index):
            evo_id = build_splash_id(hero_id, skin_index, evo5=True)
            _download(f"{SPLASH_URL}{evo_id}.jpg", hero_dir, f"{evo_id}.jpg")


def _splash_b_variant(hero_id, hero_dir, b_suffix):
    """B-suffix variants: {hero_id}00_B{b_suffix}.jpg"""
    file_id = f"{hero_id}00_B{b_suffix}"
    _download(f"{SPLASH_URL}{file_id}.jpg", hero_dir, f"{file_id}.jpg")


# ── Head ──────────────────────────────────────────────────────────────────────

def process_head_downloads(hero_id, miss_counter):
    hero_dir = os.path.join(HEAD_DIR, str(hero_id))
    base_id = build_head_id(hero_id, 0)
    result = _download(f"{HEAD_URL}{base_id}.jpg", hero_dir, f"{base_id}.jpg")

    base_path = os.path.join(hero_dir, f"{base_id}.jpg")
    if result == "missing" and not os.path.exists(base_path):
        return

    for skin_index in SUFFIX_RANGE:
        if skin_index == 0:
            continue
        if miss_counter.stopped:
            print(f"[head] Hero {hero_id}: miss limit reached, stopping skin loop.")
            break
        _head_variant(hero_id, hero_dir, skin_index, miss_counter)


def _head_variant(hero_id, hero_dir, skin_index, miss_counter):
    file_id = build_head_id(hero_id, skin_index)
    result = _download(f"{HEAD_URL}{file_id}.jpg", hero_dir, f"{file_id}.jpg")

    if result == "missing":
        miss_counter.miss()
    else:
        miss_counter.hit()
        # EVO5 variant — check by skin ID (e.g. 11620 = hero 116, skin 20)
        if is_evo5_skin(hero_id, skin_index):
            evo_id = build_head_id(hero_id, skin_index, evo5=True)
            _download(f"{HEAD_URL}{evo_id}.jpg", hero_dir, f"{evo_id}.jpg")



# ── Frame ─────────────────────────────────────────────────────────────────────

def build_frame_id(hero_id, skin_index, evo5=False):
    """
    Frame skin ID: 30{hero_id}{skin_index}[_2]  (giống head nhưng không có 'head' ở cuối)
    e.g. hero=196, skin=2        → 301962
         hero=196, skin=2, evo5  → 301962_2
    """
    skin_part = str(skin_index) if skin_index != 0 else "0"
    evo_part = EVO5_ALT_SUFFIX if evo5 else ""
    return f"{HEAD_REQUIRED_PREFIX}{hero_id}{skin_part}{evo_part}"


def build_frame_flowborn_id(hero_id, gender):
    """
    Flowborn frame ID: 30{hero_id}{FLOWBORN_UNIQUE_SUFFIX_ID}{gender}
    e.g. hero=582, gender=m → 3058200m
    """
    return f"{HEAD_REQUIRED_PREFIX}{hero_id}{FLOWBORN_UNIQUE_SUFFIX_ID}{gender}"


def _parse_special_frame_hero_id(file_id):
    """Lấy hero_id từ file_id đặc biệt.
    Quy tắc: bỏ prefix HEAD_REQUIRED_PREFIX (2 ký tự), lấy các chữ số liên tiếp tiếp theo.
    e.g. '301270_B51' → prefix='30', digits='1270' → hero_id_str='127' (bỏ chữ số 0 padding cuối? Không — lấy toàn bộ digits phần hero)
    Thực ra: 301270 → 30 + 127 + 0(skin=0), nên hero_id = int('127')
    Ta dùng cách: bỏ prefix '30', lấy phần trước '_' hoặc hết, rồi bỏ chữ số cuối (skin index).
    """
    import re
    # Bỏ prefix "30"
    without_prefix = file_id[len(HEAD_REQUIRED_PREFIX):]
    # Lấy phần số đầu tiên (trước _)
    digits = re.match(r'(\d+)', without_prefix).group(1)
    # digits = "1270" → hero_id = digits[:-1] = "127", skin = digits[-1] = "0"
    return int(digits[:-1])


def _download_special_frames(hero_id, hero_dir):
    """Tải các frame đặc biệt trong SPECIAL_FRAME nếu thuộc về hero_id này."""
    for file_id in SPECIAL_FRAME:
        if _parse_special_frame_hero_id(file_id) == hero_id:
            _download(f"{HEAD_URL}{file_id}.jpg", hero_dir, f"{file_id}.jpg")


def process_frame_downloads(hero_id, miss_counter):
    hero_dir = os.path.join(FRAME_DIR, str(hero_id))

    # Flowborn: chỉ tải theo quy tắc đặc biệt, bỏ qua vòng lặp skin thường
    if hero_id in FLOWBORN_SPECIAL_HERO_ID:
        for gender in FLOWBORN_GENDER_SUFFIX_FRAME:
            file_id = build_frame_flowborn_id(hero_id, gender)
            _download(f"{HEAD_URL}{file_id}.jpg", hero_dir, f"{file_id}.jpg")
        return

    # Special frames — tải trực tiếp khi đúng hero
    _download_special_frames(hero_id, hero_dir)

    # Frame thường
    base_id = build_frame_id(hero_id, 0)
    result = _download(f"{HEAD_URL}{base_id}.jpg", hero_dir, f"{base_id}.jpg")

    base_path = os.path.join(hero_dir, f"{base_id}.jpg")
    if result == "missing" and not os.path.exists(base_path):
        return

    for skin_index in SUFFIX_RANGE:
        if skin_index == 0:
            continue
        if miss_counter.stopped:
            print(f"[frame] Hero {hero_id}: miss limit reached, stopping skin loop.")
            break
        _frame_variant(hero_id, hero_dir, skin_index, miss_counter)


def _frame_variant(hero_id, hero_dir, skin_index, miss_counter):
    file_id = build_frame_id(hero_id, skin_index)
    result = _download(f"{HEAD_URL}{file_id}.jpg", hero_dir, f"{file_id}.jpg")

    if result == "missing":
        miss_counter.miss()
    else:
        miss_counter.hit()
        # EVO5 variant — check by skin ID (e.g. 11620 = hero 116, skin 20)
        if is_evo5_skin(hero_id, skin_index):
            evo_id = build_frame_id(hero_id, skin_index, evo5=True)
            _download(f"{HEAD_URL}{evo_id}.jpg", hero_dir, f"{evo_id}.jpg")

# ── Main ──────────────────────────────────────────────────────────────────────

def process_hero(hero_id, mode):
    """Process one hero — mỗi loại (splash/head/frame) dùng MissCounter riêng
    để tránh counter của splash làm dừng vòng lặp skin của head/frame."""
    if mode in ("splash", "all"):
        process_splash_downloads(hero_id, MissCounter(limit=MISS_LIMIT))
    if mode in ("head", "all"):
        process_head_downloads(hero_id, MissCounter(limit=MISS_LIMIT))
    if mode in ("frame", "all"):
        process_frame_downloads(hero_id, MissCounter(limit=MISS_LIMIT))


def main():
    mode = select_mode()

    os.makedirs(SPLASH_DIR, exist_ok=True)
    os.makedirs(HEAD_DIR, exist_ok=True)
    os.makedirs(FRAME_DIR, exist_ok=True)

    hero_ids = fetch_hero_ids()

    with ThreadPoolExecutor(max_workers=10) as executor:
        for hero_id in hero_ids:
            executor.submit(process_hero, hero_id, mode)

    finished_at = datetime.now()
    write_session_log(finished_at)


def test_specific():
    # Chỉ định danh sách hero chứa các skin EVO5 bạn muốn test
    test_heroes = [116, 133, 167]
    mode = "all" # hoặc "head", "frame" tùy bạn
    
    print(f"--- Đang test các hero: {test_heroes} ---")
    with ThreadPoolExecutor(max_workers=5) as executor:
        for hero_id in test_heroes:
            executor.submit(process_hero, hero_id, mode)

    finished_at = datetime.now()
    write_session_log(finished_at)
    
if __name__ == "__main__":
    # main()
    test_specific()