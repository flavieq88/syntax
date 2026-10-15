"""Check that every nonterminal referenced in a BGF grammar is defined.

For each grammar, a reference is well-formed only if it is either a
``Terminal`` (a literal) or a ``Nonterminal`` naming a production defined
somewhere in the same grammar. This reports any nonterminal reference that
resolves to neither: an undefined name, and any declared root that has no
matching production.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Iterator

from bgf_parser import (
    Choice,
    Expression,
    Grammar,
    Marked,
    Not,
    Nonterminal,
    OneOrMore,
    Optional,
    Production,
    SeparatedOneOrMore,
    SeparatedZeroOrMore,
    Selectable,
    Sequence,
    ZeroOrMore,
    parse,
)


def _referenced_nonterminals(expression: Expression) -> Iterator[str]:
    """Yield every nonterminal name referenced anywhere inside ``expression``.

    Terminals, epsilon, empty, any, and built-in ``Value`` categories are not
    nonterminal references and are silently skipped.
    """

    if isinstance(expression, Nonterminal):
        yield expression.name
    elif isinstance(expression, Sequence):
        for member in expression.members:
            yield from _referenced_nonterminals(member)
    elif isinstance(expression, Choice):
        for alternative in expression.alternatives:
            yield from _referenced_nonterminals(alternative)
    elif isinstance(expression, (Optional, ZeroOrMore, OneOrMore, Not)):
        yield from _referenced_nonterminals(expression.expression)
    elif isinstance(expression, (Selectable, Marked)):
        yield from _referenced_nonterminals(expression.expression)
    elif isinstance(expression, (SeparatedZeroOrMore, SeparatedOneOrMore)):
        yield from _referenced_nonterminals(expression.expression)
        yield from _referenced_nonterminals(expression.separator)


def find_undefined_references(grammar: Grammar) -> dict[str, list[str]]:
    """Return ``{undefined_name: [referencing production names]}``."""

    defined = {production.nonterminal for production in grammar.productions}
    referencers: dict[str, list[str]] = defaultdict(list)
    for production in grammar.productions:
        for name in _referenced_nonterminals(production.expression):
            if name not in defined:
                referencers[name].append(production.nonterminal)
    return dict(referencers)


def find_undefined_roots(grammar: Grammar) -> list[str]:
    """Return declared root names that have no matching production."""

    defined = {production.nonterminal for production in grammar.productions}
    return [root for root in grammar.roots if root not in defined]


def check_directory(input_directory: Path) -> int:
    """Check every top-level ``.bgf`` file, printing a report.

    Returns the number of grammars with at least one problem.
    """

    inputs = sorted(input_directory.glob("*.bgf"))
    failures = 0
    for source in inputs:
        grammar = parse(source)
        undefined_references = find_undefined_references(grammar)
        undefined_roots = find_undefined_roots(grammar)
        if not undefined_references and not undefined_roots:
            print(f"OK   {source.name} ({len(grammar.productions)} productions)")
            continue
        failures += 1
        print(f"FAIL {source.name}")
        for root in undefined_roots:
            print(f"  root {root!r} has no production")
        for name, referencers in sorted(undefined_references.items()):
            cited_by = ", ".join(sorted(set(referencers)))
            print(f"  {name!r} is undefined (referenced by: {cited_by})")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="directory containing .bgf files")
    arguments = parser.parse_args()
    failures = check_directory(arguments.input)
    total = len(sorted(arguments.input.glob("*.bgf")))
    print(f"\n{total - failures}/{total} grammars have no undefined references")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
