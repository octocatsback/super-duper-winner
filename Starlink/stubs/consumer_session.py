#!/usr/bin/env python3
"""Consumer LAN Device API stub.

Default: print official get_diagnostics fixtures for this site.
STARLINK_LIVE=1: attempt a plaintext gRPC Handle call on the LAN.
Never reads cookies, Wi-Fi passwords, or account tokens.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site.yaml"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_site() -> dict:
    text = SITE.read_text(encoding="utf-8")
    site: dict = {}
    section = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if line.endswith(":") and not line.startswith(" "):
            section = line[:-1].strip()
            site[section] = {}
            continue
        if section and ":" in line:
            key, value = line.strip().split(":", 1)
            site[section][key.strip()] = value.strip()
    forbidden = {"wifi_password", "password", "cookie", "cookies", "client_secret"}
    found = forbidden.intersection(k.lower() for k in _flatten_keys(site))
    if found:
        raise SystemExit(f"site.yaml must not contain {sorted(found)}")
    return site


def _flatten_keys(obj, prefix=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _flatten_keys(v, f"{prefix}.{k}" if prefix else k)
    else:
        yield prefix


def fixture_mode(site: dict) -> dict:
    router = json.loads((FIXTURES / "router_diagnostics.json").read_text(encoding="utf-8"))
    dish = json.loads((FIXTURES / "dish_diagnostics.json").read_text(encoding="utf-8"))
    return {
        "mode": "fixture",
        "router_id": site.get("router", {}).get("id"),
        "ssid": site.get("router", {}).get("ssid"),
        "rpc": "SpaceX.API.Device.Device/Handle",
        "request": {"get_diagnostics": {}},
        "router": router,
        "dish": dish,
    }


def live_mode(site: dict) -> dict:
    host = os.environ.get("STARLINK_ROUTER_HOST", site["router"]["grpc_host"])
    port = os.environ.get("STARLINK_ROUTER_PORT", site["router"]["grpc_port"])
    # Optional live call uses grpcurl if present. No metadata/cookies.
    import shutil
    import subprocess

    grpcurl = shutil.which("grpcurl")
    if not grpcurl:
        return {
            "mode": "live-unavailable",
            "reason": "grpcurl not installed; staying on fixtures",
            "target": f"{host}:{port}",
            "fixture": fixture_mode(site),
        }
    target = f"{host}:{port}"
    cmd = [
        grpcurl,
        "-plaintext",
        "-d",
        '{"get_diagnostics":{}}',
        target,
        "SpaceX.API.Device.Device/Handle",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"mode": "live-error", "target": target, "error": str(exc), "fixture": fixture_mode(site)}
    if proc.returncode != 0:
        return {
            "mode": "live-error",
            "target": target,
            "stderr": proc.stderr.strip(),
            "fixture": fixture_mode(site),
        }
    return {"mode": "live", "target": target, "response": proc.stdout}


def main() -> int:
    site = load_site()
    if os.environ.get("STARLINK_LIVE") == "1":
        payload = live_mode(site)
    else:
        payload = fixture_mode(site)
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
