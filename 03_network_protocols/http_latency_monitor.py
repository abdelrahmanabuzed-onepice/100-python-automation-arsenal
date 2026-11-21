#!/usr/bin/env python3
"""
HTTP/HTTPS SLA Latency & SSL Certificate Inspector
==================================================
Profiles web endpoint SLA health, network latency breakdowns, and TLS certificate life:
- DNS resolution, TCP handshake, TLS negotiation, and TTFB latency
- SSL certificate issuer, expiry date, and days remaining warnings
- HTTP response codes, headers, and payload throughput

Keywords: http monitor, ssl certificate check, ttfb latency, website uptime, sla profiler
"""

import sys
import ssl
import time
import socket
import json
import argparse
from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any


def inspect_ssl_certificate(hostname: str, port: int = 443, timeout: float = 4.0, existing_ssock: Optional[Any] = None) -> Dict[str, Any]:
    """Retrieve and parse remote SSL certificate details (reuses existing TLS socket if provided)."""
    context = ssl.create_default_context()
    cert_info = {
        "hostname": hostname,
        "valid": False,
        "issuer": "Unknown",
        "subject": "Unknown",
        "expires_utc": None,
        "days_remaining": 0,
        "tls_version": "Unknown",
        "error": None
    }

    def parse_cert(cert: dict, version: str):
        cert_info["tls_version"] = version
        exp_str = cert.get('notAfter')
        if exp_str:
            exp_date = datetime.strptime(exp_str, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
            now_utc = datetime.now(timezone.utc)
            days_left = (exp_date - now_utc).days
            cert_info["expires_utc"] = exp_date.isoformat()
            cert_info["days_remaining"] = days_left
            cert_info["valid"] = days_left > 0

        for item in cert.get('issuer', ()):
            for k, v in item:
                if k in ('organizationName', 'commonName'):
                    cert_info["issuer"] = v
                    break

        for item in cert.get('subject', ()):
            for k, v in item:
                if k == 'commonName':
                    cert_info["subject"] = v
                    break

    try:
        if existing_ssock is not None:
            cert = existing_ssock.getpeercert()
            if cert:
                parse_cert(cert, existing_ssock.version() or "Unknown")
        else:
            with socket.create_connection((hostname, port), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    if cert:
                        parse_cert(cert, ssock.version() or "Unknown")
    except Exception as e:
        cert_info["error"] = str(e)

    return cert_info


def profile_http_endpoint(url: str, timeout: float = 6.0) -> Dict[str, Any]:
    """Profile comprehensive latency milestones for an HTTP/HTTPS endpoint."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    hostname = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path or "/"
    if parsed.query:
        path += f"?{parsed.query}"

    metrics = {
        "url": url,
        "hostname": hostname,
        "status_code": 0,
        "dns_ms": 0.0,
        "tcp_ms": 0.0,
        "tls_ms": 0.0,
        "ttfb_ms": 0.0,
        "total_ms": 0.0,
        "ssl": None,
        "error": None
    }

    # 1. DNS Timing
    t0 = time.perf_counter()
    try:
        ip = socket.gethostbyname(hostname)
        t_dns = time.perf_counter()
        metrics["dns_ms"] = round((t_dns - t0) * 1000, 2)
    except Exception as e:
        metrics["error"] = f"DNS lookup failed: {e}"
        return metrics

    # 2. TCP Timing
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    t_start_tcp = time.perf_counter()
    try:
        sock.connect((ip, port))
        t_connected = time.perf_counter()
        metrics["tcp_ms"] = round((t_connected - t_start_tcp) * 1000, 2)
    except Exception as e:
        metrics["error"] = f"TCP connection failed: {e}"
        sock.close()
        return metrics

    client_sock = sock

    # 3. TLS Handshake Timing (if https)
    if parsed.scheme == "https":
        t_start_tls = time.perf_counter()
        try:
            ctx = ssl.create_default_context()
            client_sock = ctx.wrap_socket(sock, server_hostname=hostname)
            t_tls_done = time.perf_counter()
            metrics["tls_ms"] = round((t_tls_done - t_start_tls) * 1000, 2)
            metrics["ssl"] = inspect_ssl_certificate(hostname, port, timeout, existing_ssock=client_sock)
        except Exception as e:
            metrics["error"] = f"TLS handshake failed: {e}"
            client_sock.close()
            return metrics

    # 4. Request / TTFB Timing
    t_start_req = time.perf_counter()
    req = f"GET {path} HTTP/1.1\r\nHost: {hostname}\r\nUser-Agent: ArsenalHTTP/1.0\r\nConnection: close\r\n\r\n"
    try:
        client_sock.sendall(req.encode('utf-8'))
        first_chunk = client_sock.recv(4096)
        t_first_byte = time.perf_counter()
        metrics["ttfb_ms"] = round((t_first_byte - t_start_req) * 1000, 2)

        # Read remaining body
        while client_sock.recv(8192):
            pass

        t_end = time.perf_counter()
        metrics["total_ms"] = round((t_end - t0) * 1000, 2)

        # Parse HTTP status
        header_text = first_chunk.decode('latin-1', errors='ignore')
        first_line = header_text.split("\r\n", 1)[0]
        parts = first_line.split()
        if len(parts) >= 2 and parts[1].isdigit():
            metrics["status_code"] = int(parts[1])

    except Exception as e:
        metrics["error"] = f"HTTP transfer error: {e}"
    finally:
        client_sock.close()

    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="HTTP/HTTPS SLA Latency & SSL Certificate Inspector"
    )
    parser.add_argument("urls", nargs="+", help="One or more URLs to profile")
    parser.add_argument("--timeout", type=float, default=6.0,
                        help="Request timeout in seconds (default: 6.0)")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")

    args = parser.parse_args()
    results = [profile_http_endpoint(u, timeout=args.timeout) for u in args.urls]

    if args.json:
        print(json.dumps(results if len(results) > 1 else results[0], indent=2))
        return

    print("\n" + "=" * 80)
    print(f"{'Target URL':<28} | {'Status':<6} | {'DNS':<8} | {'TCP':<8} | {'TLS':<8} | {'TTFB':<8} | {'Total'}")
    print("=" * 80)

    for r in results:
        if r.get("error"):
            print(f"{r['url']:<28} | ERROR  | {r['error']}")
            continue

        st = str(r["status_code"])
        print(f"{r['url']:<28} | {st:<6} | {r['dns_ms']:>6.1f}ms | {r['tcp_ms']:>6.1f}ms | {r['tls_ms']:>6.1f}ms | {r['ttfb_ms']:>6.1f}ms | {r['total_ms']:>6.1f}ms")

        if r.get("ssl") and not r["ssl"].get("error"):
            ssl_data = r["ssl"]
            status_tag = f"[OK: {ssl_data['days_remaining']} days left]" if ssl_data['valid'] else "[EXPIRED]"
            print(f"   -> SSL Cert: {ssl_data['issuer']} | TLS: {ssl_data['tls_version']} {status_tag}")
    print("=" * 80)


if __name__ == "__main__":
    main()
