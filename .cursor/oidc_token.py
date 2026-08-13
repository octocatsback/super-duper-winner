#!/usr/bin/env python3
"""Mint and cache short-lived Cursor Cloud Agent OIDC tokens.

Talks to the local identity socket (CURSOR_AGENT_SOCKET, default
/run/cursor/api.sock). See https://cursor.com/docs/cloud-agent/identity
"""

from __future__ import annotations

import argparse
import http.client
import json
import os
import socket
import sys
import threading
import time
from typing import Any, Optional, Tuple

SOCKET = os.environ.get("CURSOR_AGENT_SOCKET", "/run/cursor/api.sock")
AUDIENCE = "sts.amazonaws.com"
REFRESH_BUFFER_SECS = 30
TOKEN_TTL_SECS = 300
OIDC_PATH = "/v1/tokens/oidc"
MINT_TIMEOUT_SECS = 10


class UnixHTTPConnection(http.client.HTTPConnection):
    """HTTP/1.1 over a Unix domain socket. The URL hostname is ignored."""

    def __init__(self, unix_socket: str, timeout: float = MINT_TIMEOUT_SECS) -> None:
        super().__init__("localhost", timeout=timeout)
        self._unix_socket = unix_socket

    def connect(self) -> None:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        sock.connect(self._unix_socket)
        self.sock = sock


class OIDCTokenCache:
    def __init__(
        self,
        aud: str = AUDIENCE,
        buffer: int = REFRESH_BUFFER_SECS,
        socket_path: str = SOCKET,
        nonce: Optional[str] = None,
        sub_claim: Optional[str] = None,
    ) -> None:
        self.aud = aud
        self.buffer = buffer
        self.socket_path = socket_path
        self.nonce = nonce
        self.sub_claim = sub_claim
        self._token: Optional[str] = None
        self._expires_at: float = 0.0
        self._lock = threading.Lock()

    def get(self) -> str:
        """Return a valid token, minting or refreshing if necessary."""
        with self._lock:
            now = time.time()
            if self._token and now < (self._expires_at - self.buffer):
                return self._token
            return self._mint_and_store()

    def _mint_and_store(self) -> str:
        """Must be called while holding the lock."""
        token, expires_at = self._mint()
        self._token = token
        self._expires_at = expires_at
        return token

    def _mint(self) -> Tuple[str, float]:
        payload: dict[str, Any] = {"aud": self.aud}
        if self.nonce is not None:
            payload["nonce"] = self.nonce
        if self.sub_claim is not None:
            payload["sub_claim"] = self.sub_claim
        body = json.dumps(payload).encode("utf-8")

        conn = UnixHTTPConnection(self.socket_path, timeout=MINT_TIMEOUT_SECS)
        try:
            conn.request(
                "POST",
                OIDC_PATH,
                body=body,
                headers={"Content-Type": "application/json"},
            )
            response = conn.getresponse()
            raw = response.read().decode("utf-8")
            if response.status != 200:
                raise RuntimeError(
                    f"OIDC mint failed: HTTP {response.status} from {OIDC_PATH}"
                )
        finally:
            conn.close()

        data = json.loads(raw)
        token = data["token"]
        expires_at = float(data.get("expires_at") or (time.time() + TOKEN_TTL_SECS))
        if not token or not isinstance(token, str):
            raise RuntimeError("OIDC mint returned an empty token")
        return token, expires_at

    def invalidate(self) -> None:
        """Force a refresh on the next get() (for example after STS rejection)."""
        with self._lock:
            self._token = None
            self._expires_at = 0.0


token_cache = OIDCTokenCache()


def _check() -> int:
    """Mint once and report success without printing the token."""
    if not os.path.exists(token_cache.socket_path):
        print(f"oidc check failed: socket missing at {token_cache.socket_path}", file=sys.stderr)
        return 1

    first = token_cache.get()
    cached = token_cache.get()
    if first != cached:
        print("oidc check failed: cache did not reuse an unexpired token", file=sys.stderr)
        return 1

    remaining = token_cache._expires_at - time.time()
    print("oidc mint ok")
    print(f"aud={token_cache.aud}")
    print(f"expires_in_secs={int(remaining)}")
    print(f"cached_reuse={'yes' if first == cached else 'no'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Cursor Cloud Agent OIDC helper")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Mint a token and print status only (never the JWT).",
    )
    args = parser.parse_args()
    if args.check:
        return _check()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
