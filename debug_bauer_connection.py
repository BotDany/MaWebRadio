import socket
import ssl
import sys
import textwrap
from urllib.parse import urlparse

import argparse
import requests


def _print_kv(title: str, value: str):
    print(f"{title}: {value}")


def _resolve(host: str):
    print("\n== DNS ==")
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
        uniq = []
        for family, socktype, proto, canonname, sockaddr in infos:
            ip, port = sockaddr[0], sockaddr[1]
            if (family, ip) not in uniq:
                uniq.append((family, ip))
        for family, ip in uniq:
            fam = "IPv6" if family == socket.AF_INET6 else "IPv4"
            print(f"- {fam}: {ip}")
    except Exception as e:
        print(f"DNS error: {e}")


def _tls_probe(host: str, port: int = 443, sni: str | None = None, insecure: bool = False):
    print("\n== TLS handshake ==")
    ctx = ssl.create_default_context()
    if insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    server_name = sni or host

    with socket.create_connection((host, port), timeout=10) as sock:
        with ctx.wrap_socket(sock, server_hostname=server_name) as ssock:
            _print_kv("TLS version", ssock.version() or "?")
            cipher = ssock.cipher()
            if cipher:
                _print_kv("Cipher", f"{cipher[0]} ({cipher[1]}, {cipher[2]} bits)")
            try:
                cert = ssock.getpeercert()
                if cert:
                    subj = cert.get("subject", [])
                    issuer = cert.get("issuer", [])
                    _print_kv("Cert subject", str(subj))
                    _print_kv("Cert issuer", str(issuer))
                    _print_kv("Not before", str(cert.get("notBefore")))
                    _print_kv("Not after", str(cert.get("notAfter")))
            except Exception as e:
                print(f"Cert read error: {e}")


def _http_probe(
    url: str,
    method: str = "GET",
    insecure: bool = False,
    headers: dict | None = None,
    trust_env: bool = True,
):
    print("\n== HTTP probe ==")
    sess = requests.Session()
    sess.trust_env = trust_env
    req_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }
    if headers:
        for k, v in headers.items():
            if v is None:
                continue
            req_headers[k] = v

    next_url_from_body = None

    try:
        proxies = sess.proxies or {}
        _print_kv("Requests trust_env", "yes" if trust_env else "no")
        _print_kv("Requests proxies", str(proxies) if proxies else "(none)")
        r = sess.request(
            method,
            url,
            headers=req_headers,
            allow_redirects=False,
            timeout=15,
            verify=not insecure,
            stream=True,
        )
        _print_kv("Status", f"{r.status_code} {r.reason}")
        if "location" in r.headers:
            _print_kv("Redirect", r.headers.get("location", ""))
        print("\n-- Response headers --")
        for k, v in r.headers.items():
            print(f"{k}: {v}")

        # Read a small chunk (some HLS endpoints may start returning data immediately)
        try:
            chunk = next(r.iter_content(chunk_size=2048), b"")
            _print_kv("First bytes", repr(chunk[:80]))

            ctype = (r.headers.get("content-type") or "").lower()
            if ".m3u8" in url.lower() or "application/vnd.apple.mpegurl" in ctype or "application/x-mpegurl" in ctype:
                try:
                    preview = chunk.decode("utf-8", errors="replace")
                    print("\n-- Body preview (first ~2KB) --")
                    print(preview.rstrip())

                    try:
                        with open("debug_bauer_last.m3u8", "w", encoding="utf-8", newline="\n") as f:
                            f.write(preview)
                        _print_kv("Saved", "debug_bauer_last.m3u8")
                    except Exception as e:
                        print(f"File write error: {e}")

                    next_url = None
                    for line in preview.splitlines():
                        s = line.strip()
                        if s.startswith("http://") or s.startswith("https://"):
                            next_url = s
                            break
                    if next_url:
                        next_url_from_body = next_url
                        print("\n-- Next URL (copier-coller) --")
                        print(next_url)
                        try:
                            with open("debug_bauer_next_url.txt", "w", encoding="utf-8", newline="\n") as f:
                                f.write(next_url + "\n")
                            _print_kv("Saved", "debug_bauer_next_url.txt")
                        except Exception as e:
                            print(f"File write error: {e}")
                except Exception:
                    pass
        except Exception as e:
            print(f"Body read error: {e}")
        finally:
            r.close()

    except requests.exceptions.SSLError as e:
        print("SSL error (HTTP):")
        print(textwrap.indent(str(e), "  "))
    except requests.exceptions.ConnectTimeout:
        print("Connect timeout")
    except requests.exceptions.ReadTimeout:
        print("Read timeout")
    except Exception as e:
        print(f"HTTP error: {e}")

    return next_url_from_body


def _parse_headers_kv(items: list[str]) -> dict:
    out: dict[str, str] = {}
    for it in items:
        if ":" not in it:
            raise ValueError(f"Invalid header '{it}'. Expected 'Key: Value'.")
        k, v = it.split(":", 1)
        out[k.strip()] = v.strip()
    return out


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "url",
        nargs="?",
        default="https://stream-hls.bauermedia.pt/",
        help="URL to probe (e.g. full .m3u8 playlist URL).",
    )
    parser.add_argument("--insecure", action="store_true", help="Disable TLS verification (diagnostic only).")
    parser.add_argument(
        "--no-proxy",
        action="store_true",
        help="Ignore system proxy environment (use direct connection).",
    )
    parser.add_argument(
        "--follow-next",
        type=int,
        default=0,
        help="Automatically follow the next URL extracted from an m3u8 response (number of hops).",
    )
    parser.add_argument("--ua", dest="user_agent", default=None, help="Override User-Agent.")
    parser.add_argument("--lang", dest="accept_language", default=None, help="Override Accept-Language.")
    parser.add_argument(
        "--session",
        dest="playback_session_id",
        default=None,
        help="Set x-playback-session-id header.",
    )
    parser.add_argument(
        "--header",
        action="append",
        default=[],
        help="Extra header 'Key: Value' (repeatable).",
    )

    args = parser.parse_args()

    url = args.url
    insecure = args.insecure
    trust_env = not args.no_proxy
    follow_next = max(0, int(args.follow_next or 0))

    parsed = urlparse(url)
    host = parsed.hostname or "stream-hls.bauermedia.pt"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    extra_headers: dict[str, str] = {}
    try:
        extra_headers.update(_parse_headers_kv(args.header))
    except Exception as e:
        print(f"Header parse error: {e}")
        sys.exit(2)

    if args.user_agent:
        extra_headers["User-Agent"] = args.user_agent
    if args.accept_language:
        extra_headers["Accept-Language"] = args.accept_language
    if args.playback_session_id:
        extra_headers["x-playback-session-id"] = args.playback_session_id

    print("=== Bauer Media HLS debug ===")
    _print_kv("URL", url)
    _print_kv("Host", host)
    _print_kv("Port", str(port))
    _print_kv("Verify TLS", "no" if insecure else "yes")

    _resolve(host)

    if port == 443:
        try:
            _tls_probe(host, port=port, sni=host, insecure=insecure)
        except ssl.SSLError as e:
            print("TLS handshake failed:")
            print(textwrap.indent(str(e), "  "))
        except Exception as e:
            print(f"TLS probe error: {e}")

    _http_probe(url, method="HEAD", insecure=insecure, headers=extra_headers, trust_env=trust_env)
    next_url = _http_probe(url, method="GET", insecure=insecure, headers=extra_headers, trust_env=trust_env)

    hops_done = 0
    while follow_next > 0 and next_url and hops_done < follow_next:
        hops_done += 1
        follow_next -= 1
        print("\n" + "=" * 60)
        print(f"Auto-follow next URL (hop {hops_done}):")
        print(next_url)
        print("=" * 60)
        _http_probe(next_url, method="HEAD", insecure=insecure, headers=extra_headers, trust_env=trust_env)
        next_url = _http_probe(next_url, method="GET", insecure=insecure, headers=extra_headers, trust_env=trust_env)


if __name__ == "__main__":
    main()
