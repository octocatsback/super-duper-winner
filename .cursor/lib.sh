# Shared helpers for Cloud Agent install and the Astro dev server.
# shellcheck shell=bash

find_gareth_site() {
  local script_dir repo_root candidate
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  repo_root="$(cd "${script_dir}/.." && pwd)"

  for candidate in \
    "${repo_root}/site" \
    "${PWD}/site" \
    "${PWD}/Gareth/site" \
    "${PWD}/repos/Gareth/site" \
    "/agent/repos/Gareth/site"
  do
    if [[ -f "${candidate}/package.json" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done

  echo "error: could not find Gareth site/package.json (cwd=${PWD})" >&2
  return 1
}
