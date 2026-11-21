#!/usr/bin/env bash
set -euo pipefail

if (( $# == 0 )); then
  echo 'Expected at least one repaired architecture.' >&2
  exit 2
fi

sources=()
generated=(locks/kernel.lock)
for arch in "$@"; do
  case "$arch" in x86_64|aarch64) ;; *) echo "Unexpected architecture: $arch" >&2; exit 2 ;; esac
  config="6.18-$arch-azl.config"
  sources+=("base/comps/kernel/$config")
  generated+=("specs/k/kernel/$config")
done

commit() {
  git -c user.name='Azure Linux Automation' -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
    -c core.hooksPath=/dev/null commit -m "$@"
}
in_mock() {
  timeout 10m docker run --rm --cap-add=SYS_ADMIN --security-opt seccomp=unconfined \
    --security-opt apparmor=unconfined -v "$PWD:/workdir" localhost/azldev-runner azldev "$@"
}

commit 'ci: apply verified Kconfig repair' -- "${sources[@]}"
in_mock comp update -p kernel
in_mock comp render -p kernel
test ! -e specs/k/kernel/RENDER_FAILED
for arch in "$@"; do
  config="6.18-$arch-azl.config"
  cmp -- "base/comps/kernel/$config" "specs/k/kernel/$config"
done
git add -- "${generated[@]}"
git diff --exit-code
git diff --cached --check
commit 'ci: refresh generated kernel build inputs'
in_mock comp render -p kernel
test ! -e specs/k/kernel/RENDER_FAILED
git diff --exit-code HEAD
