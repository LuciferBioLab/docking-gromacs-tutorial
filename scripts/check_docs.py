"""Verify relative Markdown destinations, explicit anchors, and code-block parity."""

import argparse
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^````*(\w*)[^\n]*\n(.*?)^````*\s*$", re.M | re.S)
LINK = re.compile(r"!?\[[^\n\[\]]+\]\(([^\s)]+)\)")
ANCHOR = re.compile(r'<a (?:name|id)="([^"]+)"></a>')
HEAD = re.compile(r"^(#+) .+?$", re.M)


def normalize_link(url):
    return url.replace(".zh-CN.md", ".md").replace(".zh-CN.webp", ".webp").replace(".zh-CN.png", ".png")


def verify():
    errors = []
    pairs = [json.loads(p.read_text())["output"] for p in sorted((ROOT / "docs/source").glob("*.json"))]
    for pair in pairs:
        bodies = {}
        for lang, name in pair.items():
            path = ROOT / name
            text = path.read_text(encoding="utf-8")
            prose = FENCE.sub("", text)
            bodies[lang] = (prose, [(k, v) for k, v in FENCE.findall(text) if k != "mermaid"])
            for raw in LINK.findall(prose):
                url = urlsplit(raw)
                if url.scheme or not raw:
                    continue
                if not url.path:
                    dest = path
                else:
                    dest = path.parent / unquote(url.path)
                if not dest.exists():
                    errors.append(f"{name}: missing {raw}")
                    continue
                if url.fragment and dest.suffix == ".md":
                    target = FENCE.sub("", dest.read_text(encoding="utf-8"))
                    if unquote(url.fragment) not in ANCHOR.findall(target):
                        errors.append(f"{name}: missing explicit anchor {raw}")
        en, zh = bodies["en"], bodies["zh"]
        if en[1] != zh[1]:
            errors.append(f"{pair['en']}: executable code or outputs differ across languages")
        if HEAD.findall(en[0]) != HEAD.findall(zh[0]):
            errors.append(f"{pair['en']}: heading levels differ across languages")
        if ANCHOR.findall(en[0]) != ANCHOR.findall(zh[0]):
            errors.append(f"{pair['en']}: anchors differ across languages")
        targets = [
            [normalize_link(url) for url in LINK.findall(x[0])]
            for x in (en, zh)
        ]
        if targets[0] != targets[1]:
            for x in targets:
                # Each language switch points at the paired file.
                if x:
                    x.pop(0)
            if targets[0] != targets[1]:
                errors.append(f"{pair['en']}: link targets or order differ across languages")
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"Verified {len(pairs)} language pairs and their local links.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="show the read-only checks")
    if parser.parse_args().dry_run:
        print("Compare language pairs, executable code, headings, and local links.")
    else:
        verify()
