import re
import requests

def main() -> None:

    s = requests.Session()
    s.trust_env = False

    base = "https://manager7.streamradio.fr:1970"
    url = f"{base}/nowplaying"
    r = s.get(url, timeout=10, verify=False)
    html = r.text or ""

    print("status", r.status_code, "len", len(html))

    scripts = sorted(set(re.findall(r'src="([^"]+\.js[^"]*)"', html)))
    print("scripts:")
    for x in scripts[:50]:
        print(x)

    js_paths = [
        "/media/js/scenter_app.js",
        "/media/js/scenter_lib.js",
        "/media/static/js/current_track_widget/status_widget.js",
        "/media/static/js/sc_player/sc_player.js",
        "/media/static/js/current_track_widget/status_widget.js",
    ]

    print("\nscan:")
    for path in js_paths:
        try:
            jr = s.get(f"{base}{path}", timeout=10, verify=False)
            text = jr.text or ""
            print(path, "status", jr.status_code, "len", len(text))
            if jr.status_code != 200 or not text:
                continue

            for key in [
                "nowplaying",
                "NowPlaying",
                "trackImage",
                "/media/tracks",
                "tracks",
                "artist",
                "title",
                "/api",
                "/rest",
                "/services",
            ]:
                if key in text:
                    print("FOUND", key)

            candidates = set()
            for m in re.findall(r"/[^\"'\s]{1,120}", text):
                if "now" in m.lower() or "track" in m.lower() or "meta" in m.lower() or "play" in m.lower():
                    candidates.add(m)
            for c in sorted(candidates)[:50]:
                print(" ", c)

            api_paths = sorted(set(re.findall(r"/api/[^\"'\s]{1,120}", text)))
            if api_paths:
                print("api:")
                for ap in api_paths[:50]:
                    print(" ", ap)

            for needle in ["nowplaying", "current_track", "trackImage", "StreamTitle", "/media/tracks/"]:
                if needle not in text:
                    continue
                print("snip", needle, ":")
                idx = 0
                for _ in range(8):
                    idx = text.find(needle, idx)
                    if idx == -1:
                        break
                    start = max(0, idx - 80)
                    end = min(len(text), idx + 200)
                    print(text[start:end].replace("\n", " "))
                    idx = idx + len(needle)
        except Exception as e:
            print(path, "ERR", type(e).__name__)

    print("\nstreamapps manager.php (probe):")

    server_candidates = [
        "manager7.streamradio.fr",
        "manager7.streamradio.fr:1985",
        "manager7.streamradio.fr:1970",
        "http://manager7.streamradio.fr:1985/stream",
        "http://manager7.streamradio.fr:1970/stream",
        "https://manager7.streamradio.fr:1970",
    ]
    radio_candidates = ["1", "2", "3", "4", "5", "6"]

    found = False
    for srv in server_candidates:
        for rid in radio_candidates:
            try:
                r = s.get(
                    "https://api.streamapps.fr/manager.php",
                    params={"server": srv, "radio": rid, "nowrap": "true"},
                    timeout=5,
                )
                if r.status_code != 200:
                    continue
                try:
                    data = r.json()
                except Exception:
                    continue
                if not isinstance(data, dict):
                    continue
                md = data.get("metadata") if isinstance(data.get("metadata"), dict) else None
                if not isinstance(md, dict):
                    continue
                title = md.get("title")
                artist = md.get("artist")
                cover = md.get("cover")
                if title or artist or cover:
                    print("FOUND server=", srv, "radio=", rid)
                    print(" listenUrl=", data.get("listenUrl"))
                    print(" title=", title)
                    print(" artist=", artist)
                    print(" cover=", cover)
                    found = True
                    break
            except Exception:
                continue
        if found:
            break

    if not found:
        print("No metadata found for tested server/radio combinations")

if __name__ == "__main__":
    main()