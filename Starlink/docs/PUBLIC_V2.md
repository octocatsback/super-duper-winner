# Starlink Public API v2

Copyright (c) 2026 Gareth Lee Douglas Kirman.

Public v2 is the **Business / enterprise** HTTP API. A residential consumer login is not enough.

## Why a service account is required

- V2 credentials are a **Client ID + secret** minted on a Starlink **account**, not a user cookie.
- Only users with **Admin** or **Service Account Management** can create them (https://starlink.com/account/settings).
- Auth is OIDC client credentials against `https://starlink.com/api/auth/.well-known/openid-configuration`.
- Bearer tokens authorize `https://starlink.com/api/public/v2/...`.
- V1 sunsets 2026-06-01; new work should use v2.

Gareth has not stored a service account in this repo. The stub prints the missing-credential path and serves fixtures instead.

## Router-shaped calls for this kit

Once a Business v2 service account exists, the interesting router calls for `Router-010000000000000001F29264` are:

| Method | Path | Permission (from public spec) |
| ------ | ---- | ----------------------------- |
| GET | `/public/v2/routers/{routerId}` | Device management, View |
| POST | `/public/v2/routers/{routerId}/reboot` | Device command and configuration, Edit |
| GET | `/public/v2/routers/configs` | Device command and configuration, View |
| GET | `/public/v2/account` | Account information, View |

SSID `Wanjer` is a LAN identifier. v2 does not take a Wi-Fi password in these stubs.

## How to call (do not commit secrets)

```bash
# gitignored .env.local — never commit
export STARLINK_CLIENT_ID='from-starlink-settings'
export STARLINK_CLIENT_SECRET='from-starlink-settings'
python3 stubs/public_v2.py --live
```

Token request (client credentials, no cookies):

```http
POST https://starlink.com/api/auth/connect/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=...&client_secret=...
```

Then `Authorization: Bearer <access_token>` on `https://starlink.com/api/public/v2/routers/Router-010000000000000001F29264`.

## Catalog

[`../openapi/public-v2-catalog.json`](../openapi/public-v2-catalog.json) is a path index harvested from the public swagger document on 2026-09-12. Refresh from:

https://starlink.com/api/public/swagger/v2/swagger.json

## Official guides

- https://starlink.readme.io/docs/getting-started
- https://starlink.readme.io/docs/api-v2-service-accounts
- https://starlink.readme.io/docs/authentication
- https://starlink.readme.io/docs/migrating-from-v1-to-v2
