#!/usr/bin/env bash
set -euo pipefail

target=${1:?Usage: bash scripts/init_project.sh DIRECTORY}
mkdir -p -- "$(dirname -- "$target")"
mkdir -- "$target"
mkdir -- "$target"/{input,dock,md,analysis,logs,provenance}
printf 'Project directories created: %s\n' "$target"
