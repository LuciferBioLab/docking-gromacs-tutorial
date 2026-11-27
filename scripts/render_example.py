"""Render search-box, pocket and trajectory diagnostics for the public 1IEP smoke."""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
import numpy as np

LABELS = {
    "en": ("Docking box (XY projection)", "Pocket frame (XY projection)",
           "Ligand RMSD", "Time (ps)", "RMSD (nm)",
           "1IEP • public reference smoke"),
    "zh": ("对接搜索盒（XY 投影）", "口袋构象帧（XY 投影）",
           "配体 RMSD", "时间（ps）", "RMSD（nm）", "1IEP • 公开参考短测试"),
}


def coordinates(path, select):
    points = [
        [float(line[start:start + 8]) for start in (30, 38, 46)]
        for line in path.read_text().splitlines()
        if line.startswith(("ATOM  ", "HETATM")) and select(line)
    ]
    if not points:
        raise ValueError(f"Empty atom selection in {path.name}")
    return np.asarray(points)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--language", choices=LABELS, default="en")
    parser.add_argument("--font", type=Path, help="CJK font file for the Chinese panel")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.dry_run:
        print("Read the public receptor, box, complex frame and RMSD series; render three diagnostics.")
        return
    typography = {}
    if args.language == "zh":
        font = args.font or font_manager.findfont("Noto Sans CJK SC", fallback_to_default=False)
        typography["fontproperties"] = font_manager.FontProperties(fname=font)

    run = args.run
    receptor = coordinates(run / "input/1iep_receptorH.pdb", lambda atom: atom[12:16].strip() == "CA")
    box = dict(tuple(part.strip() for part in line.split("=", 1)) for line in (run / "dock/box.txt").read_text().splitlines() if "=" in line)
    center = np.array([float(box[f"center_{axis}"]) for axis in "xyz"])
    size = np.array([float(box[f"size_{axis}"]) for axis in "xyz"])
    complex_path = run / "analysis/complex.pdb"
    ligand = coordinates(complex_path, lambda atom: atom[17:20] == "UNL" and not atom[12:16].strip().startswith("H"))
    protein = coordinates(complex_path, lambda atom: atom[17:20] != "UNL" and not atom[12:16].strip().startswith("H"))
    near = protein[np.min(np.linalg.norm(protein[:, None] - ligand, axis=2), axis=1) < 4.0]
    rmsd = np.loadtxt(run / "analysis/ligand-rmsd.xvg", comments=("#", "@"))

    titles = LABELS[args.language]
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(11, 3.5), layout="constrained")
    fig.patch.set_facecolor("#f5f8ff")
    fig.suptitle(titles[5], fontweight="bold", color="#152743", **typography)
    a.scatter(receptor[:, 0], receptor[:, 1], s=8, color="#7592ba", alpha=0.65)
    a.add_patch(Rectangle((center - size / 2)[:2], *size[:2], fill=False, color="#a54b35", linewidth=1.8))
    b.scatter(near[:, 0], near[:, 1], s=17, color="#7592ba", alpha=0.65)
    b.scatter(ligand[:, 0], ligand[:, 1], s=19, color="#a54b35")
    c.plot(rmsd[:, 0] * 1000, rmsd[:, 1], marker=".", color="#284e81")
    c.set_xlabel(titles[3], **typography)
    c.set_ylabel(titles[4], **typography)
    for axis in (a, b):
        axis.set(xlabel="X (Å)", ylabel="Y (Å)", aspect="equal")
    for axis, title in zip((a, b, c), titles):
        axis.set_title(title, fontsize=12, **typography)
        axis.grid(alpha=0.18)
        axis.spines[["right", "top"]].set_visible(False)
    with args.output.open("xb") as output:
        fig.savefig(output, dpi=160, format="png")


if __name__ == "__main__":
    main()
