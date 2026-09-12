#!/usr/bin/env python3
"""Consumer LAN Device API stub.

Default: print the dish grpcurl catalog and fixtures for this site.
STARLINK_LIVE=1 <command>: optional plaintext Handle call on 192.168.100.1:9200.
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
DISH_TARGET = "192.168.100.1:9200"
SERVICE = "SpaceX.API.Device.Device/Handle"

COMMANDS = {
    "get_status": {"get_status": {}},
    "reboot": {"reboot": {}},
    "dish_stow": {"dish_stow": {}},
    "unstow": {"dish_stow": {"unstow": True}},
    "get_diagnostics": {"get_diagnostics": {}},
}


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


def grpcurl_line(payload: dict) -> str:
    return f"grpcurl -plaintext -d '{json.dumps(payload, separators=(',', ':'))}' {DISH_TARGET} {SERVICE}"


def fixture_mode(site: dict, command: str = "get_status") -> dict:
    router = json.loads((FIXTURES / "router_diagnostics.json").read_text(encoding="utf-8"))
    dish = json.loads((FIXTURES / "dish_diagnostics.json").read_text(encoding="utf-8"))
    status = json.loads((FIXTURES / "dish_status.json").read_text(encoding="utf-8"))
    payload = COMMANDS[command]
    return {
        "mode": "fixture",
        "router_id": site.get("router", {}).get("id"),
        "ssid": site.get("router", {}).get("ssid"),
        "rpc": SERVICE,
        "command": command,
        "request": payload,
        "grpcurl": grpcurl_line(payload),
        "catalog": {name: grpcurl_line(body) for name, body in COMMANDS.items() if name != "get_diagnostics"},
        "router": router,
        "dish": dish,
        "dish_status": status,
    }


def live_mode(site: dict, command: str) -> dict:
    import shutil
    import subprocess

    payload = COMMANDS[command]
    target = os.environ.get("STARLINK_DISH_TARGET", DISH_TARGET)
    grpcurl = shutil.which("grpcurl")
    if not grpcurl:
        return {
            "mode": "live-unavailable",
            "reason": "grpcurl not installed; staying on fixtures",
            "target": target,
            "fixture": fixture_mode(site, command),
        }
    cmd = [grpcurl, "-plaintext", "-d", json.dumps(payload, separators=(",", ":")), target, SERVICE]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=8, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"mode": "live-error", "target": target, "error": str(exc), "fixture": fixture_mode(site, command)}
    if proc.returncode != 0:
        return {
            "mode": "live-error",
            "target": target,
            "stderr": proc.stderr.strip(),
            "fixture": fixture_mode(site, command),
        }
    return {"mode": "live", "target": target, "command": command, "request": payload, "response": proc.stdout}


def main() -> int:
    site = load_site()
    command = sys.argv[1] if len(sys.argv) > 1 else "get_status"
    if command not in COMMANDS:
        raise SystemExit(f"unknown command {command!r}; choose from {sorted(COMMANDS)}")
    if os.environ.get("STARLINK_LIVE") == "1":
        payload = live_mode(site, command)
    else:
        payload = fixture_mode(site, command)
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
