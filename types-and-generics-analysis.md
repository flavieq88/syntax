# Types, generics, and null-safety across `grammar-zoo-flavie`

An analysis of type-annotation requirements, generics/templates, nullable
types, and variant/union types across the languages in
`grammar-zoo-flavie`, based on the actual productions in
`normalized-ebnf-flavie-adapted/`.

**A caveat before anything else.** "Strongly vs. weakly typed" is a
*semantic* property — whether a language permits silent, unsafe
conversions (does `1 + "1"` type-check, and if so, as what?) — and a
context-free grammar cannot show that: the production for `+` looks
identical whether or not the language performs implicit coercion
underneath it. What a BGF grammar *can* show reliably is a real, useful
proxy: whether a type annotation is syntactically mandatory, optional, or
doesn't exist as a grammatical possibility at all. This document uses that
proxy throughout, and is explicit about the difference between "no type
annotation was written" (which can mean three different things depending
on the language) and any claim about type-checking strength itself.

## 1. Mandatory, optional, or entirely absent type annotations

**Mandatory on every declaration:** C99, C++98, C#, Java 5, Ada, Fortran-90,
Pascal/Delphi, Modula-3, and Eiffel all require a type in the grammar
itself — there's no path through a variable, parameter, or field
declaration that skips it.

**A fifth category PL/I adds: an open-ended, genuinely optional
*attribute list*, not a single type slot at all.**

```
pl1: statement ::= ... | ("DECLARE" sep+(([level] name (attribute)* ["SYSTEM"]), ",") ";") | ...
```

`(attribute)*` is zero-or-more — a bare `DECLARE x;` with no attributes
at all is syntactically valid, which is a genuinely different shape from
every category above: not one mandatory type keyword (C99), not one
dynamically-typed absence (Python), not VB6's single optional `as_type`
slot with one named fallback. PL/I instead accumulates an open set of
independent, freely-ordered descriptors — `FIXED`, `DECIMAL`,
`CHARACTER(10)`, `STATIC`, `CONTROLLED`, and dozens more (the full 45-way
`attribute` choice is worth a look in `grammar-zoo-flavie-adapted/` —
it's the richest single production in the whole corpus) — any subset of
which, including none, is grammatically acceptable on one declaration.
Real PL/I's semantics for the empty case are a well-documented piece of
language-design history worth citing even though this CFG can't show
it: an undeclared or under-declared identifier gets a *default* type
based on the **first letter of its own name** (`I` through `N` default to
`FIXED BINARY`, every other starting letter defaults to `FLOAT BINARY`) —
a rule with no grammatical trace at all, since it depends on reading the
identifier's own spelled-out text, not any structural property a
production could condition on. It's frequently cited as one of the more
notorious implicit-typing design missteps in language history, and it's
a clean example of this document's opening caveat: the CFG shows that an
attribute list *can* be empty, but what filling that emptiness in
actually means is semantics, invisible here by construction.

**COBOL — PL/I's exact contemporary and fellow 1960s IBM mainframe
language — independently arrives at the identical open-ended-clause-list
shape**, via a structurally near-identical production:

```
cobol: data_description_entry_format_i ::= level_number [data_name | "FILLER"]
                                            [redefines_clause] data_clauses ["."]
       data_clauses ::= (blank_when_zero_clause | ... | occurs_clause | picture_clause
                        | sign_clause | ... | usage_clause | value_clause_format_ii
                        | renames_clause)*
```

Same shape as PL/I's `(attribute)*`: an accumulating, freely-ordered,
zero-or-more set of independent descriptors, with `PICTURE` (the closest
thing COBOL has to "a type") sitting as just one more optional clause
among `OCCURS` (array dimensioning), `SIGN`, `USAGE`, `VALUE`, and others —
not a single mandatory type keyword the way C99's grammar has one. The
empty case means something different from PL/I's implicit-default-type
rule, though: a COBOL data item with no `PICTURE` and no `USAGE` clause
isn't given a silent default elementary type at all — it becomes a
*group item*, a pure structural container whose "type" is just the
concatenation of whatever elementary items are declared under it at the
next level number. COBOL and PL/I solve the "declaration is a list of
orthogonal properties" problem the same way at the grammar level, for the
same era-and-institution reason (both are IBM mainframe languages from
the same decade, built for the same category of large, record-heavy
business data), but land on different semantics for what an empty list
actually denotes.

**Entirely absent — no type-annotation production exists anywhere in the
grammar:**

```
python:  expr_stmt ::= testlist | testlist augassign assign_value
js:      js_variable_description ::= id [js_variable_initialization]
php:     InstanceVariable ::= TVariable [EqualsStaticScalar]
```

This is a stronger claim than "the type was omitted" — there is no
grammatical slot a type could occupy in any of these three productions.
Python, this JS grammar, and this PHP grammar are dynamically typed by
grammar construction, not just by convention.

**Optional, with a defined static fallback type — a genuine third
category:**

```
basic:  single_var_description ::= id [initial_value] [as_type]
```

VB6's `[as_type]` is genuinely optional, but omitting it doesn't make the
variable typeless: it falls back to VB6's `Variant`, a real type with its
own (dynamically-behaving) semantics. This is neither the Python/JS/PHP
camp (no annotation possible) nor the mandatory-everywhere camp
(annotation always required) — it's "statically typed by default, with an
explicit, grammatically visible opt-out into dynamic behavior."

**A related but categorically different thing: type inference is not
dynamic typing.**

```
c#:  local-variable-type ::= type | "var"
```

`var` in C# 4.0 looks superficially similar to VB6's omitted `as_type` —
no type token is written either way — but it means something different in
kind: the compiler still infers and permanently fixes one concrete static
type at compile time. `var x = 5;` makes `x` an `int` forever, checked
identically to writing `int x = 5;` explicitly. It's sugar over static
typing, not an escape hatch from it, and is worth keeping distinct from
both VB6's Variant fallback and Python's total absence of type syntax,
even though all three surface as "no type written" at a glance.

**A fourth category Haskell adds: optional, fully static, and structurally
detached from the definition it describes.**

```
haskell: decl    ::= gendecl | (funlhs rhs) | (pat0n rhs)
         gendecl ::= (vars "::" qualtype) | ...
```

A Haskell type signature (`add :: Int -> Int -> Int`) and the binding it
describes (`add x y = x + y`) are two *separate* alternatives of the same
`decl` production — two independent top-level declarations that happen to
share a name, not one declaration with an optional type slot. Nothing in
the grammar requires both to be present, requires them to be adjacent, or
even forbids writing the signature without ever supplying a matching
binding at all (a parse error waits until a later compiler phase, not
here). This is a genuinely different shape from every other category
above: it isn't "mandatory" (C99's `type` token is bolted directly onto
the one declaration there is), isn't "absent" (the slot for a full type
exists and is routinely used), and isn't VB6's "optional with a named
fallback type" either, since omitting it doesn't select any particular
concrete type — the compiler still infers one, every time, exactly as
precisely as if the signature had been written. In that sense Haskell's
inference goes further than C#'s `var`, which still requires a placeholder
token to be present; Haskell requires nothing at all, in either the type
or value slot, for inference to kick in.

## 2. Generics and templates: real divergence in sophistication and philosophy

| Language | Mechanism |
|---|---|
| Ada 2005 | `generic_formal_parameter_declaration ::= formal_object_declaration \| formal_type_declaration \| formal_subprogram_declaration \| formal_package_declaration` — parameterizable not just by type, but by a value, an entire subprogram, or an entire package. Requires a separate, explicit, *named* instantiation step before use: `generic_instantiation ::= "package" name "is" "new" generic_package_name [actual_part] ";"` — a two-step process, unlike everyone else's inline `Foo<T>` |
| C++98 | `type-parameter ::= "class" [id] \| "typename" [id] \| "template" "<" template-parameter-list ">" "class" [id]` — the last alternative is a **template-template parameter**: a template parameterized by another template, recursively. `template-parameter` also permits plain non-type (value) parameters via `parameter-declaration`. The richest single generic vocabulary in the corpus |
| C# 4.0 | `type-parameter-constraints-clause ::= "where" type-parameter ":" type-parameter-constraints`, combinable across `primary-constraint`, `secondary-constraints`, and `constructor-constraint` — multiple simultaneous constraints per parameter. Also `variant-type-parameter-list`: **declaration-site variance** (`in`/`out`), fixed once by the generic type's author |
| Java 5 | `typeParameter ::= Identifier [("extends" typeBound)]` — a single bound only. Variance is handled by an entirely different mechanism: `typeArgument ::= type \| "?" [("extends" \| "super") type]` — **use-site variance**, where the *caller* decides `List<? extends Number>` at each point of use, not the type's author |
| Eiffel | `Formal_generics ::= "[" Formal_generic_list "]"` — square brackets, not angle brackets: `LIST [INTEGER]` rather than `List<Integer>`. `Formal_generic ::= ["frozen"] Formal_generic_name [Constraint]`, with `Formal_generic_name ::= ["?"] Identifier` |
| Dart | `typeParameter ::= identifier [(EXTENDS type)]` — the same simple single-bound shape as Java, no variance mechanism captured |
| Modula-3 | **no generics production anywhere in the grammar** — not an extraction gap: Modula-3 generics are instantiated by the `m3makefile` build system through textual substitution of whole source files, entirely outside the core language's expression/declaration grammar this corpus captures |
| Haskell | `simpletype ::= (tycon simpletype_1_1) | tycon`, `simpletype_1_1 ::= (tyvar simpletype_1_1) | tyvar` — no brackets of any kind. `data Tree a = ...` applies the type variable `a` to `Tree` by plain juxtaposition, the exact same mechanism `function-analysis.md` §2/§7 already documents for *value*-level application (`fexp ::= (fexp aexp) | aexp`) and parameter lists. Ordinary type application reuses it too: `btype ::= (btype atype) | atype` is what makes `Maybe Int` or `Either String Int` well-formed, with no angle brackets, square brackets, or commas anywhere in the production |

Haskell is the one language in this table with no dedicated generics
syntax at all, for the same reason it has no dedicated call syntax in
`function-analysis.md`: applying a type constructor to a type argument and
applying a function to a value argument are, grammatically, not two
features — they're the same juxtaposition idiom showing up at two
different syntactic levels (types and values) of one uniform language
design. No other language in this corpus shares that property; everywhere
else, "declare a generic parameter" and "call a function" are handled by
visibly different grammar machinery.

Haskell's constrained polymorphism (ad-hoc rather than parametric, and
covered properly in `classes-and-inheritance-analysis.md`) attaches
differently from any constraint mechanism above, too:

```
haskell: qualtype   ::= optcontext type
         optcontext ::= epsilon | (context "=>")
         context    ::= type
```

`(Eq a, Ord a) => a -> a -> Bool` puts the constraint in a dedicated
prefix clause on the *whole type*, ahead of a `=>` token, rather than as
an annotation attached to the generic parameter itself the way Java's
`<T extends Comparable<T>>` or C#'s `where T : IComparable` or Eiffel's
bracketed `Constraint` do. It's a fourth distinct attachment point for the
same general idea (bound a type parameter to an interface/contract it
must satisfy), on top of the parameter-annotation and `where`-clause
styles already covered below. One nuance invisible at this level of the
grammar: `context` and the `scontext` used for `class`/`instance`
declarations are written as literally the same production here
(`N("scontext") ::= N("type")`), but the Haskell 98 Report's own prose
restricts `scontext` to simple, single-type-variable class applications
only (`C a`, never `C (Maybe a)`) — exactly the kind of rule a
context-free grammar can't express that this whole document keeps running
into (the strong/weak-typing caveat at the top of this file, the "nearest
if" convention in `dangling-else-analysis.md`).

The Java/C# contrast is the sharpest single data point here: **both solve
the identical generic-variance problem — can `List<Cat>` be used where
`List<Animal>` is expected — at opposite ends of the type.** Java lets the
*caller* decide per use-site with wildcards; C# lets the *type's author*
decide once, permanently, at the declaration site with `in`/`out`. Two
well-documented, deliberately different design philosophies for the same
underlying question.

## 3. Nullable/optional types — only three languages have anything at all

- **C#**: `nullable-type ::= non-nullable-value-type "?"` (`int?`), plus a
  null-coalescing operator `"??"` and the ternary `"?:"`. Scoped
  specifically to *value* types (structs/primitives, non-nullable by
  default) — C# 4.0 predates non-nullable *reference* types, added later
  in C# 8.
- **Ada**: `null_exclusion ::= "not" "null"`, applied to access (pointer)
  types — `not null access Integer`. Ada's default is that access types
  *can* be null; the language requires an explicit opt-in to
  non-nullability.
- **Eiffel**: `Attachment_mark ::= "?" | "!"` on `Class_type`. `!` marks a
  type "attached" (guaranteed non-void); `?` marks it "detachable" (may be
  void). Eiffel is the only one of the three offering an explicit
  *two-way* marker — opting into either nullable or non-nullable
  explicitly — rather than one fixed default with a single opt-out
  direction, as in Ada or C#.

No other language in the corpus (C99, C++98, Java 5, Dart, Python, PHP,
this JS grammar, Pascal, Fortran-90, Modula-3, Basic, PL/I, COBOL) has any
comparable mechanism at these grammar versions.

**Haskell needs no mechanism here at all, for a reason worth stating
precisely: not because it lacks the concept "a value might be absent,"
but because it has no special-cased `null`/`nil` to begin with.** Absence
is expressed with the ordinary `data`/`constrs` machinery covered in §4
below (`data Maybe a = Nothing | Just a`), the same general-purpose
sum-type production every other variant type in the language goes
through — no dedicated nullable-type grammar rule exists because none is
needed. This is the clearest illustration in this whole document of why
C#, Ada, and Eiffel each had to *invent* a special-purpose annotation:
their base type systems have no general "one of these alternatives,
possibly carrying data" construct built into ordinary type declarations,
so "might be absent" had to be bolted on as its own dedicated piece of
syntax. A language whose data declarations already express arbitrary
tagged unions gets nullability for free, as one unremarkable instance of a
mechanism it needed for other reasons anyway.

## 4. Union/variant types — a visible safety gradient

- **COBOL**: `redefines_clause ::= "REDEFINES" data_name`, attached
  optionally to any `data_description_entry`. This is more primitive than
  every other mechanism below, not just less safe: it isn't a grouped
  choice between named alternative shapes at all (there's no `union`-style
  keyword gathering alternatives together) — it's a pairwise declaration
  that one *new* data item simply occupies the same storage as one
  *already-declared* item, with no shared "this is a variant" wrapper, no
  discriminant of any kind, and no limit on how many items can redefine
  the same storage in sequence. Even C's union groups its alternatives
  under one declaration; COBOL's `REDEFINES` doesn't even do that much —
  it's closer to a raw storage alias than a type.
- **C99**: `struct-or-union ::= "struct" | "union"`. A C `union` carries
  **no discriminant at all** — the grammar offers no way to know which
  member was written last, and reading the wrong one is undefined
  behavior. The least safe variant mechanism in the corpus.
- **Pascal/Delphi**: `record_variant ::= (expr)+ ":" "(" visibility_default
  ")" ...` — a case-labeled variant part tied to a discriminating
  expression. Safer than C's union: the grammar's own shape associates
  each variant with a specific tag value.
- **Ada**: `variant_part ::= "case" discriminant_direct_name "is"
  (variant)+ "end" "case" ";"` — ties the variant directly to a proper,
  typed `discriminant_direct_name`, itself a declared field in the
  record's `discriminant_part`. The most structurally rigorous of the
  three.

- **Haskell**: `constrs ::= (constr)+ | ...`, each `constr` a named
  constructor with its own argument types (`con (atype)* | con "{"
  fielddecls "}"`). The discriminant here isn't a separate field at all —
  it's the constructor name itself, which must be supplied at every
  construction site and named again at every pattern-match site
  (`pat10n ::= apat | (gcon apat (apat)*)`, `alt ::= (pat "->" exp
  ...) | ...`). There is no way to produce a `Tree` value without
  committing to `Leaf` or `Node` up front, and no way to inspect one
  without naming which constructor is expected — tag and data are the same
  syntactic act, at both ends, rather than a tag the grammar lets you
  attach loosely (Pascal) or declare once and forget to check (Ada, in
  principle, if a case arm goes unhandled). The grammar itself can't show
  exhaustiveness-checking, but the structural fact that reading a field
  always goes through naming a specific constructor is what makes
  exhaustiveness checkable by a compiler at all.

This is a five-point safety gradient — pairwise storage aliasing with no
grouping or discriminant at all (COBOL), untagged but at least grouped
(C), tagged by an expression (Pascal), tagged by a real typed discriminant
field (Ada), tagged by the constructor name itself at both construction
and read sites (Haskell) — visible entirely in how much grammatical
structure each
language wraps around the same underlying "one of several possible
shapes" idea.

## Why each design was chosen

**Mandatory type annotations (the majority).** All nine languages in this
category were designed with compile-time verification as a primary goal —
catching mismatched types, missing conversions, and misused values before
a program ever runs, at some cost in declaration verbosity.

**No type-annotation syntax at all (Python, this JS grammar, this PHP
grammar).** All three prioritize rapid, exploratory development and
runtime flexibility over compile-time guarantees, consistent with their
origins as scripting/glue languages where the cost of a type error
surfacing at runtime was judged less important than minimizing the
friction of writing and changing code quickly.

**VB6's optional annotation with a Variant fallback.** This reflects VB6's
target audience directly: it was designed to let non-specialist and
beginner programmers get something running immediately (skip the type,
get a working Variant-typed variable) while still giving more careful
programmers the option to declare precise types where performance or
correctness mattered — an explicit two-tier design rather than a single
uniform stance.

**C#'s `var`.** Type inference exists purely to reduce visual noise in
cases where the type is already obvious from the initializer (`var list =
new List<int>();`), without weakening any static guarantee — a
readability convenience layered on top of an unchanged type system, not a
loosening of it.

**Ada's uniquely broad generic-parameter vocabulary (types, objects,
subprograms, whole packages) plus mandatory named instantiation.** Both
choices trace to the same source as Ada's other design decisions
throughout this analysis: an emphasis on catching errors and making
intent explicit ahead of runtime. Letting a generic unit be parameterized
by an entire subprogram or package (not just a type) supports building
highly reusable, verifiable library components — a natural extension for
a language whose Ada 83 predecessor already had a strong module
(package) system to parameterize over. Requiring a separate, named
instantiation (`... is new Generic_Name(...)`) rather than inline
parameterization keeps every instantiation an explicit, auditable
declaration in its own right, consistent with Ada's general preference
for explicit, statically-checkable structure over terse inline
convenience.

**C++'s template-template parameters and value parameters.** C++
templates were designed as a general-purpose, Turing-complete
compile-time metaprogramming facility, not merely a way to write one
container class generically — allowing a template to take another
template, or a plain value, as a parameter is exactly the kind of
compositional power that later enabled template metaprogramming as an
entire (unintended, but embraced) programming style within C++. This
reflects the C++ tradition of maximizing what's expressible at compile
time, in keeping with its systems-programming emphasis on paying no
runtime cost for abstraction.

**C#'s declaration-site variance vs. Java's use-site variance.** Both are
answers to the same real problem (assignment compatibility between
generic types with related type arguments), designed independently and a
decade apart. Java's wildcards let *any* caller decide variance per call
site without requiring the original type's author to have anticipated it
— valuable for a language that had to retrofit generics onto a huge
existing standard library (Java 5's generics were added while preserving
backward compatibility with pre-generic code). C#'s declaration-site
`in`/`out` instead asks the type's author to commit once, which is
simpler to reason about at every call site but requires the variance
decision to be made when the generic interface is first designed —
practical for a newer language with a smaller, still-evolving standard
library at the time.

**Eiffel's square-bracket generics.** A minor but real notational choice:
Eiffel had already established `[...]` for other purposes in its own
syntax before angle-bracket generics became the near-universal convention
via C++ and its many descendants — the bracket choice reflects Eiffel's
independent design lineage rather than any technical constraint.

**Haskell's lack of any dedicated generics syntax.** This traces to the
same source as its lack of dedicated call syntax in
`function-analysis.md`: a language built around a small set of maximally
general, uniformly-applied mechanisms (juxtaposition for application,
algebraic data types for data) doesn't need a special case for
"parameterize this by a type" once ordinary application already covers
"apply this to an argument," whatever kind of thing is on each side.
Introducing bracket syntax specifically for generics, the way C++/Java/C#
all did, would have been adding a second application mechanism to a
language whose entire design bet is that one, uniform mechanism is enough.

**Nullable/optional-type mechanisms (C#, Ada, Eiffel) all trace to the
same motivation: null-pointer errors are a well-documented, extremely
common class of runtime failure**, and each of the three built a different
piece of syntax to let the type system catch a mistaken null (or a
mistaken assumption of non-null) before it manifests as a runtime crash.
Ada and C# each fixed one default and let the programmer opt out of it
in one direction (Ada: access types are nullable by default, opt into
`not null`; C#: value types are non-nullable by default, opt into `T?`).
Eiffel's two-symbol `?`/`!` scheme is the most explicit of the three,
letting either direction be stated directly rather than leaving one
direction as an unmarked default. Haskell targets the identical underlying
failure mode and reaches a cheaper fix by solving it one level up: rather
than add syntax to mark absence on existing types, it makes "a type that
can also be absent" an ordinary value of an ordinary algebraic data type
(`Maybe a`), paying for the general sum-type mechanism exactly once and
getting nullability as one unremarkable consequence of it, rather than a
fourth bespoke mechanism solving the same problem a fourth separate way.

**The union/variant safety gradient (COBOL, C, Pascal, Ada).** This tracks
each language's era and general safety philosophy directly. COBOL's
`REDEFINES` reflects 1959 batch data-processing's core concern — the
exact physical layout of a fixed-width record, often shared across
programs and even hardware generations — treating "reinterpret this
storage" as an ordinary, low-ceremony declarative tool for working with
externally-imposed record formats, not a language feature that needed any
safety apparatus wrapped around it. C's untagged
`union` reflects its systems-programming, close-to-the-machine design —
a union is essentially "reinterpret these bytes as a different type,"
with safety entirely the programmer's responsibility, consistent with C's
general stance of trusting the programmer over restricting them. Pascal
and Ada both wanted the safety of knowing which variant is active, and
Ada — true to its now-familiar pattern throughout this analysis — went
further than Pascal by tying the variant to a genuinely typed,
declared discriminant field rather than an arbitrary expression, making
the association checkable rather than merely conventional. Haskell goes
further again, for a reason specific to its own design history: algebraic
data types (and pattern matching against them) were a foundational feature
of the ML lineage Haskell draws its data-declaration syntax from, not a
safety feature retrofitted onto an existing record/union mechanism the way
Ada's discriminant was. Because construction and inspection were designed
together as two views of the same constructor-tagged value from the
start, there was never a separate, looser "union" concept in the language
for the safer, constructor-tagged form to be added alongside — this is the
only form the language ever had.

## Summary of cross-cutting patterns

- **The mandatory/optional/absent split for type annotations lines up with
  "how the language wants users to trade correctness for
  speed of iteration"** — the same underlying design stance already found
  driving modifier granularity (`function-analysis.md` §8) and constructor
  syntax (`classes-and-inheritance-analysis.md` §5): languages willing to
  push more into the grammar tend to do so consistently across every
  feature area, and languages that favor convention over syntax do the
  same.
- **Ada is, once again, the language that consistently goes furthest
  toward catching errors statically** — its generic system, its
  discriminated variant records, and its earlier-documented parameter
  modes (`function-analysis.md` §3) are all instances of the same
  underlying design commitment showing up in unrelated grammar
  productions.
- **Java and C#'s independent, opposite solutions to generic variance are
  the clearest single illustration in this whole set of analyses that two
  languages can solve the identical design problem with genuinely
  different, well-reasoned answers** — neither use-site nor
  declaration-site variance is strictly better; they represent different
  bets about who should bear the cognitive cost of deciding variance (the
  generic type's author, once, or every caller, every time).
- **Type inference (`var`) and dynamic typing produce visually similar
  "no type written" syntax but are not the same feature**, and conflating
  them is an easy category error — the corpus now offers a clean four-way
  contrast (Python: no type system at that slot at all; VB6: a real
  static/dynamic fallback choice; C#: sugar over an unchanged static
  system; Haskell: a fully separate, fully optional declaration that, when
  omitted entirely, still leaves inference with no placeholder token
  needed at all) that's worth keeping distinct.
- **Haskell is this analysis's second confirmation (after
  `function-analysis.md`) that one uniform mechanism can quietly replace
  several features other languages treat as separate grammar
  constructs** — plain juxtaposition does the job of both generic-type
  application and function application (§2), and one general sum-type
  mechanism (`data`) does the job that nullable types, union/variant
  types, and (per `function-analysis.md` §4) optional parameters are each
  given their own bespoke syntax for everywhere else in the corpus. The
  pattern is the same each time: a feature that looks absent in a
  feature-by-feature table usually isn't absent at all, it's been
  generalized into a different, more general feature the table doesn't
  have its own row for.
