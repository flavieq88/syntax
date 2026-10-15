"""Parser and typed abstract syntax tree for BGF grammar files.

The parser normalizes XML namespace prefixes and formatting, but retains every
piece of grammar-level information represented by the BGF corpus.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import TypeAlias
import xml.etree.ElementTree as ET


BGF_NAMESPACE = "http://planet-sl.org/bgf"


class BGFParseError(ValueError):
    """A BGF document is syntactically valid XML but malformed as BGF."""


class Expression:
    """Base class for all BGF expression nodes."""


@dataclass(frozen=True, slots=True)
class Terminal(Expression):
    value: str


@dataclass(frozen=True, slots=True)
class Nonterminal(Expression):
    name: str


@dataclass(frozen=True, slots=True)
class Sequence(Expression):
    members: tuple[Expression, ...]


@dataclass(frozen=True, slots=True)
class Choice(Expression):
    alternatives: tuple[Expression, ...]


@dataclass(frozen=True, slots=True)
class Optional(Expression):
    expression: Expression


@dataclass(frozen=True, slots=True)
class ZeroOrMore(Expression):
    expression: Expression


@dataclass(frozen=True, slots=True)
class OneOrMore(Expression):
    expression: Expression


@dataclass(frozen=True, slots=True)
class Epsilon(Expression):
    pass


@dataclass(frozen=True, slots=True)
class Empty(Expression):
    """The empty language (distinct from Epsilon, the empty string)."""


@dataclass(frozen=True, slots=True)
class Any(Expression):
    pass


@dataclass(frozen=True, slots=True)
class Not(Expression):
    expression: Expression


@dataclass(frozen=True, slots=True)
class Selectable(Expression):
    selector: str
    expression: Expression


@dataclass(frozen=True, slots=True)
class Marked(Expression):
    mark: str
    expression: Expression


@dataclass(frozen=True, slots=True)
class SeparatedZeroOrMore(Expression):
    expression: Expression
    separator: Expression


@dataclass(frozen=True, slots=True)
class SeparatedOneOrMore(Expression):
    expression: Expression
    separator: Expression


@dataclass(frozen=True, slots=True)
class Value(Expression):
    """A BGF built-in value category, such as ``string`` or ``integer``."""

    kind: str


BGFExpression: TypeAlias = (
    Terminal
    | Nonterminal
    | Sequence
    | Choice
    | Optional
    | ZeroOrMore
    | OneOrMore
    | Epsilon
    | Empty
    | Any
    | Not
    | Selectable
    | Marked
    | SeparatedZeroOrMore
    | SeparatedOneOrMore
    | Value
)


@dataclass(frozen=True, slots=True)
class Production:
    nonterminal: str
    expression: Expression
    label: str | None = None


@dataclass(frozen=True, slots=True)
class Grammar:
    roots: tuple[str, ...]
    productions: tuple[Production, ...]
    namespace: str | None = BGF_NAMESPACE


def parse(path: str | Path) -> Grammar:
    """Parse a BGF file into an immutable :class:`Grammar` AST.

    XML well-formedness errors are reported by ``xml.etree.ElementTree``;
    violations of the BGF structure raise :class:`BGFParseError`.
    """

    source = Path(path)
    try:
        root = ET.parse(source).getroot()
    except ET.ParseError as error:
        raise BGFParseError(f"{source}: invalid XML: {error}") from error
    return _parse_grammar(root, str(source))


def parse_string(document: str | bytes, *, source: str = "<string>") -> Grammar:
    """Parse a BGF document held in memory."""

    try:
        root = ET.fromstring(document)
    except ET.ParseError as error:
        raise BGFParseError(f"{source}: invalid XML: {error}") from error
    return _parse_grammar(root, source)


def format_expression(expression: Expression) -> str:
    """Return a canonical, information-preserving EBNF-like expression.

    Strings use JSON quoting, making terminals and arbitrary BGF names
    unambiguous.  ``sequence()`` and ``choice()`` explicitly represent their
    otherwise ambiguous zero-argument forms.
    """

    quote = lambda value: json.dumps(value, ensure_ascii=False)

    if isinstance(expression, Terminal):
        return quote(expression.value)
    if isinstance(expression, Nonterminal):
        return f"N({quote(expression.name)})"
    if isinstance(expression, Sequence):
        if not expression.members:
            return "sequence()"
        return "(" + " ".join(map(format_expression, expression.members)) + ")"
    if isinstance(expression, Choice):
        if not expression.alternatives:
            return "choice()"
        return "(" + " | ".join(map(format_expression, expression.alternatives)) + ")"
    if isinstance(expression, Optional):
        return f"[{format_expression(expression.expression)}]"
    if isinstance(expression, ZeroOrMore):
        return f"({format_expression(expression.expression)})*"
    if isinstance(expression, OneOrMore):
        return f"({format_expression(expression.expression)})+"
    if isinstance(expression, Epsilon):
        return "epsilon"
    if isinstance(expression, Empty):
        return "empty"
    if isinstance(expression, Any):
        return "any"
    if isinstance(expression, Not):
        return f"not({format_expression(expression.expression)})"
    if isinstance(expression, Selectable):
        return f"select({quote(expression.selector)}, {format_expression(expression.expression)})"
    if isinstance(expression, Marked):
        return f"marked({quote(expression.mark)}, {format_expression(expression.expression)})"
    if isinstance(expression, SeparatedZeroOrMore):
        return (
            f"sep*({format_expression(expression.expression)}, "
            f"{format_expression(expression.separator)})"
        )
    if isinstance(expression, SeparatedOneOrMore):
        return (
            f"sep+({format_expression(expression.expression)}, "
            f"{format_expression(expression.separator)})"
        )
    if isinstance(expression, Value):
        return f"value({quote(expression.kind)})"
    raise TypeError(f"unsupported expression node {type(expression).__name__}")


def format_production(production: Production) -> str:
    """Return one production in canonical EBNF-like notation."""

    lhs = f"N({json.dumps(production.nonterminal, ensure_ascii=False)})"
    label = (
        ""
        if production.label is None
        else f" @label({json.dumps(production.label, ensure_ascii=False)})"
    )
    return f"{lhs}{label} ::= {format_expression(production.expression)};"


def format_grammar(grammar: Grammar) -> str:
    """Return a complete grammar with one root or production per line."""

    lines = [
        f"@root N({json.dumps(root, ensure_ascii=False)});" for root in grammar.roots
    ]
    if lines and grammar.productions:
        lines.append("")
    lines.extend(format_production(production) for production in grammar.productions)
    return "\n".join(lines) + ("\n" if lines else "")


def _split_tag(tag: str) -> tuple[str | None, str]:
    if tag.startswith("{"):
        namespace, local = tag[1:].split("}", 1)
        return namespace, local
    return None, tag


def _local(element: ET.Element) -> str:
    return _split_tag(element.tag)[1]


def _error(source: str, context: str, message: str) -> BGFParseError:
    return BGFParseError(f"{source}: {context}: {message}")


def _require_no_attributes(element: ET.Element, source: str, context: str) -> None:
    if element.attrib:
        raise _error(source, context, f"unexpected attributes {element.attrib!r}")


def _leaf_text(element: ET.Element, source: str, context: str) -> str:
    _require_no_attributes(element, source, context)
    if len(element):
        raise _error(source, context, "expected text, found child elements")
    return element.text or ""


def _children(element: ET.Element, names: tuple[str, ...], source: str, context: str) -> list[ET.Element]:
    _require_no_attributes(element, source, context)
    result = list(element)
    actual = tuple(_local(child) for child in result)
    if actual != names:
        raise _error(source, context, f"expected children {names!r}, found {actual!r}")
    return result


def _wrapped_expression(element: ET.Element, source: str, context: str) -> Expression:
    children = _children(element, ("expression",), source, context)
    return _parse_expression(children[0], source, f"{context}/expression")


def _parse_expression(wrapper: ET.Element, source: str, context: str) -> Expression:
    children = list(wrapper)
    _require_no_attributes(wrapper, source, context)
    if _local(wrapper) != "expression" or len(children) != 1:
        raise _error(source, context, "expression must contain exactly one construct")

    node = children[0]
    tag = _local(node)
    node_context = f"{context}/{tag}"

    if tag == "terminal":
        return Terminal(_leaf_text(node, source, node_context))
    if tag == "nonterminal":
        return Nonterminal(_leaf_text(node, source, node_context))
    if tag == "value":
        return Value(_leaf_text(node, source, node_context))
    if tag in {"epsilon", "empty", "any"}:
        _children(node, (), source, node_context)
        return {"epsilon": Epsilon, "empty": Empty, "any": Any}[tag]()
    if tag in {"optional", "star", "plus", "not"}:
        expression = _wrapped_expression(node, source, node_context)
        constructor = {
            "optional": Optional,
            "star": ZeroOrMore,
            "plus": OneOrMore,
            "not": Not,
        }[tag]
        return constructor(expression)
    if tag in {"sequence", "choice"}:
        _require_no_attributes(node, source, node_context)
        if any(_local(child) != "expression" for child in node):
            raise _error(source, node_context, "expected only expression children")
        expressions = tuple(
            _parse_expression(child, source, f"{node_context}/expression[{index}]")
            for index, child in enumerate(node)
        )
        return Sequence(expressions) if tag == "sequence" else Choice(expressions)
    if tag in {"sepliststar", "seplistplus"}:
        item, separator = _children(
            node, ("expression", "expression"), source, node_context
        )
        arguments = (
            _parse_expression(item, source, f"{node_context}/expression[0]"),
            _parse_expression(separator, source, f"{node_context}/expression[1]"),
        )
        constructor = SeparatedZeroOrMore if tag == "sepliststar" else SeparatedOneOrMore
        return constructor(*arguments)
    if tag == "selectable":
        selector, expression = _children(
            node, ("selector", "expression"), source, node_context
        )
        return Selectable(
            _leaf_text(selector, source, f"{node_context}/selector"),
            _parse_expression(expression, source, f"{node_context}/expression"),
        )
    if tag == "marked":
        mark, expression = _children(node, ("mark", "expression"), source, node_context)
        return Marked(
            _leaf_text(mark, source, f"{node_context}/mark"),
            _parse_expression(expression, source, f"{node_context}/expression"),
        )
    raise _error(source, node_context, f"unknown BGF expression construct {tag!r}")


def _parse_production(element: ET.Element, source: str, index: int) -> Production:
    context = f"grammar/production[{index}]"
    _require_no_attributes(element, source, context)
    children = list(element)
    names = tuple(_local(child) for child in children)
    if names == ("nonterminal", "expression"):
        label = None
        nonterminal, expression = children
    elif names == ("label", "nonterminal", "expression"):
        label_element, nonterminal, expression = children
        label = _leaf_text(label_element, source, f"{context}/label")
    else:
        raise _error(
            source,
            context,
            "expected [label,] nonterminal, expression; " f"found {names!r}",
        )
    return Production(
        nonterminal=_leaf_text(nonterminal, source, f"{context}/nonterminal"),
        expression=_parse_expression(expression, source, f"{context}/expression"),
        label=label,
    )


def _parse_grammar(root: ET.Element, source: str) -> Grammar:
    namespace, local = _split_tag(root.tag)
    if local != "grammar":
        raise _error(source, "document", f"expected grammar root, found {local!r}")
    if namespace not in {None, BGF_NAMESPACE}:
        raise _error(source, "grammar", f"unexpected namespace {namespace!r}")
    _require_no_attributes(root, source, "grammar")

    roots: list[str] = []
    productions: list[Production] = []
    seen_production = False
    for child in root:
        tag = _local(child)
        if tag == "root" and not seen_production:
            roots.append(_leaf_text(child, source, f"grammar/root[{len(roots)}]"))
        elif tag == "production":
            seen_production = True
            productions.append(_parse_production(child, source, len(productions)))
        else:
            detail = "root after production" if tag == "root" else f"unexpected child {tag!r}"
            raise _error(source, "grammar", detail)

    return Grammar(tuple(roots), tuple(productions), namespace)


__all__ = [
    "Any", "BGFExpression", "BGFParseError", "BGF_NAMESPACE", "Choice",
    "Empty", "Epsilon", "Expression", "Grammar", "Marked", "Nonterminal",
    "Not", "OneOrMore", "Optional", "Production", "Selectable",
    "SeparatedOneOrMore", "SeparatedZeroOrMore", "Sequence", "Terminal",
    "Value", "ZeroOrMore", "format_expression", "format_grammar",
    "format_production", "parse", "parse_string",
]
