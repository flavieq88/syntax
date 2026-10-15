# Upstream fixes

These three files replace the plain `grammar-zoo-flavie` copies of the same
name when building `grammar-zoo-flavie-adapted` (see `adapt_lexical_grammar.py`).
They are not reconstructed by us -- they're the Grammar Zoo project's own
more-mature-tier grammars, fetched as-is from the upstream repository:

| File | Fetched from | Tier |
|---|---|---|
| `eiffel-iso-25436-2006.bgf` | `github.com/slebok/zoo/blob/master/zoo/eiffel/iso-25436-2006/connected/grammar.bgf` | connected |
| `modula-modula-3-src-052.bgf` | `github.com/slebok/zoo/blob/master/zoo/modula/modula-3/src-052/connected/grammar.bgf` | connected |
| `csharp-v4.0-microsoft.bgf` | `github.com/slebok/zoo/blob/master/zoo/csharp/v4.0/microsoft/corrected/grammar.bgf` | corrected |

Fetched 2026-09-15. Each fixes real extraction bugs (mismatched/typo'd
nonterminal names -- e.g. the C# file resolves `right-shift` and
`right-shift-assignment`) that are out of scope for a lexical-grammar
addition pass; using the project's own fix is more accurate than
re-deriving it. They still have genuine lexical-grammar gaps of their own
(e.g. Eiffel's `Identifier`, C#'s `identifier`/`literal`), which
`adapt_lexical_grammar.py` fills in on top.
