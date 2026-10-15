# Functions across `grammar-zoo-flavie`: definitions, calls, and parameters

An analysis of how each of the 14 languages with real function/procedure
syntax (excluding the three data-schema grammars — `cobol-bruneliere`,
`ml-ocaml-amble`, `pl1-bruneliere` — which have no such production) handles
function definition, invocation, parameter passing, and return values,
based on the actual productions in `normalized-ebnf-flavie-adapted/`.

## 1. Procedure vs. function: one keyword or two?

Languages split cleanly into those that treat "returns a value" as a
different *grammatical category* of thing, and those that treat it as an
incidental detail of one unified category.

**Two distinct concepts, two keywords**

| Language | Evidence |
|---|---|
| Ada | `subprogram_specification ::= procedure_specification \| function_specification` — separate productions, separate keywords `"procedure"`/`"function"` |
| Fortran-90 | `FunctionSubprogram` and `SubroutineSubprogram` are entirely separate productions with separate `End...Stmt` closers |
| Pascal/Delphi | `procedure_keyword ::= "function" \| "procedure" \| "constructor" \| "destructor"` — one production, but the keyword itself still carries the distinction (and constructors/destructors are folded into the *same* choice, treating them as "just another kind of procedure") |
| Basic (VB6) | `sub_or_function ::= "sub" \| "function"` — same pattern as Pascal: one production, keyword-level distinction |

**One concept, return-value is just a type annotation**

| Language | Evidence |
|---|---|
| Modula-3 | `ProcedureHead ::= "PROCEDURE" Ident Signature`, and `Signature ::= "(" Formals ")" [":" Type] [...]` — the `: Type` is bracketed (optional) directly on the *same* production. There is no `FUNCTION` keyword anywhere in the grammar. |
| C99/C++98/C# | `function-definition`/`method-declaration` always exists once; `void` is a type like any other, not a grammatical fork |
| Java, JS, Python, PHP, Dart | same — a single definition production, "no return value" expressed at the type/body level, not the grammar level |

This is a real lineage signal: every language on the "two keywords" side
(Ada, Fortran, Pascal, Basic) predates or was contemporaneous with the
early structured-programming era and inherited the distinction from Algol
60's own `procedure` (Algol only had procedures; a "function" was a
procedure whose body assigns to its own name). Modula-3 — designed by
Wirth's collaborators specifically as a cleanup of Pascal-family clutter —
is the one member of that lineage that deliberately *dropped* the
distinction. Every other language in the corpus (all younger, and outside
that direct lineage) never had it to drop.

## 2. Function calls: a dedicated node, or folded into expression grammar?

Splits almost exactly along "does the language have a separate statement
form for calls used only for their side effect" vs. "a call is just one
more kind of expression."

**Dedicated call production**

| Language | Production |
|---|---|
| Ada | `procedure_call_statement ::= procedure_name ";" \| procedure_prefix actual_parameter_part ";"` — note this is a genuinely distinct rule from `function_call`, because Ada's grammar-level procedure/function split (§1) carries all the way through to call sites |
| Fortran-90 | `CallStmt ::= "call" SubroutineNameUse [( "(" SubroutineArgList ")" )]` — the `call` *keyword* itself is required, unlike everywhere else in the corpus |
| Modula-3 | `CallStmt ::= Expr "(" [Actual, ...] ")"` |
| Basic (VB6) | `call_statement ::= ["call"] reference [subroutine_bracketless_params]` — keyword is *optional*, a vestige of older Basic dialects that required it |
| Eiffel | `Call ::= Object_call | Non_object_call`, further split into `Unqualified_call`/`Explicit_creation_call`/`Non_object_call` — the richest call taxonomy in the corpus, reflecting Eiffel's object-call-centric design (every call is conceptually "send a message to a target") |
| PHP | `CallParams ::= "(" CallParam,* ")"` as its own node, referenced from a general `VariableOrFunctionCall` |

**No dedicated call node — folded into the primary/postfix expression chain**

| Language | Where the call lives |
|---|---|
| C99/C++98 | `postfix-expression ::= postfix-expression "(" [argument-expression-list] ")" | ...` — a call is just one more postfix operator, alongside `[]`, `.`, `->`, `++` |
| C# | `invocation-expression ::= primary-expression "(" [argument-list] ")"`, one alternative of `primary-no-array-creation-expression` |
| Java | folded into `identifierSuffix`/`arguments` off of `primary` |
| Dart | folded into `selector`/`arguments` off of `postfixExpression` |
| Python | `trailer ::= "(" arglist ")" | "[" ... "]" | "." id` — a call is one of three possible *trailers* on an atom, exactly parallel to indexing and attribute access |

The second group is a genuine convergent pattern across otherwise unrelated
lineages (C, Java, Dart, Python) — all of them model "call", "index", and
"member access" as the *same kind of grammatical thing* (a postfix operator
chained onto a primary expression), which is precisely why `f(x)[0].y(z)`
parses uniformly in all of them. The first group (Ada, Fortran, Eiffel, PHP,
Basic) is exactly the same set of languages that also keep a strict
statement/expression distinction elsewhere in their grammars.

## 3. Parameter-passing mode: explicit in the grammar, or left implicit?

A parameter's passing convention (by value vs. by reference) is either a
first-class grammatical annotation on the parameter, or entirely absent
from the syntax (left to semantics/typing rules the BGF-level grammar
doesn't capture).

| Language | Mechanism |
|---|---|
| Ada | `mode ::= ["in"] | ("in" "out") | "out"` — three-way mode is mandatory grammar, directly on `parameter_specification` |
| Modula-3 | `Formal ::= [("VALUE" | "VAR" | "READONLY")] IDList ":" Type ...` — same three-way idea (by-value / by-reference / read-only-reference), inherited straight from Modula-3's Ada-adjacent design lineage |
| Basic (VB6) | `byref_or_byval ::= "byref" | "byval"` — binary choice, appears on `subprogram_argument`, `event_argument`, and `property_argument` alike |
| C# | `parameter-modifier ::= "ref" | "out" | "this"` — binary reference modifiers, plus the C#-specific `this` marking an extension-method receiver |
| C99, C++98, Java, JS, Python, PHP, Dart, Eiffel | **no such production at all** — parameter passing convention isn't expressed in the syntax; it's a fixed, non-negotiable semantic rule of the language (C/Java/JS: always by value, or by reference-to-object for objects; Python: same; PHP has an explicit `&` reference-sigil, see below) |

PHP is a partial exception worth calling out on its own: `Param ::= (
[TypeHint] ["&"] TVariable [EqualsStaticScalar] ) | ...` — the `&` here
*is* a by-reference marker, but it's a lone optional token bolted onto an
otherwise ordinary parameter, not a first-class mode system like Ada's.

Fortran-90 is a second partial exception, structurally unlike all four
above: `IntentStmt ::= "intent" "(" IntentSpec ")" [ColonColon] IntentParList`
and `OptionalStmt ::= "optional" [ColonColon] OptionalParList` exist, but
as their own free-standing declarative *statements* inside the
specification part, naming already-declared dummy arguments by reference —
not as an inline annotation on the parameter list itself the way Ada's
`x : in out Integer` or Basic's `ByRef x` are. Fortran-90 genuinely has
both concepts (mode and optionality); it just can't attach them at the
parameter-list production the way the others do.

The pattern: **only Ada, Modula-3, Basic, and C# make parameter-passing
mode syntactically explicit on the parameter itself**, and three of those
four are again the "two-keyword" structured-programming lineage from §1 —
a language family that consistently treats things other languages leave to
convention as worth spelling out in the grammar itself. C# is the
interesting outlier, reaching for the same idea for entirely different,
much later reasons (interop with unmanaged code, LINQ extension methods).

## 4. Variadic and default parameters

**Variadic (arbitrary-arity) parameters**

| Language | Form |
|---|---|
| C99 | `parameter-type-list ::= parameter-list | parameter-list "," "..."` — trailing literal `...` |
| C++98 | identical `... ` form, plus it's also legal as a parameter list *by itself* with nothing before it |
| Java 5 | `formalParameterDeclsRest ::= ... | "..." variableDeclaratorId` — Java 5's newly-added varargs, deliberately reusing C's `...` spelling for familiarity |
| Python | (from the base grammar, confirmed via `varargslist`) `"*" id` / `"**" id` — single- and double-star forms, for positional- and keyword-variadic respectively; entirely different spelling from the C lineage despite the same purpose |
| PHP (this Cordy grammar) | no variadic form present — `func_get_args()` was the only mechanism at the PHP version this grammar targets |
| C# | `parameter-array ::= [attributes] "params" array-type identifier` — variadic via a keyword (`params`) plus an ordinary array type, not special punctuation |

Three different notations for the same concept — trailing `...` (C
lineage), a leading sigil (Python's `*`/`**`), and a keyword plus an array
type (C#) — is a clean three-way split with no clear convergence.

**Default parameter values**

| Language | Form |
|---|---|
| Ada | `parameter_specification ::= ... [":=" default_expression]` |
| C++98 | `parameter-declaration ::= decl-specifier-seq declarator ["=" assignment-expression] | ...` — present since C++98 itself (corrected from an earlier version of this analysis, which missed it) |
| C# | `fixed-parameter ::= ... [default-argument]` |
| Dart | `defaultFormalParameter ::= normalFormalParameter ["=" constantExpression]` — but only inside `namedFormalParameters` (Dart's bracketed optional-parameter group), not on ordinary positional parameters |
| PHP | `Param ::= ... [EqualsStaticScalar]` |
| Basic (VB6) | `subprogram_argument ::= ["optional"] ... [equals_expn]` — notably requires an explicit `optional` keyword *in addition to* the default value, where every other language treats "has a default" as sufficient by itself to make a parameter optional |
| Modula-3 | grammar has `Formal ::= [mode] IDList ":" Type "&" ":=" ConstExpr` — but the `":=" ConstExpr` is *not* bracketed optional, and the literal `"&"` immediately before it doesn't correspond to any real Modula-3 syntax. The same `"&" ":="` pair also appears verbatim in `VariableDecl`, `Field`, and `Method`, which strongly suggests a bug introduced by the Grammar Zoo's automated "connect" mutation (see `upstream-fixes/README.md`) rather than a real language feature captured correctly — real Modula-3 *does* allow `x: T := default` on formals, so this looks like a corpus defect, not a design choice |
| C99, Java, JS (this grammar), Fortran-90, Eiffel | none |

VB6's `["optional"] ... [equals_expn]` is the one genuine oddity here: it's
the only grammar in the corpus where the optionality and the default value
are two independently-optional grammatical slots rather than one implying
the other (`Optional x, Optional y = 5` and `Optional z` are all
syntactically valid — a default without `Optional` would be, per this
grammar, a parse error even though every other language would treat it as
redundant-but-fine).

## 5. Returning a value: explicit statement vs. implicit convention

This is the sharpest three-way split in the whole analysis.

**Explicit `return` keyword, a real statement production**

Ada (`simple_return_statement`/`extended_return_statement`), C99, C++98,
C#, Java, JS, Dart, PHP, Python, Modula-3, Fortran-90, and VB6 (which
*also* has a bare `return_statement ::= "return"`, with no expression
slot at all — because VB6 uses the mechanism below for the value itself
and `Return` alone only unwinds control) all have a dedicated statement
node containing the literal keyword `return`/`RETURN`.

**No `return` keyword anywhere in the grammar — implicit assign-to-name convention**

- **Eiffel**: there is no `return` production in this grammar at all. A
  function's result is produced by assigning to the identifier `Result`,
  which the grammar wires in as a literal alternative directly inside
  `Local ::= Identifier | "Result"` — `Result` is grammatically indistinguishable
  from an ordinary local variable except for being a reserved spelling.
  Nothing about the grammar marks a function's *last* statement as special;
  the value is whatever `Result` holds when the routine's body finishes.
- **Pascal/Delphi**: same absence — no `return` production exists, and the
  only relevant rule is the fully generic `assign_stm ::= expr ":=" expr`.
  Classic Pascal's convention (assign to the function's own name) and
  Delphi's added `Result :=` are both just ordinary uses of that one
  generic assignment rule; the grammar can't tell a return-value
  assignment from any other assignment.
- **VB6** actually straddles both camps: it has *both* a bare `Return`
  keyword (control-only, no value) *and* the classic Basic convention of
  assigning to the function's own name via the fully generic
  `assignment_statement ::= ["let"] reference "=" expn` — the same
  duplication pattern already seen in VB6's if-statement (§ dangling-else
  analysis) and default-parameter handling above: give the modern explicit
  form *and* keep the old implicit one working side by side.

The implicit-convention languages (Eiffel, Pascal) are a direct
illustration of *why* the explicit-`return` design eventually won almost
everywhere else: a return value that's just "whatever a magic variable
holds at the end" can be silently produced by control flow the reader
didn't expect (an exception handler, a nested block, an early `if`) with no
`return` keyword anywhere nearby to flag it — exactly the kind of
implicit, position-dependent behavior that the explicit-terminator
languages in the dangling-else analysis (Ada, Eiffel itself, Modula-3)
otherwise go out of their way to avoid. Eiffel resolves the ambiguity
elsewhere in its design (routines are short and single-exit by convention,
enforced by style rather than grammar) — it's a case where the same
language makes exactly opposite trade-offs in two different corners of its
own design.

## 6. Anonymous functions / lambdas / closures

| Language | Form | Notable detail |
|---|---|---|
| Python | `lambdef ::= "lambda" [varargslist] ":" test` | body restricted to a single *expression* (`test`), not a full statement block — Python's lambda is deliberately weaker than a `def` |
| C# 4.0 | `lambda-expression ::= anonymous-function-signature "=>" anonymous-function-body`, plus a *separate*, older `anonymous-method-expression ::= "delegate" [signature] block` | C# 4.0 grammar preserves **two** anonymous-function forms side by side — the pre-3.0 `delegate { }` syntax and the newer `=>` lambda — rather than replacing one with the other |
| Dart | `functionExpression` — an unnamed function literal usable as an expression, structurally identical to a named `functionDeclaration` minus the name | |
| JS (this Cordy grammar) | `js_function_expn ::= "function" [id] "(" ... ")" ... "{" ... "}"` | the *same* production optionally takes a name — JS's function-expression and named-function-declaration are one grammar rule apart, differing only in whether `id` is present |
| Eiffel | `Call_agent ::= "agent" Call_agent_body` | Eiffel's "agent" mechanism is closer to a first-class reference to an existing routine (`agent foo`) or a routine literal, not a lambda in the C/Python sense — it's built on the same `Call` grammar as an ordinary call rather than its own expression-body syntax |
| Ada, C99, C++98, Java 5, Fortran, Modula-3, Pascal/Delphi, PHP, VB6, Basic, COBOL, PL/I | **none** | |

The absence list is telling for dating: C++98, Java 5, and this PHP/VB6
grammar all predate their respective languages' actual lambda features
(C++11, Java 8, PHP 5.3, VB.NET's `Function(...)`) — the *grammar version*
captured in this corpus is simply from before each language added the
feature, not evidence the feature never existed. Ada, Fortran, Modula-3,
Pascal, and COBOL genuinely never had function-valued expressions at these
grammar versions, consistent with their era and design goals.

## Summary of cross-cutting patterns

- **The "two structured-programming keywords" cluster (Ada, Fortran-90,
  Pascal, Basic) is the single strongest recurring signal in this whole
  analysis** — it independently predicts three separate findings: a
  separate procedure/function grammatical category (§1), a dedicated
  call-statement node instead of folding calls into expressions (§2), and
  (for Ada/Basic; Modula-3 breaks from Pascal here) explicit
  parameter-passing-mode syntax (§3). These aren't three unrelated design
  choices — they're one underlying stance (make control- and data-flow
  structure explicit and machine-checkable, sacrificing brevity) showing up
  in three different grammar productions.
- **The call-as-postfix-operator convergence (C, Java, Dart, Python)** is
  the cleanest example in this analysis of unrelated lineages arriving at
  the identical grammatical solution independently, because chaining
  `()`/`[]`/`.` uniformly is simply the more composable design once a
  language commits to "everything is an expression."
- **VB6 is the corpus's consistent "keep both" outlier**: bare `Return` +
  name-assignment return, `Optional` keyword + independent default value,
  and (from the dangling-else analysis) both a bracketed `end if` form and
  a C-style compact `if`. Across three unrelated features, VB6's design
  pattern is the same: add the modern/explicit mechanism without ever
  removing the older/implicit one.
- **Feature absence is often a dating artifact, not a design statement** —
  most clearly for lambdas (§6), where four of the "doesn't have this"
  languages (C++98, Java 5, this PHP, this VB6) simply predate their own
  language's later addition of the feature. Reading an absence in this
  corpus as "language X can't do Y" needs the grammar's vintage checked
  first.

## Why each design was chosen

Every decision above traces back to a real, documented motivation — either
the language's stated design philosophy, a concrete engineering constraint
of its era, or (in two cases below) a limitation of this specific corpus
rather than the language itself.

### Procedure/function unification (§1)

**Why Algol/Ada/Fortran/Pascal/Basic split them.** The split traces to
Algol 60, which had only `procedure`; a "function" was defined as a
procedure whose body assigns to its own name to produce a value. This
mapped a mathematical distinction — a *function* computes a value, like
`f(x)` in mathematics, with no side effect implied — onto a *linguistic*
one, and structured-programming pedagogy (Wirth, Dijkstra) leaned on that
mapping deliberately: separating the two categories at the grammar level
teaches (and can enforce) that value-producing computation and
effect-causing action are different kinds of work. Ada pushes this
furthest for a concrete reason: because `procedure_call_statement` and
`function_call` are different productions, a function call cannot appear
as a bare statement in Ada, which prevents accidentally invoking a
value-producing routine and silently discarding its result — a real bug
class (e.g. ignoring an error code) that Ada's DoD safety-critical mandate
specifically targeted. Fortran's split reflects its literal origin
(FORmula TRANslation): `FUNCTION` mirrors mathematical function notation
directly, since Fortran's original purpose was numerical computation
expressed close to mathematical notation, while `SUBROUTINE` covers
everything else.

**Why Modula-3 (and the C-descended languages) merge them.** Modula-3 was
explicitly designed by its Olympus-consortium authors as a deliberate
simplification of both Modula-2 and the Ada it was reacting against — Ada
had gained a reputation for size and complexity, and Modula-3's stated
goal was a small, orthogonal core. Since a function is *always* expressible
as a procedure with a return type, keeping both as separate grammar
categories is exactly the kind of redundant machinery Modula-3 set out to
cut. C's motivation is different but converges on the same answer: C was
built to model the machine closely and to treat every subroutine
uniformly, so a `void`-returning function is simply a function whose
result type happens to carry no value — not a different category of
thing. This uniformity is also a practical requirement once functions
become values you can point to or pass around (function pointers, and
later closures/first-class functions): a single "callable" grammatical
category is much easier to give a consistent type/pointer syntax to than
two.

### Calls as a dedicated node vs. a postfix operator (§2)

**Why Ada/Fortran/Eiffel/PHP/Basic keep calls separate from expressions.**
This is mostly a direct downstream consequence of §1: once procedures and
functions are different *categories*, a procedure call (no value, so it
can only be a statement) and a function call (a value, so it's an
expression) have to be different productions too — the grammar has nowhere
else to put a valueless call. Fortran's mandatory `CALL` keyword has an
additional, more practical reason: leading with a distinguishing keyword
makes a statement's type recognizable from its very first token, which
matters enormously for the parsing technology available when Fortran was
designed (late 1950s) — long before general context-free parsing theory
(LR/LALR parsing was formalized in the mid-1960s), a compiler benefits
hugely from every statement being unambiguous from its first symbol.
Eiffel's rich call taxonomy (`Object_call`/`Non_object_call`/
`Explicit_creation_call`) reflects that Eiffel is built entirely around a
message-passing object model (a Bertrand Meyer design commitment,
elaborated in *Design by Contract*) — a call in Eiffel is conceptually
always "send this message to that target," so the grammar mirrors that
object-oriented mental model directly rather than treating a call as a
generic operator. PHP's separate call-parameter grammar reflects its
dynamic, interpreted nature: PHP functions can be looked up and invoked by
name at runtime (`$fn()`, `call_user_func`), so giving call syntax its own
grammatical identity, distinguishable from ordinary variable access, made
the original ad hoc PHP interpreter's job more tractable.

**Why C/Java/Dart/Python fold calls into the postfix-expression chain.**
Once a language treats "everything is an expression, statements are
mostly just expressions plus a semicolon" as a core design stance, calls,
indexing, and member access are naturally the same *kind* of grammatical
thing — operators applied to a value, chainable indefinitely
(`f(x)[0].y(z)`). This isn't just elegance: it's close to a requirement for
function pointers and, later, first-class/higher-order functions and
fluent/chained APIs, all of which need "whatever this expression evaluates
to, call it" without a separate call-statement wrapper for every possible
kind of callable expression.

### Explicit parameter-passing mode (§3)

**Why Ada and Modula-3 spell it out.** Both were engineered with static
correctness as an explicit goal. An inline mode annotation (`in`/`out`/`in
out` in Ada; `VALUE`/`VAR`/`READONLY` in Modula-3) lets the compiler check,
at every call site, that an `in`/`VALUE`/`READONLY` parameter is never
mutated by the callee and that an `out` parameter is always assigned
before the routine returns — turning a whole class of aliasing and
uninitialized-output bugs into compile-time errors instead of runtime
surprises. This is squarely in line with Ada's DoD-mandated
safety-critical mission, and Modula-3 inherited the same instinct from
its intellectual lineage even while cutting Ada's procedure/function
split.

**Why Basic (VB6) spells it out.** VB6's `byref`/`byval` is best explained
by its COM/OLE Automation heritage: on Windows, COM method calls and
`Declare`-based calls into external DLLs (including the Win32 API)
historically defaulted to passing arguments by reference. Making
`byref`/`byval` an explicit, visible choice on every parameter let VB
programmers override that default deliberately and avoid a real, common
source of crashes — passing a value where a native API expected a pointer,
or vice versa.

**Why C# spells it out, decades later, for different reasons.** C#'s
`ref`/`out`/`this` modifiers are motivated by concrete interop and API
design needs rather than Ada-style formal correctness: `ref`/`out` support
calling into unmanaged code (P/Invoke) where by-reference parameters are
the norm, and `out` specifically enables the extremely common .NET
"TryXxx" pattern (`bool TryParse(string s, out int result)`), where the
compiler enforces that an `out` parameter is definitely assigned on every
path before the method returns — a narrower, more pragmatic version of
Ada's same idea. `this` (marking an extension-method receiver) is unrelated
to passing convention and was added purely to support LINQ's extension-
method mechanism.

**Why Fortran-90 does it as separate statements instead.** Fortran-90 had
to remain compatible with three decades of existing FORTRAN 77 code and
compilers, whose parameter-list grammar was fixed and simple. Rather than
redesign that core production to carry inline mode/optionality markers
(as Ada did from scratch), Fortran-90's designers bolted `INTENT` and
`OPTIONAL` on as new, independent declarative statements referring back to
already-declared dummy argument names — a classic backward-compatible
language-extension strategy: add new syntax alongside the old, touch
nothing that already parses.

**Why C99, C++98 (except via reference types), Java, JS, Python, PHP,
Dart, and Eiffel leave it unmarked.** Each of these settled on one single,
non-negotiable passing rule for the whole language (C: always by value;
Java/Python/JS: object references passed by value of the reference;
similarly for the rest), so there is nothing per-parameter left to
annotate. C++ is a partial exception in spirit if not in this specific
grammar slot: it achieves explicit reference semantics through the *type*
system (`T&` in a parameter's type) rather than a separate mode keyword —
the same expressive goal as Ada's `out`, reached via an entirely different
grammatical mechanism (the type grammar, not a parameter-mode grammar).
This is the general "orthogonality" design principle at work: don't invent
a second mechanism for something the type system can already express.

### Variadic-parameter notation (§4)

**C's trailing `...`.** C is deliberately minimal and close to the
machine; its variadic mechanism (`va_list`/`va_arg`) is a genuinely unsafe,
low-level trick that walks the call stack or argument registers with no
type checking at all past the ellipsis. The unusual, attention-grabbing
punctuation is an intentional signal: "ordinary type-checked parameters
end here; what follows is handled specially, and unsafely, at runtime."

**Java's `...`, despite a completely different, safe implementation.**
Java's varargs (added in Java 5, which is exactly the version in this
corpus) compile to an ordinary, fully type-checked array parameter — none
of C's unsafety applies. The choice to reuse C's exact spelling anyway was
about programmer psychology and migration cost, not mechanism: reusing a
syntax C and C++ programmers already recognized lowered the learning cost
of adopting the feature, even though what happens underneath is unrelated.

**Python's `*args`/`**kwargs`.** This is a deliberate symmetry with
Python's own call-site unpacking operators (`f(*seq)` unpacks a sequence
into positional arguments at a call site; `**dict` unpacks a mapping into
keyword arguments) — reusing the identical `*`/`**` sigils on the
definition side means "pack" and "unpack" are visually and conceptually
the same operation viewed from two ends, consistent with Python's general
"there should be one obvious way to do it" design ethos.

**C#'s `params` plus an ordinary array type.** This reflects two C#
tendencies at once: a general preference for readable keywords over
cryptic punctuation (in contrast to C/C++), and the fact that a `params`
argument genuinely *is* just a normal array parameter under the hood, with
the compiler providing call-site sugar (letting the caller pass loose
values instead of constructing the array explicitly) rather than a
separate calling convention. The syntax honestly reflects the mechanism:
no special punctuation was needed because there's no truly special
mechanism, just one keyword's worth of sugar over an ordinary type.

### Default parameter values (§4)

**Why Ada, C++, C#, Dart, PHP, and Basic support them.** All six are
general-purpose or enterprise/application languages where APIs
accumulate many optional, configuration-style parameters over time. Ada's
motivation is explicit in its own design rationale: defaults reduce the
need for combinatorial procedure/function overloading when only a
trailing subset of parameters varies, letting one flexible signature
replace many near-duplicate overloads.

**Why Java deliberately has none.** This is a documented design choice,
not an oversight: Java's designers chose method overloading as the sole
mechanism for "optional-seeming" parameters, partly to avoid the
interaction complexity that arises when default arguments and overload
resolution combine (a known source of surprising behavior in C++), and
partly out of a general preference for one obvious mechanism over two
overlapping ones.

**Why Eiffel deliberately has none.** Also a stated design principle
rather than an absence: Eiffel avoids both overloading and default
argument values on purpose. Bertrand Meyer's design-by-contract philosophy
depends on a routine's exact signature being unambiguous at every call
site, since preconditions and postconditions are attached to one specific,
fully-determined routine — a call whose meaning could silently shift
depending on which optional arguments were supplied would undermine that
guarantee. Eiffel's style guidance instead recommends multiple, separately
named routines or named constants.

**Why C99, JS (this grammar), and Fortran-90 have none here.** These are
dating artifacts, not philosophy: JS added default parameters in ES6
(2015), well after the pre-ES6 grammar captured in this corpus. C99
predates C++'s addition of `constexpr`-adjacent conveniences but was never
going to gain this feature regardless, since C's design deliberately never
adopted C++'s function-overloading-adjacent machinery at all — no
overloading, hence no natural place for default arguments to interact
with it. Fortran-90's `OPTIONAL` (§3) lets a dummy argument be omitted, but
omission is deliberately *not* paired with an automatic substitute value —
the subprogram body must check `PRESENT(x)` and decide what to do itself.
This reflects Fortran's numerical/scientific-library use case, where
"the caller didn't supply this" often needs to trigger genuinely different
behavior (a different algorithm branch), not just silently plugging in a
number.

**Why Modula-3's status is unclear.** As noted in §4's table, the fetched
`Formal` production for Modula-3 has a non-optional `"&" ":=" ConstExpr`
tail that doesn't match any real Modula-3 syntax, and the identical `"&"
":="` pair recurs in three unrelated productions (`VariableDecl`, `Field`,
`Method`) — evidence of an automated grammar-mutation bug in the Grammar
Zoo's "connected" tier (see `upstream-fixes/README.md`) rather than a
genuine design absence. Real Modula-3 does support `x: T := default` on
formals.

### Return-value convention (§5)

**Why most languages use an explicit `return` statement.** An explicit
keyword makes the exit point of a function, and the fact that a value is
being produced there, visible exactly where it happens in the source text
— readable locally, without needing to track a magic variable's state
across the whole routine body.

**Why Eiffel and Pascal don't.** Pascal's convention (assign to the
function's own name) is inherited directly from Algol 60, which had the
same mechanism for the same reason procedures and functions were unified
via assignment rather than a dedicated keyword in the first place — Algol
predates the idea of `return` as a distinct control-flow keyword entirely.
Eiffel's `Result` variable is a deliberate design choice within Meyer's
broader philosophy that a routine should have (by convention, if not
grammar-enforced) a single, predictable point where its outcome is
determined, rather than a value that can escape from anywhere via a
`return` scattered through nested conditionals — but as the original
analysis noted, this is also the one place where Eiffel's own design
works against its usual anti-implicitness instincts, since nothing in the
grammar actually marks where `Result`'s final value is decided.

**Why VB6 keeps both.** This is the same "add the new mechanism, never
retire the old one" pattern VB6 shows for `if`/`end if` and for
`Optional`/default values: BASIC's original name-assignment convention
predates VB6 by decades, and a bare `Return` (control-only, no value slot)
was added later without displacing it — backward compatibility with
existing BASIC code and habits took priority over grammatical
consistency.

### Lambdas / anonymous functions (§6)

**Why Python, C#, Dart, JS, and Eiffel have some form.** Each added it for
a distinct, language-specific reason: Python's `lambda` supports its
functional-programming-adjacent idioms (`map`/`filter`/`sorted(key=...)`)
without needing a full `def`; C# 4.0's `=>` lambdas exist to support LINQ,
which relies heavily on passing small inline predicates and projections to
query operators; JS function expressions are central to its
event-driven/callback-oriented design going back to its earliest browser
use; Eiffel's `agent` mechanism is a natural extension of its
message-passing object model — an agent is a first-class reference to a
routine call, consistent with "everything is a call to a target" rather
than a value-producing lambda body in the C/Python sense.

**Why the "no lambda" list mostly isn't a design statement.** As the
original analysis flagged, C++98, Java 5, and the PHP/VB6 versions
captured in this corpus all predate their own language's later addition
of lambdas (C++11, Java 8, PHP 5.3, VB.NET). Ada, Fortran, Modula-3,
Pascal, and COBOL are the genuine cases: at these grammar versions and in
these language families' design eras (pre-1990s structured/procedural
programming, with a strong preference for named, statically-checkable
subprograms over anonymous inline code), function-valued expressions
simply weren't part of the design space being worked in.

## 7. Parameter-list delimiters: comma-flat, two-tier, or no delimiter at all

Beyond *whether* a parameter list is parenthesized, the languages in this
corpus separate individual parameters in three structurally different
ways.

**Flat comma-separated, one type repeated per parameter.** C99, C++98,
C#, Java, JS, Python, PHP, Dart, Fortran-90, and Basic (VB6) all use one
comma-separated list where every parameter spells out its own type:

```
c-c99-iso-9899-tc3:  parameter-list ::= parameter-declaration | parameter-list "," parameter-declaration
```

`int add(int a, int b)` — `int add(int a, b)` is not legal C, even though
`int a, b;` as an ordinary variable declaration *does* let two names share
one type. That asymmetry matters: C's parameter-list grammar is a
genuinely separate production from its declaration-list grammar, even
though both happen to use commas.

**Two-tier: comma within a type-group, semicolon between groups.** Ada,
Pascal/Delphi, Modula-3, and Eiffel all do the same distinctive thing:

```
ada:       formal_part ::= "(" parameter_specification (";" parameter_specification)* ")"
           defining_identifier_list ::= defining_identifier ("," defining_identifier)*
pascal:    formal_parameters ::= "(" formal_parameter (";" formal_parameter)* ")"
           parameter ::= (id,)* [parameter_type]
modula-3:  Formals ::= [Formal (";" Formal)* [";"]]
           Formal ::= [mode] IDList ":" Type ...   where IDList ::= Ident ("," Ident)*
eiffel:    Formal_arguments ::= "(" Entity_declaration_list ")"
           Entity_declaration_list ::= sep+(Entity_declaration_group, ";")
```

This lets you write `(a, b: Integer; c: String)` — comma groups names
sharing a type, semicolon starts a new type group. It isn't a separate
parameter-list design: it's these languages reusing their own ordinary
variable-declaration grammar verbatim for parameters (Pascal's
`var a, b: Integer;` is the identical shape). C can never do this, because
C's "declaration mirrors use" philosophy ties a type to each individual
declarator directly — there is no grammatical slot for "these two names
share this type" in a C parameter list to reuse in the first place. The
two-tier scheme is only reachable for a language whose variable-declaration
syntax already separates "names" from "type" as independent pieces, which
is exactly the same Algol/Pascal/Ada lineage responsible for §1 and §3
above — the same underlying trait (a parameter is *a declaration*, not
*a typed slot*) showing up a third time.

**Whitespace-only, no delimiter at all — not verifiable in this corpus.**
The real examples of this pattern (OCaml/Haskell-style curried
`let add a b = a + b`; Lisp/Scheme `(defn add [a b] ...)`) belong to
languages not present in `grammar-zoo-flavie`, and the one file that could
have been a candidate, `ml-ocaml-amble.bgf`, is the mislabeled
process/state-machine schema already flagged elsewhere in this repo — not
real OCaml syntax. Conceptually, the reason the pattern works at all: in a
truly curried ML-family function, `add a b` is not a two-argument call —
it desugars to `(add a) b`, one single-argument function applied twice in
a row. There is no "parameter list" node in the grammar for a delimiter to
live in, because each "parameter" is really the argument of its own
separate, nested single-argument function; juxtaposition is just repeated
function application, not a list construct, so there is nothing for a
comma to separate.

### A related question: are the parens themselves ever optional?

Checking whether the entire `( ... )` group can be dropped for a
zero-parameter routine — not just left empty — turns up a clean split
that lands on the same language cluster yet again.

**Parens are structurally mandatory, even with zero parameters:** C99,
C++98, C#, Java, JS, Python, PHP, Dart, and Modula-3 — Modula-3's
`Signature ::= "(" Formals ")" [":" Type]` requires the literal `(` `)`
even when `Formals` expands to nothing.

**The whole parenthesized group is optional and can vanish entirely:**

```
ada:      parameter_and_result_profile ::= [formal_part] "return" ...
pascal:   procedure_signature ::= ... [formal_parameters] ...
fortran:  FunctionParList ::= ("(" FunctionPars ")") | epsilon
basic:    subprogram_declaration ::= ... [subprogram_argument_description] ...
```

So `function Foo return Integer;`, `procedure Foo;`, and `Sub Foo` are all
valid with no parens anywhere in the text. This is the same four-language
cluster again (Ada, Pascal, Fortran, Basic), and the reason connects
directly to §2 above (calls as a dedicated statement vs. a postfix
operator on expressions). In C/Java/JS/Python, a call is folded into the
general expression grammar, so a bare name and a zero-argument call need
to stay visually distinct — if parens were optional, `foo` could mean
either "the function value itself" or "call it with no arguments," a real
ambiguity once functions are first-class expressions. Ada/Pascal/
Fortran/Basic never run into this: a procedure call is already its own
dedicated statement production, so the parser knows structurally that a
call is happening from the surrounding statement shape, without needing
`()` to signal it. Requiring `()` as a disambiguator only becomes
necessary once a language has committed to calls-as-postfix-expressions;
the languages that never made that commitment never needed the
disambiguator either.

## 8. Function modifiers: how strictly does the grammar constrain them?

The most useful axis here isn't which keywords exist, but *how much of
"which modifier is valid on which kind of declaration" the grammar itself
enforces*, versus leaving that check to a later semantic pass.

**C# is the most granular in the corpus — a separate modifier production
per declaration kind.** Not one `modifier` rule but twelve:
`class-modifier`, `method-modifier`, `field-modifier`, `property-modifier`,
`event-modifier`, `indexer-modifier`, `operator-modifier`,
`constructor-modifier`, `struct-modifier`, `interface-modifier`,
`enum-modifier`, `delegate-modifier`. Each repeats the shared access-level
keywords (`public`/`protected`/`internal`/`private`) but only admits the
kind-specific ones where they're actually meaningful:
`virtual`/`sealed`/`override`/`abstract`/`extern` appear on
`method-modifier`/`property-modifier`/`event-modifier`/`indexer-modifier`,
while `readonly`/`volatile` appear only on `field-modifier`; the static
constructor even gets its own dedicated production,
`static-constructor-modifiers ::= (["extern"] "static") | ("static" ["extern"])`.
Writing `abstract` on a field is a **parse error** in this grammar, not
just a semantic one — validity is pushed as far left as it can go, into
the CFG itself.

**C and C++ sit at the opposite extreme: one shared list covering both
functions and variables.** C99's `function-specifier` is just `"inline"`,
reached through `declaration-specifiers` — the identical production that
governs ordinary variable declarations
(`storage-class-specifier | type-specifier | type-qualifier | function-specifier`,
freely interchangeable in the same repetition). `inline int x;` is
grammatically well-formed C, even though `inline` is meaningless on a
variable — the grammar accepts anything shaped like a declaration and
defers the actual validity check to the compiler's semantic phase, the
direct opposite of C#'s strategy. C++98 extends the same shared list with
`virtual`/`explicit` for its OOP additions but keeps the same underlying
philosophy: one specifier vocabulary, checked later.

**Java folds user-defined annotations into the same list as built-in
keywords.** `modifier ::= annotation | "public" | "protected" | ... |
"native" | "synchronized" | "transient" | "volatile" | "strictfp"` — a
custom `@Override` or `@Deprecated` sits in the identical repeated slot as
the built-in keywords, freely interleaved in any order (`modifiers ::=
(modifier)*` enforces no sequence). This is a real point of contrast with
C#, where `[attributes]` is a *separate*, order-fixed slot that must
precede `[method-modifiers]` in `method-header`. Java made annotations
first-class modifiers, extensible by any programmer without a new
keyword; C# keeps "what this is" (metadata/attributes) and "how it
behaves" (modifiers) as two distinct grammatical categories. Java also
keeps `native`/`synchronized`/`transient`/`volatile` — keywords that only
really make sense on methods or only on fields respectively — in the
*same* unified `modifier` list used for both, rather than splitting them
the way C# does; Java accepts the invalid combination grammatically and
leaves catching it to semantic analysis.

**Ada, Fortran-90, and Modula-3 don't attach visibility to the declaration
at all — it's purely positional.** Ada has no `public`/`private` keyword
anywhere near an individual subprogram. Instead,
`package_specification ::= "package" name "is" (declarative_item)*
["private" (declarative_item)*] "end" ...` — one `private` keyword marks
where a package's private section begins; everything declared before it
is visible outside the package, everything after is hidden. Visibility is
a property of *where* something is written, not *what keyword* is
attached to it. Fortran-90 lands halfway between this and a per-declaration
modifier: it has a genuine `AccessSpec ::= "public" | "private"` keyword,
but it names a whole list of module entities in one statement rather than
annotating each subprogram individually.

**Eiffel's visibility mechanism is the most expressive thing in the
corpus.** Rather than a fixed set of visibility levels, Eiffel names the
exact classes permitted to call a feature:
`Feature_clause ::= "feature" [Clients] ... Feature_declaration_list`,
where `Clients ::= "{" Class_list "}"`. `feature {ACCOUNT, LOGGER}` exports
that group of routines to precisely those two classes; `feature {NONE}` is
fully private; omitting the braces entirely is fully public; anything else
is a custom, per-feature client whitelist. This ties directly to Meyer's
Design-by-Contract philosophy — knowing exactly which classes may rely on
a contract is more valuable than the usual public/protected/private
three-way split nearly every other object-oriented language in this
corpus settles for.

**Two real grammar quirks worth flagging on their own.** PHP's
`ClassMember ::= [VarModifiers] "abstract" [VarModifiers] "function" ...`
sandwiches the `abstract` keyword between two *independent* optional
modifier lists, so both `public abstract function foo();` and
`abstract public function foo();` are grammatically valid. Basic (VB6) has
a real redundancy: `access_modifier` already includes `"static"` as one of
its own alternatives, yet `subprogram_declaration ::= [access_modifier]
["static"] ...` also carries a *separate* `["static"]` slot immediately
after it — so `Static Static Sub Foo` is technically well-formed per this
grammar, almost certainly a small blemish from the hand-written TXL
extraction rather than an intentional VB6 rule.

**A mechanism this corpus can't show at all: naming-convention privacy.**
Dart and Python are both well known for using a leading underscore
(`_foo`) as their privacy signal instead of any modifier keyword — but
that's a property of identifier *text*, read by the compiler/interpreter,
not something a context-free grammar can express as a production. Neither
grammar has anything resembling a modifier rule for this reason, which is
expected — not a gap in the extraction, just a mechanism that operates
below the level a BGF grammar can capture.
