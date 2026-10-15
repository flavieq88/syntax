"""Add the missing lexical-grammar productions to grammar-zoo-flavie's gaps.

`check_bgf_references.py` shows that most `grammar-zoo-flavie` grammars
reference nonterminals with no production in the same file: either because
the original fetched source only covers phrase-structure syntax (e.g. the
ISO C99/C++98/C# standards keep their lexical grammar in a separate clause
that this corpus's extraction didn't capture), or because the grammar was
extracted from TXL, whose scanner primitives (`id`, `number`, `stringlit`,
...) are never spelled out in any per-language TXL file.

Per the Grammar Zoo's own maturity model (see `dangling-else-analysis.md`'s
companion discussion, or grammarware.net/text/2015/zoo.pdf), "adding a
lexical part" to an extracted grammar is literally the definition of
*adapting* it to the next maturity level. This script performs exactly that
adaptation, reading from `grammar-zoo-flavie/` and writing the result to
`grammar-zoo-flavie-adapted/` -- the original extracted-tier files are never
modified, only copied and then extended.

Every addition here is sourced, not invented:

- For the six TXL-derived grammars (Basic, Pascal/Delphi, PHP, Python,
  Fortran, JS), the exact token regexes were pulled from the real fetched
  `.grm`/`.Grm` sources in the upstream Grammar Zoo repository
  (github.com/slebok/zoo, `zoo/<lang>/.../fetched/`), and from the official
  TXL Programming Language reference manual for the handful of primitives
  TXL itself predefines (`id`, `number`, `stringlit`, `charlit`, `comment`).
  TXL's `[NL]`, `[IN]`, `[EX]`, `[SP]`, `[SPOFF]`, `[SPON]` (and Fortran's
  numbered variants `IN_2`/`EX_2`/...) are, per that manual, pretty-printer
  formatting directives with "no effect on either the parse or the
  transformation" -- confirmed against Python's own `indent`/`dedent`
  productions, which consume the literal text "INDENT"/"DEDENT" and use
  `[IN]`/`[EX]` only as a cosmetic indarker alongside it. They are rendered
  here as `epsilon`.
- Eiffel's gaps (`Identifier`, `Character`, `Real`, `Simple_string`, ...)
  come from ECMA-367 (ISO/IEC 25436:2006) directly: every one of them is
  explicitly headed "Syntax (non-production)" in the standard itself --
  i.e. the standard's own authors chose informal prose over a formal BNF-E
  production for these, which is exactly why no BGF extractor could ever
  produce one. Where the prose gives a precise recipe (`Blanks_or_tabs`,
  `Line_wrapping_part`) it is formalized; where it just names an
  unenumerable set (`Character`, `Simple_string`) it is left as an abstract
  `value(...)` citing the standard section.
- C99/C++98/C#'s `identifier`/`constant`/`literal`/`string-literal` chains
  are the standard ISO/ECMA lexical grammars (C99 Annex A.1.3/A.1.5-7,
  C++98 clause 2, C# ECMA-334 clause 9) -- these sections are fully formal
  in their source standards, just extracted separately from the
  phrase-structure grammar reproduced in this corpus.
- Ada's Unicode general-category names (`letter_uppercase`, ...) are
  rendered as `value("Unicode category Lu")` etc., citing Ada 2005 RM 2.1's
  own use of Unicode General Category codes; enumerating the underlying
  code points would not add precision.
- Dart's `EOF` is ANTLR's built-in end-of-token-stream marker; Modula-3's
  `DQUOTE` is the literal `"` character used inside its string-escape
  productions.

Three files are substituted wholesale before the additions below are
applied, because the Grammar Zoo project already publishes a more mature
version of each -- see `upstream-fixes/README.md` for exactly which tier
and URL. They fix real extraction bugs (mismatched/typo'd names) that are
out of scope for a lexical-grammar pass; using the project's own fix is
more accurate than re-deriving it.

Usage:
    python3 adapt_lexical_grammar.py grammar-zoo-flavie grammar-zoo-flavie-adapted
"""

from __future__ import annotations

import argparse
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from bgf_parser import (
    Choice, Empty, Epsilon, Expression, Nonterminal, OneOrMore,
    Optional as Opt, Production, Sequence, Terminal, Value, ZeroOrMore, parse,
)

# --------------------------------------------------------------------------
# A tiny DSL for building Production trees, plus a serializer back to BGF
# XML. bgf_parser's own tag vocabulary is namespace-agnostic on read, so the
# elements below are written unprefixed.


def t(s: str) -> Terminal: return Terminal(s)
def n(s: str) -> Nonterminal: return Nonterminal(s)
def seq(*xs: Expression) -> Sequence: return Sequence(tuple(xs))
def ch(*xs: Expression) -> Choice: return Choice(tuple(xs))
def opt(x: Expression) -> Opt: return Opt(x)
def star(x: Expression) -> ZeroOrMore: return ZeroOrMore(x)
def plus(x: Expression) -> OneOrMore: return OneOrMore(x)
def eps() -> Epsilon: return Epsilon()
def empty() -> Empty: return Empty()
def val(kind: str) -> Value: return Value(kind)
def chars(s: str) -> Choice: return Choice(tuple(Terminal(c) for c in s))
def prod(nonterminal: str, expr: Expression) -> Production:
    return Production(nonterminal=nonterminal, expression=expr)


LOWER, UPPER, DIGITS = "abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789"
letter = ch(chars(LOWER), chars(UPPER))
digit = chars(DIGITS)
hexdigit = ch(digit, chars("abcdefABCDEF"))
octdigit = chars("01234567")
bindigit = chars("01")
sign = chars("+-")
exp_part = seq(chars("eE"), opt(sign), plus(digit))


def _expr_to_xml(parent: ET.Element, expr: Expression) -> None:
    wrapper = ET.SubElement(parent, "expression")
    if isinstance(expr, Terminal):
        ET.SubElement(wrapper, "terminal").text = expr.value
    elif isinstance(expr, Nonterminal):
        ET.SubElement(wrapper, "nonterminal").text = expr.name
    elif isinstance(expr, Value):
        ET.SubElement(wrapper, "value").text = expr.kind
    elif isinstance(expr, Epsilon):
        ET.SubElement(wrapper, "epsilon")
    elif isinstance(expr, Empty):
        ET.SubElement(wrapper, "empty")
    elif isinstance(expr, Sequence):
        e = ET.SubElement(wrapper, "sequence")
        for m in expr.members:
            _expr_to_xml(e, m)
    elif isinstance(expr, Choice):
        e = ET.SubElement(wrapper, "choice")
        for a in expr.alternatives:
            _expr_to_xml(e, a)
    elif isinstance(expr, Opt):
        _expr_to_xml(ET.SubElement(wrapper, "optional"), expr.expression)
    elif isinstance(expr, ZeroOrMore):
        _expr_to_xml(ET.SubElement(wrapper, "star"), expr.expression)
    elif isinstance(expr, OneOrMore):
        _expr_to_xml(ET.SubElement(wrapper, "plus"), expr.expression)
    else:
        raise TypeError(f"unsupported for serialization: {expr!r}")


def _production_to_xml(p: Production) -> ET.Element:
    el = ET.Element("production")
    ET.SubElement(el, "nonterminal").text = p.nonterminal
    _expr_to_xml(el, p.expression)
    return el


def _append_productions(path: Path, productions: list[Production]) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    for p in productions:
        root.append(_production_to_xml(p))
    tree.write(path, encoding="UTF-8", xml_declaration=True)


# --------------------------------------------------------------------------
# Generic TXL predefined nonterminals (TXL reference manual section 3.2),
# used where a grammar doesn't locally override them.


def p_id(): return prod("id", seq(letter, star(ch(letter, digit, t("_")))))
def p_number(): return prod("number", ch(
    seq(plus(digit), opt(seq(t("."), star(digit))), opt(exp_part)),
    seq(t("."), plus(digit), opt(exp_part))))
def p_stringlit(): return prod("stringlit", seq(t('"'), star(val("character")), t('"')))
def p_charlit(): return prod("charlit", seq(t("'"), val("character"), t("'")))
def p_token(): return prod("token", val("token"))
def p_eps(name): return prod(name, eps())


# ============================================================ BASIC (VB6)
# Source: zoo/basic/visual/concrete/fetched/VisualBasic6.Grm
VB_KEYS = ("access alias and as attribute beep begin binary byval call case chdir chdrive "
    "close const currency date debug declare dim do double each else elseif empty end enum eqv "
    "erase error event exit explicit false for friend function get global gosub goto if imp implements "
    "in input integer is len let lib like line load local lock long loop lset me mid mkdir name new next "
    "not nothing null on open option optional or paramarray preserve print private property public "
    "raiseevent randomize redim rem resume return rmdir rset seek select set shared single static step "
    "stop string sub then to true type typeof unload until variant wend while width with withevents "
    "write xor").split()

BASIC_ADDITIONS = [
    prod("id", seq(ch(t("_"), letter), star(ch(letter, digit, t("_"))), opt(chars("%&@!#$")))),
    prod("stringlit", seq(t('"'), star(ch(t('""'), val("character"))), t('"'))),
    prod("charlit", empty()),  # VB has no character literal form
    prod("vbcomment", ch(seq(t("'"), star(val("character"))), seq(t("rem "), star(val("character"))))),
    prod("hexnumber", ch(seq(t("0"), chars("xX"), plus(hexdigit)), seq(t("&"), chars("hH"), plus(hexdigit), opt(t("&"))))),
    prod("octnumber", ch(seq(t("0"), chars("oO"), plus(octdigit)), seq(t("&"), chars("oO"), plus(octdigit), opt(t("&"))))),
    prod("datelit", seq(t("#"), star(val("character")), t("#"))),
    prod("returncode", seq(plus(digit), t("&"))),
    prod("newline", t("\n")),
    p_number(),
    prod("key", Choice(tuple(t(k) for k in VB_KEYS))),
    p_eps("SP"), p_eps("SPOFF"), p_eps("SPON"), p_eps("IN"), p_eps("EX"), p_eps("TAB"),
]

# ============================================================ PASCAL/DELPHI
# Source: zoo/pascal/delphi/delphi2006/cangas/fetched/delphi.grammar
PASCAL_ADDITIONS = [
    p_id(), p_number(),
    prod("stringlit", seq(t('"'), star(val("character")), t('"'))),
    prod("hexnumber", ch(seq(t("$"), plus(hexdigit)), seq(t("0"), plus(hexdigit), t("H")))),
    prod("charlit", ch(seq(t("#"), plus(digit)), seq(t("#$"), plus(hexdigit)),
                       seq(t("'"), star(ch(t("''"), val("character"))), t("'")))),
    p_eps("SP"), p_eps("SPOFF"), p_eps("SPON"), p_eps("IN"), p_eps("EX"), p_eps("NL"),
]

# ============================================================ PHP
# Source: zoo/php/cordy/fetched/php.grm
PHP_KEYS = ("abstract and array as break case catch class continue declare default do echo else "
    "elseif enddeclare endfor endforeach endif endswitch endwhile eval exit extends for foreach "
    "function global if include include_once list new null or print require require_once return "
    "static switch try unset var while xor cfunction old_function").split()

PHP_ADDITIONS = [
    p_id(), p_number(), p_token(),
    prod("charlit", seq(t("'"), star(ch(t("\\\\"), t("\\'"), val("character"))), t("'"))),
    prod("stringlit", seq(t('"'), star(ch(t("\\\\"), t('\\"'), val("character"))), t('"'))),
    prod("Hexa", seq(t("0"), chars("xX"), plus(hexdigit))),
    prod("Octa", seq(t("0"), plus(octdigit))),
    prod("CommandString", seq(t("`"), star(val("character")), t("`"))),
    prod("MagicConstant", seq(t("__"), plus(val("character")), t("__"))),
    prod("key", Choice(tuple(t(k) for k in PHP_KEYS))),
    p_eps("SP"), p_eps("SPOFF"), p_eps("SPON"), p_eps("IN"), p_eps("EX"), p_eps("NL"), p_eps("FL"),
]

# ============================================================ PYTHON
# Source: zoo/python/v2.x/sorochan-cordy/fetched/python.grm
PYTHON_ADDITIONS = [
    p_id(),
    prod("charlit", seq(t("'"), val("character"), t("'"))),
    prod("stringlit", seq(t('"'), star(val("character")), t('"'))),
    prod("comment", seq(t("#"), star(val("character")))),
    prod("newline", t("\n")),
    prod("longstringlit", seq(t('"""'), star(ch(t('"""'), val("character"))), t('"""'))),
    prod("longcharlit", seq(t("'''"), star(ch(t("'''"), val("character"))), t("'''"))),
    prod("hexinteger", seq(t("0"), chars("Xx"), plus(hexdigit))),
    prod("octinteger", seq(t("0"), plus(octdigit))),
    prod("pointfloat", ch(seq(star(digit), t("."), plus(digit), opt(exp_part)),
                          seq(plus(digit), t("."), star(digit), opt(exp_part)))),
    prod("integernumber", plus(digit)),
    prod("number", seq(plus(digit), exp_part)),
    p_eps("SPOFF"), p_eps("SPON"), p_eps("IN"), p_eps("EX"),
]

# ============================================================ FORTRAN
# Source: zoo/fortran/f90/waite-cordy/fetched/fortran.grm
FORTRAN_ADDITIONS = [
    p_id(),
    prod("comment", ch(seq(t("\n"), ch(chars("cC"), t("*")), star(val("character"))),
                       seq(t("!"), star(val("character"))))),
    prod("newline", t("\n")),
    prod("Icon", plus(digit)),
    prod("Dop", seq(t("."), plus(letter), t("."))),
    prod("Bcon", ch(seq(chars("bB"), t("'"), plus(bindigit), t("'")),
                    seq(chars("bB"), t('"'), plus(bindigit), t('"')))),
    prod("Ocon", ch(seq(chars("oO"), t("'"), plus(octdigit), t("'")),
                    seq(chars("oO"), t('"'), plus(octdigit), t('"')))),
    prod("Zcon", ch(seq(chars("zZ"), t("'"), plus(hexdigit), t("'")),
                    seq(chars("zZ"), t('"'), plus(hexdigit), t('"')))),
    prod("Pcon", seq(opt(sign), plus(digit), chars("pP"))),
    prod("Xcon", seq(plus(digit), chars("xX"))),
    prod("RDcon", ch(
        seq(plus(digit), opt(seq(t("."), star(digit))), chars("eEdD"), opt(sign), plus(digit), opt(chars("eEdD"))),
        seq(star(digit), t("."), plus(digit), opt(seq(chars("eEdD"), opt(sign), plus(digit)))),
    )),
    prod("Scon", ch(seq(t("'"), star(ch(t("''"), val("character"))), t("'")),
                    seq(t('"'), star(ch(t('""'), val("character"))), t('"')))),
    prod("Hcon", ch(
        seq(t("1"), chars("hH"), val("character")),
        seq(t("2"), chars("hH"), val("character"), val("character")),
        seq(t("3"), chars("hH"), val("character"), val("character"), val("character")),
        seq(plus(digit), chars("hH"), plus(val("character"))),
    )),
    prod("Fcon", seq(chars("aAbBeEdDqQfFgGiIlLoOzZ"), opt(plus(digit)), opt(t("*")),
                     opt(seq(t("."), plus(digit), opt(seq(chars("eEdDqQ"), plus(digit))))))),
    p_eps("SP"), p_eps("SPOFF"), p_eps("SPON"),
    p_eps("IN_2"), p_eps("EX_2"), p_eps("IN_6"), p_eps("EX_6"),
    p_eps("TAB_2"), p_eps("TAB_7"), p_eps("TAB_9"),
]

# ============================================================ JS
# Source: zoo/js/synytskyy-cordy/fetched/js.grm
JS_ADDITIONS = [
    p_id(),
    prod("charlit", seq(t("'"), val("character"), t("'"))),
    prod("stringlit", seq(t('"'), star(val("character")), t('"'))),
    prod("comment", val("comment")),
    prod("number", ch(seq(plus(digit), opt(seq(t("."), star(digit))), opt(exp_part)),
                      seq(t("."), plus(digit), opt(exp_part)))),
    prod("js_hex_number", seq(t("0"), chars("xX"), plus(hexdigit))),
    prod("js_regexp", seq(t("/"), star(val("character")), t("/"), opt(plus(letter)))),
    p_eps("SPOFF"), p_eps("SPON"), p_eps("IN"), p_eps("EX"), p_eps("NL"),
]

# ============================================================ ADA
# Ada 2005 RM 2.1: Unicode General Category codes used directly by name.
ADA_ADDITIONS = [
    prod("underline", t("_")),
    prod("graphic_character", val("character")),
    prod("letter_uppercase", val("Unicode category Lu")),
    prod("letter_lowercase", val("Unicode category Ll")),
    prod("letter_titlecase", val("Unicode category Lt")),
    prod("letter_modifier", val("Unicode category Lm")),
    prod("letter_other", val("Unicode category Lo")),
    prod("mark_non_spacing", val("Unicode category Mn")),
    prod("mark_spacing_combining", val("Unicode category Mc")),
    prod("number_decimal", val("Unicode category Nd")),
    prod("number_letter", val("Unicode category Nl")),
    prod("punctuation_connector", val("Unicode category Pc")),
    prod("other_format", val("Unicode category Cf")),
]

# ============================================================ EIFFEL (applied to the upstream
# `connected` grammar.bgf; every one of these is headed "Syntax (non-production)" in ECMA-367)
EIFFEL_ADDITIONS = [
    prod("Identifier", seq(letter, star(ch(letter, digit)))),  # 8.32.16: sequence of alpha_numerics, first a letter
    prod("Blanks_or_tabs", plus(ch(t(" "), t("\t")))),  # 8.32.6
    prod("New_line", val("newline")),  # 8.32.6: "a New Line"
    prod("Character", val("character")),  # 8.32.1: full ISO 10646 character-set table
    prod("Real", seq(opt(n("Integer")), t("."), opt(n("Integer")),
                     opt(seq(chars("eE"), opt(n("Sign")), n("Integer"))))),  # 8.32.31
    prod("Simple_string", val("string")),  # 8.32.26
    prod("Line_sequence", val("string")),  # 8.29.11
    prod("Line_wrapping_part", seq(t("%"), star(ch(t(" "), t("\t"))), n("New_line"),
                                   star(ch(t(" "), t("\t"))), t("%"))),  # 8.29.13, fully formalizable
    prod("Free_binary", val("operator symbol")),  # 8.32.21: "distinct from all standard binary operators"
    prod("Free_unary", val("operator symbol")),
]

# ============================================================ MODULA-3 (applied to the upstream
# `connected` grammar.bgf)
MODULA_ADDITIONS = [
    prod("DQUOTE", t('"')),
]

# ============================================================ DART (ANTLR's built-in end-of-stream token)
DART_ADDITIONS = [
    prod("EOF", eps()),
]

# ============================================================ C99 (ISO/IEC 9899:1999 Annex A.1.3/A.1.5-7)
C99_ADDITIONS = [
    prod("identifier", seq(n("identifier-nondigit"), star(ch(n("identifier-nondigit"), n("digit"))))),
    prod("identifier-nondigit", ch(n("nondigit"), n("universal-character-name"))),
    prod("nondigit", ch(t("_"), letter)),
    prod("digit", digit),
    prod("universal-character-name", ch(seq(t("\\u"), n("hex-quad")), seq(t("\\U"), n("hex-quad"), n("hex-quad")))),
    prod("hex-quad", seq(n("hexadecimal-digit"), n("hexadecimal-digit"), n("hexadecimal-digit"), n("hexadecimal-digit"))),
    prod("hexadecimal-digit", hexdigit),
    prod("constant", ch(n("integer-constant"), n("floating-constant"), n("enumeration-constant"), n("character-constant"))),
    prod("enumeration-constant", n("identifier")),
    prod("integer-constant", seq(ch(n("decimal-constant"), n("octal-constant"), n("hexadecimal-constant")), opt(n("integer-suffix")))),
    prod("decimal-constant", seq(chars("123456789"), star(n("digit")))),
    prod("octal-constant", seq(t("0"), star(n("octal-digit")))),
    prod("octal-digit", octdigit),
    prod("hexadecimal-constant", seq(ch(t("0x"), t("0X")), plus(n("hexadecimal-digit")))),
    prod("integer-suffix", ch(t("u"), t("U"), t("l"), t("L"), t("ul"), t("uL"), t("Ul"), t("UL"),
                              t("ll"), t("LL"), t("ull"), t("uLL"), t("Ull"), t("ULL"))),
    prod("floating-constant", ch(n("decimal-floating-constant"), n("hexadecimal-floating-constant"))),
    prod("decimal-floating-constant", ch(
        seq(n("fractional-constant"), opt(n("exponent-part")), opt(n("floating-suffix"))),
        seq(n("digit-sequence"), n("exponent-part"), opt(n("floating-suffix"))))),
    prod("hexadecimal-floating-constant", seq(ch(t("0x"), t("0X")), ch(n("hexadecimal-digit-sequence"), n("hexadecimal-fractional-constant")),
                                              n("binary-exponent-part"), opt(n("floating-suffix")))),
    prod("hexadecimal-fractional-constant", ch(seq(opt(n("hexadecimal-digit-sequence")), t("."), n("hexadecimal-digit-sequence")),
                                               seq(n("hexadecimal-digit-sequence"), t(".")))),
    prod("hexadecimal-digit-sequence", plus(n("hexadecimal-digit"))),
    prod("binary-exponent-part", seq(ch(t("p"), t("P")), opt(n("sign")), n("digit-sequence"))),
    prod("fractional-constant", ch(seq(opt(n("digit-sequence")), t("."), n("digit-sequence")),
                                   seq(n("digit-sequence"), t(".")))),
    prod("exponent-part", seq(ch(t("e"), t("E")), opt(n("sign")), n("digit-sequence"))),
    prod("sign", chars("+-")),
    prod("digit-sequence", plus(n("digit"))),
    prod("floating-suffix", chars("fFlL")),
    prod("character-constant", seq(opt(t("L")), t("'"), n("c-char-sequence"), t("'"))),
    prod("c-char-sequence", plus(n("c-char"))),
    prod("c-char", ch(val("character"), n("escape-sequence"))),
    prod("escape-sequence", ch(n("simple-escape-sequence"), n("octal-escape-sequence"), n("hexadecimal-escape-sequence"), n("universal-character-name"))),
    prod("simple-escape-sequence", ch(t("\\'"), t('\\"'), t("\\?"), t("\\\\"), t("\\a"), t("\\b"), t("\\f"), t("\\n"), t("\\r"), t("\\t"), t("\\v"))),
    prod("octal-escape-sequence", seq(t("\\"), n("octal-digit"), opt(n("octal-digit")), opt(n("octal-digit")))),
    prod("hexadecimal-escape-sequence", seq(t("\\x"), plus(n("hexadecimal-digit")))),
    prod("string-literal", seq(opt(t("L")), t('"'), opt(n("s-char-sequence")), t('"'))),
    prod("s-char-sequence", plus(n("s-char"))),
    prod("s-char", ch(val("character"), n("escape-sequence"))),
]

# ============================================================ C++98 (ISO/IEC 14882:1998 clause 2)
CPP_ADDITIONS = [
    prod("identifier", seq(n("identifier-nondigit"), star(ch(n("identifier-nondigit"), n("digit"))))),
    prod("identifier-nondigit", ch(n("nondigit"), n("universal-character-name"))),
    prod("nondigit", ch(t("_"), letter)),
    prod("digit", digit),
    prod("universal-character-name", ch(seq(t("\\u"), n("hex-quad")), seq(t("\\U"), n("hex-quad"), n("hex-quad")))),
    prod("hex-quad", seq(n("hexadecimal-digit"), n("hexadecimal-digit"), n("hexadecimal-digit"), n("hexadecimal-digit"))),
    prod("hexadecimal-digit", hexdigit),
    prod("literal", ch(n("integer-literal"), n("character-literal"), n("floating-literal"), n("string-literal"), n("boolean-literal"))),
    prod("boolean-literal", ch(t("false"), t("true"))),
    prod("integer-literal", seq(ch(n("decimal-literal"), n("octal-literal"), n("hexadecimal-literal")), opt(n("integer-suffix")))),
    prod("decimal-literal", seq(chars("123456789"), star(n("digit")))),
    prod("octal-literal", seq(t("0"), star(n("octal-digit")))),
    prod("octal-digit", octdigit),
    prod("hexadecimal-literal", seq(ch(t("0x"), t("0X")), plus(n("hexadecimal-digit")))),
    prod("integer-suffix", ch(t("u"), t("U"), t("l"), t("L"), t("ul"), t("uL"), t("Ul"), t("UL"))),
    prod("character-literal", seq(opt(t("L")), t("'"), plus(n("c-char")), t("'"))),
    prod("c-char", ch(val("character"), n("escape-sequence"))),
    prod("escape-sequence", ch(n("simple-escape-sequence"), n("octal-escape-sequence"), n("hexadecimal-escape-sequence"), n("universal-character-name"))),
    prod("simple-escape-sequence", ch(t("\\'"), t('\\"'), t("\\?"), t("\\\\"), t("\\a"), t("\\b"), t("\\f"), t("\\n"), t("\\r"), t("\\t"), t("\\v"))),
    prod("octal-escape-sequence", seq(t("\\"), n("octal-digit"), opt(n("octal-digit")), opt(n("octal-digit")))),
    prod("hexadecimal-escape-sequence", seq(t("\\x"), plus(n("hexadecimal-digit")))),
    prod("floating-literal", ch(
        seq(n("fractional-constant"), opt(n("exponent-part")), opt(n("floating-suffix"))),
        seq(n("digit-sequence"), n("exponent-part"), opt(n("floating-suffix"))))),
    prod("fractional-constant", ch(seq(opt(n("digit-sequence")), t("."), n("digit-sequence")),
                                   seq(n("digit-sequence"), t(".")))),
    prod("exponent-part", seq(ch(t("e"), t("E")), opt(n("sign")), n("digit-sequence"))),
    prod("sign", chars("+-")),
    prod("digit-sequence", plus(n("digit"))),
    prod("floating-suffix", chars("fFlL")),
    prod("string-literal", seq(opt(t("L")), t('"'), star(n("s-char")), t('"'))),
    prod("s-char", ch(val("character"), n("escape-sequence"))),
]

# ============================================================ C# 4.0 (ECMA-334 clause 9)
CSHARP_ADDITIONS = [
    prod("identifier", ch(n("available-identifier"), seq(t("@"), n("identifier-or-keyword")))),
    prod("available-identifier", n("identifier-or-keyword")),
    prod("identifier-or-keyword", seq(n("identifier-start-character"), star(n("identifier-part-character")))),
    prod("identifier-start-character", ch(letter, t("_"))),
    prod("identifier-part-character", ch(letter, digit, t("_"))),
    prod("literal", ch(t("true"), t("false"), n("integer-literal"), n("real-literal"), n("character-literal"), n("string-literal"), t("null"))),
    prod("integer-literal", ch(
        seq(plus(digit), opt(n("integer-type-suffix"))),
        seq(ch(t("0x"), t("0X")), plus(hexdigit), opt(n("integer-type-suffix"))))),
    prod("integer-type-suffix", ch(t("U"), t("u"), t("L"), t("l"), t("UL"), t("Ul"), t("uL"), t("ul"),
                                   t("LU"), t("Lu"), t("lU"), t("lu"))),
    prod("real-literal", ch(
        seq(star(digit), t("."), plus(digit), opt(n("exponent-part")), opt(n("real-type-suffix"))),
        seq(plus(digit), n("exponent-part"), opt(n("real-type-suffix"))),
        seq(plus(digit), n("real-type-suffix")))),
    prod("exponent-part", seq(chars("eE"), opt(sign), plus(digit))),
    prod("real-type-suffix", chars("FfDdMm")),
    prod("character-literal", seq(t("'"), n("character"), t("'"))),
    prod("character", ch(val("character"), n("simple-escape-sequence"), n("hexadecimal-escape-sequence"), n("unicode-escape-sequence"))),
    prod("simple-escape-sequence", ch(t("\\'"), t('\\"'), t("\\\\"), t("\\0"), t("\\a"), t("\\b"), t("\\f"), t("\\n"), t("\\r"), t("\\t"), t("\\v"))),
    prod("hexadecimal-escape-sequence", seq(t("\\x"), hexdigit, opt(hexdigit), opt(hexdigit), opt(hexdigit))),
    prod("unicode-escape-sequence", ch(seq(t("\\u"), hexdigit, hexdigit, hexdigit, hexdigit),
                                      seq(t("\\U"), hexdigit, hexdigit, hexdigit, hexdigit, hexdigit, hexdigit, hexdigit, hexdigit))),
    prod("string-literal", ch(n("regular-string-literal"), n("verbatim-string-literal"))),
    prod("regular-string-literal", seq(t('"'), star(n("character")), t('"'))),
    prod("verbatim-string-literal", seq(t('@"'), star(ch(t('""'), val("character"))), t('"'))),
    prod("right-shift", t(">>")),
    prod("right-shift-assignment", t(">>=")),
]

ADDITIONS_BY_FILE = {
    "ada-ada2005-lncs-4348.bgf": ADA_ADDITIONS,
    "basic-visual-concrete.bgf": BASIC_ADDITIONS,
    "pascal-delphi-delphi2006-cangas.bgf": PASCAL_ADDITIONS,
    "php-cordy.bgf": PHP_ADDITIONS,
    "python-v2.x-sorochan-cordy.bgf": PYTHON_ADDITIONS,
    "fortran-f90-waite-cordy.bgf": FORTRAN_ADDITIONS,
    "js-synytskyy-cordy.bgf": JS_ADDITIONS,
    "eiffel-iso-25436-2006.bgf": EIFFEL_ADDITIONS,
    "modula-modula-3-src-052.bgf": MODULA_ADDITIONS,
    "dart-google.bgf": DART_ADDITIONS,
    "c-c99-iso-9899-tc3.bgf": C99_ADDITIONS,
    "cpp-cpp98-iso-14882-1998.bgf": CPP_ADDITIONS,
    "csharp-v4.0-microsoft.bgf": CSHARP_ADDITIONS,
}


UPSTREAM_FIXES = Path(__file__).parent / "upstream-fixes"


def adapt_directory(input_directory: Path, output_directory: Path) -> int:
    """Copy every ``.bgf`` file, substitute upstream fixes, append lexical additions."""

    if output_directory.exists():
        shutil.rmtree(output_directory)
    shutil.copytree(input_directory, output_directory)

    for fixed in UPSTREAM_FIXES.glob("*.bgf"):
        target = output_directory / fixed.name
        if target.exists():
            shutil.copy(fixed, target)

    changed = 0
    for filename, productions in ADDITIONS_BY_FILE.items():
        path = output_directory / filename
        if not path.exists():
            continue
        _append_productions(path, productions)
        changed += 1

    for filename in ADDITIONS_BY_FILE:
        path = output_directory / filename
        if path.exists():
            parse(path)  # re-validate well-formedness
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path, help="directory containing the extracted-tier .bgf files")
    parser.add_argument("output", type=Path, help="directory for the adapted .bgf files")
    arguments = parser.parse_args()
    count = adapt_directory(arguments.input, arguments.output)
    print(f"Adapted {count} grammars into {arguments.output}")


if __name__ == "__main__":
    main()
