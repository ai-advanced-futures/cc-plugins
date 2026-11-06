#!/usr/bin/env python3
"""Commercial detector adapters (ADR-003, opt-in api tier).

Keys via env vars ONLY (never config files). No key / timeout / bad payload
-> {"status": "UNAVAILABLE", "reason": ...} — degrade loudly, never raise.
stdlib urllib (no requests dep — keeps requirements-dev.txt pip-light).
Composite = p(AI) * 100 at this boundary; downstream is composite-only.
30s timeout, no retries in v0.1.0 (spec §7 (retry/backoff explicitly out of scope per §11))."""
import json
import os
import urllib.request

TIMEOUT_S = 30


def _post(url, payload, headers):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:  # noqa: S310
        return json.loads(resp.read().decode())


class _Adapter:
    name = ""
    env_key = ""

    def _score(self, text, key):          # -> p(AI) in [0,1]
        raise NotImplementedError

    def check(self, text):
        key = os.environ.get(self.env_key, "")
        if not key:
            return {"id": self.name, "status": "UNAVAILABLE",
                    "reason": f"{self.env_key} key not set", "composite": None}
        try:
            p = self._score(text, key)
            return {"id": self.name, "status": "OK",
                    "composite": round(float(p) * 100, 1), "reason": None}
        except (OSError, KeyError, IndexError, TypeError, ValueError) as e:
            return {"id": self.name, "status": "UNAVAILABLE",
                    "reason": f"{type(e).__name__}: {e}", "composite": None}


class GPTZeroAdapter(_Adapter):
    name = "gptzero"
    env_key = "GPTZERO_API_KEY"

    def _score(self, text, key):
        data = _post("https://api.gptzero.me/v2/predict/text",
                     {"document": text}, {"x-api-key": key})
        return data["documents"][0]["class_probabilities"]["ai"]


class OriginalityAdapter(_Adapter):
    name = "originality"
    env_key = "ORIGINALITY_API_KEY"

    def _score(self, text, key):
        data = _post("https://api.originality.ai/api/v1/scan/ai",
                     {"content": text}, {"X-OAI-API-KEY": key})
        return data["score"]["ai"]


class SaplingAdapter(_Adapter):
    name = "sapling"
    env_key = "SAPLING_API_KEY"

    def _score(self, text, key):
        data = _post("https://api.sapling.ai/api/v1/aidetect",
                     {"key": key, "text": text}, {})
        return data["score"]


ADAPTERS = {a.name: a for a in (GPTZeroAdapter(), OriginalityAdapter(), SaplingAdapter())}


def check_all(text):
    return [a.check(text) for a in ADAPTERS.values()]
