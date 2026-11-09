# Numbers and identifiers across `grammar-zoo-flavie-adapted`

An analysis of how the 20 grammars in `grammar-zoo-flavie-adapted` tell a
number apart from a name, and of the letters that turn up *inside* numeric
literals anyway (`0x1F`, `1.5e3`, `16#FF#`, `10L`). Every production quoted
here is from `normalized-ebnf-flavie-adapted/`; character classes are
abbreviated as `[0-9]`, `[a-fA-F]` and so on, where the files spell out each
character as its own alternative.

**A caveat on where these rules come from.** Unlike the other analyses in
this repository, almost everything here lives in the *lexical* grammar —
exactly the part most source extractions left out and that
`adapt_lexical_grammar.py` filled back in. For the ISO/ECMA-derived
grammars (C99, C++98, C#, Ada, Eiffel) and the ANTLR/Happy/TXL ones
(Java, Dart, Swift, Lua, Smalltalk, Erlang, Haskell, Basic, Pascal, PHP,
Python, JS, Fortran, Modula-3), the rules come from the grammar's own
source or standard, but for the six TXL grammars that rely on TXL's
predefined `id` and `number` tokens (Pascal/Delphi, PHP, Python, JS,
Fortran; Basic overrides `id` with its own rule) both rules are the
adaptation's rendering of TXL's built-ins, not something the per-language
grammar states. Section 5 lists the places where that matters.

## 1. Can a name start with a digit?

| Language | Identifier rule (first character → rest) |
|---|---|
| C99, C++98 | `identifier ::= identifier-nondigit (identifier-nondigit \| digit)*`, `nondigit ::= "_" \| [a-zA-Z]` |
| C# 4.0 | `identifier-start-character ::= [a-zA-Z] \| "_"`, plus `"@" identifier-or-keyword` |
| Java 5 | `Identifier ::= Letter (Letter \| JavaIDDigit)*`, `Letter ::= [a-zA-Z]` |
| Dart | `IDENTIFIER_START ::= LETTER \| "_" \| "$"` |
| Swift | `Identifier_head` (letters, `_`, and large Unicode ranges); separately `Implicit_parameter_name ::= "$" Decimal_digits` |
| Ada 2005 | `identifier_start ::= letter_uppercase \| letter_lowercase \| … \| number_letter` (Unicode categories Lu, Ll, Lt, Lm, Lo, Nl) |
| Eiffel | `Identifier ::= [a-zA-Z] ([a-zA-Z] \| [0-9])*` |
| Modula-3 | `Ident ::= Letter (Letter \| Digit \| "_")*` |
| Haskell 98 | `varid ::= [a-z] ([a-zA-Z0-9] \| "'")*`, `conid ::= [A-Z] (…)*` |
| Erlang | `TokAtom ::= [a-z@] [0-9a-zA-Z_@]* \| "'" … "'"`, `TokVar ::= [A-Z_] [0-9a-zA-Z_]*` |
| Lua 5.2 | `NAME ::= [a-zA-Z_] [a-zA-Z_0-9]*` |
| Smalltalk | `IDENTIFIER ::= [a-zA-Z] [a-zA-Z0-9_]*` |
| VB6 (Basic) | `id ::= ("_" \| [a-zA-Z]) ([a-zA-Z0-9_])* [[%&@!#$]]` |
| Pascal/Delphi, PHP, Python, JS, Fortran | `id ::= [a-zA-Z] ([a-zA-Z0-9_])*` (TXL's predefined `id`, as adapted) |
| COBOL | `cobol_word ::= [a-zA-Z0-9] ([a-zA-Z0-9] \| "-")*` |

**19 of the 20 grammars forbid a digit as the first character of a name;
COBOL is the one exception.** In every other grammar, the identifier rule
opens with a letter class (sometimes plus `_`, `$` or `@`) and admits
digits only from the second position on, while every numeric-literal rule
opens with a digit (or a `.` followed by a digit — see §4). The two
first-character sets are disjoint, so a lexer can decide which kind of
token it's reading from the very first character, before it has seen
anything else. That's the whole point of the restriction: it isn't that
`2x` would be meaningless as a name, it's that the lexer would have to
look ahead arbitrarily far to find out whether `2e10` or `123` was going
to turn into a name after all.

**COBOL is the exception, and the grammar shows the cost.** `cobol_word`
accepts a digit in first position, which is real COBOL: paragraph and
section names like `100-MAIN-LOGIC` are the conventional style. But
`numeric ::= [("+" | "-")] ([0-9])+ [("." ([0-9])+)]` also matches `100`,
so `100` is derivable as *both* a word and a number in this grammar. Real
COBOL resolves this with a rule this CFG doesn't carry — a user-defined
word must contain at least one letter (ISO COBOL word-formation rules;
`adapt_lexical_grammar.py` notes this constraint and deliberately leaves it
unenforced, since it's a "somewhere in the token" condition rather than a
"first character" one). COBOL can afford this because it is a
whitespace- and period-delimited language where a word ends at a space,
not at the first character that can't continue it; the C-family lexers,
which split `x+1` into three tokens with no spaces, can't.

**Two near-exceptions, each fenced off by a sigil.**

- **Swift's `$0`, `$1`, …** (`Implicit_parameter_name ::= "$" Decimal_digits`)
  are names made entirely of digits — the closure's implicit parameters —
  but the leading `$` keeps the first character out of the number class,
  so the first-character rule still holds.
- **Fortran's Hollerith constants** go the other way: a token that *starts*
  with a digit and then contains letters. `Hcon ::= … | ([0-9])+ ("h" | "H") (value("character"))+`
  — `3Habc` is a three-character string, its length written in front as a
  count. This is safe only because Fortran's lexer reads the count first and
  then consumes exactly that many characters; it's a digit-led token, but
  it's a *string*, not a name.

**Where the first letter's case matters too.** Haskell and Erlang go
further than "letter vs. digit": the *case* of the first letter decides
which kind of name it is, at the grammar level.

- Haskell: `varid` starts lowercase (variables and functions), `conid`
  starts uppercase (types, constructors, classes, modules).
- Erlang: `TokVar` starts uppercase or `_` (variables), `TokAtom` starts
  lowercase or `@` (atoms — symbolic constants). Lowercase-first `ok` is a
  value, uppercase-first `Ok` is a variable.

In every other grammar here, case is not part of the identifier's
category.

**Leading underscore.** Allowed in C99, C++98, C#, Dart, Swift, Lua, VB6,
and Erlang variables; not allowed in Java, Eiffel, Modula-3, Ada, Haskell,
Smalltalk, COBOL, or in the TXL-derived `id` used by Pascal/Delphi, PHP,
Python, JS, and Fortran. That last group needs a caveat — see §5.

**Characters at the other end.** VB6 is the only grammar where an
identifier can *end* in a symbol: the optional type-declaration character
`[%&@!#$]` (`count%` for Integer, `name$` for String — general knowledge
for the meanings). It's the mirror image of the numeric suffixes in §3,
applied to names instead.

## 2. Letters inside numbers: the exponent

Because no number may start with a letter, letters are free to appear
*after* the first digit without ever being confused with a name. The most
common use is the exponent marker.

| Exponent letters | Languages |
|---|---|
| `e` / `E` | C99, C++98, C#, Java, Dart, JS, PHP, Python, Lua, Haskell, Erlang, Swift, Eiffel, VB6, Pascal/Delphi |
| `e` / `E` **and** `d` / `D` | Fortran-90 (`RDcon ::= … [eEdD] …`), Modula-3 (`Exponent ::= [EeDd] …`) |
| `E` only (uppercase) | Ada (`exponent ::= ("E" ["+"] numeral) \| ("E" "-" numeral)`) |
| `e` only (lowercase) | Smalltalk (`EXP ::= "e"`) |
| `p` / `P` (binary exponent, hex floats) | C99 (`binary-exponent-part`), Lua 5.2 (`HexExponentPart`), Swift (`Hexadecimal_exponent`) |
| none | COBOL (`numeric` has no exponent form) |

Fortran's and Modula-3's `D` is not a different notation but a different
*type*: in both, `1.0D0` means a double-precision literal and `1.0E0` a
single-precision one (general knowledge), so the exponent letter doubles
as a type annotation. The `p`/`P` form exists because inside a hexadecimal
float `e` is already a hex digit (`0x1e` is thirty), so it cannot also mean
"exponent"; a different letter is the only way out. That is a clean
grammar-level consequence of §3 below: once `a`–`f` are digits, the
exponent marker has to move.

## 3. Letters inside numbers: base, type, and digits

### Radix markers

| Form | Example | Languages |
|---|---|---|
| `0x` / `0X` prefix | `0x1F` | C99, C++98, C#, Java, Dart, JS, PHP, Python, Lua, Haskell, VB6 |
| `0x` lowercase only | `0x1F` | Swift |
| `0o` / `0O` prefix | `0o17` | Haskell, VB6 |
| `0o` lowercase only | `0o17` | Swift |
| `0b` lowercase only | `0b101` | Swift (`Binary_literal ::= "0b" …`) |
| `0b` / `0c` / `0x` prefix | `0c17` | Eiffel (`Integer_base_letter ::= [bcxBCX]`) — `c` for o**c**tal |
| leading `0` alone | `017` | C99, C++98, Java, Python 2, PHP (octal) |
| sigil prefix | `$1F`, `&H1F`, `&O17` | Pascal/Delphi (`$`), VB6 (`&H`, `&O`, optional trailing `&`) |
| letter suffix | `0FFH` | Pascal/Delphi (`"0" hexdigits+ "H"`) |
| base then `#` | `16#FF`, `16#FF#` | Erlang (`TokInteger ::= ["-"] [0-9]+ ["#" [0-9a-zA-Z]+]`), Ada (`base "#" based_numeral … "#"`) |
| base then `_` | `16_FF` | Modula-3 (`(Digit)+ "_" (HexDigit)+`) |
| base then `r` | `16rFF` | Smalltalk (`HEX ::= "16r"`) |
| letter + quoted digits | `Z'1F'`, `B'101'`, `O'17'` | Fortran-90 (`Zcon`, `Bcon`, `Ocon`) |
| no radix forms at all | | COBOL |

Every form keeps the token's first character outside the identifier class,
and the table shows how much ingenuity that took. The `0x` prefix exists
precisely so the token starts with a digit; Delphi's suffix form needs the
same leading `0`, because `FFH` on its own would be an identifier; Pascal's
`$` and VB6's `&` use a symbol that can't start a name. **Fortran is the
one grammar where a number starts with a letter** — `Z'1F'` — and it gets
away with it only because the quote immediately after the letter can't
appear in a name. Ada, Erlang, Modula-3 and Smalltalk all put the base
*first*, as an ordinary decimal number, which is both safe (it starts with
a digit) and general: Erlang's `[0-9a-zA-Z]+` admits any base up to 36,
and Ada's `extended_digit` any base up to 16. Smalltalk's grammar here only
admits `16r`, though Smalltalk's radix notation is general in the language
itself (`2r1010`, `36rZZ` — general knowledge).

**The leading-zero octal trap.** C99, C++98, Java, Python 2 and PHP all read
a leading `0` as "octal", so `010` means eight. This grammar-level fact is
visible directly in C's `octal-constant ::= "0" (octal-digit)*` alongside
`decimal-constant ::= [1-9] (digit)*`: the only way to write a decimal
integer with a leading zero is `0` itself. Haskell and Swift (and later
Python 3, outside this corpus) use an explicit `0o` instead, so `010` is
plain ten.

### Hex digits as letters

`a`–`f` are digits inside every hex form above. Case is usually free;
**Ada's grammar admits only uppercase** (`extended_digit ::= digit | "A" | … | "F"`)
and Erlang's admits the whole alphabet in both cases, since its base can go
to 36.

### Type suffixes

| Suffix letters | Meaning | Languages |
|---|---|---|
| `u`/`U`, `l`/`L`, `ll`/`LL` and combinations | unsigned, long, long long | C99 (`integer-suffix`, 14 spellings) |
| `u`/`U`, `l`/`L` and combinations | unsigned, long | C++98 (8 spellings), C# (12, including `LU`) |
| `l`/`L` | long | Java (`IntegerTypeSuffix`), Python 2 (`long`) |
| `f`/`F`, `l`/`L` | float, long double | C99, C++98 (`floating-suffix`) |
| `f`/`F`, `d`/`D` | float, double | Java (`FloatTypeSuffix`) |
| `f`/`F`, `d`/`D`, `m`/`M` | float, double, decimal | C# (`real-type-suffix`) |
| `j`/`J` | imaginary | Python 2 (`imag`) |
| `_` + kind | kind parameter | Fortran-90 (`Icon "_" KindParam`, e.g. `1_8`) |

The suffix family is a C-lineage habit: the type of a literal is fixed by
its spelling, so a separate letter is needed whenever the default type
isn't wanted. Languages without suffixes either infer the literal's type
from context (Haskell, Swift, Ada — general knowledge) or have a single
number type (Lua 5.2, JS — general knowledge).

### Digit separators

Swift (`Decimal_literal_character ::= Decimal_digit | "_"`, and the same for
binary, octal, hex) and Ada (`numeral ::= digit ([underline] digit)*`) allow
`_` between digits for readability: `1_000_000`. Ada's rule is the stricter
one — at most one `_` at a time, never at either end — while Swift's admits
runs of underscores and a trailing one. Modula-3's `_` is not a separator
but the radix marker (`16_FF`).

## 4. Where the decimal point may go

| Form | Allowed in |
|---|---|
| leading dot, `.5` | C99, C++98, C#, Java, Dart, JS, PHP, Python, Lua, VB6, Pascal/Delphi, Fortran-90, Eiffel |
| trailing dot, `5.` | C99, C++98, Java, JS, PHP, Python, Lua, VB6, Pascal/Delphi, Eiffel |
| digits required on both sides | Ada, Modula-3, Haskell, Erlang, Smalltalk, Swift, COBOL, Dart (trailing), C# (trailing) |

Requiring digits on both sides of the point isn't fussiness. In Haskell,
Erlang, Smalltalk and Swift, `.` is also a significant operator or
terminator (function composition, the clause terminator, the statement
terminator, member access) and `5.` or `.5` would collide with it; in Ada
and Modula-3 it avoids confusion with the range operator `..` (`1..10`) —
the last two points are general knowledge rather than something these
grammars state.

**A sign inside the literal.** Erlang (`TokInteger ::= ["-"] …`,
`TokFloat ::= ["-"] …`), Smalltalk (`stInteger ::= [MINUS] …`) and COBOL
(`numeric ::= [("+" | "-")] …`) put an optional sign inside the numeric
*token*, and Eiffel's `Integer_constant ::= [Sign] Integer` puts it in the
constant rule. Everywhere else, `-5` is the unary minus operator applied to
`5`. Smalltalk is the one where this matters most: its `operand ::= literal |
reference | subexpression` has no prefix-operator alternative, and `-` is
only ever a `BINARY_SELECTOR`, so a negative number can only be written as
part of the literal. Erlang is the opposite case: it has the sign inside
the literal *and* a prefix operator (`prefixOp ::= "+" | "-" | "bnot" |
"not"`), so `-5` is derivable both as one negative literal and as `-`
applied to `5` — a small ambiguity that is harmless only because both
readings mean the same value.

## 5. Gaps and oddities in these specific grammars

These are places where the grammar on file disagrees with the language as
generally documented. They're worth knowing before relying on this corpus
for lexical claims.

- **TXL `id` and the leading underscore.** Pascal/Delphi, PHP, Python, JS
  and Fortran all use `adapt_lexical_grammar.py`'s rendering of TXL's
  predefined `id`, which starts with a letter only. Real Python and JS
  identifiers can start with `_` (`_private`, `__init__`), JS ones also
  with `$`, and PHP variables are written `$name` (general knowledge). It
  is not settled here whether TXL's own predefined `id` allows a leading
  underscore — the TXL reference manual wasn't available to check — so
  this is either a limitation of TXL's default or of the adaptation.
- **Eiffel's `Digit` includes hex letters and `_`.** `Digit ::= [0-9a-fA-F_]`
  serves every base, so `Integer ::= [Integer_base] Digit_sequence` also
  accepts `12ab` as a plain decimal. The grammar defers the per-base digit
  check to elsewhere. Separately, `Real ::= [Integer] "." [Integer] [...]`
  makes both sides optional, so a lone `.` is a `Real`.
- **Ada's uppercase-only letters.** `exponent` uses `"E"` and
  `extended_digit` uses `"A"`–`"F"` only, but Ada is case-insensitive and
  `1.0e3` and `16#ff#` are legal Ada (general knowledge).
- **Smalltalk's radix and exponent are narrowed.** Only `16r` and only
  lowercase `e`, where the language accepts any base and also other
  exponent letters (general knowledge).
- **Java's `JavaIDDigit ::= [0-9a-zA-Z]`** includes letters. It's harmless
  (they're already allowed by `Letter`) but it's not "digit".
- **COBOL's `cobol_word` overlaps `numeric`**, as discussed in §1.

## Summary

- **The first character decides.** 19 of 20 grammars keep the first
  character of a name and the first character of a number in disjoint
  sets, so the lexer can classify a token immediately. COBOL is the
  exception, and its grammar shows exactly the ambiguity (`100` as word
  and as number) that the rule exists to prevent.
- **Every numeric notation is designed around that rule.** `0x`, `$`, `&H`,
  `16#`, `16r` and Delphi's `0…H` all exist to keep a letter out of the
  first position; Fortran's `Z'1F'` is the only number that starts with a
  letter, and it relies on the quote that follows.
- **After the first character, letters are free.** They mark the
  exponent (`e`, and `p` once `e` is a hex digit), the base (`x`, `o`, `b`,
  `c`, `r`, `H`), hex digits (`a`–`f`), and the type (`L`, `u`, `f`, `d`, `m`,
  `j`, and Fortran's `D` exponent).
- **Case can be grammar.** Haskell and Erlang decide what kind of name a
  token is from the case of its first letter.
- **The lineages show through.** The C family shares `0x`, leading-zero
  octal, and type suffixes; Ada, Erlang and Smalltalk share a
  base-first notation that works for any base; Fortran keeps its own
  quoted `B`/`O`/`Z` forms, `D` exponents, and Hollerith counts.

## References

The grammar claims in this document are checked against the productions in
`normalized-ebnf-flavie-adapted/`. Remarks marked as general knowledge are
not cited claim by claim.

- Zaytsev, V. (2015). Grammar Zoo: A corpus of experimental grammarware. *Science of Computer Programming*, 98, 28–51. https://doi.org/10.1016/j.scico.2014.07.010 — the source corpus every grammar here comes from.
- Lämmel, R., & Verhoef, C. (2001). Semi-automatic grammar recovery. *Software: Practice and Experience*, 31(15), 1395–1438. https://doi.org/10.1002/spe.423 — the recovery of the VS COBOL II grammar used as this corpus's COBOL (`cobol-vscobolii-lammel-gdk`).
- Sebesta, R. W. (2019). *Concepts of Programming Languages* (12th ed.). Pearson. — textbook coverage of lexical analysis and literal design across languages.
