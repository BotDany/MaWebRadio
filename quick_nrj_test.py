#!/usr/bin/env python3
import requests
import json
import os
import sys
import time

def test_nrj_api():
    radio_ids = ["1640", "1283"]

    endpoints = [
        "https://players.nrjaudio.fm/wr_api/live/fr/",
        "https://players.nrjaudio.fm/wr_api/live/de/",
        "http://players.nrjaudio.fm/wr_api/live/fr/",
        "http://players.nrjaudio.fm/wr_api/live/de/",
    ]

    default_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/xml, text/xml, application/json, */*",
        "Referer": "https://www.nostalgie.fr/",
        "Origin": "https://www.nostalgie.fr",
    }

    extra_headers = {}
    headers_path = os.environ.get("NRJ_HEADERS") or "nrj_headers.json"
    if os.path.exists(headers_path):
        try:
            with open(headers_path, "r", encoding="utf-8") as f:
                extra_headers = json.load(f) or {}
                if not isinstance(extra_headers, dict):
                    extra_headers = {}
        except Exception:
            extra_headers = {}

    combined_headers = dict(default_headers)
    combined_headers.update(extra_headers)

    session = requests.Session()
    session.headers.update(combined_headers)

    params_variants = [
        {"q": "getMetaData", "id": None},
        {"q": "getMetaData", "id": None, "format": "json"},
        {"q": "getMetaData", "id": None, "callback": "jsonp"},
    ]

    for radio_id in radio_ids:
        for base in endpoints:
            for params in params_variants:
                p = dict(params)
                p["id"] = radio_id
                url = base
                t0 = time.time()
                try:
                    r = session.get(url, params=p, timeout=4)
                except KeyboardInterrupt:
                    raise
                except Exception:
                    continue
                dt_ms = int((time.time() - t0) * 1000)
                clen = len(r.content or b"")
                head = (r.content or b"")[:200]
                print(f"ID={radio_id} {r.status_code} {clen}B {dt_ms}ms {r.url}")
                if clen:
                    print("--- HEAD(200B) ---")
                    try:
                        print(head.decode("utf-8", errors="replace"))
                    except Exception:
                        print(head)
                    return True

    print("Tried headers:")
    for k in sorted(session.headers.keys()):
        if k.lower() in ("cookie", "authorization"):
            print(f"  {k}: <hidden>")
        else:
            print(f"  {k}: {session.headers.get(k)}")
    return False

if __name__ == "__main__":
    try:
        ok = test_nrj_api()
        print("Found working NRJ API!" if ok else "No working NRJ API found")
        sys.exit(0 if ok else 1)
    except KeyboardInterrupt:
        print("Interrupted")
        sys.exit(130)
