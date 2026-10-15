"""Structural production-shape analysis for parsed BGF grammars."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json

from bgf_parser import (
    Any,
    Choice,
    Empty,
    Epsilon,
    Expression,
    Grammar,
    Marked,
    Nonterminal,
    Not,
    OneOrMore,
    Optional,
    Selectable,
    SeparatedOneOrMore,
    SeparatedZeroOrMore,
    Sequence,
    Terminal,
    Value,
    ZeroOrMore,
)


@dataclass(frozen=True, slots=True)
class ShapeFrequency:
    count: int
    shape: str


@dataclass(frozen=True, slots=True)
class ProductionShapeAnalysis:
    production_count: int
    frequencies: tuple[ShapeFrequency, ...]

    @property
    def distinct_shape_count(self) -> int:
        return len(self.frequencies)


def _quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def production_shape(expression: Expression) -> str:
    """Normalize a production RHS to its structural shape.

    Nonterminal names are replaced by ``N`` and ``selectable`` wrappers are
    transparent. Terminals and all other BGF constructs are preserved.
    """

    if isinstance(expression, Selectable):
        return production_shape(expression.expression)
    if isinstance(expression, Terminal):
        return _quote(expression.value)
    if isinstance(expression, Nonterminal):
        return "N"
    if isinstance(expression, Sequence):
        return _call("sequence", expression.members)
    if isinstance(expression, Choice):
        return _call("choice", expression.alternatives)
    if isinstance(expression, Optional):
        return _call("optional", (expression.expression,))
    if isinstance(expression, ZeroOrMore):
        return _call("star", (expression.expression,))
    if isinstance(expression, OneOrMore):
        return _call("plus", (expression.expression,))
    if isinstance(expression, Epsilon):
        return "epsilon"
    if isinstance(expression, Empty):
        return "empty"
    if isinstance(expression, Any):
        return "any"
    if isinstance(expression, Not):
        return _call("not", (expression.expression,))
    if isinstance(expression, Marked):
        return f"marked({_quote(expression.mark)}, {production_shape(expression.expression)})"
    if isinstance(expression, SeparatedZeroOrMore):
        return _call("sepliststar", (expression.expression, expression.separator))
    if isinstance(expression, SeparatedOneOrMore):
        return _call("seplistplus", (expression.expression, expression.separator))
    if isinstance(expression, Value):
        return f"value({_quote(expression.kind)})"
    raise TypeError(f"unsupported expression node {type(expression).__name__}")


def _call(name: str, expressions: tuple[Expression, ...]) -> str:
    arguments = ", ".join(production_shape(expression) for expression in expressions)
    return f"{name}({arguments})"


def analyze_production_shapes(grammar: Grammar) -> ProductionShapeAnalysis:
    """Count normalized, complete RHS shapes in a grammar."""

    counts = Counter(production_shape(p.expression) for p in grammar.productions)
    frequencies = tuple(
        ShapeFrequency(count, shape)
        for shape, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )
    return ProductionShapeAnalysis(len(grammar.productions), frequencies)


def format_analysis(analysis: ProductionShapeAnalysis, *, source: str | None = None) -> str:
    """Format a complete shape analysis as deterministic UTF-8 text."""

    lines = ["# BGF production shape analysis"]
    if source is not None:
        lines.append(f"source: {source}")
    lines.extend((
        f"productions: {analysis.production_count}",
        f"distinct_shapes: {analysis.distinct_shape_count}",
        "nonterminal_names: ignored",
        "selectors: ignored",
        "terminals: preserved",
        "",
        "count\tshape",
    ))
    lines.extend(f"{entry.count}\t{entry.shape}" for entry in analysis.frequencies)
    return "\n".join(lines) + "\n"


__all__ = [
    "ProductionShapeAnalysis",
    "ShapeFrequency",
    "analyze_production_shapes",
    "format_analysis",
    "production_shape",
]
