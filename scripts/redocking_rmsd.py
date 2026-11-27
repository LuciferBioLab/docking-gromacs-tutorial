"""Report fixed-frame, symmetry-aware heavy-atom RMSD in angstroms for each pose."""

import argparse
import csv
import math
import subprocess
import tempfile
from pathlib import Path

from example_io import read_sdf


def compare(reference, poses, output, dry_run):
    if dry_run:
        print(f"Compare {poses} with {reference} without independent ligand alignment.")
        return
    from rdkit import Chem

    records = read_sdf(poses)
    values = []
    with tempfile.TemporaryDirectory() as tmp:
        structure = Path(tmp) / "pose.sdf"
        for pose in records:
            with Chem.SDWriter(str(structure)) as writer:
                writer.write(pose)
            result = subprocess.check_output(["obrms", str(reference), str(structure)], text=True)
            number = float(result.splitlines()[-1].split()[-1])
            if not math.isfinite(number):
                raise ValueError("Nonfinite RMSD. Inspect ligand connectivity and atom correspondence.")
            values.append(number)
    with output.open("x", newline="") as handle:
        table = csv.writer(handle)
        table.writerow(["rank", "rmsd_A"])
        table.writerows((i, f"{value:.6f}") for i, value in enumerate(values, 1))
    print(f"Top-1 RMSD {values[0]:.3f} Å; best sampled RMSD {min(values):.3f} Å.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("poses", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    compare(args.reference, args.poses, args.output, args.dry_run)
