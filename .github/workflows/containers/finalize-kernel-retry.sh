#!/usr/bin/env bash
set -euo pipefail

scratch="$PWD/base/build/work/scratch"
proposed=()
blocked=false
declare -A statuses=()
for arch in x86_64 aarch64; do
  headers="$scratch/kernel-result-$GITHUB_RUN_ATTEMPT-kernel-headers-$arch/status"
  if [[ ! -f "$headers" || "$(cat -- "$headers")" != passed ]]; then
    echo "No verified kernel-headers RPM result for $arch; refusing draft." >&2
    exit 1
  fi
  [[ "$BUILD_FULL_KERNEL" == true ]] || continue
  evidence="$scratch/kernel-result-$GITHUB_RUN_ATTEMPT-kernel-$arch"
  if [[ ! -f "$evidence/status" ]]; then
    echo "No publishable kernel RPM result for $arch; refusing draft." >&2
    exit 1
  fi
  statuses[$arch]="$(cat -- "$evidence/status")"
  case "${statuses[$arch]}" in
    passed) ;;
    retry-failed)
      test -s "$evidence/notes.md"
      blocked=true
      ;;
    *) echo "Invalid kernel RPM result for $arch; refusing draft." >&2; exit 1 ;;
  esac
  test -f "$evidence/notes.md"
  if [[ -s "$evidence/notes.md" ]]; then
    test -s "$evidence/repaired.config"
    proposed+=("$arch")
  else
    test ! -e "$evidence/repaired.config"
  fi
done
{
  if [[ "$blocked" == true ]]; then
    echo '**Blocked: kernel RPM build failed after a Kconfig retry. Do not merge.**'
  fi
  printf '%s\n' '- kernel-headers RPM verified on x86_64 and arm64 (aarch64).'
  if [[ "$BUILD_FULL_KERNEL" == true ]]; then
    for arch in x86_64 aarch64; do
      if [[ "${statuses[$arch]}" == passed ]]; then
        printf -- '- kernel RPM verified on %s.\n' "$arch"
      else
        printf -- '- kernel RPM build failed on %s after one Kconfig retry.\n' "$arch"
      fi
    done
  else
    printf '%s\n' '- Full kernel RPM build was not requested.'
  fi
  printf '%s\n' '- Boot tests were not run.'
} >> "$scratch/kernel-status"
if (( ${#proposed[@]} == 0 )); then
  exit 0
fi

git apply --index "$scratch/kernel.patch"
test "$(git write-tree)" = "$CANDIDATE_TREE"
git -c user.name='Azure Linux Automation' -c user.email='41898282+github-actions[bot]@users.noreply.github.com' \
  -c core.hooksPath=/dev/null commit -m 'ci: stage prepared kernel update'
for arch in "${proposed[@]}"; do
  cp -- "$scratch/kernel-result-$GITHUB_RUN_ATTEMPT-kernel-$arch/repaired.config" "base/comps/kernel/6.18-$arch-azl.config"
done

containers=.github/workflows/containers
docker build --build-arg "UID=$(id -u)" \
  --build-arg "AZLDEV_VERSION=$(cat .azldev-version)" \
  -t localhost/azldev-runner -f "$containers/azldev-runner.Dockerfile" "$containers"
bash "$containers/refresh-kernel-retry.sh" "${proposed[@]}"
(
  cd scripts/ci/kernel/kernel-config-checker
  python3 -m pip install --requirement=requirements.txt
  python3 -m pytest -q tests/test_kernel_config_validation.py --base-sha "$GITHUB_SHA" --head-sha HEAD
)
git diff --check "$GITHUB_SHA" HEAD
git diff --binary "$GITHUB_SHA" HEAD > "$scratch/kernel.patch"
{
  printf '\n**Kconfig changes**\n\n'
  for arch in "${proposed[@]}"; do
    if [[ "${statuses[$arch]}" == retry-failed ]]; then
      printf '\n**%s: proposal included for review; the rebuild failed.**\n\n' "$arch"
    fi
    cat -- "$scratch/kernel-result-$GITHUB_RUN_ATTEMPT-kernel-$arch/notes.md"
  done
} >> "$scratch/kernel-status"
