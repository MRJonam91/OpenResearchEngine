"""Small, bounded client for an explicitly configured local Ollama runtime."""

from __future__ import annotations

from hashlib import sha256
import ipaddress
import json
import math
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError("Ollama endpoint redirects are not allowed")


def normalized(vector: list) -> list[float]:
    if not isinstance(vector, list) or not 1 <= len(vector) <= 8192 or any(type(value) not in (int, float) or not math.isfinite(value) for value in vector):
        raise ValueError("Ollama returned an invalid embedding vector")
    norm = math.sqrt(sum(value * value for value in vector))
    if not math.isfinite(norm) or norm == 0:
        raise ValueError("Ollama returned a zero/invalid embedding vector")
    return [value / norm for value in vector]


class OllamaClient:
    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout: float = 120):
        parts = urlsplit(base_url)
        host = "127.0.0.1" if parts.hostname == "localhost" else parts.hostname
        try:
            valid = host is not None and ipaddress.ip_address(host).is_loopback
        except ValueError:
            valid = False
        if not valid or parts.scheme not in {"http", "https"} or parts.username or parts.password or parts.path not in {"", "/"} or parts.query or parts.fragment:
            raise ValueError("Ollama requires a loopback HTTP/HTTPS endpoint")
        authority = f"[{host}]" if ":" in host else host
        self.base_url = f"{parts.scheme}://{authority}:{parts.port or (443 if parts.scheme == 'https' else 80)}"
        self.timeout = timeout
        self.opener = build_opener(ProxyHandler({}), _NoRedirect())

    def request(self, path: str, payload: dict | None = None) -> dict:
        request = Request(self.base_url + path, data=json.dumps(payload).encode() if payload is not None else None, headers={"Content-Type": "application/json"})
        try:
            with self.opener.open(request, timeout=min(5, self.timeout) if path in {"/api/tags", "/api/show"} else self.timeout) as response:
                data = response.read(8 * 1024 * 1024 + 1)
                if len(data) > 8 * 1024 * 1024:
                    raise ValueError("Ollama response exceeds the size limit")
                result = json.loads(data)
                if not isinstance(result, dict) or "error" in result:
                    raise ValueError("Ollama returned an invalid/error response")
                return result
        except HTTPError as exc:
            raise ValueError(f"Ollama returned HTTP {exc.code}; check installed model and context limits") from exc
        except (URLError, OSError) as exc:
            raise ValueError("Ollama is unavailable; start the configured local runtime") from exc
        except (json.JSONDecodeError, UnicodeError) as exc:
            raise ValueError("Ollama returned invalid JSON") from exc

    def model_info(self, name: str, capability: str) -> dict:
        if not name or len(name) > 200 or ":cloud" in name.lower():
            raise ValueError("Configure an installed local Ollama model")
        models = self.request("/api/tags").get("models", [])
        item = next((item for item in models if item.get("name") in {name, name + ":latest"}), None)
        if item is None or not re.fullmatch(r"[0-9a-f]{64}", str(item.get("digest", ""))):
            raise ValueError(f"Ollama model is not installed locally: {name}")
        details = self.request("/api/show", {"model": name})
        if details.get("remote_host") or details.get("remote_model") or item.get("remote_host") or item.get("remote_model"):
            raise ValueError("Ollama cloud/remote models are not supported")
        if capability not in details.get("capabilities", []):
            raise ValueError(f"Ollama model does not support {capability}")
        return {"name": name, "digest": item["digest"], "key": sha256(f"{self.base_url}|{name}|{item['digest']}".encode()).hexdigest()}

    def embed(self, model: str, texts: list[str]) -> list[list[float]]:
        result = self.request("/api/embed", {"model": model, "input": texts, "truncate": False})
        vectors = result.get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(texts):
            raise ValueError("Ollama returned the wrong embedding count")
        output = [normalized(vector) for vector in vectors]
        if len({len(vector) for vector in output}) != 1:
            raise ValueError("Ollama returned inconsistent embedding dimensions")
        return output

    def generate(self, model: str, system: str, prompt: str, schema: dict) -> dict:
        result = self.request("/api/generate", {"model": model, "system": system, "prompt": prompt, "format": schema, "stream": False, "options": {"temperature": 0, "seed": 0, "num_predict": 2048, "num_ctx": 8192}})
        if result.get("done") is not True or result.get("done_reason") == "length":
            raise ValueError("Ollama generation was incomplete; use a smaller input or another model")
        try:
            answer = json.loads(result.get("response", ""))
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValueError("Ollama proposal is not valid JSON") from exc
        return answer
