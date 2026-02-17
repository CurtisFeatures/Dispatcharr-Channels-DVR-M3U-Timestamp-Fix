#!/usr/bin/env python3
"""
M3U Modifier Script
Reads multiple M3U playlists from URLs, adds tvc-stream-timestamps="rewrite"
to each stream entry, and saves each modified playlist using the name
extracted from the /m3u/<name> portion of the URL.

Compatible with Python 3.8+
"""

import requests
import re
import sys
import os
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Optional, Tuple


# ── Configuration ────────────────────────────────────────────────────────────

M3U_URLS = [
    "http://10.0.60.51:9191/output/m3u/Sky?cachedlogos=false",
    "http://10.0.60.51:9191/output/m3u/FTA IPTV?cachedlogos=false",
    "http://10.0.60.51:9191/output/m3u/Kids?cachedlogos=false",
    # Add more URLs here as needed...
]

OUTPUT_DIR = "/caddy/M3U"   # Folder where modified .m3u files will be saved

# ─────────────────────────────────────────────────────────────────────────────


def extract_playlist_name(url: str) -> str:
    """
    Extract the playlist name from the URL path.

    e.g. http://host/output/m3u/FTA IPTV?cachedlogos=false  →  "FTA IPTV"
         http://host/output/m3u/Sky?cachedlogos=false          →  "Sky"
    """
    parsed = urlparse(url)
    path = unquote(parsed.path)          # decode %20 etc.

    # Grab everything after the last '/'
    name = path.split("/")[-1].strip()

    # Fallback if name is empty
    if not name:
        name = "playlist"

    return name


def fetch_m3u(url: str) -> Optional[str]:
    """Fetch M3U content from a URL. Returns None on failure."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        print(f"    ✓ Downloaded {len(response.text):,} characters")
        return response.text
    except requests.exceptions.ConnectionError:
        print(f"    ✗ Connection error – is the server reachable?")
        return None
    except requests.exceptions.Timeout:
        print("    ✗ Request timed out.")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"    ✗ HTTP error: {e}")
        return None


def add_timestamp_attribute(m3u_content: str) -> Tuple[str, int]:
    """
    Insert tvc-stream-timestamps="rewrite" into every #EXTINF line,
    placed immediately after the duration token.

    Before: #EXTINF:-1 tvg-id="250" ...
    After:  #EXTINF:-1 tvc-stream-timestamps="rewrite" tvg-id="250" ...

    Returns the modified content and a count of lines changed.
    """
    attribute = 'tvc-stream-timestamps="rewrite"'
    modified_lines = []
    count = 0

    for line in m3u_content.splitlines():
        if line.startswith("#EXTINF:") and attribute not in line:
            line = re.sub(
                r"(#EXTINF:-?\d+)",
                rf"\1 {attribute}",
                line,
                count=1
            )
            count += 1
        modified_lines.append(line)

    return "\n".join(modified_lines), count


def save_m3u(content: str, name: str, output_dir: str) -> Path:
    """Write the modified M3U content to a named file inside output_dir."""
    output_path = Path(output_dir) / f"{name}.m3u"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def process_url(url: str, output_dir: str) -> bool:
    """Fetch, modify, and save a single M3U URL. Returns True on success."""
    name = extract_playlist_name(url)
    print(f"\n  [{name}]")
    print(f"    URL: {url}")

    # Fetch
    raw_content = fetch_m3u(url)
    if raw_content is None:
        print(f"    ✗ Skipping '{name}' due to fetch error.")
        return False

    # Modify
    modified_content, count = add_timestamp_attribute(raw_content)
    print(f"    ✓ Added tvc-stream-timestamps to {count} stream entries")

    # Save
    output_path = save_m3u(modified_content, name, output_dir)
    size_kb = output_path.stat().st_size / 1024
    print(f"    ✓ Saved → {output_path.resolve()}  ({size_kb:.1f} KB)")

    return True


def main():
    print("=" * 60)
    print("  M3U Modifier – adding tvc-stream-timestamps")
    print(f"  Processing {len(M3U_URLS)} playlist(s)")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    for url in M3U_URLS:
        if process_url(url, OUTPUT_DIR):
            success_count += 1
        else:
            fail_count += 1

    print("\n" + "=" * 60)
    print(f"  Completed:  {success_count} succeeded  |  {fail_count} failed")
    print(f"  Output dir: {Path(OUTPUT_DIR).resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
