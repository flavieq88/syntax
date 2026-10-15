# Classes and inheritance across `grammar-zoo-flavie`

An analysis of how the languages in `grammar-zoo-flavie` with real
object-oriented syntax handle class definition, inheritance, interfaces,
and constructors, based on the actual productions in
`normalized-ebnf-flavie-adapted/`. Not every language in the corpus has a
class concept at all: C99, Fortran-90, COBOL, and PL/I genuinely have none
(consistent with their era and non-OO design), and this JS grammar has none
for a different reason — it's a pre-ES6 (2015) grammar, predating JS
classes entirely, the same vintage caveat already flagged for lambdas in
`function-analysis.md` §6.

## 1. Not every language even says "class"

Most of the corpus uses `"class"` directly — C++98, C# 4.0, Java 5, Dart,
Python, PHP, Basic (VB6), and Pascal/Delphi, where
`class_keyword ::= "class" | "record" | "object"` treats all three as
interchangeable object-type introducers. Two languages deliberately avoid
the word:

**Modula-3** has no `class` keyword at all:

```
ObjectType ::= [Ancestor] [Brand] "OBJECT" Fields [("METHODS" Methods)] "END"
Ancestor   ::= TypeName | ObjectType | "UNTRACED"
```

Consistent with Modula-3's general minimalism (see `function-analysis.md`
§1), it also structurally separates data from behavior within one type:
fields come first, and methods — if any — sit in their own, separately
keyworded `METHODS` block, unlike every other language here, which freely
interleaves fields and methods in one body. Modula-3 also has a genuinely
unique feature nowhere else in the corpus: `Brand ::= "BRANDED"
[TextLiteral]`. Because Modula-3 (like several minimalist languages of its
era) checks object types *structurally* rather than *nominally*, two
separately-defined object types with identical fields and methods would
otherwise be indistinguishable to the type checker; branding attaches an
explicit, unique text label to a type specifically to force it to be
treated as nominally distinct even when structurally identical to another.

**Ada** also has no `class` keyword. Ada 2005 retrofitted object
orientation onto an already-mature type system, so it extends types using
type-derivation vocabulary instead:

```
record_type_definition   ::= [[abstract] "tagged"] [limited] record_definition
derived_type_definition  ::= [abstract] [limited] "new" parent_subtype_indication
                              [[("and" interface_list)] record_extension_part]
```

The actual Ada idiom is `type Dog is new Animal with record ... end
record;` — "Dog is a new type derived from Animal, extended with a
record" — a genuinely different mental model from "Dog is a class
extending Animal," expressed in genuinely different grammar, even though
it accomplishes the same result.

## 2. Single vs. multiple implementation inheritance

| Language | Mechanism | Multiplicity |
|---|---|---|
| Modula-3 | `[Ancestor]` — one optional `TypeName \| ObjectType \| "UNTRACED"` | single, at most one parent |
| Java 5, C# 4.0, Dart | `["extends" type]` (one) + `["implements" typeList]` (list) | single class inheritance, multiple interfaces |
| Ada 2005 | `"new" parent_subtype_indication` (one) + `["and" interface_list]` (`and`-separated list) | identical shape to Java/C#/Dart, different keywords |
| PHP | `ExtendsClause ::= "extends" id` (one) + `ImplementsClause ::= "implements" sep+(Name, ",")` (list) | same pattern again |
| C++98 | `base-specifier-list ::= base-specifier ("," base-specifier)*`, each with its own optional `access-specifier` and `"virtual"` | genuine multiple *implementation* inheritance |
| Eiffel | `Parent_list ::= sep+(Parent, ";")`, each `Parent` carrying its own `Feature_adaptation` | genuine multiple *implementation* inheritance |
| Python 2 | `classdef ::= "class" [id] "(" [testlist] ")" ":" suite` — bases are a comma-separated `testlist` (arbitrary expressions, not just class names) | multiple, and unusually permissive |
| Pascal/Delphi | `heritage_list ::= "(" sep*(qualified_id, ",") ")"` | one undifferentiated list (see §3) |
| Basic (VB6) | no inheritance production at all | **none** |

The striking convergence: **Java, C#, Dart, Ada, and PHP all
independently arrived at the identical "one base type, many interfaces"
shape**, despite different eras and unrelated keyword choices
(`extends`/`implements` vs. `new`/`and`). That convergence is a strong
signal this split solves a real, recurring problem — the diamond-shaped
ambiguity of multiple *implementation* inheritance — by simply forbidding
it while still allowing multiple *behavioral contracts*, since interfaces
carry no state or implementation to conflict over in the first place.

**C++ and Eiffel are the two languages that actually allow multiple
implementation inheritance**, and they resolve the resulting conflicts in
completely different ways.

**C++** lets each base carry its own access level and virtual marker:

```
base-specifier ::= ["::"] [nested-name-specifier] class-name
                  | "virtual" [access-specifier] ["::"] [nested-name-specifier] class-name
                  | access-specifier ["virtual"] ["::"] [nested-name-specifier] class-name
access-specifier ::= "private" | "protected" | "public"
```

`class D : public A, private B, virtual public C` controls, per base, how
much of that parent's interface stays visible outside `D`, and whether
`virtual` collapses a shared ancestor to a single instance (the classic
"diamond problem" fix). This per-base access idea appears nowhere else in
the corpus.

**Eiffel** solves the same problem per parent, with a name-level
conflict-resolution toolkit instead of a visibility-level one:

```
Feature_adaptation ::= [Undefine] [Redefine] [Rename] [New_exports] [Select] "end"
Rename    ::= "rename" Rename_list
Redefine  ::= "redefine" Feature_list
Undefine  ::= "undefine" Feature_list
Select    ::= "select" Feature_list
```

`rename` gives a clashing inherited feature a new local name; `undefine`
removes one outright to eliminate an ambiguity; `redefine` overrides a
parent's implementation; `select` explicitly names which parent's version
wins when two parents supply a feature of the same name. This is the most
elaborate conflict-resolution machinery in the corpus, and it exists
specifically *because* Eiffel allows unrestricted multiple inheritance and
never took the Java/C#/Ada/PHP/Dart route of simply banning it.
Eiffel also has one more nuance nothing else in the corpus has:
`Non_conformance ::= "{" "NONE" "}"`, used as `inherit {NONE} PARENT` —
"non-conforming" inheritance, which reuses a parent's implementation
*without* creating an is-a subtyping relationship, deliberately decoupling
code reuse from polymorphism.

## 3. The extends/implements split — and its absence

Every language in §2's "one base, many interfaces" row keeps the base
class and the interface list as two grammatically distinct concepts.
**Pascal/Delphi is the one real exception**: its `heritage_list` is a
single, undifferentiated comma-separated list —

```
heritage_list ::= "(" sep*(qualified_id, ",") ")"
```

`class(TParent, IInterface1, IInterface2)` puts the superclass and any
implemented interfaces side by side with no grammatical distinction
whatsoever. The grammar genuinely cannot tell you which identifier is the
one parent class and which are interfaces — that distinction is resolved
entirely by what kind of type each name happens to reference, outside the
grammar altogether.

**Basic (VB6) has no inheritance production at all.** Its only related
construct is `implements_declaration ::= "implements" id`, listed as an
ordinary `declaration` alternative alongside `class_declaration` — meaning
`Implements SomeInterface` is a plain *statement inside* a class's body
(VB6 classes are separate `.cls` module files whose body is just a
sequence of statements), not part of a class header the way
`class Foo implements Bar` is everywhere else. There is genuinely no
class-to-class implementation inheritance in classic VB6: `Implements`
only promises that a class will supply every method of a given COM
interface, each of which then has to be hand-written from scratch with no
code reuse at all. (VB.NET's later `Inherits` keyword doesn't exist in
this grammar.)

## 4. Interfaces have their own, sometimes looser, multiplicity rules

Interfaces extending other interfaces don't always follow the same
multiplicity rule as classes extending classes in the same language:

```
php:   InterfaceExtendsClause ::= "extends" sep+(Name, ",")
java:  interfaceDeclaration ::= normalInterfaceDeclaration | annotationTypeDeclaration
c#:    interface-declaration ::= ... interface-base ...
dart:  interfaceDefinition ::= "interface" identifier [typeParameters] [superinterfaces] ...
```

PHP is the clearest illustration: a PHP *class* can only `extends` one
other class, but a PHP *interface* can `extends` several at once
(`interface Foo extends Bar, Baz`) — because interface-to-interface
extension only ever combines method signatures, never conflicting
implementations, the diamond problem that justifies restricting class
inheritance to one parent simply doesn't apply to interfaces.

## 5. Constructors: a spectrum from fully dedicated to pure convention

| Language | Mechanism |
|---|---|
| C# 4.0 | `constructor-declaration` **and** `destructor-declaration` are their own dedicated productions, the destructor unmistakable via its `"~" identifier` prefix — the most explicit mechanism in the corpus |
| Dart | `constructorDeclaration` is its own production, further distinguishing `redirection` (one constructor forwarding to another) from `initializers` (a member-initializer list) as two different constructor bodies |
| C++98 | **no dedicated constructor production at all** — a constructor is an ordinary `function-definition` whose declarator happens to match the class name (a semantic check, not a grammar one); the one syntactic tell is the optional `ctor-initializer ::= ":" mem-initializer-list`, a clause only a constructor can carry |
| Java 5 | `constructorDeclaratorRest` exists as its own alternative inside `genericMethodOrConstructorRest`, distinguished purely structurally: a constructor is a bare `Identifier` followed directly by parameters with **no preceding return type**, unlike every ordinary method — recognizable, but by shape rather than by keyword |
| Python 2, PHP (this grammar) | **zero grammar involvement** — `__init__`/`__construct` (or PHP's older same-name-as-class convention) are ordinary method definitions using the identical `funcdef`/`FunctionDecl` production as everything else; the "this one is special" meaning is a pure runtime naming convention, invisible to the grammar entirely |

This is the same axis that already showed up for modifiers in
`function-analysis.md` §8 — how much of a construct's special status is
pushed into the grammar itself versus left to a semantic or runtime
convention — landing on a five-point spectrum here instead of a binary
split.

## 6. Abstract classes and members: a class-level flag, or a member-level one?

C# (`class-modifier ::= ... | "abstract" | ...`), Java
(`classOrInterfaceModifier ::= ... | "abstract" | ...`), and PHP
(`ClassType ::= "class" | ("abstract" "class") | ("final" "class")`) all
mark abstractness on the *class* itself. Dart does it differently: there
is no `abstract` alternative anywhere on `classDefinition` in this
grammar. Instead, `ABSTRACT` appears only on individual members —
`declaration ::= ... | (ABSTRACT specialSignatureDefinition) | (ABSTRACT
functionDeclaration) | ...` — so a Dart class becomes "abstract" as a
consequence of containing abstract members, not by being labeled abstract
itself at this grammar version. Dart also treats several of its own
keywords, including `ABSTRACT`, `CLASS`, `EXTENDS`, `IMPLEMENTS`, and
`INTERFACE`, as *contextual* keywords: `identifier ::= IDENTIFIER \|
ABSTRACT \| CLASS \| EXTENDS \| ...` explicitly allows any of them to also
be used as an ordinary identifier — a design choice that trades a small
amount of grammar ambiguity for never permanently reserving a word an
existing program might already use as a variable name.

## Why each design was chosen

**Avoiding the word "class" (Modula-3, Ada).** Both reflect what kind of
type system the language was already committed to before adding
object-oriented features. Modula-3 was built as a small, structurally-typed
core language; keeping `OBJECT` rather than introducing a `class` keyword
kept object types looking like just one more member of its existing
`Type` alternatives (`ArrayType`, `RecordType`, `EnumType`, ...), rather
than carving out a special new category. Ada added OOP in the 1995/2005
revisions on top of a language whose entire identity was already "a rich,
static type system with derivation" — expressing inheritance as `new
Parent with record ...` extends that existing type-derivation machinery
rather than importing an unrelated class-based vocabulary wholesale.

**Restricting to single implementation inheritance plus multiple
interfaces (Java, C#, Dart, Ada, PHP).** All five independently chose this
because it sidesteps the diamond-inheritance conflict (two parents
supplying incompatible implementations of the same member) without giving
up the ability to satisfy multiple behavioral contracts — an interface has
no state or implementation to conflict over, so allowing many of them
costs nothing while allowing many *base classes* would reopen the exact
ambiguity every one of these languages' designers wanted to close. This is
functionally the same trade-off C++'s designers rejected and Eiffel's
designers rejected — the difference is what each side was willing to build
to manage the resulting complexity.

**C++'s per-base access-specifier and `virtual` inheritance.** C++ kept
genuine multiple implementation inheritance (unlike its Java/C# successors)
because it was designed as a systems language prioritizing expressive
power and direct control, consistent with C's own philosophy of trusting
the programmer over restricting them. The per-base access-specifier and
`virtual` keyword are the direct engineering cost of that choice:
`virtual` inheritance specifically exists to solve the diamond problem
(so a repeated common ancestor is stored once, not once per inheritance
path) — a mechanism that only needs to exist because C++ allowed the
diamond shape to occur in the first place.

**Eiffel's rename/redefine/undefine/select toolkit.** This is a direct
consequence of Bertrand Meyer's stated design position that multiple
inheritance is a valuable modeling tool that should not be restricted for
implementation convenience — Eiffel's Design by Contract philosophy treats
composing behavior from multiple sources as a first-class use case (a
`SAVINGS_ACCOUNT` genuinely might need to combine `ACCOUNT` and
`INTEREST_BEARING` capabilities). Rather than banning the diamond shape,
Eiffel's answer is to give the programmer explicit, fine-grained tools to
resolve every possible naming conflict by hand, keeping multiple
inheritance's expressive power while making every conflict resolution
decision visible in the source text rather than resolved by an implicit
rule.

**Pascal/Delphi's undifferentiated heritage list.** This is best
understood as a side effect of Delphi's object model being added to
Pascal incrementally, layer by layer, over many language versions (Object
Pascal, then Delphi's own COM-interface support) rather than being
designed as one unified feature. Reusing the exact same "list of type
names in parens" shape both for the one real superclass and for any
interfaces was the path of least grammatical disruption — the base
language's own type-reference syntax didn't need a new, separate slot
invented for the interface case.

**VB6 having no implementation inheritance at all.** COM, the platform
VB6 was built around, was deliberately designed around interface-based
polymorphism rather than implementation inheritance (a well-documented COM
design principle — COM objects communicate purely through interfaces, and
COM itself has no notion of inheriting an existing object's code). VB6's
`Implements`-only, no-`Inherits` object model is a direct reflection of
the platform it was designed to be a thin, approachable layer over, not an
arbitrary limitation of the language's own grammar design.

**The constructor spectrum.** This tracks the same "how much does the
grammar encode vs. leave to convention" axis seen throughout this whole
analysis. C# and Dart's fully dedicated constructor productions reflect
languages designed with static tooling (IDEs, compilers catching
mismatched constructor signatures) as a first-class concern from the
start. Java's structurally-recognizable-but-unmarked approach and C++'s
minimal-plus-one-tell approach both reuse as much of the ordinary
function/method grammar as possible, adding just enough new syntax to
cover what genuinely can't be expressed otherwise (the member-initializer
list). Python and PHP's pure-convention approach is the natural extreme of
each language's general preference for dynamic, late-bound behavior over
compile-time-checked structure — treating `__init__`/`__construct` as
"just a method with a name the runtime happens to look for" is consistent
with treating essentially everything else about the object model
(attribute existence, method resolution) the same dynamic way.

## Summary of cross-cutting patterns

- **The single-base-plus-multiple-interfaces shape is the strongest
  convergent signal in this analysis** — five unrelated languages across
  four decades (Ada 1995/2005, Java 1995, PHP, C# 2000s, Dart 2010s)
  arrived at the identical structural solution to the same underlying
  problem, using entirely different keywords each time.
- **The two languages that reject that restriction (C++, Eiffel) both
  had to build real conflict-resolution machinery to compensate** — and
  built two structurally unrelated toolkits (visibility/virtual-slots
  in C++, explicit rename/redefine/select in Eiffel) — confirming that
  banning multiple implementation inheritance isn't a stylistic choice so
  much as a genuine complexity trade-off with a real cost on either side
  of the decision.
- **"How much of this concept lives in the grammar vs. is left to
  convention" is the single most recurring axis across every section of
  this and the companion functions analysis** — it explains the
  constructor spectrum here exactly as it explained the modifier systems,
  the return-value conventions, and the call-vs-postfix-operator split in
  `function-analysis.md`.
- **Feature absence keeps needing an era check before it's read as a
  design statement** — this JS grammar's missing classes are a vintage
  artifact (pre-ES6), not evidence JS can't do OOP, exactly the same
  caveat already established for lambdas.
