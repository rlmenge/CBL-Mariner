#!/usr/bin/env bash
set -euo pipefail

packages=(-p kernel -p kernel-headers)
if [[ "${1:-}" == --headers-only ]]; then
  packages=(-p kernel-headers)
  shift
fi

if (( $# > 1 )) || [[ "${1:-}" == -* ]]; then
  echo "Usage: $0 [--headers-only] [azurelinux-checkout]" >&2
  exit 2
fi

checkout="${1:-.}"
if [[ ! -f "$checkout/azldev.toml" ]]; then
  printf 'No azldev.toml in checkout: %s\n' "$checkout" >&2
  exit 2
fi

exec azldev -C "$checkout" comp build "${packages[@]}"
