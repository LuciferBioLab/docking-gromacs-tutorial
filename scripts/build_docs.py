"""Render paired English and Simplified Chinese GFM from the canonical source."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "docs" / "source"


def build(check=False, dry_run=False):
    stale = []
    for source in sorted(SOURCES.glob("*.json")):
        spec = json.loads(source.read_text(encoding="utf-8"))
        paths = spec["output"]
        for language in ("en", "zh"):
            expected = "\n\n".join(
                block["shared"] if "shared" in block else block[language]
                for block in spec["blocks"]
            ).rstrip() + "\n"
            dest = ROOT / paths[language]
            if dry_run:
                print(dest.relative_to(ROOT))
                continue
            if check:
                if not dest.is_file() or dest.read_text(encoding="utf-8") != expected:
                    stale.append(str(dest.relative_to(ROOT)))
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(expected, encoding="utf-8")
    if stale:
        raise SystemExit("Regenerate with make docs: " + ", ".join(stale))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    build(args.check, args.dry_run)
