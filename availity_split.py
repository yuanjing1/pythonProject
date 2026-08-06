"""Split Availity report files by 'File Name:' and combine per claim file.

Scans every report in FOLDER (skipping .txt outputs), cuts each into sections
at 'File Name:  Av_clinic_70_10276_102760801.837P' lines, and appends all
sections that belong to the same base name into one combined output in the
Combined subfolder, e.g.
    Combined\\Av_clinic_70_10276.txt
Output files are rewritten from scratch each run, so re-running is safe.

Usage:
    python availity_split.py            # uses FOLDER below
    python availity_split.py D:\\some\\other\\folder
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

FOLDER = Path(r"D:\EDI\working\Availity\ReceiveFiles")

FILE_NAME_RE = re.compile(r"^File Name:\s+(\S+)")


def base_name(reported: str) -> str:
    """Av_clinic_70_10276_102760801.837P -> Av_clinic_70_10276"""
    stem = reported.split(".")[0]           # drop .837P etc.
    return stem.rsplit("_", 1)[0]           # drop trailing control number


def split_sections(text: str):
    """Yield (base_name, section_text). Section = header + content until next File Name."""
    lines = text.splitlines(keepends=True)
    starts = [i for i, ln in enumerate(lines) if FILE_NAME_RE.match(ln)]
    for n, start in enumerate(starts):
        name = base_name(FILE_NAME_RE.match(lines[start]).group(1))
        first = 0 if n == 0 else starts[n - 1] + 1
        # section begins right after the previous File Name line; for the
        # first section include the report header at the top of the file
        end = starts[n + 1] + 1 if n + 1 < len(starts) else len(lines)
        # content runs until (and including) the next File Name's preceding lines
        section = "".join(lines[first:end - 1] if n + 1 < len(starts) else lines[first:])
        yield name, section


def main() -> None:
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else FOLDER
    combined = defaultdict(list)  # base name -> [(source file, section text)]

    for f in sorted(folder.iterdir()):
        if not f.is_file() or f.suffix.lower() == ".txt":
            continue
        text = f.read_text(encoding="latin-1")
        found = False
        for name, section in split_sections(text):
            combined[name].append((f.name, section))
            found = True
        if not found:
            print(f"skipped (no 'File Name:'): {f.name}")

    out_dir = folder / "Combined"
    out_dir.mkdir(exist_ok=True)
    for name, parts in combined.items():
        out = out_dir / f"{name}.txt"
        with open(out, "w", encoding="latin-1") as fh:
            for src, section in parts:
                fh.write(f"========== from {src} ==========\n")
                fh.write(section)
                if not section.endswith("\n"):
                    fh.write("\n")
        print(f"{out.name}: {len(parts)} section(s) <- {', '.join(src for src, _ in parts)}")


if __name__ == "__main__":
    main()
