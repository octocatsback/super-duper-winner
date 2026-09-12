# Publish notes

Copyright (c) 2026 Gareth Lee Douglas Kirman.

This file replaces the broken path `Starlink/publish ` (literal trailing space; contents were only `all my repos`). Use this name — `Starlink/publish.md` — with no trailing space.

No cookies, Wi-Fi passwords, account sessions, or API client secrets belong in this tree.

## 1. Umbrella publish of public octocatsback repos

This repository is the public monorepo for [octocatsback](https://github.com/octocatsback). Every **public** source repo is imported as a subdirectory (squash subtree or shallow submodule). The umbrella itself is not nested. The private `skills-agentic-workflows-that-read-the-room` tree stays out.

Inventory and pins: [`../README.md`](../README.md), [`../packages.yaml`](../packages.yaml).

History that published that inventory onto `main`:

| PR | What landed |
| -- | ----------- |
| [#10](https://github.com/octocatsback/super-duper-winner/pull/10) | Public octocatsback imports, remaining public repo `Cunts-`, and the first umbrella-owned `Starlink/` docs + stubs (solo-dev, linear graph). |
| [#11](https://github.com/octocatsback/super-duper-winner/pull/11) | Forward-fix: Bugbot High/Medium (Gareth hygiene/site scope) plus the local dish grpcurl catalog (`get_status` / `reboot` / `dish_stow` / unstow). |

`Starlink/` is umbrella-owned. It is not an imported GitHub repo.

## 2. Starlink Wi-Fi publish (`wifi_set_config`)

Site (public identifiers only):

| Field | Value |
| ----- | ----- |
| Router id | `Router-010000000000000001F29264` |
| SSID | `Wanjer` |
| Router gRPC | `192.168.1.1:9000` |
| Router gRPC-Web | `192.168.1.1:9001` |

Wi-Fi publish for this kit is an **authenticated gRPC-Web** `Handle` call on the router, not a dish grpcurl and not public API v2:

- Service: `SpaceX.API.Device.Device/Handle`
- Read: `wifi_get_config` (retrieve the current `WifiConfig`)
- Write: `wifi_set_config` (reapply that retrieved config)
- Bypass: leave **off** (`bypass` / bypass-mode disabled) so LAN traffic still goes through the Starlink router Wi-Fi, SSID `Wanjer`
- Auth: the Starlink app / router admin session that gRPC-Web already uses. Do **not** commit cookies, session tokens, or the Wi-Fi password.

Safe apply pattern:

1. Call `wifi_get_config` on `192.168.1.1:9001` (`Handle`).
2. Redact password / PSK / cookie fields **before** any log or file write.
3. Reapply the same config with `wifi_set_config` (same SSID `Wanjer`, same router id). Do not invent a new PSK in-repo.
4. Confirm bypass is off in the payload you send.
5. Confirm the live SSID is still `Wanjer` for `Router-010000000000000001F29264`.

The official SpaceX [`proto/device.proto`](proto/device.proto) snapshot only documents `get_diagnostics` for the published Device API. `wifi_get_config` / `wifi_set_config` are consumer-firmware `Handle` methods used by the Starlink app over gRPC-Web. This repo does not store a captured session and does not log those payloads.

## 3. Local dish grpcurl catalog

Same host, port, and service. No credentials.

```bash
grpcurl -plaintext -d '{"get_status":{}}' 192.168.100.1:9200 SpaceX.API.Device.Device/Handle
grpcurl -plaintext -d '{"reboot":{}}' 192.168.100.1:9200 SpaceX.API.Device.Device/Handle
grpcurl -plaintext -d '{"dish_stow":{}}' 192.168.100.1:9200 SpaceX.API.Device.Device/Handle
grpcurl -plaintext -d '{"dish_stow":{"unstow":true}}' 192.168.100.1:9200 SpaceX.API.Device.Device/Handle
```

| Payload | Effect |
| ------- | ------ |
| `{"get_status":{}}` | Dish status |
| `{"reboot":{}}` | Reboot the user terminal |
| `{"dish_stow":{}}` | Stow |
| `{"dish_stow":{"unstow":true}}` | Unstow |

`reboot` / `dish_stow` move hardware. Run them only on this LAN kit, never from CI. See [`docs/CONSUMER_SESSION.md`](docs/CONSUMER_SESSION.md) and [`stubs/consumer_session.py`](stubs/consumer_session.py).

Router `get_diagnostics` stays on `192.168.1.1:9000` and is not a Wi-Fi password API.
