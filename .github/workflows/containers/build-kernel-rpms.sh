#!/usr/bin/env bash
set -euo pipefail

packages=(-p kernel -p kernel-headers)
case "${1:-}" in
  --headers-only) packages=(-p kernel-headers); shift ;;
  --kernel-only) packages=(-p kernel); shift ;;
esac

if (( $# > 1 )) || [[ "${1:-}" == -* ]]; then
  echo "Usage: $0 [--headers-only|--kernel-only] [azurelinux-checkout]" >&2
  exit 2
fi

checkout="${1:-.}"
if [[ ! -f "$checkout/azldev.toml" ]]; then
  printf 'No azldev.toml in checkout: %s\n' "$checkout" >&2
  exit 2
fi

exec azldev -C "$checkout" comp build "${packages[@]}"
