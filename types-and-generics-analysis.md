# Types, generics, and null-safety across `grammar-zoo-flavie-adapted`

An analysis of type-annotation requirements, generics/templates, nullable
types, and variant/union types across the languages in
`grammar-zoo-flavie-adapted`, based on the actual productions in
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

**Mandatory on ordinary variable and field declarations:** C99, C++98,
C#, Java 5, Ada, Pascal/Delphi, Modula-3, and Eiffel all put a type slot
directly into the declaration production itself — e.g.
`var_decl ::= identlist colon_type [hint_directive] [var_init] ";" NL`
(Pascal), `Entity_declaration_group ::= Identifier_list Type_mark`
(Eiffel), `object_declaration ::= defining_identifier_list ":" ["aliased"]
["constant"] subtype_indication [":=" expression] ";" | ...` (Ada).

A few narrow, grammar-visible exceptions are worth recording rather than
glossing over:

- **Ada** has a second, typeless declaration form for named numbers:
  `number_declaration ::= defining_identifier_list ":" "constant" ":="
  static_expression ";"` (`Pi : constant := 3.14159;`).
- **Pascal/Delphi** makes the parameter type optional:
  `parameter ::= sep*(id, ",") [parameter_type]`, which is how Delphi's
  untyped `var`/`const`/`out` parameters are written.
- **C99**'s `declaration-specifiers` can be satisfied by a
  `storage-class-specifier` alone, so `static x;` is derivable from the
  CFG; it's the standard's prose constraints (not the grammar) that
  require at least one type specifier since C99 dropped implicit `int`.
- **Modula-3**'s captured `VariableDecl ::= IDList ":" Type "&" ":=" Expr`
  (and the same shape in `Formal` and `Field`) contains a literal `"&"`
  terminal. That is an extraction artifact: in the Modula-3 report's own
  EBNF, `A & B` is meta-notation for "A or B or both," so per the report
  (general language knowledge) `VAR x := 5;` is legal with the type
  inferred from the initializer. Read literally, the grammar here makes
  the type mandatory; read as intended, Modula-3 belongs closer to the
  inference discussion below.

**Entirely absent — no type-annotation production exists anywhere in the
grammar:**

```
python:     expr_stmt ::= (testlist (is_expr)*) | (testlist augassign assign_value)
js:         js_variable_description ::= id [js_variable_initialization]
lua:        stat ::= ... | "local" namelist ["=" explist]
            parlist ::= (namelist ["," "..."]) | "..."
smalltalk:  temps ::= PIPE (ws IDENTIFIER)* ws PIPE
```

This is a stronger claim than "the type was omitted" — there is no
grammatical slot a type could occupy in any of these productions, or
anywhere else in these four grammars. Python, this JS grammar, Lua 5.2,
and this Smalltalk grammar are dynamically typed by grammar construction,
not just by convention. (The Redline Smalltalk grammar covers only
method/statement bodies — temporaries, assignments, message sends, blocks
— not class definitions, so instance-variable declarations aren't in it
at all; but the temporaries and block parameters it does have are bare
identifiers.)

**PHP is almost, but not quite, in the same camp:**

```
php:  InstanceVariable ::= TVariable [EqualsStaticScalar]
      Param            ::= ([TypeHint] ["&"] TVariable [EqualsStaticScalar])
                         | ("const" TVariable)
      TypeHint         ::= id
```

Variables and properties have no type slot at all, but function and
method parameters accept an optional `TypeHint` — PHP 5's class/interface
type hints, which (general language knowledge) are checked at runtime when
the function is called, not at compile time. Omitting it doesn't select
any fallback type; the parameter is simply unchecked. So PHP is
"absent everywhere except an optional, runtime-checked guard on
parameters."

**Optional, with a defined static fallback type — a genuine third
category:**

```
basic:    single_var_description ::= id [initial_value] [as_type]
dart:     declaredIdentifier ::= (FINAL [type] identifier) | (VAR identifier)
                               | (type identifier)
          simpleFormalParameter ::= declaredIdentifier | identifier
fortran:  ImplicitStmt ::= LblDef "implicit" ImplicitSpecList EOS
                         | LblDef "implicit" "none" EOS
          ImplicitSpec ::= (TypeSpec ImplicitRanges) | (TypeSpec "(" ImplicitRanges ")")
```

VB6's `[as_type]` is genuinely optional, but omitting it doesn't make the
variable typeless: it falls back to VB6's `Variant`, a real type with its
own (dynamically-behaving) semantics. This is neither the Python/JS/Lua
camp (no annotation possible) nor the mandatory-everywhere camp
(annotation always required) — it's "statically typed by default, with an
explicit, grammatically visible opt-out into dynamic behavior."

Dart (1.x, which this grammar reflects) has the same shape: a declaration
can carry a `type`, or just `var`/`final`, and a parameter can be a bare
`identifier`. Per the language specification (general language
knowledge), an omitted type means `dynamic`, Dart's named "anything goes"
type — the direct analogue of VB6's `Variant`.

Fortran-90 reaches this category by a different route. Its
`TypeDeclarationStmt ::= LblDef TypeSpec [AttrSpecSeq] "::" EntityDeclList
EOS` does require a `TypeSpec`, but nothing requires a variable to appear
in one: `DimensionStmt`, `CommonStmt`, and plain first use
all introduce variables without a type, and the grammar's `ImplicitStmt`
exists precisely to configure the fallback. Per the standard (general
language knowledge), the default rule types undeclared names by first
letter (`I`–`N` integer, otherwise real), `implicit <type> (<ranges>)`
re-maps those letter ranges, and `implicit none` switches the fallback
off — effectively making declarations mandatory, on request. Unlike VB6
and Dart, Fortran's fallback is a fully static concrete type, not a
dynamic catch-all.

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

Swift sits in this same inference camp, but splits it by declaration
kind:

```
swift:  constant_declaration ::= [attributes] [declaration_specifiers] "let"
                                 pattern_initializer_list
        pattern_initializer  ::= pattern [initializer]
        pattern              ::= (identifier_pattern [type_annotation]) | ...
        type_annotation      ::= ":" [attributes] type
        parameter            ::= ([inout] [let] ["#"] parameter_name [local_parameter_name]
                                  type_annotation [default_argument_clause]) | ...
```

For `let`/`var` bindings the `type_annotation` is optional and, per the
language (general knowledge), the compiler infers a fixed static type
from the initializer — C#'s `var` semantics, except that Swift needs no
separate placeholder token, because the `let`/`var` keyword is there
anyway whether or not a type follows. For function parameters,
`type_annotation` is not bracketed: mandatory. So Swift is
"inference for local bindings, mandatory annotation at function
boundaries," a split this grammar makes visible directly.

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

**Erlang shares Haskell's detached shape, but not its static guarantee.**

```
erlang: form      ::= (attribute | function | ruleClauses) "."
        attribute ::= ("-" tokAtom attrVal) | ("-" tokAtom typedAttrVal)
                    | ("-" tokAtom "(" typedAttrVal ")") | (AttrName typeSpec)
        AttrName  ::= "-" ("spec" | "callback")
        typeSpec  ::= (specFun typeSigs) | ("(" specFun typeSigs ")")
        typeSig   ::= funType ["when" typeGuards]
        typedExpr ::= expr "::" topType
```

A `-spec` is its own top-level `form`, separate from the `function` form
it describes — exactly Haskell's arrangement of signature and binding as
sibling declarations. Type aliases (`-type t() :: ...`) have no dedicated
keyword at all: they parse through the generic `"-" tokAtom typedAttrVal`
attribute alternative, with `type` just being the atom, and record fields
can carry `:: topType` via `typedRecordFields`. Function clauses and
variable bindings themselves have no type slot anywhere. The difference
from Haskell is one the grammar can't show: per the language (general
knowledge), the Erlang compiler doesn't type-check against specs; they
are consumed by the separate Dialyzer tool, which only reports
definite contradictions. So Erlang is a dynamically typed language with a
complete, optional, detached annotation language bolted on beside it —
with a type sublanguage (`topType`, `type200` … `type500`, `funType`,
`binaryType`) as elaborate as many statically typed languages' while
being, semantically, advisory.

**A fifth category COBOL adds: an open-ended, genuinely optional *clause
list*, not a single type slot at all.**

```
cobol: data_description_entry_format_i ::= level_number [data_name | "FILLER"]
                                            [redefines_clause] data_clauses ["."]
       data_clauses ::= (blank_when_zero_clause | ... | occurs_clause | picture_clause
                        | sign_clause | ... | usage_clause | value_clause_format_ii
                        | renames_clause)*
```

`data_clauses` is zero-or-more: an accumulating, freely-ordered set of
independent descriptors, with `PICTURE` (the closest thing COBOL has to
"a type") sitting as just one more optional clause among `OCCURS` (array
dimensioning), `SIGN`, `USAGE`, `VALUE`, and others. That is a genuinely
different shape from every other category here: not one mandatory type
slot (C99), not one dynamically-typed absence (Python), not VB6's
single optional `as_type` slot with one named fallback, not Haskell's or
Erlang's separate signature declaration. The empty case is also worth
spelling out, since it's a clean example of this document's opening
caveat: a COBOL data item with no `PICTURE` and no `USAGE` clause isn't
given a silent default elementary type at all — it becomes a *group
item*, a pure structural container whose "type" is just the
concatenation of whatever elementary items are declared under it at the
next level number. The CFG shows that the clause list *can* be empty, but
what that emptiness actually denotes is semantics, invisible here by
construction.

## 2. Generics and templates: real divergence in sophistication and philosophy

| Language | Mechanism |
|---|---|
| Ada 2005 | `generic_formal_parameter_declaration ::= formal_object_declaration \| formal_type_declaration \| formal_subprogram_declaration \| formal_package_declaration` — parameterizable not just by type, but by a value, an entire subprogram, or an entire package. Requires a separate, explicit, *named* instantiation step before use: `generic_instantiation ::= ("package" defining_program_unit_name "is" "new" generic_package_name [generic_actual_part] ";") \| ...` (with parallel `procedure`/`function` alternatives) — a two-step process, unlike the inline `Foo<T>` of the C++ family. A `formal_package_declaration` (`"with" "package" defining_identifier "is" "new" generic_package_name formal_package_actual_part ";"`) takes an *instance* of another generic package as a parameter |
| C++98 | `type-parameter ::= ("class" [identifier]) \| ("class" [identifier] "=" type-id) \| ("typename" [identifier]) \| ... \| ("template" "<" template-parameter-list ">" "class" [identifier]) \| ...` — each form also has a defaulted (`= ...`) variant, and the `template` form is a **template-template parameter**: a template parameterized by another, *uninstantiated* template, recursively. `template-parameter ::= type-parameter \| parameter-declaration` also permits plain non-type (value) parameters. The only grammar in the corpus where a generic can take another not-yet-instantiated generic as a parameter (Ada's formal packages take an *instance*) |
| C# 4.0 | `type-parameter-constraints-clause ::= "where" type-parameter ":" type-parameter-constraints`, combinable across `primary-constraint`, `secondary-constraints`, and `constructor-constraint` — multiple simultaneous constraints per parameter. Also `variant-type-parameter-list`: **declaration-site variance** (`in`/`out`), fixed once by the generic type's author |
| Java 5 | `typeParameter ::= Identifier [("extends" typeBound)]`, with `typeBound ::= type ("&" type)*` — one `extends` clause, but that clause can name several intersected bounds (`<T extends Number & Comparable<T>>`). Variance is handled by an entirely different mechanism: `typeArgument ::= type \| "?" [("extends" \| "super") type]` — **use-site variance**, where the *caller* decides `List<? extends Number>` at each point of use, not the type's author |
| Eiffel | `Formal_generics ::= "[" Formal_generic_list "]"` — square brackets, not angle brackets: `LIST [INTEGER]` rather than `List<Integer>`. `Formal_generic ::= ["frozen"] Formal_generic_name [Constraint]`, with `Formal_generic_name ::= ["?"] Identifier` |
| Dart | `typeParameter ::= identifier [(EXTENDS type)]` — the same simple single-bound shape as Java, no variance mechanism captured |
| Modula-3 | **no generics production anywhere in the grammar**: `Compilation ::= ["UNSAFE"] (Interface \| Module)`, with no `GENERIC` alternative. This *is* a coverage gap at the compilation-unit level rather than an absence from the language: per the Modula-3 report (general language knowledge), generics are whole `GENERIC INTERFACE`/`GENERIC MODULE` units, instantiated by a separate named unit (`INTERFACE IntList = List(Integer) END IntList.`) — a two-step, named instantiation much like Ada's, just at the granularity of whole compilation units |
| Haskell | `simpletype ::= (tycon simpletype_1_1) \| tycon`, `simpletype_1_1 ::= (tyvar simpletype_1_1) \| tyvar` — no brackets of any kind. `data Tree a = ...` applies the type variable `a` to `Tree` by plain juxtaposition, the exact same mechanism `function-analysis.md` §2/§7 already documents for *value*-level application (`fexp ::= (fexp aexp) \| aexp`) and parameter lists. Ordinary type application reuses it too: `btype ::= (btype atype) \| atype` is what makes `Maybe Int` or `Either String Int` well-formed, with no angle brackets, square brackets, or commas anywhere in the production |
| Swift | `generic_parameter_clause ::= "<" generic_parameter_list [requirement_clause] ">"`, `generic_parameter ::= type_name \| (type_name ":" type_identifier) \| (type_name ":" protocol_composition_type)` — a single conformance per parameter inline, plus an optional `where` clause *inside* the angle brackets: `requirement ::= conformance_requirement \| same_type_requirement`, the latter `type_identifier "==" type_identifier`, the only same-type ("these two type parameters must be equal") constraint in the corpus. Use sites: `generic_argument_clause ::= "<" generic_argument_list ">"`. No variance mechanism captured |
| Erlang | Only inside the separate `-spec`/`-type` annotation language (§1): a type variable is a bare `tokVar`, applied with parentheses, `type ::= ... \| (tokAtom "(" topTypes ")") \| ...` (`list(T)`, `dict(K, V)`), and bounded by `typeSig ::= funType ["when" typeGuards]`, `typeGuard ::= (tokAtom "(" topTypes ")") \| (tokVar "::" topType)`. Advisory only (Dialyzer), as with every Erlang type |

**No generics at all in the grammar:** C99, Pascal/Delphi (Delphi
generics arrived in Delphi 2009; this grammar is Delphi 2006), Fortran-90,
VB6, COBOL, Python, this JS grammar, PHP, Lua, and Smalltalk — the last
five being dynamically typed, where the question doesn't arise.
Fortran-90's `GenericSpec`/`GenericName` (`InterfaceStmt ::= LblDef
"interface" GenericName EOS | ...`) are a false friend: a Fortran
"generic interface" is one name overloaded over several specific
procedures, not a parameterized type or procedure.

Haskell is the one language in this table with no dedicated generics
syntax at all, for the same reason it has no dedicated call syntax in
`function-analysis.md`: applying a type constructor to a type argument and
applying a function to a value argument are, grammatically, not two
features — they're the same juxtaposition idiom showing up at two
different syntactic levels (types and values) of one uniform language
design. No other language in this corpus shares that property; everywhere
else, "declare a generic parameter" and "call a function" are handled by
visibly different grammar machinery. Erlang comes closest: its type
application `tokAtom "(" topTypes ")"` (`list(T)`) is written exactly
like a function call — but it's a separate production in a separate
annotation sublanguage that merely imitates the call notation, not one
shared mechanism serving both levels.

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
bracketed `Constraint` do. It's a third distinct attachment point for the
same general idea (bound a type parameter to an interface/contract it
must satisfy), alongside the parameter-annotation style (Java, Dart,
Eiffel, Swift's inline `T: P`) and the separate-clause style (C#'s
`where`, Swift's in-bracket `where`) in the table above. Erlang's
`"when" typeGuards` is its nearest relative — also a clause on the whole
signature rather than on one parameter — but trailing the type instead of
leading it (`-spec f(T) -> T when T :: atom().`). One nuance invisible at this level of the
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

## 3. Nullable/optional types — only four languages have anything at all

- **C#**: `nullable-type ::= non-nullable-value-type "?"` (`int?`), plus a
  null-coalescing operator, `null-coalescing-expression ::=
  conditional-or-expression | (conditional-or-expression "??"
  null-coalescing-expression)`. Scoped
  specifically to *value* types (structs/primitives, non-nullable by
  default) — C# 4.0 predates non-nullable *reference* types, added later
  in C# 8.
- **Ada**: `null_exclusion ::= "not" "null"`, applied to access (pointer)
  types — `not null access Integer`. Ada's default is that access types
  *can* be null; the language requires an explicit opt-in to
  non-nullability.
- **Eiffel**: `Attachment_mark ::= "?" | "!"` on `Class_type`. `!` marks a
  type "attached" (guaranteed non-void); `?` marks it "detachable" (may be
  void). Eiffel is the only one of the four offering an explicit
  *two-way* marker — opting into either nullable or non-nullable
  explicitly — rather than one fixed default with a single opt-out
  direction, as in Ada, C#, or Swift.
- **Swift**: `type ::= ... | (type "?") | (type "!") | ...` — a postfix
  `?` (optional) or `!` (implicitly unwrapped optional) on *any* type,
  reference or value alike, plus matching expression-level operators:
  `expression ::= ... | (expression "!") | (expression "?")` (force-unwrap
  and optional chaining) and `type_casting_operator ::= ("is" type) |
  ("as" ["?"] type)` (a conditional cast that yields an optional). Unlike
  Eiffel's pair, both of Swift's marks mean "may be absent"; they differ
  only in whether the compiler (per the language, general knowledge)
  makes you unwrap explicitly (`T?`) or unwraps implicitly and traps at
  runtime on absence (`T!`). The unmarked default is non-optional for
  every type — the reverse of Ada's access types, and wider in scope than
  C# 4.0's value-types-only `T?`. This grammar has no `nil` literal
  (`literal ::= integer_literal | Floating_point_literal |
  String_literal`) and no `??` token; `??` would go through the
  user-definable `binary_operator ::= operator`.

No other language in the corpus (C99, C++98, Java 5, Dart, Python, PHP,
this JS grammar, Pascal/Delphi, Fortran-90, Modula-3, VB6, COBOL, Erlang,
Lua, Smalltalk) has any comparable mechanism at these grammar versions;
Haskell, the remaining one, is discussed next. Several of them have a
null *value* — `"nil"` in Lua's `exp`, Pascal's `atom_expr`, and
Smalltalk's `RESERVED_WORD`; `"null"` in Dart, JS, and PHP literals and in
Ada's `primary`; `"nothing"` in VB6's `set_object_expn` — but nothing in
the type grammar to say which variables may hold it. Erlang has neither:
no null value in the grammar, and (per general knowledge) absence is
conventionally an ordinary atom such as `undefined`.

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

Swift is the instructive in-between case. Its grammar has both a
dedicated `type "?"` production *and* a general sum-type mechanism
(`union_style_enum`, §4) able to express `Maybe`-style absence on its
own; per the language (general knowledge), `T?` is in fact sugar for the
standard library's `Optional<T>` enum. The dedicated syntax is there for
ergonomics (postfix `?`, `!`, chaining), not because the type system
needed it — a Haskell-style design underneath, with a C#-style surface
on top.

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
- **Pascal/Delphi**: `variant_section ::= "case" [id_colon] type_spec "of"
  (record_variant)+`, `record_variant ::= (expr)+ colon "("
  visibility_default ")" [";"] NL` — a case-labeled variant part whose
  arms are each labeled with constant values of the selector's type.
  Safer than C's union: the grammar's own shape associates each variant
  with a specific tag value. But note the `[id_colon]`: the tag *field*
  is optional, so `case Integer of ...` declares labeled variants with no
  stored tag at all — at runtime as unchecked as a C union.
- **Ada**: `variant_part ::= "case" discriminant_direct_name "is"
  (variant)+ "end" "case" ";"` — ties the variant directly to a proper,
  typed `discriminant_direct_name`, itself a declared field in the
  record's `discriminant_part`. The most structurally rigorous of the
  four above.

- **Haskell**: `constrs ::= (constr constrs_1_1) | constr`, with
  `constrs_1_1` supplying the `"|" constr` repetitions, each `constr` a
  named constructor with its own argument types (`(con constr_1_1) | con
  | ... | (con "{" fielddecls "}")`, where `constr_1_1` is a sequence of
  `[strictness] atype`). The discriminant here isn't a separate field at all —
  it's the constructor name itself, which must be supplied at every
  construction site and named again at every pattern-match site
  (`pat10n ::= apat | (gcon apat funlhs_2_1) | (gcon apat)`, `alt ::=
  (pat "->" exp wheredecls) | ...`). There is no way to produce a `Tree` value without
  committing to `Leaf` or `Node` up front, and no way to inspect one
  without naming which constructor is expected — tag and data are the same
  syntactic act, at both ends, rather than a tag the grammar lets you
  attach loosely (Pascal) or declare once and forget to check (Ada, in
  principle, if a case arm goes unhandled). The grammar itself can't show
  exhaustiveness-checking, but the structural fact that reading a field
  always goes through naming a specific constructor is what makes
  exhaustiveness checkable by a compiler at all.

- **Swift**: `union_style_enum ::= enum_name [generic_parameter_clause]
  "{" [union_style_enum_members] "}"`, `union_style_enum_case ::=
  enum_case_name [tuple_type]` — each case optionally carries its own
  tuple of payload types — read back through `enum_case_pattern ::=
  [type_identifier] "." enum_case_name [tuple_pattern]`. Structurally the
  same arrangement as Haskell's: the case name is the tag, supplied at
  construction and named again at every match. (The grammar's own
  nonterminal name, `union_style_enum`, distinguishes it from the C-style
  `raw_value_style_enum`.) Swift is the only other language in the corpus
  with a constructor-tagged sum type in its grammar.

Three more grammars have something in this territory without adding a
new point to the gradient: **C++98** inherits C's untagged union as a
`class-key ::= "class" | "struct" | "union"`; **Fortran-90**'s
`EquivalenceStmt ::= LblDef "equivalence" EquivalenceSetList EOS`, where
each `EquivalenceSet ::= "(" EquivalenceObject "," EquivalenceObjectList
")"` makes a group of variables share storage, is COBOL-style storage
aliasing (though it at least gathers a set together in one statement);
and **Erlang**'s annotation language has true union types,
`topType100 ::= type200 ["|" topType100]` (`-type r() :: ok | {error,
term()}.`), describing the conventional tagged-tuple values, but as with
all Erlang types (§1) they are advisory, not enforced by the compiler.

This is a five-point safety gradient — pairwise storage aliasing with no
grouping or discriminant at all (COBOL), untagged but at least grouped
(C), tagged by case labels with an optional tag field (Pascal), tagged by a real typed discriminant
field (Ada), tagged by the constructor name itself at both construction
and read sites (Haskell, and Swift's `union_style_enum`) — visible
entirely in how much grammatical structure each language wraps around the
same underlying "one of several possible shapes" idea.

## Why each design was chosen

**Mandatory type annotations (the largest single group).** All eight
languages in this category were designed with compile-time verification as a primary goal —
catching mismatched types, missing conversions, and misused values before
a program ever runs, at some cost in declaration verbosity.

**No type-annotation syntax at all (Python, this JS grammar, Lua,
Smalltalk, and PHP apart from its parameter hints).** Python, JS, Lua, and
PHP prioritize rapid, exploratory development and runtime flexibility over
compile-time guarantees, consistent with their origins as scripting,
embedding, and glue languages where the cost of a type error surfacing at
runtime was judged less important than minimizing the friction of writing
and changing code quickly. PHP 5's optional parameter type hints are the
first step of the later retrofit of gradual typing onto such a language:
a check at the one boundary (function entry) where a wrong argument is
cheapest to diagnose. Smalltalk's reason is different and older: in a
pure message-passing language, what matters about an object is which
messages it answers, decided at send time by late binding, so a declared
static type would describe something the language deliberately doesn't
fix in advance.

**Erlang's detached, advisory `-spec` language.** Erlang was designed
(at Ericsson, for telecom switching) with fault tolerance through
"let it crash" process isolation rather than static proof as its safety
story, so it was born dynamically typed; the spec/type annotation
language was added much later alongside the Dialyzer tool as optional
documentation-plus-analysis that could be adopted incrementally across
large existing codebases without changing what any program means —
which is exactly why it lives in separate attribute forms the compiler
can ignore.

**VB6's optional annotation with a Variant fallback.** This reflects VB6's
target audience directly: it was designed to let non-specialist and
beginner programmers get something running immediately (skip the type,
get a working Variant-typed variable) while still giving more careful
programmers the option to declare precise types where performance or
correctness mattered — an explicit two-tier design rather than a single
uniform stance. Dart 1.x's optional types with a `dynamic` fallback were
an explicit bet on the same two-tier idea for web developers coming from
JavaScript: start untyped, add types as a program grows. Fortran's
implicit typing is much older and has a different origin — it dates to
the first Fortran's goal of letting scientists write formulas with almost
no declarations, using the mathematical convention of `i`–`n` for integer
indices — and `implicit none` was the later, opt-in recognition that
silently typed misspellings are a real source of bugs.

**Swift's split between inferred local bindings and mandatory parameter
types.** Function signatures are the boundary other code (and separate
compilation) depends on, so Swift makes them explicit, while letting
local `let`/`var` bindings rely on inference to keep everyday code as
terse as a scripting language's — the same readability motive as C#'s
`var`, applied by default rather than by opt-in token.

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

**Nullable/optional-type mechanisms (C#, Ada, Eiffel, Swift) all trace to
the same motivation: null-pointer errors are a well-documented, extremely
common class of runtime failure**, and each of the four built a different
piece of syntax to let the type system catch a mistaken null (or a
mistaken assumption of non-null) before it manifests as a runtime crash.
Ada and C# each fixed one default and let the programmer opt out of it
in one direction (Ada: access types are nullable by default, opt into
`not null`; C#: value types are non-nullable by default, opt into `T?`).
Eiffel's two-symbol `?`/`!` scheme is the most explicit of the four,
letting either direction be stated directly rather than leaving one
direction as an unmarked default. Swift, the youngest, took the strictest
default — no type of any kind admits absence unless marked — because it
was designed after decades of evidence about null errors, and had the
freedom to make that choice without C#'s or Ada's backward-compatibility
constraints (only Objective-C interoperability, which is what the
implicitly-unwrapped `T!` exists to smooth over). Haskell targets the identical underlying
failure mode and reaches a cheaper fix by solving it one level up: rather
than add syntax to mark absence on existing types, it makes "a type that
can also be absent" an ordinary value of an ordinary algebraic data type
(`Maybe a`), paying for the general sum-type mechanism exactly once and
getting nullability as one unremarkable consequence of it, rather than a
fourth bespoke mechanism solving the same problem a fourth separate way.

**The union/variant safety gradient (COBOL, C, Pascal, Ada, Haskell,
Swift).** This tracks
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
declared discriminant field rather than an optional tag Pascal lets you
leave out entirely, making the association checkable rather than merely
conventional. Haskell goes
further again, for a reason specific to its own design history: algebraic
data types (and pattern matching against them) were a foundational feature
of the ML lineage Haskell draws its data-declaration syntax from, not a
safety feature retrofitted onto an existing record/union mechanism the way
Ada's discriminant was. Because construction and inspection were designed
together as two views of the same constructor-tagged value from the
start, there was never a separate, looser "union" concept in the language
for the safer, constructor-tagged form to be added alongside — this is the
only form the language ever had. Swift's `union_style_enum` imports the
same ML-family idea into a C-family surface syntax (`enum`, `case`,
braces), consistent with its general strategy of offering functional-
language safety features in a form familiar to C and Objective-C
programmers.

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
  them is an easy category error — the corpus now offers a clean six-way
  contrast (Python/Lua/Smalltalk: no type system at that slot at all;
  VB6/Dart: a real static/dynamic fallback choice; Fortran: a static
  fallback chosen by the name's first letter; C#: sugar over an unchanged
  static system; Swift: the same inference with no placeholder token
  beyond `let`/`var`; Haskell: a fully separate, fully optional
  declaration that, when omitted entirely, still leaves inference with no
  placeholder token needed at all) that's worth keeping distinct — and
  Erlang shows that even Haskell's detached-signature *shape* doesn't
  imply static checking, since its identically detached `-spec` is
  advisory.
- **Haskell is this analysis's second confirmation (after
  `function-analysis.md`) that one uniform mechanism can quietly replace
  several features other languages treat as separate grammar
  constructs** — plain juxtaposition does the job of both generic-type
  application and function application (§2), and one general sum-type
  mechanism (`data`) does the job that nullable types, union/variant
  types, and (per `function-analysis.md` §4) optional parameters are each
  given their own bespoke syntax for elsewhere in the corpus (Swift,
  which has a general sum type *and* a dedicated `T?`, being the hybrid
  case). The
  pattern is the same each time: a feature that looks absent in a
  feature-by-feature table usually isn't absent at all, it's been
  generalized into a different, more general feature the table doesn't
  have its own row for.

## References

The grammar claims in this document are checked against the productions in
`normalized-ebnf-flavie-adapted/` and need no outside source. The design-history
remarks marked as general knowledge are not cited claim by claim; the works
below are the background reading for them. HOPL-II and HOPL-III are the
proceedings of the second (1993) and third (2007) ACM SIGPLAN History of
Programming Languages conferences.

**Corpus**

- Zaytsev, V. (2015). Grammar Zoo: A corpus of experimental grammarware. *Science of Computer Programming*, 98, 28–51. https://doi.org/10.1016/j.scico.2014.07.010 — the source corpus every grammar here comes from.
- Lämmel, R., & Verhoef, C. (2001). Semi-automatic grammar recovery. *Software: Practice and Experience*, 31(15), 1395–1438. https://doi.org/10.1002/spe.423 — the recovery of the VS COBOL II grammar used as this corpus's COBOL (`cobol-vscobolii-lammel-gdk`).

**General**

- Sebesta, R. W. (2019). *Concepts of Programming Languages* (12th ed.). Pearson. — textbook comparison of the same construct-by-construct design choices across many languages.
- Hoare, C. A. R. (1973). *Hints on Programming Language Design* (Stanford AI Lab Memo AIM-224 / STAN-CS-73-403). Stanford University, Computer Science Department. — design-rationale background.

**Language histories**

- Stroustrup, B. (1993). A history of C++: 1979–1991. In *HOPL-II* (pp. 271–297). ACM. https://doi.org/10.1145/154766.155375
- Wirth, N. (2007). Modula-2 and Oberon. In *HOPL-III*. ACM. https://doi.org/10.1145/1238844.1238847
- Hudak, P., Hughes, J., Peyton Jones, S., & Wadler, P. (2007). A history of Haskell: Being lazy with class. In *HOPL-III*. ACM. https://doi.org/10.1145/1238844.1238856
- Armstrong, J. (2007). A history of Erlang. In *HOPL-III*. ACM. https://doi.org/10.1145/1238844.1238850
