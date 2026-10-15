"""Render BGF grammars as railroad diagrams (one self-contained HTML page per grammar).

Each production's expression tree is converted directly from the typed BGF AST
(see ``bgf_parser.py``) into a diagram built with the ``railroad-diagrams``
package, then serialized to inline SVG.
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path

import railroad as rr

from bgf_parser import (
    Any,
    Choice,
    Empty,
    Epsilon,
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
    Terminal,
    Value,
    ZeroOrMore,
    parse,
)

Node = str | rr.DiagramItem


def _to_node(expression: Expression) -> Node:
    """Convert one BGF expression node into a railroad-diagrams node."""

    if isinstance(expression, Terminal):
        return rr.Terminal(expression.value)
    if isinstance(expression, Nonterminal):
        return rr.NonTerminal(expression.name)
    if isinstance(expression, Sequence):
        members = [_to_node(member) for member in expression.members]
        return rr.Sequence(*members) if members else rr.Skip()
    if isinstance(expression, Choice):
        alternatives = [_to_node(alternative) for alternative in expression.alternatives]
        return rr.Choice(0, *alternatives) if alternatives else rr.Skip()
    if isinstance(expression, Optional):
        return rr.Optional(_to_node(expression.expression))
    if isinstance(expression, ZeroOrMore):
        return rr.ZeroOrMore(_to_node(expression.expression))
    if isinstance(expression, OneOrMore):
        return rr.OneOrMore(_to_node(expression.expression))
    if isinstance(expression, SeparatedZeroOrMore):
        return rr.ZeroOrMore(
            _to_node(expression.expression), repeat=_to_node(expression.separator)
        )
    if isinstance(expression, SeparatedOneOrMore):
        return rr.OneOrMore(
            _to_node(expression.expression), repeat=_to_node(expression.separator)
        )
    if isinstance(expression, Epsilon):
        return rr.Skip()
    if isinstance(expression, Empty):
        return rr.Comment("∅")
    if isinstance(expression, Any):
        return rr.Terminal("<any>")
    if isinstance(expression, Not):
        return rr.Group(_to_node(expression.expression), label="not")
    if isinstance(expression, (Selectable, Marked)):
        return _to_node(expression.expression)
    if isinstance(expression, Value):
        return rr.NonTerminal(f"#{expression.kind}")
    raise TypeError(f"Unsupported expression node: {expression!r}")


def render_production_svg(production: Production) -> str:
    """Render a single production as a standalone SVG string."""

    diagram = rr.Diagram(_to_node(production.expression))
    parts: list[str] = []
    diagram.writeStandalone(parts.append)
    return "".join(parts)


def render_grammar_html(grammar: Grammar, title: str) -> str:
    """Return a self-contained HTML page with one diagram per production."""

    roots = set(grammar.roots)
    toc_items = []
    sections = []
    for production in grammar.productions:
        name = html.escape(production.nonterminal)
        anchor = html.escape(production.nonterminal, quote=True)
        is_root = production.nonterminal in roots
        badge = '<span class="badge">root</span>' if is_root else ""
        toc_items.append(f'<li><a href="#{anchor}">{name}</a>{badge}</li>')
        try:
            svg = render_production_svg(production)
        except TypeError as error:
            svg = f'<p class="error">{html.escape(str(error))}</p>'
        sections.append(
            f'<section id="{anchor}">'
            f'<h2>{name}{badge}</h2>'
            f'<div class="diagram">{svg}</div>'
            f"</section>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
:root {{ color-scheme: light; --ink:#17212b; --muted:#5d6874; --line:#d8dee5;
  --paper:#fff; --wash:#f4f7f9; --accent:#315e75; }}
* {{ box-sizing:border-box }}
body {{ margin:0; color:var(--ink); background:var(--wash); font:15px/1.45 system-ui,sans-serif }}
.layout {{ display:grid; grid-template-columns:280px 1fr; min-height:100vh }}
nav {{ border-right:1px solid var(--line); background:var(--paper); padding:20px; overflow-y:auto;
  max-height:100vh; position:sticky; top:0 }}
nav h1 {{ font-size:17px; margin:0 0 12px }}
nav ul {{ list-style:none; margin:0; padding:0 }}
nav li {{ margin:2px 0 }}
nav a {{ color:var(--accent); text-decoration:none; font-size:13px }}
nav a:hover {{ text-decoration:underline }}
.badge {{ margin-left:6px; font-size:10px; color:var(--accent); border:1px solid var(--accent);
  border-radius:8px; padding:0 6px; vertical-align:middle }}
main {{ padding:28px 32px }}
section {{ background:var(--paper); border:1px solid var(--line); border-radius:9px;
  margin:0 0 22px; padding:18px 20px; scroll-margin-top:16px }}
h2 {{ margin:0 0 12px; font-size:16px; font-family:ui-monospace,SFMono-Regular,Consolas,monospace }}
.diagram {{ overflow-x:auto }}
.diagram svg {{ display:block }}
.error {{ color:#a33; font-family:ui-monospace,monospace }}
</style>
</head>
<body>
<div class="layout">
<nav>
<h1>{html.escape(title)}</h1>
<ul>
{"".join(toc_items)}
</ul>
</nav>
<main>
{"".join(sections)}
</main>
</div>
</body>
</html>
"""


def render_directory(input_directory: Path, output_directory: Path) -> int:
    """Render every top-level ``.bgf`` file to an HTML railroad diagram page."""

    inputs = sorted(input_directory.glob("*.bgf"))
    output_directory.mkdir(parents=True, exist_ok=True)
    for source in inputs:
        grammar = parse(source)
        page = render_grammar_html(grammar, title=source.stem)
        target = output_directory / f"{source.stem}.html"
        target.write_text(page, encoding="utf-8")
    return len(inputs)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="directory containing .bgf files")
    parser.add_argument("output", type=Path, help="directory for rendered .html pages")
    arguments = parser.parse_args()
    count = render_directory(arguments.input, arguments.output)
    print(f"Wrote {count} railroad diagram pages to {arguments.output}")


if __name__ == "__main__":
    main()
