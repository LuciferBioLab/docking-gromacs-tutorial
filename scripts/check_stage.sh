#!/usr/bin/env bash
set -euo pipefail

step=${1:?Supply step 01–12}
if [[ ${2:-} == --help ]]; then
    printf 'Usage: bash scripts/check_%s.sh [--dry-run] RUN_DIRECTORY\n' "$step"
    exit 0
fi
if [[ ${2:-} == --dry-run ]]; then
    printf 'Read-only verification: stage %s in %s\n' "$step" "${3:?Supply the run directory}"
    exit 0
fi
run=${2:?Supply the run directory}
cd -- "$run"
profile=$(cat provenance/profile.txt)
require() {
    local file
    for file in "$@"; do
        if [[ ! -s $file ]]; then printf 'Missing or empty: %s\n' "$file" >&2; exit 1; fi
    done
}
has() {
    require "$2"
    if ! grep -Eq -- "$1" "$2"; then printf 'Expected pattern missing in %s: %s\n' "$2" "$1" >&2; exit 1; fi
}
has_final_step() {
    local mdp=$1 log=$2
    require "$mdp" "$log"
    awk '
        FNR == NR {
            sub(/;.*/, "")
            split($0, setting, "=")
            key = tolower(setting[1])
            gsub(/[[:space:]_-]/, "", key)
            value = setting[2]
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
            if (key == "nsteps") steps = value
            if (key == "initstep") start = value
            next
        }
        $1 == "Step" && $2 == "Time" {
            if (getline > 0 && $1 ~ /^[0-9]+$/) last = $1
        }
        END {
            if (steps !~ /^[0-9]+$/ || start !~ /^[0-9]+$/) {
                printf "Cannot read finite nsteps and init-step from %s.\n", ARGV[1]
                exit 1
            }
            expected = start + steps
            if (last == "" || last + 0 != expected) {
                printf "%s: expected final step %.0f, found %s.\n", ARGV[2], expected, last == "" ? "no step" : last
                exit 1
            }
        }
    ' "$mdp" "$log" >&2
}
case "$step" in
    01)
        for name in python vina mk_prepare_receptor.py mk_prepare_ligand.py mk_export.py obrms; do command -v "$name" >/dev/null; done
        python -c 'import rdkit, meeko'
        if [[ $profile != dock ]]; then
            for name in gmx acpype obabel; do command -v "$name" >/dev/null; done
        fi
        ;;
    02) require input/SHA256SUMS dock/box.txt; (cd input && sha256sum -c SHA256SUMS) ;;
    03) has '^ATOM' dock/receptor.pdbqt; has '^REMARK SMILES' dock/ligand.pdbqt ;;
    04) has '^REMARK VINA RESULT:' dock/docked.pdbqt; has '^ENDMDL' dock/docked.pdbqt ;;
    05)
        has 'identity and formal charge [+]1 match' logs/pose.log
        has '^\$\$\$\$' dock/lig_pose.sdf
        require dock/redocking.csv
        awk -F, '
            NR > 1 {
                sub(/\r$/, "", $2)
                if (NF != 2 || $1 !~ /^[1-9][0-9]*$/ || $2 !~ /^[0-9]+(\.[0-9]+)?$/) invalid = 1
                else if ($2 + 0 <= 2) ok = 1
            }
            END {
                if (invalid) {print "Malformed rank or RMSD in redocking.csv"; exit 1}
                if (!ok) {print "No 1IEP pose at or under 2 Å"; exit 1}
            }
        ' dock/redocking.csv >&2
        ;;
    06) require md/LIG.acpype/LIG_GMX.itp md/LIG.acpype/LIG_GMX.gro; has 'MOL2 fixed-frame heavy-atom RMSD' logs/mol2_check.log ;;
    07) require md/complex.gro md/topol.top md/ligand_atomtypes.itp md/analysis.ndx; has '^#include "ligand.itp"' md/topol.top ;;
    08) require md/{ions,em,nvt,npt,md}.mdp; has '^nsteps' md/md.mdp ;;
    09)
        require md/solv_ions.gro md/em.gro md/nvt.cpt md/npt.cpt
        has 'Finished mdrun' md/nvt.log
        has 'Finished mdrun' md/npt.log
        has_final_step md/nvt-processed.mdp md/nvt.log
        has_final_step md/npt-processed.mdp md/npt.log
        if grep -Eiq 'LINCS WARNING|constraint failure|non-finite' md/{em,nvt,npt}.log; then
            echo 'Constraint or nonfinite failure in an equilibration log.' >&2
            exit 1
        fi
        ;;
    10)
        require md/md.tpr md/md.cpt md/md.xtc md/md-processed.top
        has 'Finished mdrun' md/md.log
        has_final_step md/md-processed.mdp md/md.log
        if grep -Eiq 'LINCS WARNING|constraint failure|non-finite' md/md.log; then
            echo 'Constraint or nonfinite failure in the production log.' >&2
            exit 1
        fi
        ;;
    11) require analysis/centered.xtc analysis/ligand-rmsd.xvg analysis/complex.pdb; has '^[[:space:]]*[0-9]' analysis/ligand-rmsd.xvg ;;
    12) require provenance/versions.txt provenance/outputs.sha256; sha256sum -c provenance/outputs.sha256 ;;
    *) printf 'Unknown stage %s\n' "$step" >&2; exit 2 ;;
esac
printf 'PASS stage %s\n' "$step"
