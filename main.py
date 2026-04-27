"""AovImageCrawler — download AoV splash art from the KGTW server."""

import argparse
import os
import sys
import time

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.kgtw.net"
HEROES_PATH = "/hero"
DEFAULT_OUTPUT = "images"
REQUEST_TIMEOUT = 30
RETRY_DELAY = 2
POLITE_DELAY = 0.5


def get_hero_links(session: requests.Session, base_url: str) -> list[str]:
    """Return all hero detail-page URLs found on the heroes listing page."""
    url = base_url.rstrip("/") + HEROES_PATH
    print(f"Fetching hero list from {url} …")
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    links: list[str] = []
    for anchor in soup.select("a[href]"):
        href: str = anchor["href"]
        if "/hero/" in href:
            full = href if href.startswith("http") else base_url.rstrip("/") + href
            if full not in links:
                links.append(full)

    print(f"Found {len(links)} hero page(s).")
    return links


def get_splash_url(session: requests.Session, hero_url: str) -> str | None:
    """Return the splash-art image URL from a single hero page, or None."""
    try:
        response = session.get(hero_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"  WARNING: could not fetch {hero_url}: {exc}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Try common patterns: og:image meta tag first, then the first large <img>.
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return og["content"]

    for img in soup.find_all("img"):
        src: str = img.get("src", "")
        if any(kw in src.lower() for kw in ("splash", "hero", "character", "art")):
            if src.startswith("http"):
                return src
            return BASE_URL.rstrip("/") + ("" if src.startswith("/") else "/") + src

    return None


def download_image(
    session: requests.Session, url: str, dest_dir: str, filename: str
) -> bool:
    """Download *url* and save it as *filename* inside *dest_dir*."""
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, filename)
    if os.path.exists(dest_path):
        print(f"  Skipping (already exists): {filename}")
        return True
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT, stream=True)
        response.raise_for_status()
        with open(dest_path, "wb") as fout:
            for chunk in response.iter_content(chunk_size=8192):
                fout.write(chunk)
        print(f"  Saved: {filename}")
        return True
    except requests.RequestException as exc:
        print(f"  ERROR downloading {url}: {exc}")
        return False


def safe_filename(url: str) -> str:
    """Derive a safe local filename from an image URL."""
    name = url.split("?")[0].rstrip("/").split("/")[-1]
    # Replace characters that are unsafe on common file systems.
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "_")
    # Fall back when the result is empty or consists only of underscores.
    return name.strip("_") or "image.jpg"


def run(base_url: str, output_dir: str) -> None:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; AovImageCrawler/1.0; "
            "+https://github.com/KotexChick00/AovImageCrawler)"
        )
    }
    with requests.Session() as session:
        session.headers.update(headers)

        hero_links = get_hero_links(session, base_url)
        if not hero_links:
            print("No hero links found. Check BASE_URL or the site structure.")
            sys.exit(1)

        downloaded = 0
        for i, hero_url in enumerate(hero_links, start=1):
            print(f"[{i}/{len(hero_links)}] {hero_url}")
            splash_url = get_splash_url(session, hero_url)
            if not splash_url:
                print("  No splash image found — skipping.")
                continue
            filename = safe_filename(splash_url)
            if download_image(session, splash_url, output_dir, filename):
                downloaded += 1
            time.sleep(POLITE_DELAY)  # be polite to the server

    print(f"\nDone. Downloaded {downloaded} image(s) to '{output_dir}'.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download AoV splash art from the KGTW server."
    )
    parser.add_argument(
        "--url",
        default=BASE_URL,
        help=f"Base URL of the KGTW site (default: {BASE_URL})",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Directory to save images (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    run(args.url, args.output)


if __name__ == "__main__":
    main()
