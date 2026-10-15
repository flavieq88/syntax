# BGF grammar parsing and structural analysis

This repository contains Python tools for parsing the BGF grammars in
`grammar-zoo`, converting them to a readable canonical notation, and mining
recurring structural shapes across a corpus.

Most tools use only the Python standard library. Python 3.10 or later is
required. `railroad_bgf.py` additionally needs the `railroad-diagrams`
package (see `requirements.txt`):

```bash
pip install -r requirements.txt
```

## Repository layout

| Path | Purpose |
|---|---|
| `grammar-zoo/` | Complete input corpus of BGF XML grammars |
| `grammar-zoo-curated/` | Smaller curated input corpus |
| `grammar-zoo-flavie/` | Curated input corpus (one grammar per language, incl. JavaScript), extracted tier, unmodified |
| `grammar-zoo-flavie-adapted/` | Same corpus, adapted: lexical-grammar gaps filled in (see below) |
| `upstream-fixes/` | Three grammars substituted from Grammar Zoo's own more-mature tier before adaptation |
| `bgf_parser.py` | Typed BGF AST, XML parser, and canonical pretty-printer |
| `normalize_bgf.py` | Convert every BGF file in a directory to `.ebnf` text |
| `bgf_analysis.py` | Normalize and count complete production shapes |
| `analyze_bgf.py` | Produce one production-shape report per grammar |
| `bgf_mining.py` | Mine recurring subtrees, structural patterns, and containment evidence |
| `mine_bgf.py` | Produce a corpus-wide mining report in JSON |
| `render_analysis_html.py` | Convert the mining JSON into an interactive HTML report |
| `railroad_bgf.py` | Render every production as a railroad diagram, one HTML page per grammar |
| `check_bgf_references.py` | Report nonterminal references with no matching production in the same grammar |
| `adapt_lexical_grammar.py` | Fill in `grammar-zoo-flavie`'s lexical-grammar gaps, sourced not invented |
| `tests/` | Unit and corpus-wide tests |
| `dangling-else-analysis.md` | How each `grammar-zoo-flavie` language resolves the dangling-else ambiguity |

Generated results currently live in:

| Path | Contents |
|---|---|
| `normalized-ebnf/` | One canonical `.ebnf` file per full-corpus grammar |
| `normalized-ebnf-flavie/` | One canonical `.ebnf` file per `grammar-zoo-flavie` grammar |
| `normalized-ebnf-flavie-adapted/` | One canonical `.ebnf` file per `grammar-zoo-flavie-adapted` grammar |
| `production-shape-analysis/` | One `.shapes.txt` report per full-corpus grammar |
| `railroad-diagrams-flavie/` | One railroad-diagram `.html` page per `grammar-zoo-flavie` grammar |
| `railroad-diagrams-flavie-adapted/` | One railroad-diagram `.html` page per `grammar-zoo-flavie-adapted` grammar |
| `corpus-analysis/recurring-structures.json` | Full-corpus subtree and pattern data |
| `corpus-analysis/recurring-structures.html` | Interactive full-corpus report |
| `corpus-analysis/curated-recurring-structures.json` | Curated-corpus data |
| `corpus-analysis/curated-recurring-structures.html` | Interactive curated report |

## Quick start

Run the tests:

```bash
python3 -m unittest discover -v
```

Regenerate the main artifacts:

```bash
python3 normalize_bgf.py grammar-zoo normalized-ebnf
python3 analyze_bgf.py grammar-zoo production-shape-analysis

python3 mine_bgf.py \
  grammar-zoo \
  corpus-analysis/recurring-structures.json \
  --minimum-frequency 2 \
  --examples 5

python3 render_analysis_html.py \
  corpus-analysis/recurring-structures.json \
  corpus-analysis/recurring-structures.html
```

Analyze the curated corpus:

```bash
python3 mine_bgf.py \
  grammar-zoo-curated \
  corpus-analysis/curated-recurring-structures.json \
  --minimum-frequency 2 \
  --examples 5

python3 render_analysis_html.py \
  corpus-analysis/curated-recurring-structures.json \
  corpus-analysis/curated-recurring-structures.html
```

Regenerate the `grammar-zoo-flavie` artifacts:

```bash
python3 normalize_bgf.py grammar-zoo-flavie normalized-ebnf-flavie
python3 railroad_bgf.py grammar-zoo-flavie railroad-diagrams-flavie
```

The HTML files are self-contained and can be opened directly in a browser; no
web server is needed.

## `bgf_parser.py`: parser, AST, and pretty-printer

The parser reads BGF XML into an immutable typed AST. XML namespace prefixes
and formatting are normalized, while grammar-level information is retained.
Unknown constructs or malformed BGF structures raise `BGFParseError` rather
than being silently discarded.

Basic use:

```python
from bgf_parser import parse, format_grammar

grammar = parse("grammar-zoo/c-c90-rascal.bgf")
print(grammar.roots)
print(grammar.productions[0])
print(format_grammar(grammar))
```

Documents already held in memory can be parsed with `parse_string()`.

### AST nodes

The top-level nodes are:

- `Grammar(roots, productions, namespace)`
- `Production(nonterminal, expression, label)`

Expression nodes are:

| AST node | BGF XML abstraction | Meaning |
|---|---|---|
| `Terminal` | `terminal` | Exact terminal text |
| `Nonterminal` | `nonterminal` | Nonterminal reference |
| `Sequence` | `sequence` | Ordered concatenation |
| `Choice` | `choice` | Alternatives within an expression |
| `Optional` | `optional` | Zero or one occurrence |
| `ZeroOrMore` | `star` | Zero or more occurrences |
| `OneOrMore` | `plus` | One or more occurrences |
| `Epsilon` | `epsilon` | Empty string |
| `Empty` | `empty` | Empty language |
| `Any` | `any` | Arbitrary symbol |
| `Not` | `not` | Negated expression |
| `Selectable` | `selectable` / `selector` | Named structural annotation |
| `Marked` | `marked` / `mark` | Marked expression |
| `SeparatedZeroOrMore` | `sepliststar` | Possibly empty list with an explicit separator |
| `SeparatedOneOrMore` | `seplistplus` | Nonempty list with an explicit separator |
| `Value` | `value` | Built-in value category |

For a separated list, both the element expression and separator expression are
explicit in the XML and in the AST. For example, `seplistplus(N, ",")` means a
nonempty comma-separated list; the comma is not implicit.

### Canonical EBNF-like formatting

The public formatting functions are:

- `format_expression(expression)`
- `format_production(production)`
- `format_grammar(grammar)`

The notation preserves all AST distinctions. Examples include:

```text
N("Expr")
"if"
(N("Expr") "+" N("Expr"))
[N("Expr")]
(N("Expr"))*
sep*(N("Item"), ",")
select("condition", N("Expr"))
epsilon
empty
```

`select(...)` preserves BGF selector metadata. It does not change the language
recognized by the enclosed expression.

## `normalize_bgf.py`: normalize a directory

Usage:

```text
python3 normalize_bgf.py INPUT_DIRECTORY OUTPUT_DIRECTORY
```

Only top-level `*.bgf` files are processed. Each input file produces a file
with the same stem and an `.ebnf` extension.

Example:

```bash
python3 normalize_bgf.py grammar-zoo normalized-ebnf
```

## `bgf_analysis.py`: complete production shapes

This module analyzes only complete production right-hand sides. Its central
function is:

```python
analysis = analyze_production_shapes(grammar)
```

`production_shape(expression)` applies the following normalization:

- Every nonterminal reference becomes `N`; its name is ignored.
- `Selectable` wrappers and selector names are ignored.
- Production LHS names and labels do not participate in the shape.
- Exact terminals are preserved.
- All other BGF constructs and their ordering are preserved.

For example, these expressions have the same normalized shape:

```text
sequence(N("Target"), "=", N("Source"))
sequence(N("Name"), "=", N("Value"))
```

Their common shape is:

```text
sequence(N, "=", N)
```

Separated-list abstractions remain explicit:

```text
sepliststar(N, ",")
seplistplus(N, ",")
```

`format_analysis()` renders the result deterministically, sorting shapes by
decreasing frequency and then lexically.

## `analyze_bgf.py`: one shape report per grammar

Usage:

```text
python3 analyze_bgf.py INPUT_DIRECTORY OUTPUT_DIRECTORY
```

Each input `name.bgf` produces `name.shapes.txt`. A report contains the number
of productions, the number of distinct complete-production shapes, and every
shape with its frequency.

Example:

```bash
python3 analyze_bgf.py grammar-zoo production-shape-analysis
```

## `bgf_mining.py`: recurring subtrees and structural evidence

This analysis considers every AST subtree, not only complete production RHSs.
Selectors remain transparent, nonterminal names become `N`, and exact terminals
are retained.

It produces two related collections.

### Recurring subtrees

These are exact normalized AST fragments, such as:

```text
sequence("(", N, ")")
sepliststar(N, ",")
sequence(N, "=", N)
```

### Structural patterns

These record selected positional relationships without assigning semantic
names to them:

| Relation | Evidence recorded |
|---|---|
| `sequence(T1, subtree, T2)` | Exact terminals surrounding a subtree |
| `separated-repetition(subtree, T)` | Repeated elements with an exact terminal separator |
| `sequence(repetition(subtree), T)` | Repetition followed by an exact terminal |
| `sequence(T, N)` | Exact terminal immediately before a nonterminal |
| `sequence(N, T)` | Exact terminal immediately after a nonterminal |
| `sequence(N, T, N)` | Exact terminal between two nonterminals |

Here `T`, `T1`, and `T2` describe terminal positions in the relation category.
The actual terminal identity appears in the associated exact shape. For
example:

```text
relation: sequence(N, T)
shape:    sequence(N, ")")
```

### Counts and provenance

Every recurring subtree and structural pattern records:

- `frequency`: total number of occurrences; one production may contribute
  multiple occurrences.
- `language_count` and `languages`: number and names of distinct grammar files.
- `production_count` and `productions`: number and identifiers of distinct
  source productions.
- `terminals`: exact terminal values and their derived classifications.
- `examples`: a bounded list of representative original productions.
- `containing_structures`: recurring larger structures that contain the item.

Production identifiers have this form:

```text
grammar-stem:zero-based-production-index:LHS#optional-label
```

### Terminal classification

Terminal identity is never discarded. Each terminal is additionally classified
as:

- `keyword`: Unicode identifier-shaped text, such as `while` or `struct`.
- `punctuation`: everything else, including delimiters, operators, whitespace,
  and mixed lexical fragments.

This is a mechanical classification, not a claim about a language's lexer.

### Containing structures

For exact AST subtrees, containing structures are recurring immediate parents
after selector wrappers have been removed. For synthetic positional patterns,
such as an adjacent `sequence(N, T)` observation, they are the concrete sequence
subtrees from which the pattern was extracted.

For example, expanding:

```text
sepliststar(N, ",")
```

may show:

```text
sequence("(", sepliststar(N, ","), ")")
```

with separate occurrence, language, and production counts for that containment
relationship.

## `mine_bgf.py`: produce the JSON report

Usage:

```text
python3 mine_bgf.py INPUT_DIRECTORY OUTPUT_JSON \
  [--minimum-frequency N] [--examples N]
```

Options:

- `--minimum-frequency`: include records occurring at least this many times;
  default `2`.
- `--examples`: retain at most this many representative productions per
  record; default `5`. Use `0` to omit examples.

Only top-level `*.bgf` files in the input directory are analyzed.

## `render_analysis_html.py`: interactive report

Usage:

```text
python3 render_analysis_html.py INPUT_JSON OUTPUT_HTML
```

The generated page embeds the complete JSON report and requires no external
assets. It provides:

- Separate recurring-subtree and structural-pattern views.
- Search over shapes, terminals, grammars, and production identifiers.
- Minimum frequency and minimum language-count filters.
- Structural-relation filtering.
- Terminal-presence and terminal-class filters.
- Sorting and pagination.
- Expandable provenance and representative examples.
- Clickable containing shapes that navigate to the exact recurring-subtree
  record.

The default terminal filter is **Has at least one terminal**, which hides purely
structural records such as `N`, `sequence(N, N)`, `epsilon`, and `plus(N)`.
Choose **Any terminal content** to include them.

## `railroad_bgf.py`: railroad diagrams

Converts each production's expression tree directly from the typed BGF AST
into a diagram built with the `railroad-diagrams` package, then renders one
self-contained HTML page per grammar with an inline SVG diagram per
production (with a jump-link table of contents and root productions marked).

Usage:

```text
python3 railroad_bgf.py INPUT_DIRECTORY OUTPUT_DIRECTORY
```

Only top-level `*.bgf` files are processed. Each input file produces a file
with the same stem and an `.html` extension.

Example:

```bash
pip install -r requirements.txt
python3 railroad_bgf.py grammar-zoo-flavie railroad-diagrams-flavie
```

## `check_bgf_references.py`: reference-integrity audit

For each grammar, checks that every nonterminal referenced by a production is
either a `Terminal` or names a production defined somewhere in that same
grammar. Also flags any declared root with no matching production. Prints an
`OK`/`FAIL` line per grammar plus one line per undefined name (with the
productions that cite it), and exits non-zero if any grammar has a problem.

Usage:

```text
python3 check_bgf_references.py INPUT_DIRECTORY
```

Example:

```bash
python3 check_bgf_references.py grammar-zoo-flavie
```

Many BGF extractions intentionally omit the lexical grammar (e.g. ISO
standards separate lexical elements like `identifier` and `string-literal`
from the phrase-structure grammar) or reference a TXL scanner's built-in
token classes (`SPOFF`/`SPON`, `IN`/`EX`, `id`, `number`, `stringlit`, ...).
These names are undefined by design in the source corpus — this tool reports
them rather than inventing definitions for them. `grammar-zoo-flavie-adapted/`
(see next section) is the corpus with those gaps actually filled in; running
this checker against it reports 17/17 grammars clean.

## `adapt_lexical_grammar.py`: filling in the lexical grammar

`check_bgf_references.py` shows that 13 of the 17 `grammar-zoo-flavie`
grammars reference nonterminals with no production in the same file — either
because the original fetched source only covers phrase-structure syntax (the
ISO C99/C++98/C# standards keep their lexical grammar in a separate clause),
or because the grammar was extracted from TXL, whose scanner primitives
(`id`, `number`, `stringlit`, ...) are never spelled out in any per-language
TXL file. Per the Grammar Zoo's own maturity model, adding a missing lexical
part to an extracted grammar is literally the definition of *adapting* it —
see the module docstring in `adapt_lexical_grammar.py` for the full,
per-language account of exactly where every addition was sourced from (the
real fetched TXL grammars in the upstream repo, the TXL reference manual,
ECMA-367, the ISO C/C++ standards, ECMA-334, and Ada 2005 RM 2.1) — nothing
is invented from scratch. `grammar-zoo-flavie/` itself is never modified;
this script only reads it and writes the adapted result to
`grammar-zoo-flavie-adapted/`.

Usage:

```text
python3 adapt_lexical_grammar.py INPUT_DIRECTORY OUTPUT_DIRECTORY
```

Example:

```bash
python3 adapt_lexical_grammar.py grammar-zoo-flavie grammar-zoo-flavie-adapted
python3 normalize_bgf.py grammar-zoo-flavie-adapted normalized-ebnf-flavie-adapted
python3 railroad_bgf.py grammar-zoo-flavie-adapted railroad-diagrams-flavie-adapted
```

## Tests

Run everything with:

```bash
python3 -m unittest discover -v
```

The test suite covers parsing, AST distinctions, canonical formatting,
production-shape normalization, recurring-structure mining, containment
evidence, HTML embedding, and generated JavaScript safety. It also parses every
grammar in the full `grammar-zoo` corpus.

