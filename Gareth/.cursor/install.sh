#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

SITE_DIR="$(find_gareth_site)"
echo "[install] Installing Mona Astro site dependencies in ${SITE_DIR}"
npm ci --prefix "${SITE_DIR}"

SOCKET_PATH="${CURSOR_AGENT_SOCKET:-/run/cursor/api.sock}"
if [[ -S "${SOCKET_PATH}" ]]; then
  echo "[install] Checking Cloud Agent OIDC identity socket..."
  python3 "${SCRIPT_DIR}/oidc_token.py" --check
else
  echo "[install] Skipping OIDC check (no identity socket at ${SOCKET_PATH})"
fi

echo "[install] Done."
