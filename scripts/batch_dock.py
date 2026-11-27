"""Resume independent Vina preparations from a CSV manifest and hashed outputs."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

FIELDS = ["id", "receptor_pdbqt", "ligand_pdbqt", "box", "seed", "exhaustiveness", "num_modes"]


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def jobs(path):
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"Expected CSV columns: {', '.join(FIELDS)}")
        items = list(reader)
    ids = [item["id"] for item in items]
    if not items or len(set(ids)) != len(ids) or not all(re.fullmatch(r"[A-Za-z0-9_-]+", i) for i in ids):
        raise ValueError("Expected nonempty, unique job IDs with letters, digits, hyphens or underscores.")
    for item in items:
        for name in FIELDS[4:]:
            if not item[name].isdigit() or int(item[name]) < 1:
                raise ValueError(f"Expected a positive integer for {item['id']}:{name}")
    return items


def execute(manifest, output, threads, dry_run):
    if threads < 1:
        raise ValueError("--threads must be positive.")
    items = jobs(manifest)
    if not dry_run:
        output.mkdir(parents=True, exist_ok=True)
        version = subprocess.check_output(["vina", "--version"], text=True).strip()
    for item in items:
        base = manifest.parent
        inputs = [(base / item[field]).resolve() for field in FIELDS[1:4]]
        pose = output / f"{item['id']}.pdbqt"
        partial = pose.with_suffix(".partial.pdbqt")
        done = pose.with_suffix(".json")
        cmd = [
            "vina", "--receptor", str(inputs[0]), "--ligand", str(inputs[1]), "--config", str(inputs[2]),
            "--scoring", "vina", "--cpu", str(threads), "--seed", item["seed"],
            "--exhaustiveness", item["exhaustiveness"], "--num_modes", item["num_modes"], "--out", str(partial),
        ]
        if dry_run:
            import shlex

            print(shlex.join(cmd))
            continue
        spec = {"version": version, "arguments": cmd[9:-2], "sha256": [sha(path) for path in inputs]}
        if done.exists():
            saved = json.loads(done.read_text())
            if not pose.exists() or saved != {"spec": spec, "pose_sha256": sha(pose)}:
                raise ValueError(f"Output or inputs changed: {item['id']}. Use a new output location.")
            print(f"Already verified: {item['id']}")
            continue
        if pose.exists():
            raise ValueError(f"An output without a completion marker exists: {pose}")
        # The exclusive lock prevents two workers from writing the same job.
        lock = pose.with_suffix(".lock")
        with lock.open("x"):
            pass
        try:
            with pose.with_suffix(".log").open("a") as log:
                subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)
            result = partial.read_text()
            if "REMARK VINA RESULT:" not in result or not result.rstrip().endswith("ENDMDL"):
                raise ValueError(f"Incomplete pose output: {partial}")
            marker = done.with_suffix(".json.partial")
            marker.write_text(json.dumps({"spec": spec, "pose_sha256": sha(partial)}, indent=2) + "\n")
            partial.replace(pose)
            marker.replace(done)
        finally:
            lock.unlink()
        print(f"Verified: {item['id']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true", help="print commands before execution")
    args = parser.parse_args()
    execute(args.manifest, args.output, args.threads, args.dry_run)
