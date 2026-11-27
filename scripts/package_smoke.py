"""Package only reviewed public smoke outputs and a checksum manifest."""

import argparse
import hashlib
import re
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]

ALLOW = (
    "input/1iep_receptorH.pdb", "input/1iep_ligand.sdf", "input/SHA256SUMS",
    "dock/box.txt", "dock/docked.pdbqt", "dock/lig_pose.sdf", "dock/redocking.csv",
    "md/md.mdp", "md/md.xtc",
    "md/md.edr", "md/md.gro",
    "md/md-processed.top", "analysis/ligand-rmsd.xvg", "analysis/complex.pdb",
    "provenance/stages.csv",
)


def package(source, destination, dry_run):
    inputs = [(path, source / path) for path in ALLOW]
    inputs.extend([
        ("input/PROVENANCE.md", ROOT / "examples/1iep/PROVENANCE.md"),
        ("input/Apache-2.0-AutoDock-Vina.txt", ROOT / "licenses/Apache-2.0-AutoDock-Vina.txt"),
    ])
    if dry_run:
        print("\n".join(path for path, _ in inputs))
        return
    if (source / "provenance/profile.txt").read_text().strip() != "smoke":
        raise ValueError("Only an explicitly identified smoke run may be packaged.")
    sums = []
    try:
        with ZipFile(destination, "x", compression=ZIP_DEFLATED) as output:
            for name, path in inputs:
                data = path.read_bytes()
                if path.suffix in {".top", ".xvg"}:
                    data = b"".join(line for line in data.splitlines(keepends=True)
                                    if not line.lstrip().startswith((b";", b"#")))
                if re.search(rb"/(?:home|workspace|mnt|Users)/|[A-Za-z]:\\Users\\|Host(?:name)?:", data):
                    raise ValueError(f"Machine-identifying text found in {name}")
                if not data:
                    raise ValueError(f"Expected a nonempty output: {path}")
                output.writestr(name, data)
                sums.append(f"{hashlib.sha256(data).hexdigest()}  {name}")
            output.writestr("SHA256SUMS", "\n".join(sums) + "\n")
    except FileExistsError:
        raise
    except Exception:
        destination.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("zip", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    package(args.run, args.zip, args.dry_run)
