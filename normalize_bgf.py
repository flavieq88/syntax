"""Convert a directory of BGF files to canonical EBNF-like text."""

from __future__ import annotations

import argparse
from pathlib import Path

from bgf_parser import format_grammar, parse


def normalize_directory(input_directory: Path, output_directory: Path) -> int:
    """Normalize all top-level ``.bgf`` files, returning the number written."""

    inputs = sorted(input_directory.glob("*.bgf"))
    output_directory.mkdir(parents=True, exist_ok=True)
    for source in inputs:
        target = output_directory / f"{source.stem}.ebnf"
        target.write_text(format_grammar(parse(source)), encoding="utf-8")
    return len(inputs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="directory containing .bgf files")
    parser.add_argument("output", type=Path, help="directory for normalized .ebnf files")
    arguments = parser.parse_args()
    count = normalize_directory(arguments.input, arguments.output)
    print(f"Wrote {count} normalized grammars to {arguments.output}")


if __name__ == "__main__":
    main()
