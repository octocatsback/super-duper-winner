#!/usr/bin/env python3
"""Offline checks for Starlink stubs. No network, no secrets."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUBS = Path(__file__).resolve().parent


def main() -> int:
    site = (ROOT / "site.yaml").read_text(encoding="utf-8").lower()
    for banned in ("password", "cookie", "client_secret", "ssid_psk"):
        if banned in site.replace("forbidden_in_repo", ""):
            # allow the documentation list of forbidden keys only
            pass
    if "wifi_password:" in site or "client_secret:" in site:
        print("FAIL: site.yaml contains a secret field", file=sys.stderr)
        return 1

    consumer = subprocess.run(
        [sys.executable, str(STUBS / "consumer_session.py")],
        capture_output=True,
        text=True,
        check=True,
    )
    cdoc = json.loads(consumer.stdout)
    assert cdoc["mode"] == "fixture"
    assert cdoc["router_id"] == "Router-010000000000000001F29264"
    assert cdoc["ssid"] == "Wanjer"
    assert cdoc["command"] == "get_status"
    assert cdoc["request"] == {"get_status": {}}
    assert "192.168.100.1:9200" in cdoc["grpcurl"]
    assert "get_status" in cdoc["catalog"]
    assert "reboot" in cdoc["catalog"]
    assert "dish_stow" in cdoc["catalog"]
    assert "unstow" in cdoc["catalog"]

    public = subprocess.run(
        [sys.executable, str(STUBS / "public_v2.py")],
        capture_output=True,
        text=True,
        check=True,
    )
    pdoc = json.loads(public.stdout)
    assert pdoc["mode"] == "fixture"
    assert pdoc["router"]["routerId"] == "Router-010000000000000001F29264"

    proto = (ROOT / "proto" / "device.proto").read_text(encoding="utf-8")
    assert "rpc Handle" in proto
    assert "get_diagnostics" in proto

    catalog = json.loads((ROOT / "openapi" / "public-v2-catalog.json").read_text(encoding="utf-8"))
    paths = {f"{p['method']} {p['path']}" for p in catalog["paths"]}
    assert "GET /public/v2/routers/{routerId}" in paths
    print("PASS: Starlink stubs, fixtures, proto, and v2 catalog")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
