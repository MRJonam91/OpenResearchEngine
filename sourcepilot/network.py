"""Bounded public URL capture with DNS pinned to the connected address."""

from __future__ import annotations

from http.client import HTTPConnection, HTTPException
import ipaddress
import socket
import ssl
from urllib.parse import quote, urljoin, urlsplit


def _target(url: str):
    if len(url) > 8192 or any(ord(char) < 32 for char in url):
        raise ValueError("Invalid URL")
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        raise ValueError("URL must use HTTP or HTTPS")
    if parts.username or parts.password:
        raise ValueError("URL credentials are not supported")
    port = 443 if parts.scheme == "https" else 80
    if parts.port not in {None, port}:
        raise ValueError("URL must use the standard HTTP or HTTPS port")
    host = parts.hostname.encode("idna").decode("ascii")
    addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    ips = list(dict.fromkeys(item[4][0] for item in addresses))
    if not ips or any(not ipaddress.ip_address(ip).is_global or ipaddress.ip_address(ip).is_multicast for ip in ips):
        raise ValueError("URL host must resolve only to public addresses")
    return parts, host, port, ips


def fetch_public(url: str, limit: int) -> tuple[bytes, str, str]:
    """Fetch directly, without proxies, revalidating and pinning each redirect."""
    try:
        for _ in range(6):
            parts, host, port, ips = _target(url)
            connection = HTTPConnection(host, port, timeout=15)
            try:
                last_error = None
                for ip in ips:
                    try:
                        connection.sock = socket.create_connection((ip, port), timeout=15)
                        break
                    except OSError as exc:
                        last_error = exc
                if connection.sock is None:
                    raise last_error or OSError("Cannot connect to URL")
                if parts.scheme == "https":
                    connection.sock = ssl.create_default_context().wrap_socket(connection.sock, server_hostname=host)
                # A closed connection must never reconnect through a fresh DNS lookup.
                connection.auto_open = False
                path = quote(parts.path or "/", safe="/%:@!$&'()*+,;=-._~")
                if parts.query:
                    path += "?" + quote(parts.query, safe="/%?:@!$&'()*+,;=-._~")
                authority = f"[{host}]" if ":" in host else host
                connection.request("GET", path, headers={"Host": authority, "User-Agent": "SourcePilot/1.0", "Accept-Encoding": "identity"})
                response = connection.getresponse()
                if response.status in {301, 302, 303, 307, 308}:
                    location = response.getheader("Location")
                    if not location:
                        raise ValueError("Redirect has no destination")
                    url = urljoin(url, location)
                    continue
                if response.status != 200:
                    raise ValueError(f"URL returned HTTP {response.status}")
                if response.getheader("Content-Encoding", "identity").lower() not in {"identity", ""}:
                    raise ValueError("Compressed HTTP responses are not supported")
                declared = response.getheader("Content-Length")
                if declared and (not declared.isdigit() or int(declared) > limit):
                    raise ValueError("URL response exceeds the size limit or has invalid length")
                data = response.read(limit + 1)
                if len(data) > limit:
                    raise ValueError("URL response exceeds the 20 MB limit")
                return data, response.getheader("Content-Type", "").split(";", 1)[0].strip().lower(), url
            finally:
                connection.close()
        raise ValueError("URL has too many redirects")
    except ValueError:
        raise
    except (OSError, UnicodeError, HTTPException) as exc:
        raise ValueError("Could not connect to the public URL") from exc
