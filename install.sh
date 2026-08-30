#!/usr/bin/env bash
# Install vibe-proof-auditor into Agent Skills dirs, including Antigravity (agy).
# `npx skills add` often lands in ~/.agents/skills but misses antigravity-cli —
# this script closes that gap so you do not symlink by hand.
set -euo pipefail

NAME="vibe-proof-auditor"
DEMO_NAME="demo-skill"
REPO_URL="${VIBE_PROOF_REPO:-https://github.com/pedroknigge/vibe-proof-auditor.git}"

SRC="$(cd "$(dirname "$0")" 2>/dev/null && pwd || true)"
cleanup_src=""
MODE="global"
UNINSTALL=0
copied=0
removed=0

usage() {
  cat <<EOF
Usage: ./install.sh [--global|--project] [--uninstall] [--help]

  --global   Install under \$HOME (default)
  --project  Install under the current workspace (.agents/skills + .gemini when present)
  --uninstall  Remove installed copies from the chosen scope
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global) MODE="global"; shift ;;
    --project) MODE="project"; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

have_local() {
  [[ -n "${SRC}" && -f "${SRC}/SKILL.md" && -d "${SRC}/vibe_proof_auditor" ]]
}

if ! have_local; then
  SRC="$(mktemp -d "${TMPDIR:-/tmp}/vibe-proof-install.XXXXXX")"
  cleanup_src="$SRC"
  git clone --depth 1 "$REPO_URL" "$SRC" >/dev/null
fi

trap '[[ -n "$cleanup_src" ]] && rm -rf "$cleanup_src"' EXIT

if [[ "$MODE" == "global" ]]; then
  base="${HOME}"
else
  base="$(pwd)"
fi

copy_one() {
  local dest="$1" source="${2:-$SRC}"
  mkdir -p "$(dirname "$dest")"
  rm -rf "$dest"
  mkdir -p "$dest"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
      --exclude .git \
      --exclude .orderfield \
      --exclude '__pycache__' \
      --exclude 'vibe-proof-audit-report.*' \
      "$source/" "$dest/"
  else
    cp -R "$source"/. "$dest/"
    rm -rf "$dest/.git" "$dest/.orderfield"
    find "$dest" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
  fi
  echo "installed $dest"
}

remove_one() {
  local dest="$1"
  if [[ -e "$dest" || -L "$dest" ]]; then
    rm -rf "$dest"
    echo "removed $dest"
    return 0
  fi
  return 1
}

# Universal + Antigravity hub/CLI. config/skills is the shared global that all
# AGY products read; antigravity-cli still needs its own tree on many builds.
agy_dests() {
  if [[ "$MODE" == "global" ]]; then
    printf '%s\n' \
      "$base/.agents/skills/$NAME" \
      "$base/.gemini/config/skills/$NAME" \
      "$base/.gemini/antigravity-cli/skills/$NAME" \
      "$base/.gemini/antigravity/skills/$NAME"
  else
    printf '%s\n' \
      "$base/.agents/skills/$NAME"
  fi
}

demo_agy_dests() {
  if [[ "$MODE" == "global" ]]; then
    printf '%s\n' \
      "$base/.gemini/config/skills/$DEMO_NAME" \
      "$base/.gemini/antigravity-cli/skills/$DEMO_NAME"
  fi
}

should_install_agy_dest() {
  local dest="$1" parent
  parent="$(dirname "$(dirname "$dest")")"
  # Always install generic .agents/skills
  if [[ "$dest" == *"/.agents/skills/"* ]]; then
    return 0
  fi
  if command -v agy >/dev/null 2>&1; then
    return 0
  fi
  [[ -d "$parent" ]]
}

if [[ "$UNINSTALL" -eq 1 ]]; then
  while IFS= read -r dest; do
    if remove_one "$dest"; then
      removed=$((removed + 1))
    fi
  done < <(agy_dests)
  while IFS= read -r dest; do
    if remove_one "$dest"; then
      removed=$((removed + 1))
    fi
  done < <(demo_agy_dests)
  echo "removed from $removed location(s)"
  exit 0
fi

while IFS= read -r dest; do
  if should_install_agy_dest "$dest"; then
    copy_one "$dest"
    copied=$((copied + 1))
  fi
done < <(agy_dests)

while IFS= read -r dest; do
  if should_install_agy_dest "$dest"; then
    copy_one "$dest" "$SRC/evals/fixtures/skill-docs"
    copied=$((copied + 1))
  fi
done < <(demo_agy_dests)

echo "copied to $copied skill dir(s)"
echo "generic: $base/.agents/skills/$NAME"
if command -v agy >/dev/null 2>&1; then
  echo "agy harden: python3 -m vibe_proof_auditor.harden_agy path/to/vibe-proof-audit-report.md"
  echo "agy fixture: /$DEMO_NAME"
fi
echo "or: npx skills add pedroknigge/vibe-proof-auditor -g -y -a antigravity -a antigravity-cli"
