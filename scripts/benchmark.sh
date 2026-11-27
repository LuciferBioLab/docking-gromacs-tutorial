#!/usr/bin/env bash
set -euo pipefail
usage() { printf '%s\n' 'Usage: bash scripts/benchmark.sh [--dry-run] TPR NEW_DIR cpu|cuda [threads=4] [steps=5000]'; }
if [[ ${1:-} == --help ]]; then usage; exit 0; fi
dry=0
if [[ ${1:-} == --dry-run ]]; then dry=1; shift; fi
tpr=${1:?Set TPR}; output=${2:?Set new directory}; backend=${3:?Set cpu or cuda}
threads=${4:-4}; nsteps=${5:-5000}
[[ $threads =~ ^[1-9][0-9]*$ && $nsteps =~ ^[1-9][0-9]*$ ]] || exit 2
cmd=(gmx mdrun -s "$(realpath "$tpr")" -deffnm bench -ntmpi 1 -ntomp "$threads" -nsteps "$nsteps")
case "$backend" in
    cpu) cmd+=(-nb cpu -pme cpu) ;;
    cuda) cmd+=(-nb gpu -pme gpu) ;;
    *) usage >&2; exit 2 ;;
esac
if ((dry)); then printf '%q ' "${cmd[@]}"; printf '\n'; exit 0; fi
test -s "$tpr"
mkdir -- "$output"
cd -- "$output"
"${cmd[@]}" > bench-console.log 2>&1
grep -E 'Performance:|Finished mdrun' bench.log
