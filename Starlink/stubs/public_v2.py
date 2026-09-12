#!/usr/bin/env python3
"""Starlink Public API v2 stub.

Default: fixture for Router-010000000000000001F29264.
--live: OIDC client-credentials against starlink.com, only if
STARLINK_CLIENT_ID and STARLINK_CLIENT_SECRET are set in the environment.
Never reads cookies. Never hardcodes secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).resolve().parent / "fixtures"
TOKEN_URL = "https://starlink.com/api/auth/connect/token"
API_BASE = "https://starlink.com/api"
ROUTER_ID = "Router-010000000000000001F29264"


def fixture_payload() -> dict:
    return {
        "mode": "fixture",
        "reason": "Public v2 needs a Starlink Business V2 service account.",
        "router": json.loads((FIXTURES / "public_v2_router.json").read_text(encoding="utf-8")),
        "docs": "Starlink/docs/PUBLIC_V2.md",
        "mint_credentials_at": "https://starlink.com/account/settings",
    }


def live_payload() -> dict:
    client_id = os.environ.get("STARLINK_CLIENT_ID", "").strip()
    client_secret = os.environ.get("STARLINK_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        payload = fixture_payload()
        payload["mode"] = "live-blocked"
        payload["reason"] = (
            "STARLINK_CLIENT_ID / STARLINK_CLIENT_SECRET are unset. "
            "A Business V2 service account is required; consumer cookies are not accepted."
        )
        return payload
    body = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
    ).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=body,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            token_doc = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return {"mode": "live-error", "step": "token", "http": exc.code, "body": exc.read().decode(errors="replace")}
    except urllib.error.URLError as exc:
        return {"mode": "live-error", "step": "token", "error": str(exc)}
    access = token_doc.get("access_token")
    if not access:
        return {"mode": "live-error", "step": "token", "error": "no access_token in OIDC response"}
    router_url = f"{API_BASE}/public/v2/routers/{ROUTER_ID}"
    api_req = urllib.request.Request(
        router_url,
        method="GET",
        headers={"Authorization": f"Bearer {access}"},
    )
    try:
        with urllib.request.urlopen(api_req, timeout=15) as resp:
            router = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        return {
            "mode": "live-error",
            "step": "router",
            "http": exc.code,
            "body": exc.read().decode(errors="replace"),
        }
    except urllib.error.URLError as exc:
        return {"mode": "live-error", "step": "router", "error": str(exc)}
    return {"mode": "live", "router_id": ROUTER_ID, "router": router}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Call public v2 with env service-account credentials")
    args = parser.parse_args()
    payload = live_payload() if args.live else fixture_payload()
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
