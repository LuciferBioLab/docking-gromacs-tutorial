#!/usr/bin/env bash
#SBATCH --job-name=1iep-cpu
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=08:00:00
#SBATCH --output=1iep-%j.log
set -euo pipefail
# Submit from the repository root. Load the site's Conda module as needed.
cd "${SLURM_SUBMIT_DIR:?}"
conda run --no-capture-output -n docking-gromacs make quickstart "RUN=runs/1iep-${SLURM_JOB_ID:?}" "THREADS=${SLURM_CPUS_PER_TASK:?}"
