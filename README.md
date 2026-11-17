# 📺 Dispatcharr → Channels DVR: M3U Timestamp Fix

> **Workaround** — Adds `tvc-stream-timestamps="rewrite"` to M3U entries so Channels DVR can correctly record IPTV streams from Dispatcharr.

> ## ⚠️ Replaced by a Dispatcharr plugin
>
> This script has been replaced by the **[M3U Stream Tag plugin](https://github.com/CurtisFeatures/Dispatcharr_m3u_stream_tag)**. The plugin runs inside Dispatcharr and adds
> the tag to its M3U output directly, so you no longer need this script, a cron job or a file server in between.
> Point Channels DVR straight at your Dispatcharr playlist addresses.
>
> **➡️ [Get the plugin](https://github.com/CurtisFeatures/Dispatcharr_m3u_stream_tag)**
>
> This repository is kept for reference and is no longer being developed.

---

## The Problem

When using [Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) as an IPTV source for [Channels DVR](https://getchannels.com/), recordings of live IPTV streams can fail or produce broken files due to incorrect stream timestamps.

Channels DVR supports a per-stream tag — `tvc-stream-timestamps="rewrite"` — that instructs it to rewrite timestamps on ingest, fixing the issue. Dispatcharr does not currently expose a way to inject this tag into its M3U output.

This script bridged that gap. It has now been replaced by the [M3U Stream Tag plugin](https://github.com/CurtisFeatures/Dispatcharr_m3u_stream_tag), which does the same job inside Dispatcharr.

---

## How It Works

```
Dispatcharr M3U URL
        │
        ▼
  Python Script
  (adds tvc-stream-timestamps="rewrite" to every #EXTINF line)
        │
        ▼
  Modified .m3u files
  served via Caddy on your LAN
        │
        ▼
  Channels DVR
  (uses modified M3U — recordings work correctly)
```

The script:
1. Fetches one or more M3U playlists from your Dispatcharr instance
2. Injects `tvc-stream-timestamps="rewrite"` into every `#EXTINF` line
3. Saves each playlist as a named `.m3u` file (e.g. `TNT Sports.m3u`, `Sky.m3u`)
4. Files are served locally over your LAN via Caddy

---

## Requirements

- Python 3.8+
- `requests` library (`pip install requests`)
- A running [Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) instance
- [Caddy](https://caddyserver.com/) (or any file server) to serve the output files

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/dispatcharr-m3u-fix.git
cd dispatcharr-m3u-fix
```

### 2. Install dependencies

```bash
pip install requests
```

### 3. Configure the script

Edit `m3u-update.py` and update the two configuration values at the top:

```python
M3U_URLS = [
    "http://<your-dispatcharr-ip>:<port>/output/m3u/TNT Sports?cachedlogos=false",
    "http://<your-dispatcharr-ip>:<port>/output/m3u/Sky?cachedlogos=false",
    # Add more playlists as needed...
]

OUTPUT_DIR = "/caddy/M3U"  # Where the modified .m3u files will be saved
```

### 4. Run the script

```bash
python m3u-update.py
```

Example output:
```
============================================================
  M3U Modifier – adding tvc-stream-timestamps
  Processing 9 playlist(s)
============================================================

  [TNT Sports]
    URL: http://10.0.60.51:9191/output/m3u/TNT Sports?cachedlogos=false
    ✓ Downloaded 48,291 characters
    ✓ Added tvc-stream-timestamps to 42 stream entries
    ✓ Saved → /caddy/M3U/TNT Sports.m3u  (47.2 KB)
  ...

============================================================
  Completed:  9 succeeded  |  0 failed
  Output dir: /caddy/M3U
============================================================
```

### 5. Automate with cron (optional)

To keep your playlists fresh, run the script on a schedule:

```bash
# Refresh every 6 hours
0 */6 * * * /usr/bin/python3 /path/to/m3u-update.py
```

---

## Caddy File Server

Serve the modified files over your LAN using Caddy. The config below restricts access to your local subnet only — no exposure outside your network.

```caddy
10.0.0.32:8080 {
    root * /caddy/M3U

    # Restrict to LAN only
    @blocked not remote_ip 10.0.0.0/24
    respond @blocked 403

    header {
        Access-Control-Allow-Origin *
        Access-Control-Allow-Methods "GET, OPTIONS"
        Access-Control-Allow-Headers *
    }

    @options method OPTIONS
    respond @options 204

    file_server
}
```

Your playlists will then be available at:
```
http://10.0.0.32:8080/TNT Sports.m3u
http://10.0.0.32:8080/Sky.m3u
```

Point Channels DVR at these URLs instead of the Dispatcharr URLs directly.

---

## What the Fix Actually Does

**Before** (from Dispatcharr):
```
#EXTINF:-1 tvg-id="250" tvg-name="Sky Arts" group-title="Entertainment"
```

**After** (served to Channels DVR):
```
#EXTINF:-1 tvc-stream-timestamps="rewrite" tvg-id="250" tvg-name="Sky Arts" group-title="Entertainment"
```

The tag tells Channels DVR to rewrite stream timestamps on ingest rather than trusting the source timestamps, which fixes broken recordings caused by non-standard timestamp values in IPTV streams.

---

## Roadmap / Status

- [x] Multi-playlist support
- [x] Auto-naming from URL path
- [x] LAN-only Caddy serving
- [x] Replaced by the [M3U Stream Tag plugin](https://github.com/CurtisFeatures/Dispatcharr_m3u_stream_tag) for Dispatcharr
- [ ] Native `tvc-stream-timestamps` support in Dispatcharr (not yet; the plugin covers this until then)

If you use the plugin you don't need this script. Point Channels DVR at your Dispatcharr playlist addresses directly.


---

## Related

- [M3U Stream Tag plugin](https://github.com/CurtisFeatures/Dispatcharr_m3u_stream_tag) — the Dispatcharr plugin that replaces this script
- [Dispatcharr](https://github.com/Dispatcharr/Dispatcharr) — the IPTV playlist manager this works around
- [Channels DVR](https://getchannels.com/) — the DVR software consuming these playlists
- [tvc-stream-timestamps documentation](https://community.getchannels.com) — Channels DVR community docs
