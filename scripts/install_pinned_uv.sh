#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "The pinned CI uv archive is for x86_64 Linux runners." >&2
  exit 2
fi

: "${RUNNER_TEMP:?GitHub Actions must set RUNNER_TEMP}"
: "${GITHUB_PATH:?GitHub Actions must set GITHUB_PATH}"

version="0.13.4"
archive="$RUNNER_TEMP/uv-x86_64-unknown-linux-gnu.tar.gz"
install_dir="$RUNNER_TEMP/uv-0.13.4"
url="https://github.com/astral-sh/uv/releases/download/0.13.4/uv-x86_64-unknown-linux-gnu.tar.gz"
expected_sha256="2b428396f12572d4429cf210ca234dd599a33b3af0958a4d5ed569d63e3f344f"

curl --fail --location --silent --show-error "$url" --output "$archive"
sha256sum "$archive"
echo "$expected_sha256  $archive" | sha256sum --check
mkdir -p "$install_dir"
tar -xzf "$archive" --directory "$install_dir" --strip-components=1
actual_version="$("$install_dir/uv" --version)"
printf '%s\n' "$actual_version"
test "$actual_version" = \
  "uv $version (7456b60bc 2026-10-20 x86_64-unknown-linux-gnu)"
printf '%s\n' "$install_dir" >> "$GITHUB_PATH"
