#!/usr/bin/env bash
set -Eeuo pipefail

project_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if [[ ${1:-} == --help ]]; then
    printf '%s\n' 'Usage: bash scripts/run_example.sh [--dry-run] dock|smoke|quickstart NEW_DIRECTORY'
    exit 0
fi
dry=0
if [[ ${1:-} == --dry-run ]]; then dry=1; shift; fi
profile=${1:?Usage: bash scripts/run_example.sh dock|smoke|quickstart NEW_DIRECTORY}
destination=${2:?Supply a new output directory}
threads=${THREADS:-2}
seed=${SEED:-202601}

case "$profile" in dock|smoke|quickstart) ;; *) printf 'Unknown profile: %s\n' "$profile" >&2; exit 2;; esac
[[ $threads =~ ^[1-9][0-9]*$ && $seed =~ ^[1-9][0-9]*$ ]] || { echo 'THREADS and SEED must be positive integers.' >&2; exit 2; }
if ((dry)); then
    end=12
    if [[ $profile == dock ]]; then end=05; fi
    printf 'Plan: stages 01–%s, profile=%s, threads=%s, seed=%s, new directory=%s\n' "$end" "$profile" "$threads" "$seed" "$destination"
    exit 0
fi
mkdir -p -- "$(dirname -- "$destination")"
mkdir -- "$destination"
run_dir=$(cd -- "$destination" && pwd)
cd -- "$run_dir"
mkdir input dock md analysis logs provenance
printf '%s\n' "$profile" > provenance/profile.txt
printf 'threads=%s\nseed=%s\n' "$threads" "$seed" > provenance/settings.txt
printf 'stage,wall_seconds,bytes\n' > provenance/stages.csv
export OMP_NUM_THREADS="$threads"
stage=01
stage_start=$SECONDS
trap 'printf "Stage %s failed. Review %s/logs before using any outputs.\n" "$stage" "$run_dir" >&2' ERR

check() {
    bash "$project_dir/scripts/check_${stage}.sh" "$run_dir"
    printf '%s,%s,%s\n' "$stage" "$((SECONDS - stage_start))" "$(du -sb "$run_dir" | cut -f1)" >> provenance/stages.csv
}

logged() {
    local log=$1
    shift
    "$@" > "logs/$log.log" 2>&1 || { tail -n 30 "logs/$log.log" >&2; return 1; }
}

check
stage=02
stage_start=$SECONDS
cp -- "$project_dir/examples/1iep/"{1iep_receptorH.pdb,1iep_ligand.sdf,SHA256SUMS} input/
cp -- "$project_dir/config/1iep-box.txt" dock/box.txt
check

stage=03
stage_start=$SECONDS
python "$project_dir/scripts/example_io.py" order-example input/1iep_receptorH.pdb input/receptor_ordered.pdb
logged meeko_receptor mk_prepare_receptor.py --read_pdb input/receptor_ordered.pdb -o dock/receptor -p
logged meeko_ligand mk_prepare_ligand.py -i input/1iep_ligand.sdf -o dock/ligand.pdbqt
check

stage=04
stage_start=$SECONDS
logged vina vina --receptor dock/receptor.pdbqt --ligand dock/ligand.pdbqt --config dock/box.txt --scoring vina --cpu "$threads" --seed "$seed" --exhaustiveness 8 --num_modes 5 --out dock/docked.pdbqt
check

stage=05
stage_start=$SECONDS
logged meeko_export mk_export.py dock/docked.pdbqt -s dock/docked.sdf
logged pose python "$project_dir/scripts/example_io.py" pose input/1iep_ligand.sdf dock/docked.sdf dock/lig_pose.sdf
logged redocking python "$project_dir/scripts/redocking_rmsd.py" "$project_dir/examples/regression/1iep/crystal_ligand.sdf" dock/docked.sdf dock/redocking.csv
cat logs/pose.log
cat logs/redocking.log
check
if [[ $profile == dock ]]; then exit 0; fi

stage=06
stage_start=$SECONDS
cp -- dock/lig_pose.sdf md/
logged mol2 obabel md/lig_pose.sdf -O md/lig_pose.mol2 --title LIG
logged mol2_roundtrip obabel md/lig_pose.mol2 -O md/lig_roundtrip.sdf
logged mol2_check python "$project_dir/scripts/example_io.py" mol2 md/lig_pose.sdf md/lig_roundtrip.sdf
logged acpype bash -c 'cd -- "$1" && acpype -i lig_pose.mol2 -b LIG -a gaff2 -c bcc -n 1' _ "$run_dir/md"
check

stage=07
stage_start=$SECONDS
logged pdb2gmx bash -c 'cd -- "$1" && gmx pdb2gmx -f ../input/receptor_ordered.pdb -o protein.gro -p protein.top -i posre.itp -ff amber99sb-ildn -water tip3p -ignh' _ "$run_dir/md"
logged assembly python "$project_dir/scripts/example_io.py" assemble md
check

stage=08
stage_start=$SECONDS
python "$project_dir/scripts/example_mdp.py" md "$profile" "$seed"
check

stage=09
stage_start=$SECONDS
# Run GROMACS from the MD directory so local include files resolve consistently.
logged md_setup bash -euo pipefail -c '
    cd -- "$1"
    gmx editconf -f complex.gro -o boxed.gro -c -d 1.2 -bt dodecahedron
    gmx solvate -cp boxed.gro -cs spc216.gro -o solvated.gro -p topol.top
    gmx grompp -f ions.mdp -c solvated.gro -p topol.top -o ions.tpr -po ions-processed.mdp
    printf "SOL\n" | gmx genion -s ions.tpr -o solv_ions.gro -p topol.top -pname NA -nname CL -neutral -conc 0.15
' _ "$run_dir/md"
python "$project_dir/scripts/example_io.py" index md
logged equilibration bash -euo pipefail -c '
    cd -- "$1"
    gmx grompp -f em.mdp -c solv_ions.gro -p topol.top -o em.tpr -pp em-processed.top -po em-processed.mdp
    gmx mdrun -deffnm em -nt "$2"
    gmx grompp -f nvt.mdp -c em.gro -r em.gro -p topol.top -o nvt.tpr -po nvt-processed.mdp
    gmx mdrun -deffnm nvt -nt "$2"
    gmx grompp -f npt.mdp -c nvt.gro -r em.gro -t nvt.cpt -p topol.top -o npt.tpr -po npt-processed.mdp
    gmx mdrun -deffnm npt -nt "$2"
' _ "$run_dir/md" "$threads"
check

stage=10
stage_start=$SECONDS
logged production bash -euo pipefail -c '
    cd -- "$1"
    gmx grompp -f md.mdp -c npt.gro -t npt.cpt -p topol.top -o md.tpr -pp md-processed.top -po md-processed.mdp
    gmx mdrun -deffnm md -nt "$2"
' _ "$run_dir/md" "$threads"
check

stage=11
stage_start=$SECONDS
logged trajectory_check gmx check -f md/md.xtc
logged rmsd bash -euo pipefail -c '
    printf "System\n" | gmx trjconv -s md/md.tpr -f md/md.xtc -o analysis/whole.xtc -pbc whole
    printf "Complex\nSystem\n" | gmx trjconv -s md/md.tpr -f analysis/whole.xtc -o analysis/centered.xtc -n md/analysis_full.ndx -center -pbc mol
    printf "Backbone\nLigand_heavy\n" | gmx rms -s md/md.tpr -f analysis/centered.xtc -n md/analysis_full.ndx -o analysis/ligand-rmsd.xvg -tu ns
    printf "Complex\n" | gmx trjconv -s md/md.tpr -f analysis/centered.xtc -n md/analysis_full.ndx -o analysis/complex.pdb -dump 0
'
check

stage=12
stage_start=$SECONDS
logged versions bash -euo pipefail -c 'vina --version; gmx --version; python -m pip show meeko acpype'
cp -- logs/versions.log provenance/versions.txt
# Keep machine-specific diagnostic logs local. The release packager uses an allowlist.
sha256sum input/1iep_receptorH.pdb input/1iep_ligand.sdf dock/lig_pose.sdf md/md.tpr md/md.cpt md/md.xtc analysis/ligand-rmsd.xvg > provenance/outputs.sha256
check
printf 'Example complete: %s\n' "$run_dir"
