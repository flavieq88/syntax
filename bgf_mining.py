"""Mine recurring subtree shapes and structural evidence from BGF grammars."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import re
from pathlib import Path
from typing import Iterable

from bgf_analysis import production_shape
from bgf_parser import (
    Choice,
    Expression,
    Grammar,
    Marked,
    Nonterminal,
    Not,
    OneOrMore,
    Optional,
    Production,
    Selectable,
    SeparatedOneOrMore,
    SeparatedZeroOrMore,
    Sequence,
    Terminal,
    ZeroOrMore,
    format_production,
    parse,
)


_KEYWORD = re.compile(r"^[^\W\d]\w*$", re.UNICODE)


def terminal_class(value: str) -> str:
    """Classify an exact terminal as ``keyword`` or ``punctuation``.

    Identifier-shaped Unicode strings are keywords. Everything else—including
    whitespace, operators, delimiters, and mixed lexical fragments—is placed in
    the punctuation class. The original value is always retained separately.
    """

    return "keyword" if _KEYWORD.fullmatch(value) else "punctuation"


def _unwrap(expression: Expression) -> Expression:
    while isinstance(expression, Selectable):
        expression = expression.expression
    return expression


def iter_subtrees(expression: Expression) -> Iterable[Expression]:
    """Yield all subtrees, treating selectable annotations as transparent."""

    expression = _unwrap(expression)
    yield expression
    if isinstance(expression, Sequence):
        children = expression.members
    elif isinstance(expression, Choice):
        children = expression.alternatives
    elif isinstance(expression, (Optional, ZeroOrMore, OneOrMore, Not, Marked)):
        children = (expression.expression,)
    elif isinstance(expression, (SeparatedZeroOrMore, SeparatedOneOrMore)):
        children = (expression.expression, expression.separator)
    else:
        children = ()
    for child in children:
        yield from iter_subtrees(child)


def _children(expression: Expression) -> tuple[Expression, ...]:
    expression = _unwrap(expression)
    if isinstance(expression, Sequence):
        return tuple(_unwrap(child) for child in expression.members)
    if isinstance(expression, Choice):
        return tuple(_unwrap(child) for child in expression.alternatives)
    if isinstance(expression, (Optional, ZeroOrMore, OneOrMore, Not, Marked)):
        return (_unwrap(expression.expression),)
    if isinstance(expression, (SeparatedZeroOrMore, SeparatedOneOrMore)):
        return (_unwrap(expression.expression), _unwrap(expression.separator))
    return ()


def _terminals(expression: Expression) -> tuple[str, ...]:
    return tuple(
        subtree.value for subtree in iter_subtrees(expression)
        if isinstance(subtree, Terminal)
    )


@dataclass(slots=True)
class _Evidence:
    frequency: int = 0
    languages: set[str] = field(default_factory=set)
    productions: set[str] = field(default_factory=set)
    examples: list[dict[str, str]] = field(default_factory=list)

    def add(self, language: str, production_id: str, example: str, limit: int) -> None:
        self.frequency += 1
        self.languages.add(language)
        self.productions.add(production_id)
        if len(self.examples) < limit and not any(e["production"] == production_id for e in self.examples):
            self.examples.append({
                "language": language,
                "production": production_id,
                "text": example,
            })


def _terminal_records(values: Iterable[str]) -> list[dict[str, str]]:
    return [{"value": value, "class": terminal_class(value)} for value in values]


def _motifs(expression: Expression) -> Iterable[tuple[str, str, tuple[str, ...]]]:
    """Yield structural relation, exact template, and involved terminals."""

    expression = _unwrap(expression)
    if isinstance(expression, Sequence):
        members = tuple(_unwrap(member) for member in expression.members)

        if len(members) >= 3 and isinstance(members[0], Terminal) and isinstance(members[-1], Terminal):
            middle = members[1:-1]
            middle_shape = (
                production_shape(middle[0]) if len(middle) == 1
                else "sequence(" + ", ".join(production_shape(item) for item in middle) + ")"
            )
            yield (
                "sequence(T1, subtree, T2)",
                f"sequence({production_shape(members[0])}, {middle_shape}, {production_shape(members[-1])})",
                (members[0].value, members[-1].value),
            )

        for left, right in zip(members, members[1:]):
            if isinstance(left, Terminal) and isinstance(right, Nonterminal):
                yield ("sequence(T, N)", f"sequence({production_shape(left)}, N)", (left.value,))
            if isinstance(left, Nonterminal) and isinstance(right, Terminal):
                yield ("sequence(N, T)", f"sequence(N, {production_shape(right)})", (right.value,))
            if isinstance(left, (ZeroOrMore, OneOrMore)) and isinstance(right, Terminal):
                yield (
                    "sequence(repetition(subtree), T)",
                    f"sequence({production_shape(left)}, {production_shape(right)})",
                    (right.value,),
                )

        for left, middle, right in zip(members, members[1:], members[2:]):
            if isinstance(left, Nonterminal) and isinstance(middle, Terminal) and isinstance(right, Nonterminal):
                yield (
                    "sequence(N, T, N)",
                    f"sequence(N, {production_shape(middle)}, N)",
                    (middle.value,),
                )

    if isinstance(expression, (SeparatedZeroOrMore, SeparatedOneOrMore)):
        separator = _unwrap(expression.separator)
        if isinstance(separator, Terminal):
            yield (
                "separated-repetition(subtree, T)",
                production_shape(expression),
                (separator.value,),
            )


def _production_id(language: str, index: int, production: Production) -> str:
    label = "" if production.label is None else f"#{production.label}"
    return f"{language}:{index}:{production.nonterminal}{label}"


def mine_corpus(
    sources: Iterable[Path], *, minimum_frequency: int = 2, example_limit: int = 5
) -> dict[str, object]:
    """Mine recurring subtree shapes and requested structural relationships."""

    subtree_evidence: dict[str, _Evidence] = defaultdict(_Evidence)
    subtree_terminals: dict[str, tuple[str, ...]] = {}
    motif_evidence: dict[tuple[str, str], _Evidence] = defaultdict(_Evidence)
    motif_terminals: dict[tuple[str, str], tuple[str, ...]] = {}
    motif_container_evidence: dict[tuple[str, str, str], _Evidence] = defaultdict(_Evidence)
    containment_evidence: dict[tuple[str, str], _Evidence] = defaultdict(_Evidence)
    grammar_count = 0
    production_count = 0

    for source in sorted(sources):
        grammar_count += 1
        language = source.stem
        grammar: Grammar = parse(source)
        production_count += len(grammar.productions)
        for index, production in enumerate(grammar.productions):
            production_id = _production_id(language, index, production)
            example = format_production(production)
            for subtree in iter_subtrees(production.expression):
                shape = production_shape(subtree)
                subtree_terminals.setdefault(shape, _terminals(subtree))
                subtree_evidence[shape].add(language, production_id, example, example_limit)
                for child in _children(subtree):
                    child_shape = production_shape(child)
                    containment_evidence[(child_shape, shape)].add(
                        language, production_id, example, example_limit
                    )
                for relation, template, terminals in _motifs(subtree):
                    key = (relation, template)
                    motif_terminals.setdefault(key, terminals)
                    motif_evidence[key].add(language, production_id, example, example_limit)
                    if template != shape:
                        motif_container_evidence[(relation, template, shape)].add(
                            language, production_id, example, example_limit
                        )

    def record(shape: str, evidence: _Evidence, terminals: tuple[str, ...]) -> dict[str, object]:
        return {
            "frequency": evidence.frequency,
            "language_count": len(evidence.languages),
            "languages": sorted(evidence.languages),
            "production_count": len(evidence.productions),
            "productions": sorted(evidence.productions),
            "shape": shape,
            "terminals": _terminal_records(terminals),
            "examples": evidence.examples,
        }

    subtrees = []
    for shape, evidence in subtree_evidence.items():
        if evidence.frequency < minimum_frequency:
            continue
        item = record(shape, evidence, subtree_terminals[shape])
        containing = []
        for (child_shape, parent_shape), parent_evidence in containment_evidence.items():
            if child_shape != shape or parent_evidence.frequency < minimum_frequency:
                continue
            containing.append({
                "frequency": parent_evidence.frequency,
                "language_count": len(parent_evidence.languages),
                "production_count": len(parent_evidence.productions),
                "shape": parent_shape,
            })
        containing.sort(key=lambda parent: (-int(parent["frequency"]), str(parent["shape"])))
        item["containing_structures"] = containing
        subtrees.append(item)
    subtrees.sort(key=lambda item: (-int(item["frequency"]), str(item["shape"])))

    motifs = []
    for key, evidence in motif_evidence.items():
        if evidence.frequency < minimum_frequency:
            continue
        relation, template = key
        item = record(template, evidence, motif_terminals[key])
        item["relation"] = relation
        containing_by_shape: dict[str, _Evidence] = {}
        # Exact motif shapes, such as sepliststar(...), use their immediate
        # AST parents. Synthetic shapes, such as sequence(N, T), use the
        # concrete sequence subtree from which the observation was extracted.
        for (child_shape, parent_shape), parent_evidence in containment_evidence.items():
            if child_shape == template and parent_shape != template:
                containing_by_shape[parent_shape] = parent_evidence
        for (container_relation, container_template, container_shape), container_evidence in motif_container_evidence.items():
            if container_relation == relation and container_template == template and container_shape != template:
                containing_by_shape[container_shape] = container_evidence
        containing = [
            {
                "frequency": parent_evidence.frequency,
                "language_count": len(parent_evidence.languages),
                "production_count": len(parent_evidence.productions),
                "shape": parent_shape,
            }
            for parent_shape, parent_evidence in containing_by_shape.items()
            if parent_evidence.frequency >= minimum_frequency
        ]
        containing.sort(key=lambda parent: (-int(parent["frequency"]), str(parent["shape"])))
        item["containing_structures"] = containing
        motifs.append(item)
    motifs.sort(key=lambda item: (-int(item["frequency"]), str(item["relation"]), str(item["shape"])))

    return {
        "grammar_count": grammar_count,
        "production_count": production_count,
        "minimum_frequency": minimum_frequency,
        "terminal_classification": {
            "keyword": "Unicode identifier-shaped terminal",
            "punctuation": "all other terminals, including whitespace and operators",
        },
        "normalization": {
            "nonterminal_names": "ignored",
            "selectors": "ignored",
            "terminals": "preserved exactly",
        },
        "subtrees": subtrees,
        "motifs": motifs,
    }


__all__ = ["iter_subtrees", "mine_corpus", "terminal_class"]
