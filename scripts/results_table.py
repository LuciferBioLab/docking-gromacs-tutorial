"""Render a comparison CSV as a Markdown table without inventing missing values."""

import argparse
import csv
from pathlib import Path

COLUMNS = (
    "case", "method", "backend", "tool_version", "seed", "poses", "best_score_kcal_mol",
    "top1_rmsd_A", "best_rmsd_A", "wall_s", "ns_per_day", "atoms", "notes"
)


def render(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError("Use the column order in examples/results-template.csv.")
        rows = list(reader)
    escaped = lambda value: (value or "—").replace("|", "\\|").replace("\n", " ")
    print("| " + " | ".join(COLUMNS) + " |")
    print("|" + "---|" * len(COLUMNS))
    for row in rows:
        print("| " + " | ".join(escaped(row[key]) for key in COLUMNS) + " |")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="preview the same generated table on stdout")
    render(parser.parse_args().csv)
