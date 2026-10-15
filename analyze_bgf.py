"""Produce one structural production-shape report per BGF grammar."""

from __future__ import annotations

import argparse
from pathlib import Path

from bgf_analysis import analyze_production_shapes, format_analysis
from bgf_parser import parse


def analyze_directory(input_directory: Path, output_directory: Path) -> int:
    """Analyze all top-level ``.bgf`` files, returning the number written."""

    inputs = sorted(input_directory.glob("*.bgf"))
    output_directory.mkdir(parents=True, exist_ok=True)
    for source in inputs:
        report = format_analysis(analyze_production_shapes(parse(source)), source=source.name)
        target = output_directory / f"{source.stem}.shapes.txt"
        target.write_text(report, encoding="utf-8")
    return len(inputs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="directory containing .bgf files")
    parser.add_argument("output", type=Path, help="directory for shape reports")
    arguments = parser.parse_args()
    count = analyze_directory(arguments.input, arguments.output)
    print(f"Wrote {count} production-shape reports to {arguments.output}")


if __name__ == "__main__":
    main()
