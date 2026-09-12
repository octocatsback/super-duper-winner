# Starlink API docs and stubs

Umbrella-owned notes and offline stubs for Gareth Lee Douglas Kirman's Starlink kit.

Copyright (c) 2026 Gareth Lee Douglas Kirman.

This is **not** an octocatsback GitHub repo import. It lives here so the consumer LAN APIs and the public Business v2 surface are documented next to the rest of the monorepo.

## Site identity (public only)

| Field | Value |
| ----- | ----- |
| Router id | `Router-010000000000000001F29264` |
| Wi-Fi SSID | `Wanjer` |

SSID is the network name, not a password. **No cookies, Wi-Fi passwords, account sessions, or API client secrets are stored in this tree.** Put Business v2 credentials in a gitignored `.env.local` if Gareth later mints a service account.

Machine-readable identity: [`site.yaml`](site.yaml).

## Two API families

| Family | Who can use it | Auth | Where |
| ------ | -------------- | ---- | ----- |
| **Consumer session (local Device API)** | Anyone on the Starlink LAN | None on the official `Handle` / `get_diagnostics` path (link-local only) | Router `192.168.1.1:9000`, dish `192.168.100.1:9200` |
| **Public API v2** | Starlink **Business / enterprise** accounts | OIDC client credentials from a **V2 service account** | `https://starlink.com/api/public/v2/...` |

A residential consumer account **cannot** call public v2 until an Admin (or Service Account Management) role on a Business account creates a V2 service account. That is a Gareth decision.

## Consumer session APIs

Official local gRPC is published by SpaceX as `device.proto` (copied in [`proto/device.proto`](proto/device.proto) from [SpaceExplorationTechnologies/enterprise-api](https://github.com/SpaceExplorationTechnologies/enterprise-api/tree/master/device-api)).

Service: `SpaceX.API.Device.Device`  
RPC: `Handle(Request) returns (Response)`  
Supported official request: `get_diagnostics` (field 6000).

```text
grpcurl -plaintext -d '{"get_diagnostics":{}}' 192.168.1.1:9000 SpaceX.API.Device.Device/Handle
grpcurl -plaintext -d '{"get_diagnostics":{}}' 192.168.100.1:9200 SpaceX.API.Device.Device/Handle
```

The Starlink phone/browser apps also speak **gRPC-Web** on router `:9001` and dish `:9201`. That is the same Device service over HTTP/1.1, still LAN-scoped. Firmware may expose additional reflected RPCs (`get_status`, `wifi_get_clients`, …). This tree stubs **only** the official `get_diagnostics` path so we do not invent undocumented cloud session APIs or scrape cookies.

Minimum software (from SpaceX): router > 2023.55, user terminal > 2023.51.0.

See [`docs/CONSUMER_SESSION.md`](docs/CONSUMER_SESSION.md).

## Public v2 (Business service account)

- Docs: https://starlink.readme.io/docs/getting-started
- Service accounts: https://starlink.readme.io/docs/api-v2-service-accounts
- Auth: https://starlink.readme.io/docs/authentication
- Swagger: https://starlink.com/api/public/swagger/index.html?urls.primaryName=V2
- OpenAPI snapshot catalog: [`openapi/public-v2-catalog.json`](openapi/public-v2-catalog.json)

Router-shaped v2 calls (once a service account exists) include `GET /public/v2/routers/{routerId}` with `routerId=Router-010000000000000001F29264`. The stub will not send a token unless `STARLINK_CLIENT_ID` and `STARLINK_CLIENT_SECRET` are provided in the environment.

See [`docs/PUBLIC_V2.md`](docs/PUBLIC_V2.md).

## Stubs

```bash
cd Starlink/stubs
python3 consumer_session.py          # fixture mode (default)
python3 public_v2.py                 # fixture / explains missing service account
STARLINK_LIVE=1 python3 consumer_session.py   # optional LAN call; no secrets
```

Fixtures live in [`stubs/fixtures/`](stubs/fixtures/). They use the published router id and SSID only.

## License

Umbrella MIT. The copied `device.proto` remains under SpaceX's upstream license in the enterprise-api repository. Official Starlink documentation is referenced, not reproduced in full.
