#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib.sh
source "${SCRIPT_DIR}/lib.sh"

SITE_DIR="$(find_gareth_site)"
cd "${SITE_DIR}"

if [[ ! -d node_modules ]]; then
  echo "[dev-server] node_modules missing; running npm ci..."
  npm ci
fi

export ASTRO_TELEMETRY_DISABLED=1
echo "[dev-server] Starting Mona Astro site from ${SITE_DIR} on 0.0.0.0:4321"
exec npm run dev -- --host 0.0.0.0 --port 4321
