#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="$REPO_ROOT/skill"
TARGET_ROOT="$CODEX_HOME/skills"
TARGET_DIR="$TARGET_ROOT/brand-reputation-monitor"

if [[ ! -d "$SOURCE_DIR" ]]; then
  echo "Source skill directory not found: $SOURCE_DIR" >&2
  exit 1
fi

mkdir -p "$TARGET_ROOT"
rm -rf "$TARGET_DIR"
cp -R "$SOURCE_DIR" "$TARGET_DIR"

echo "Installed brand-reputation-monitor to $TARGET_DIR"
