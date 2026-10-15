"""Mine recurring BGF subtree shapes and structural evidence as JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bgf_mining import mine_corpus


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="directory containing .bgf files")
    parser.add_argument("output", type=Path, help="output JSON report")
    parser.add_argument("--minimum-frequency", type=int, default=2)
    parser.add_argument("--examples", type=int, default=5)
    arguments = parser.parse_args()
    if arguments.minimum_frequency < 1:
        parser.error("--minimum-frequency must be at least 1")
    if arguments.examples < 0:
        parser.error("--examples cannot be negative")
    report = mine_corpus(
        arguments.input.glob("*.bgf"),
        minimum_frequency=arguments.minimum_frequency,
        example_limit=arguments.examples,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"Analyzed {report['grammar_count']} grammars and "
        f"{report['production_count']} productions; wrote {arguments.output}"
    )


if __name__ == "__main__":
    main()
