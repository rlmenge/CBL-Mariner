#!/usr/bin/env bash
set -euo pipefail

scratch="$PWD/base/build/work/scratch"
repaired=()
for arch in x86_64 aarch64; do
  evidence="$scratch/kernel-repair-$GITHUB_RUN_ATTEMPT-$arch"
  test -f "$evidence/notes.md"
  if [[ -s "$evidence/notes.md" ]]; then
    test -s "$evidence/repaired.config"
    repaired+=("$arch")
  else
    test ! -e "$evidence/repaired.config"
  fi
done
if (( ${#repaired[@]} == 0 )); then
  exit 0
fi

git apply --index "$scratch/kernel.patch"
test "$(git write-tree)" = "$CANDIDATE_TREE"
git -c user.name='Azure Linux Automation' -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
  -c core.hooksPath=/dev/null commit -m 'ci: stage validated kernel update'
for arch in "${repaired[@]}"; do
  cp -- "$scratch/kernel-repair-$GITHUB_RUN_ATTEMPT-$arch/repaired.config" "base/comps/kernel/6.18-$arch-azl.config"
done

containers=.github/workflows/containers
docker build --build-arg "UID=$(id -u)" \
  --build-arg "AZLDEV_VERSION=$(cat .azldev-version)" \
  -t localhost/azldev-runner -f "$containers/azldev-runner.Dockerfile" "$containers"
bash "$containers/refresh-kernel-retry.sh" "${repaired[@]}"
(
  cd scripts/ci/kernel/kernel-config-checker
  python3 -m pip install --requirement=requirements.txt
  python3 -m pytest -q tests/test_kernel_config_validation.py --base-sha "$GITHUB_SHA" --head-sha HEAD
)
git diff --check "$GITHUB_SHA" HEAD
git diff --binary "$GITHUB_SHA" HEAD > "$scratch/kernel.patch"
{
  printf '\n**Kconfig changes**\n\n'
  for arch in "${repaired[@]}"; do
    cat -- "$scratch/kernel-repair-$GITHUB_RUN_ATTEMPT-$arch/notes.md"
    printf 'Kernel rebuild passed on %s after one Kconfig retry.\n' "$arch"
  done
} >> "$scratch/kernel-status"
