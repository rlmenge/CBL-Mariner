#!/usr/bin/env bash
set -euo pipefail

mkdir -p base/build/work/scratch
status="$PWD/base/build/work/scratch/kernel-status"
patch="$PWD/base/build/work/scratch/kernel.patch"
upstream=https://github.com/microsoft/CBL-Mariner-Linux-Kernel
selector=(-p kernel -p kernel-headers)
head_sha="$(git rev-parse HEAD)"
printf '4.0 base: %s\nStarting SHA: %s\n' "$BASELINE_SHA" "$head_sha" > "$status"

noop() {
  printf 'No candidate: %s\n' "$1" | tee -a "$status"
  exit 0
}

check_paths() {
  git diff --raw --no-renames "$@" |
    awk -F '\t' '
      $1 !~ /^:100644 100644 / ||
      $2 !~ /^(base\/comps\/kernel\/(kernel\.(comp\.toml|spec)|sources|6\.18-(aarch64|x86_64)-azl\.config)|base\/comps\/kernel-headers\/kernel-headers\.(comp\.toml|spec)|locks\/kernel(-headers)?\.lock|specs\/k\/kernel\/(kernel\.spec|sources|6\.18-(aarch64|x86_64)-azl\.config)|specs\/k\/kernel-headers\/(kernel-headers\.spec|sources))$/ {
        bad = 1
      }
      END {exit bad}
    '
}

if [[ "$IS_PR" == true ]]; then
  [[ "$BASELINE_SHA" != "$head_sha" ]] || noop 'The PR head was not checked out.'
  git merge-base --is-ancestor "$BASELINE_SHA" "$head_sha" || noop 'Rebase required.'
  check_paths "$BASELINE_SHA" "$head_sha" || noop 'The PR contains changes outside the expected bump.'
fi

pin() {
  git show "$1:base/comps/$2/$2.comp.toml" |
    sed -nE 's#^origin = .*archive/rolling-lts/azl4/([0-9]+(\.[0-9]+){3})\.tar\.gz.*#\1#p'
}

old="$(pin "$BASELINE_SHA" kernel)"
[[ "$old" =~ ^[0-9]+(\.[0-9]+){3}$ && "$old" == "$(pin "$BASELINE_SHA" kernel-headers)" ]] ||
  noop 'The 4.0 source pins are missing or inconsistent.'

tags="$(git ls-remote --tags "$upstream" 'refs/tags/rolling-lts/azl4/*')"
latest="$(awk '$2 ~ /^refs\/tags\/rolling-lts\/azl4\/[0-9]+(\.[0-9]+){3}$/ {split($2, p, "/"); print p[5]}' \
  <<< "$tags" | sort -V | tail -n 1)"
[[ -n "$latest" && "$latest" != "$old" && "$(printf '%s\n' "$latest" "$old" | sort -V | tail -n 1)" == "$latest" ]] ||
  noop '4.0 has no newer AZL4 kernel tag.'
[[ "${latest%.*.*}" == "${old%.*.*}" && "${latest%.*.*}" == 6.18 ]] ||
  noop 'Kernel series changes require a maintainer.'
ref="refs/tags/rolling-lts/azl4/$latest"
tag_commit="$(awk -v ref="$ref" '$2 == ref {direct=$1} $2 == ref "^{}" {peeled=$1}
  END {print peeled ? peeled : direct}' <<< "$tags")"
[[ "$tag_commit" =~ ^[0-9a-f]{40}$ ]]

if [[ "$IS_PR" == true ]]; then
  [[ "$(pin "$head_sha" kernel)" == "$latest" && "$(pin "$head_sha" kernel-headers)" == "$latest" ]] ||
    noop 'The PR is not pinned to the current eligible tag.'
fi

scratch="$(mktemp -d "$PWD/base/build/work/scratch/kernel-bump.XXXXXX")"
# Recheck the peeled ref after hashing to catch tag movement during download.
digest="$(curl -fsSL --retry 2 --max-time 240 "$upstream/archive/rolling-lts/azl4/$latest.tar.gz" |
  sha512sum | cut -d ' ' -f 1)"
[[ "$digest" =~ ^[0-9a-f]{128}$ ]]
live_tag="$(git ls-remote --tags "$upstream" "$ref" "$ref^{}")"
[[ "$(awk -v ref="$ref" '$2 == ref {direct=$1} $2 == ref "^{}" {peeled=$1}
  END {print peeled ? peeled : direct}' <<< "$live_tag")" == "$tag_commit" ]] ||
  noop 'The tag moved during archive download.'

git init --quiet "$scratch/repo"
git -C "$scratch/repo" fetch --quiet --no-tags --no-recurse-submodules "$PWD" "$head_sha"
cd "$scratch/repo"
git switch --quiet --detach "$head_sha"
git config user.name 'github-actions[bot]'
git config user.email '41898282+github-actions[bot]@users.noreply.github.com'

python3 - "$IS_PR" "$old" "$latest" "$digest" <<'PY'
import re
import sys
import tomllib
from pathlib import Path
from time import strftime, gmtime

followup, old, target, digest = sys.argv[1:]
uri = "https://github.com/microsoft/CBL-Mariner-Linux-Kernel/archive/rolling-lts/azl4/"
version, revision = target.rsplit(".", 1)


def substitute(text, pattern, replacement):
    result, count = re.subn(pattern, lambda _: replacement, text, flags=re.MULTILINE)
    if count != 1:
        sys.exit(f"Expected exactly one match: {pattern}")
    return result


for component, version_macros in (
    ("kernel", ("specrpmversion",)),
    ("kernel-headers", ("specversion", "tarfile_release")),
):
    root = Path("base/comps") / component
    config = root / f"{component}.comp.toml"
    text = config.read_text()
    sources = tomllib.loads(text)["components"][component]["source-files"]
    expected = target if followup == "true" else old
    filename = f"kernel-{expected}.tar.gz"
    (source,) = (s for s in sources if s["filename"] == filename)
    if source["origin"]["uri"] != f"{uri}{expected}.tar.gz" or source["hash-type"] != "SHA512":
        sys.exit(f"Unexpected source origin or hash type for {component}")
    if followup == "true":
        if source["hash"] != digest:
            sys.exit(f"PR archive checksum does not match the upstream tag for {component}")
        continue
    block = (
        f'filename = "kernel-{target}.tar.gz"\n'
        f'hash = "{digest}"\nhash-type = "SHA512"\n'
        f'origin = {{ type = "download", uri = "{uri}{target}.tar.gz" }}'
    )
    config.write_text(substitute(text, rf'^filename = "{re.escape(filename)}"\nhash = "[0-9a-f]{{128}}"\n'
                                      rf'hash-type = "SHA512"\norigin = \{{[^\n]+\}}$', block))
    spec = root / f"{component}.spec"
    text = spec.read_text()
    for macro, value in [("kextraversion", revision), *((m, version) for m in version_macros)]:
        text = substitute(text, rf"^%define {macro} [0-9.]+$", f"%define {macro} {value}")
    (release,) = re.findall(r"^%define azl_pkgrelease ([0-9]+)$", text, re.MULTILINE)
    date = strftime("%a %b %d %Y", gmtime())
    spec.write_text(substitute(text, r"^%changelog$", f"%changelog\n"
                               f"* {date} Azure Linux Automation <41898282+github-actions[bot]@users.noreply.github.com>"
                               f" - {version}-{revision}.{release}\n"
                               f"- Update kernel and kernel-headers to {target}.\n"))

    if component == "kernel":
        manifest = root / "sources"
        manifest.write_text(substitute(manifest.read_text(), rf"^SHA512 \({re.escape(filename)}\) = [0-9a-f]{{128}}$",
                                       f"SHA512 (kernel-{target}.tar.gz) = {digest}"))
PY

(
  cd scripts/ci/kernel/kernel-config-checker
  # The candidate leaves both Kconfigs untouched; validate the starting revision
  # before running the container against any PR-controlled component data.
  python3 -m pytest -q tests/test_kernel_config_validation.py --base-sha "$BASELINE_SHA" --head-sha HEAD
)
run_in_container() {
  docker run --rm --cap-add=SYS_ADMIN --security-opt seccomp=unconfined \
    --security-opt apparmor=unconfined -v "$PWD:/workdir" \
    "$@"
}
render() {
  run_in_container localhost/azldev-runner azldev comp render "${selector[@]}"
  for component in kernel kernel-headers; do
    test -s "specs/k/$component/$component.spec"
    test ! -e "specs/k/$component/RENDER_FAILED"
  done
}
run_in_container localhost/azldev-runner azldev comp update "${selector[@]}"
render

git add -- base/comps/kernel base/comps/kernel-headers locks/kernel.lock locks/kernel-headers.lock \
  specs/k/kernel specs/k/kernel-headers
if git diff --cached --quiet; then
  noop 'No lock or rendered-spec drift to repair.'
fi
git diff --cached --check
check_paths --cached || noop 'The rendered candidate touched unexpected files.'
git -c core.hooksPath=/dev/null commit -qm "feat(kernel): update kernel and headers to $latest"
render
git diff --exit-code
if [[ "${BUILD_KERNEL_HEADERS:-false}" == true ]]; then
  printf 'RPM output directory (runner-local only): %s/base/out/\n' "$PWD"
  run_in_container -v "${BUILD_HELPER:?Missing trusted RPM build helper}:/build-kernel-rpms.sh:ro" \
    localhost/azldev-runner bash /build-kernel-rpms.sh --headers-only /workdir
  if [[ ! -d base/out/rpms || -z "$(find base/out/rpms -type f -name 'kernel-headers-[0-9]*.rpm' -print -quit)" ]]; then
    printf 'No binary RPM produced for kernel-headers\n' >&2
    exit 1
  fi
  git diff --exit-code
  printf 'RPM build: kernel-headers passed (%s); full kernel RPMs were not built.\n' "$(uname -m)" | tee -a "$status"
else
  printf 'RPM build: not requested.\n' >> "$status"
fi
git diff --binary "$head_sha" HEAD > "$patch"
printf 'Previous version: %s\nCandidate version: %s\nTag ref: %s\nTag commit: %s\nSHA-512: %s\n%s\n' \
  "$old" "$latest" "$ref" "$tag_commit" "$digest" \
  'Validation: lock update, clean post-commit re-render, diff check, and kernel config tests passed.' >> "$status"
