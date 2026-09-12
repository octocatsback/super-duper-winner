# Consumer session APIs (LAN)

Copyright (c) 2026 Gareth Lee Douglas Kirman.

These are the APIs a consumer Starlink kit exposes to devices already on the home LAN. They do **not** use Starlink.com account cookies and they do **not** need a Business service account.

## This site

- Router id: `Router-010000000000000001F29264`
- SSID: `Wanjer` (network name only; password is not stored here)
- Router gRPC: `192.168.1.1:9000` (gRPC-Web `:9001`)
- Dish gRPC: `192.168.100.1:9200` (gRPC-Web `:9201`)

## Local grpcurl (dish)

Same host, port, and service for every consumer dish command. No credentials.

```bash
grpcurl -plaintext -d '{"get_status":{}}' 192.168.100.1:9200 SpaceX.API.Device.Device/Handle
grpcurl -plaintext -d '{"reboot":{}}' 192.168.100.1:9200 SpaceX.API.Device.Device/Handle
grpcurl -plaintext -d '{"dish_stow":{}}' 192.168.100.1:9200 SpaceX.API.Device.Device/Handle
grpcurl -plaintext -d '{"dish_stow":{"unstow":true}}' 192.168.100.1:9200 SpaceX.API.Device.Device/Handle
```

| Payload | Effect |
| ------- | ------ |
| `{"get_status":{}}` | Dish status (`dishGetStatus`) |
| `{"reboot":{}}` | Reboot the user terminal |
| `{"dish_stow":{}}` | Stow (empty message ⇒ `unstow=false`) |
| `{"dish_stow":{"unstow":true}}` | Unstow |

`reboot` / `dish_stow` move hardware. Run them only on this LAN kit, never from CI.

## Router notes

The Starlink router still hosts `SpaceX.API.Device.Device/Handle` at `192.168.1.1:9000`. SpaceX's published `device.proto` documents `get_diagnostics` (field 6000) for router/dish diagnostics:

```bash
grpcurl -plaintext -d '{"get_diagnostics":{}}' 192.168.1.1:9000 SpaceX.API.Device.Device/Handle
```

Router response shape: `wifi_get_diagnostics` (id, hardware/software version, LAN client counts). This kit's router id is `Router-010000000000000001F29264`. The published proto does **not** take a Wi-Fi password or account cookie.

Minimum software (from SpaceX): router > 2023.55, user terminal > 2023.51.0.

The Starlink iOS/Android/web apps talk to the same service over gRPC-Web (`:9001` / `:9201`). This repo does not capture or replay those app sessions.

## What we stub

[`../stubs/consumer_session.py`](../stubs/consumer_session.py) prints the dish grpcurl catalog and fixtures by default. `STARLINK_LIVE=1` plus a command name (`get_status`, `reboot`, `dish_stow`, `unstow`) optionally runs that payload against `192.168.100.1:9200` when `grpcurl` is installed. The stub never reads cookies or passwords.

## What we do not stub

- Wi-Fi PSK / admin password changes
- Account-cookie flows on `starlink.com`
- Enterprise local HTTPS (Diagnostics / Sandbox) — that needs a router HTTPS server plus a TLS cert configured from a Business dashboard ([Local HTTPS API](https://starlink.readme.io/docs/router-api))

## Related official docs

- https://starlink.readme.io/docs/device-api
- https://starlink.readme.io/docs/starlink-wifi-routers
- https://starlink.readme.io/docs/diagnostics
- https://github.com/SpaceExplorationTechnologies/enterprise-api/tree/master/device-api
