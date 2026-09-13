# Consumer session APIs (LAN)

Copyright (c) 2026 Gareth Lee Douglas Kirman.

These are the APIs a consumer Starlink kit exposes to devices already on the home LAN. They do **not** use Starlink.com account cookies and they do **not** need a Business service account.

## This site

- Router id: `Router-010000000000000001F29264`
- SSID: `Wanjer` (network name only; password is not stored here)
- Router gRPC: `192.168.1.1:9000` (gRPC-Web `:9001`)
- Dish gRPC: `192.168.100.1:9200` (gRPC-Web `:9201`)

## Official Device API

Source: [SpaceX enterprise-api / device-api](https://github.com/SpaceExplorationTechnologies/enterprise-api/tree/master/device-api) and [Device APIs](https://starlink.readme.io/docs/device-api).

| Item | Value |
| ---- | ----- |
| Transport | gRPC (HTTP/2) plaintext on the LAN |
| Service | `SpaceX.API.Device.Device` |
| Method | `Handle` |
| Request | `Request { get_diagnostics: {} }` (oneof field 6000) |
| Router response | `wifi_get_diagnostics` — id, hardware/software version, LAN client counts |
| Dish response | `dish_get_diagnostics` — id, versions, alerts, disablement, optional location |

There is no authentication on this official path because the sockets are only reachable on the Starlink LAN.

The Starlink iOS/Android/web apps talk to the **same** service over gRPC-Web (`:9001` / `:9201`) so a browser can hold a consumer "session" without an account cookie. This repo does not capture or replay those app sessions.

## What we stub

[`../stubs/consumer_session.py`](../stubs/consumer_session.py) issues `get_diagnostics` against fixtures by default. Set `STARLINK_LIVE=1` only when you are on the Wanjer LAN and want a real `Handle` call. The stub never reads cookies or passwords.

## What we do not stub

- Wi-Fi PSK / admin password changes
- Account-cookie flows on `starlink.com`
- Unofficial reflected RPCs (`get_status`, reboot, speedtest, …) that firmware may still expose
- Enterprise local HTTPS (Diagnostics / Sandbox) — that needs a router HTTPS server plus a TLS cert configured from a Business dashboard ([Local HTTPS API](https://starlink.readme.io/docs/router-api))

## Related official docs

- https://starlink.readme.io/docs/device-api
- https://starlink.readme.io/docs/starlink-wifi-routers
- https://starlink.readme.io/docs/diagnostics
