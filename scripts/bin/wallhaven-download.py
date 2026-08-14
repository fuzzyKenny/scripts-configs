#!/usr/bin/env python3
"""Download new wallpapers from Wallhaven into a local folder.

Uses the Wallhaven API: https://wallhaven.cc/help/api
Set WALLHAVEN_API_KEY in your environment if you want authenticated results.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from math import gcd
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API_BASE = "https://wallhaven.cc/api/v1/search"
USER_AGENT = "wallhaven-download-script/1.0"


def request_json(url):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download_file(url, dest):
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=60) as resp, open(tmp, "wb") as fh:
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            fh.write(chunk)
    tmp.rename(dest)


def load_state(path):
    if not path.exists():
        return {"downloaded_ids": []}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        data.setdefault("downloaded_ids", [])
        return data
    except (OSError, json.JSONDecodeError):
        return {"downloaded_ids": []}


def save_state(path, state):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")
    tmp.rename(path)


def ext_from_wallpaper(item):
    file_type = item.get("file_type", "")
    if file_type == "image/png":
        return ".png"
    if file_type in ("image/jpeg", "image/jpg"):
        return ".jpg"
    return Path(item.get("path", "wallpaper.jpg")).suffix or ".jpg"


def detect_main_display_resolution():
    """Return (width, height) for the main macOS display, or None if unavailable."""
    try:
        output = subprocess.check_output(
            ["system_profiler", "SPDisplaysDataType"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )
    except Exception:
        return None

    blocks = re.split(r"\n\s{4,}[^\n:]+:\n", "\n" + output)
    first_resolution = None
    for block in blocks:
        match = re.search(r"Resolution:\s*(\d+)\s*x\s*(\d+)", block)
        if not match:
            continue
        resolution = (int(match.group(1)), int(match.group(2)))
        if first_resolution is None:
            first_resolution = resolution
        if "Main Display: Yes" in block:
            return resolution
    return first_resolution


def ratio_from_resolution(width, height):
    divisor = gcd(width, height)
    return f"{width // divisor}x{height // divisor}"


def closest_common_resolution(width, height):
    """Return the closest common wallpaper resolution to the detected display."""
    common = [
        (1280, 720),
        (1366, 768),
        (1440, 900),
        (1600, 900),
        (1680, 1050),
        (1920, 1080),
        (1920, 1200),
        (2048, 1152),
        (2560, 1080),
        (2560, 1440),
        (2560, 1600),
        (3440, 1440),
        (3840, 1600),
        (3840, 2160),
        (5120, 1440),
        (5120, 2160),
        (5120, 2880),
    ]
    target_ratio = width / height

    def score(resolution):
        w, h = resolution
        ratio_penalty = abs((w / h) - target_ratio) * 10000
        size_penalty = abs(w - width) + abs(h - height)
        return ratio_penalty + size_penalty

    return min(common, key=score)


def build_search_url(args, page):
    params = {
        "q": args.query,
        "categories": args.categories,
        "purity": args.purity,
        "sorting": args.sorting,
        "order": args.order,
        "page": page,
    }
    if args.atleast:
        params["atleast"] = args.atleast
    if args.resolutions:
        params["resolutions"] = args.resolutions
    if args.ratios:
        params["ratios"] = args.ratios
    if args.top_range:
        params["topRange"] = args.top_range
    if args.api_key:
        params["apikey"] = args.api_key
    return API_BASE + "?" + urlencode(params)


def main():
    parser = argparse.ArgumentParser(description="Download new wallpapers from Wallhaven.")
    parser.add_argument("--folder", default="~/Pictures/Wallpapers", help="download folder")
    parser.add_argument("--limit", type=int, default=10, help="max new wallpapers to download")
    parser.add_argument("--pages", type=int, default=3, help="max API pages to scan")
    parser.add_argument("--query", "-q", default="", help="Wallhaven search query/tags")
    parser.add_argument("--categories", default="111", help="general/anime/people bitmask; default all categories")
    parser.add_argument("--purity", default="100", help="sfw/sketchy/nsfw bitmask; default SFW only")
    parser.add_argument("--sorting", default="toplist", choices=["date_added", "relevance", "random", "views", "favorites", "toplist"], help="sort mode")
    parser.add_argument("--order", default="desc", choices=["desc", "asc"], help="sort order")
    parser.add_argument("--top-range", default="1M", choices=["1d", "3d", "1w", "1M", "3M", "6M", "1y"], help="time range when sorting=toplist")
    parser.add_argument("--atleast", default=None, help="minimum resolution, e.g. 1920x1080")
    parser.add_argument("--resolutions", default=None, help="exact resolutions, comma-separated; default uses closest common monitor resolution")
    parser.add_argument("--ratios", default=None, help="aspect ratios, comma-separated; default uses closest common monitor resolution ratio")
    parser.add_argument("--no-monitor-match", action="store_true", help="do not auto-apply detected monitor resolution/ratio")
    parser.add_argument("--no-ratio-fallback", action="store_true", help="do not retry without ratio if too few exact-ratio wallpapers are found")
    parser.add_argument("--api-key", default=os.environ.get("WALLHAVEN_API_KEY"), help="Wallhaven API key or WALLHAVEN_API_KEY env var")
    parser.add_argument("--sleep", type=float, default=1.0, help="seconds between downloads")
    args = parser.parse_args()

    if not args.no_monitor_match and (not args.resolutions or not args.ratios):
        resolution = detect_main_display_resolution()
        if resolution:
            width, height = resolution
            common_width, common_height = closest_common_resolution(width, height)
            if not args.resolutions and not args.atleast:
                args.resolutions = f"{common_width}x{common_height}"
            if not args.ratios:
                args.ratios = ratio_from_resolution(common_width, common_height)
            print(
                f"Detected monitor {width}x{height}; "
                f"using closest common resolution={args.resolutions}, ratio={args.ratios}"
            )
        else:
            print("Could not auto-detect monitor resolution; continuing without monitor match.", file=sys.stderr)

    folder = Path(args.folder).expanduser()
    folder.mkdir(parents=True, exist_ok=True)
    state_path = folder / ".wallhaven_downloads.json"
    state = load_state(state_path)
    downloaded_ids = set(state.get("downloaded_ids", []))

    new_count = 0
    failures = 0

    def search_and_download():
        nonlocal new_count, failures
        for page in range(1, args.pages + 1):
            if new_count >= args.limit:
                break
            url = build_search_url(args, page)
            try:
                payload = request_json(url)
            except HTTPError as exc:
                print(f"API error {exc.code}: {exc.reason}", file=sys.stderr)
                return 1
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                print(f"API request failed: {exc}", file=sys.stderr)
                return 1

            items = payload.get("data", [])
            if not items:
                break

            for item in items:
                if new_count >= args.limit:
                    break

                wid = item.get("id")
                if not wid or wid in downloaded_ids:
                    continue

                ext = ext_from_wallpaper(item)
                filename = f"wallhaven-{wid}{ext}"
                dest = folder / filename
                if dest.exists():
                    downloaded_ids.add(wid)
                    continue

                print(f"Downloading {wid}: {item.get('path')} -> {dest}")
                try:
                    download_file(item["path"], dest)
                except Exception as exc:  # keep going if one file fails
                    failures += 1
                    print(f"Failed {wid}: {exc}", file=sys.stderr)
                    continue

                downloaded_ids.add(wid)
                new_count += 1
                state["downloaded_ids"] = sorted(downloaded_ids)
                save_state(state_path, state)
                time.sleep(args.sleep)
        return 0

    result = search_and_download()
    if result:
        return result

    if new_count < args.limit and args.ratios and not args.no_ratio_fallback:
        old_ratio = args.ratios
        args.ratios = None
        print(f"Only found {new_count} with ratio {old_ratio}; retrying without ratio to fill the limit.")
        result = search_and_download()
        if result:
            return result

    state["downloaded_ids"] = sorted(downloaded_ids)
    save_state(state_path, state)
    print(f"Done. Downloaded {new_count} new wallpaper(s) to {folder}.")
    if failures:
        print(f"{failures} download(s) failed.", file=sys.stderr)
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
