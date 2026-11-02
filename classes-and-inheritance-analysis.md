# Classes and inheritance across `grammar-zoo-flavie-adapted`

An analysis of how the languages in the curated 20-grammar corpus with real
object-oriented syntax handle class definition, inheritance, interfaces,
and constructors, based on the actual productions in
`normalized-ebnf-flavie-adapted/`. Twelve of the twenty grammars have a
class-like type declaration (Ada, Basic/VB6, C++, C#, Dart, Eiffel, Java,
Modula-3, Pascal/Delphi, PHP, Python, Swift). The other eight have none,
and they don't all lack it for the same reason:

- **Non-OO by era and design.** C99, Fortran-90, and COBOL
  (`cobol-vscobolii-lammel-gdk`) genuinely have none. Fortran-90's
  `DerivedTypeDef` (`"type" ... TypeName`) is a plain record with no
  parent slot, and COBOL's one production literally spelled `"CLASS"`,
  `class_clause ::= "CLASS" class_name ["IS"] (literal [("THROUGH" |
  "THRU") literal])+`, defines a *character class* for a `SPECIAL-NAMES`
  condition test (e.g. "is this field all digits?"), not a type.
- **Too early a grammar snapshot.** This JS grammar is pre-ES6 (2015),
  predating JS classes entirely — the same vintage caveat already flagged
  for lambdas in `function-analysis.md` §6. It does contain the terminal
  `"class"`, but only as a bare alternative of `js_primary_expn ::= "this"
  | "class" | id | ...` — a stray atom (ES3 listed `class` as a reserved
  future word), not a declaration. What it *does* have is `"this"` and
  `js_lefthand_side_expn ::= ["new"] js_member_expn`, the raw material for
  prototype-based constructor functions, but no production that defines a
  class or a parent.
- **Built by convention, not by grammar.** Lua 5.2 has no class or object
  production at all; it has tables plus one piece of method-call sugar
  (`:`), covered in §9.
- **A different paradigm entirely.** Haskell and Erlang. Haskell is
  covered on its own in §7: not too old (Haskell 98 is contemporaneous
  with Java and C#'s early versions, both very much already "OOP
  languages" by then) and not too early a grammar snapshot, but built on a
  paradigm where the whole notion of a mutable object with identity that
  methods get dispatched against was never part of the design. Haskell
  does have a production literally spelled `"class"`, and it is not this —
  §7 exists specifically to pin down why. Erlang (§9) is the same kind of
  absence from a different direction: its units of organization are
  modules and processes, not objects.
- **A grammar that only covers expressions.** Smalltalk is the odd one
  out: the canonical pure object-oriented language, yet this Redline
  grammar contains no class-definition production at all (§9), because in
  Smalltalk defining a class is itself just a message send.

## 1. Not every language even says "class"

Most of the class-bearing grammars use `"class"` directly — C++98, C# 4.0,
Java 5, Dart, Eiffel (`Class_header ::= [Header_mark] "class"
Class_name`), Python, PHP, Basic (VB6), Swift, and Pascal/Delphi, where
`class_keyword ::= "class" | "record" | "object"` treats all three as
interchangeable object-type introducers. Swift has a similar pairing of
its own: `struct_declaration` and `class_declaration` are identical
productions apart from the leading keyword — both take the same optional
`type_inheritance_clause` and a body of ordinary `declarations` — so the
grammar does not distinguish value types from reference types, or forbid a
`struct` from naming a parent; (from general language knowledge) only
protocols are actually permitted after a `struct`'s colon, and that is
enforced by the type checker. Two languages deliberately avoid the word:

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
| Java 5, Dart | `["extends" type]` (one) + `["implements" typeList]` (list) — Dart spells them `superclass ::= EXTENDS type`, `interfaces ::= IMPLEMENTS typeList` | single class inheritance, multiple interfaces |
| C# 4.0 | `class-base ::= ":" class-type \| ":" interface-type-list \| ":" class-type "," interface-type-list` — one colon, no keywords | single class inheritance, multiple interfaces (but see §3) |
| Ada 2005 | `"new" parent_subtype_indication` (one) + `["and" interface_list]` (`and`-separated list) | identical shape to Java/Dart, different keywords |
| PHP | `ExtendsClause ::= "extends" id` (one) + `ImplementsClause ::= "implements" sep+(Name, ",")` (list) | same pattern again |
| C++98 | `base-specifier-list ::= base-specifier \| base-specifier-list "," base-specifier`, each with its own optional `access-specifier` and `"virtual"` | genuine multiple *implementation* inheritance |
| Eiffel | `Parent_list ::= sep+(Parent, ";")`, each `Parent` carrying its own `Feature_adaptation` | genuine multiple *implementation* inheritance |
| Python 2 | `classdef ::= "class" [id] ":" suite \| "class" [id] "(" [testlist] ")" ":" suite` (layout tokens omitted) — bases are a `testlist`, i.e. arbitrary expressions (`test`), not just class names | multiple, and unusually permissive |
| Pascal/Delphi | `heritage_list ::= "(" sep*(qualified_id, ",") ")" \| "helper" "for" id` | one undifferentiated list (see §3) |
| Swift | `type_inheritance_clause ::= ":" type_inheritance_list`, `type_inheritance_list ::= type_identifier ("," type_identifier)*` — shared verbatim by `class`, `struct`, `protocol`, `extension`, and associated types | one undifferentiated list (see §3) |
| Basic (VB6) | no inheritance production at all | **none** |

The striking convergence: **Java, C#, Dart, Ada, and PHP all
independently arrived at the identical "one base type, many interfaces"
rule**, despite different eras and unrelated keyword choices
(`extends`/`implements` vs. `new`/`and` vs. C#'s bare `:`). Four of them
(Java, Dart, Ada, PHP) also give the rule a grammatically distinct slot for
each side; C# states it as a rule but, as §3 shows, its grammar can't
actually tell the two sides apart. Swift (from general language knowledge)
enforces the same rule — at most one superclass, any number of protocols —
but entirely outside its grammar. That convergence is a strong
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

Java, Dart, Ada, and PHP keep the base class and the interface list as
two grammatically distinct concepts, each introduced by its own keyword.
**Pascal/Delphi is the clearest exception**: its `heritage_list` is a
single, undifferentiated comma-separated list —

```
heritage_list ::= "(" sep*(qualified_id, ",") ")"
```

`class(TParent, IInterface1, IInterface2)` puts the superclass and any
implemented interfaces side by side with no grammatical distinction
whatsoever. The grammar genuinely cannot tell you which identifier is the
one parent class and which are interfaces — that distinction is resolved
entirely by what kind of type each name happens to reference, outside the
grammar altogether. Delphi also reuses the exact same `heritage_list` for
interfaces (`interface_type ::= interface_keyword [heritage_list] ...`), and
its one non-list alternative, `"helper" "for" id`, attaches a class helper
to an existing type rather than naming a parent at all.

**Swift is the same design, arrived at independently.** Its
`type_inheritance_clause ::= ":" type_identifier ("," type_identifier)*` is
one flat list, and it is shared verbatim by `class_declaration`,
`struct_declaration`, `protocol_declaration`, `extension_declaration`, and
`protocol_associated_type_declaration`. In `class Dog : Animal, Printable`
nothing in the grammar marks `Animal` as the superclass and `Printable` as a
protocol; (from general language knowledge) the compiler resolves it by
looking up each name, and only requires that a superclass, if present, come
first.

**C# looks like it makes the distinction, but doesn't really.** Its
`class-base` lists three alternatives that read like a Java-style split —
`":" class-type`, `":" interface-type-list`, and `":" class-type ","
interface-type-list` — but the slots bottom out in the same place:
`class-type ::= type-name | "object" | "dynamic" | "string"` and
`interface-type ::= type-name`. So `class D : B` parses under *both* the
first and second alternatives, and `class D : B, I` under both the second
and third; which reading applies depends, exactly as in Delphi and Swift,
on what `B` turns out to name. The grammar names the two roles but cannot
choose between them without semantic information.

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
php:   ExtendsClause          ::= "extends" id                     (class: one)
       InterfaceExtendsClause ::= "extends" sep+(Name, ",")        (interface: many)
java:  normalClassDeclaration     ::= "class" ... [("extends" type)] ...      (one)
       normalInterfaceDeclaration ::= "interface" ... [("extends" typeList)] ... (many)
c#:    interface-base ::= ":" interface-type-list
dart:  superclass      ::= EXTENDS type                            (class: one)
       superinterfaces ::= EXTENDS typeList                        (interface: many)
ada:   interface_type_definition ::= [...] "interface" [("and" interface_list)]
```

In Java and Dart the *same keyword* `extends` takes one type after
`class` and a list after `interface`. Swift is the one language here where
the two cases are not distinguished at all: `protocol_declaration` uses the
identical `type_inheritance_clause` list as `class_declaration` (§3).

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
| Swift | `initializer_declaration ::= initializer_head [generic_parameter_clause] parameter_clause initializer_body` with `initializer_head ::= [attributes] ["convenience"] "init"`, plus `deinitializer_declaration ::= [attributes] "deinit" code_block` — dedicated keywords for both ends of an object's life, a `convenience` marker for initializers that delegate to another one, and dedicated expression forms `"self" "." "init"` and `superclass_initializer_expression ::= "super" "." "init"` for the delegation call itself. (Both declarations are alternatives of the general `declaration`, so the grammar doesn't confine them to a class body.) |
| Dart | `constructorDeclaration` is its own production, further distinguishing `redirection` (one constructor forwarding to another) from `initializers` (a member-initializer list) as two different constructor bodies |
| Pascal/Delphi | `procedure_keyword ::= "function" \| "procedure" \| "constructor" \| "destructor"` — dedicated *keywords*, but slotted into the one shared `procedure_signature` production, so a constructor is grammatically just a fourth kind of routine |
| Eiffel | creation procedures are ordinary features; `Creation_clause ::= "create" [Clients] [Header_comment] Creation_procedure_list` in the class header simply *lists* which features may be used to create an instance — dedicated syntax for designating a constructor, none for writing one |
| C++98 | **no dedicated constructor production at all** — a constructor is an ordinary `function-definition` whose declarator happens to match the class name (a semantic check, not a grammar one); the one syntactic tell is the optional `ctor-initializer ::= ":" mem-initializer-list`, a clause only a constructor can carry |
| Java 5 | `constructorDeclaratorRest` exists as its own alternative inside `genericMethodOrConstructorRest`, distinguished purely structurally: a constructor is a bare `Identifier` followed directly by parameters with **no preceding return type**, unlike every ordinary method — recognizable, but by shape rather than by keyword |
| Python 2, PHP (this grammar), Smalltalk, Lua | **zero grammar involvement** — `__init__`/`__construct` (or PHP's older same-name-as-class convention) are ordinary method definitions using the identical `funcdef`/`FunctionDecl` production as everything else; the "this one is special" meaning is a pure runtime naming convention, invisible to the grammar entirely. Smalltalk and Lua (§9) are further out still: their grammars have no class to attach a constructor *to*, so (from general language knowledge) `Dog new` and `Account.new(...)` are ordinary message sends/function calls to whatever object answers them |

This is the same axis that already showed up for modifiers in
`function-analysis.md` §8 — how much of a construct's special status is
pushed into the grammar itself versus left to a semantic or runtime
convention — landing on a many-point spectrum here instead of a binary
split.

## 6. Abstract classes and members: a class-level flag, or a member-level one?

C# (`class-modifier ::= ... | "abstract" | ...`), Java
(`classOrInterfaceModifier ::= ... | "abstract" | ...`), and PHP
(`ClassType ::= "class" | ("abstract" "class") | ("final" "class")`) all
mark abstractness on the *class* itself, as does Eiffel through its
`Header_mark ::= "deferred" | "expanded" | "frozen"` (a `deferred class`).
Ada does both: `["abstract"] "tagged"` on `record_type_definition` (and
`["abstract"]` on `derived_type_definition`) marks the type, while
`abstract_subprogram_declaration ::= [overriding_indicator]
subprogram_specification "is" "abstract" ";"` marks an individual
operation. Pascal/Delphi is member-level only: `"abstract"` appears solely
as a method `directive` (alongside `"virtual"`, `"dynamic"`, `"override"`),
never on `class_type`. Swift has no `abstract` anywhere in this grammar —
its role is filled by `protocol_declaration` — and none of `final` or
`required` either, consistent with this being an early (Swift 1.x-era)
grammar. Dart, like Delphi, works purely at member level: there
is no `abstract` alternative anywhere on `classDefinition` in this
grammar. Instead, `ABSTRACT` appears only on individual members —
`declaration ::= ... | (ABSTRACT specialSignatureDefinition) | (ABSTRACT
functionDeclaration) | ...` — so a Dart class becomes "abstract" as a
consequence of containing abstract members, not by being labeled abstract
itself at this grammar version. Dart also treats several of its own
keywords, including `ABSTRACT`, `CLASS`, `EXTENDS`, `IMPLEMENTS`, and
`INTERFACE`, as *contextual* keywords: `identifier ::= IDENTIFIER_NO_DOLLAR
| IDENTIFIER | ABSTRACT | ASSERT | CLASS | EXTENDS | ...` explicitly allows any of them to also
be used as an ordinary identifier — a design choice that trades a small
amount of grammar ambiguity for never permanently reserving a word an
existing program might already use as a variable name.

## 7. Haskell: no classes, and why `class`/`instance` are not the same idea

**First, the negative case, stated as precisely as the grammar allows.**
Every mechanism this document has surveyed so far — a class/object
keyword, an inheritance clause, a constructor production, a visibility
modifier on a member, a dot-based call on a receiver — is absent from
Haskell's grammar, and not just by missing keyword:

- There is no member-access or method-dispatch production anywhere. Every
  alternative of `aexp` is `qvar | gcon | literal | (parenthesized/list
  expressions) | (sections) | (aexp "{" fbinds "}")` — that last one is
  *record update* syntax (producing a new, independent value with one
  field changed), not `receiver.method()` dispatch. There is no `aexp "."
  name` alternative anywhere in the grammar for a method or field lookup
  to live in.
- There is no `"new"` terminal anywhere in the grammar. Values of a `data`
  type are produced by writing a constructor applied to arguments
  (`con atype*`, via the ordinary juxtaposition in `fexp`/`aexp`) — the
  same mechanism that builds every other value in the language, not a
  dedicated allocation-and-initialization step.
- There is no `this`/`self` anywhere, because there is no implicit
  receiver for a method body to be implicitly scoped against — every
  Haskell function, including one that happens to be part of an
  `instance`, takes every one of its arguments explicitly.

Modula-3 and Ada (§1 above) avoid the *word* "class" but still have
objects, dot-style field/method access, and an `Ancestor`/`new ... with`
inheritance relationship underneath a different name. Haskell is a level
further out: it has neither the word nor any of the underlying mechanism
that word would otherwise be naming.

**Second, what `class`/`instance` actually are.**

```
haskell: topdecl ::= ... | ("class" optscontext tycls tyvar "where" cdecls) | ...
         topdecl ::= ... | ("instance" optscontext qtycls inst "where" idecls) | ...
         cdecl   ::= decl
```

A Haskell `class` declares a set of operations some as-yet-unspecified
type must support — a compile-time *predicate over types* ("any `a` you
plug in here must provide these functions"), resolved by the compiler
passing an implicit dictionary of those functions around, not by runtime
dispatch through an object's identity. `cdecls` reuses the fully generic
`decl` production for default method bodies — a default implementation is
an ordinary function definition, not a distinct "virtual method" grammar
category the way C#'s `virtual`/`override` modifiers are.

An `instance` declaration is where the real contrast with every
inheritance mechanism in §2–§4 shows up. `instance Eq Int where ...`
supplies the operations `Eq` requires *for the already-existing type
`Int`* — it does not derive a new type from anything, does not add fields
to `Int`, and `Int`'s own definition (wherever it lives) never has to
mention `Eq` at all. Compare this directly to Java's
`class Foo implements Comparable`: Java's coupling is mandatory and
declared at the type's *own* definition site; a type and the interfaces it
satisfies must be written together, by the same author, in the same
place. Haskell's `instance` can be written anywhere — in a completely
different module, by a completely different author, long after both the
type and the class were independently defined — making Haskell's
polymorphism **open and retroactive** where Java's is **closed and
declaration-site-only**. This is the same "who has to coordinate, and
when" axis `types-and-generics-analysis.md` §2 already uses to contrast
Java's use-site generic variance with C#'s declaration-site variance —
here it's the same question applied to interface conformance itself
rather than to variance specifically.

**Third, the part that genuinely does look like inheritance, and why it
isn't.** `optscontext`/`scontext` let a class declaration itself carry a
constraint: `class Eq a => Ord a where ...`. Haskell's own community
jargon calls this "`Ord` is a subclass of `Eq`," and the resemblance to
§2's "base class plus interfaces" shape is real enough that the loose
description sticks. But structurally it means something different: it's
a *constraint* — "you are only permitted to write `instance Ord T` once
`instance Eq T` already exists" — not an is-a relationship between
objects, and not a code-reuse mechanism (no method bodies, fields, or
dispatch tables are inherited by writing this constraint; each `instance`
still independently supplies everything its own class requires). There is
no object whose runtime type is "an `Ord` that also happens to be an
`Eq`," because there are no runtime objects with identity here to begin
with — only ordinary values and compiler-resolved dictionaries. Calling it
"subclassing" is a convenient analogy, not an accurate description of the
grammar underneath it.

**Fourth, the closest thing to a built-in "write the common boilerplate
for me" mechanism**, and why it still isn't inheritance: `deriving ::=
"deriving" dclasses`, attached optionally to a `data`/`newtype`
declaration. `data Color = Red | Green | Blue deriving (Eq, Show)` asks
the compiler to synthesize an `Eq`/`Show` instance automatically rather
than writing one by hand. It's the one place Haskell's grammar offers
something like "get this behavior for free without writing it yourself,"
the same motivating itch that inheritance satisfies elsewhere in this
document — but what gets generated is still an ordinary, independent
`instance` for that one specific type; nothing resembling a hierarchy, an
`Ancestor`, or a shared implementation slot other types could further
override exists on the other end of it.

## 8. Swift's `extension`: retroactive conformance inside an OO language

Swift is the one class-based language in the corpus with a grammar-level
answer to the problem Haskell's `instance` solves (§7):

```
swift: extension_declaration ::= "extension" type_identifier [type_inheritance_clause] extension_body
       extension_body        ::= "{" [declarations] "}"
```

`extension Int : Printable { ... }` names an *already-existing* type,
optionally lists protocols for it to conform to, and adds members to it —
written anywhere, by anyone, without touching `Int`'s own definition. That
is the same "open and retroactive" property §7 contrasts with Java's
declaration-site-only `implements`, now sitting next to ordinary classes,
inheritance, and `self`/`super` dispatch. The grammar draws no line
between an extension that only adds methods and one that adds a
conformance: the conformance is just the same optional
`type_inheritance_clause` every other Swift type declaration uses. (Delphi's
`"helper" "for" id`, §3, is the nearest relative elsewhere in the corpus,
but it only adds members to an existing type; it can't make that type
satisfy an interface.)

## 9. Objects without class syntax: Smalltalk, Lua, Erlang

These three grammars all lack every class-declaration production surveyed
above, for three different reasons.

**Smalltalk: the class definition is a message send.** The Redline grammar
is rooted at `script ::= ws sequence EOF`, and everything below it is
expressions: `expression ::= assignment | cascade | keywordSend |
binarySend | primitive`, with message sends built from `unarySend`,
`binaryTail`, and `keywordMessage ::= (keywordPair ws)+`. There is no
class-declaration production, no superclass slot, and — notably — no
*method*-definition production either (no selector-pattern header for a
method body): the grammar describes the contents of a method or a
workspace "doit," not a source file of class definitions. The only
OO-specific vocabulary in the whole grammar is
`RESERVED_WORD ::= "nil" | "true" | "false" | "self" | "super"`, reached
through `pseudoVariable`. (From general language knowledge: Smalltalk
creates a class by sending a keyword message to its intended superclass —
`Object subclass: #Dog instanceVariableNames: 'name' classVariableNames: ''
package: 'Zoo'` — which this grammar parses as an ordinary `keywordSend`
whose arguments are a symbol and strings; methods are then added to the
class through the development environment rather than through
file-level syntax.) So the language that is the reference point for "pure
OO" has, in this grammar, *less* class syntax than C++ or Java: subclassing
is the same operation as every other computation — sending a message to an
object, here the object that happens to be the parent class.

**Lua: classes by convention, with one piece of grammar support.** Lua 5.2
has no class, object, inheritance, `new`, or `self` production — not even
a `"self"` terminal. Objects are tables (`tableconstructor ::= "{"
[fieldlist] "}"`), and the only syntax that exists for them is the colon:

```
lua: funcname    ::= NAME ("." NAME)* [(":" NAME)]
     nameAndArgs ::= [(":" NAME)] args
```

`function Account:deposit(v) ... end` and `acct:deposit(100)` are the
method-definition and method-call sugar. (From general language knowledge:
the definition form adds an implicit first parameter named `self`, and the
call form passes the receiver as that first argument; inheritance is built
by hand with metatables and `__index`, which are ordinary library calls
and table fields as far as the grammar is concerned.) Lua is therefore the
corpus's purest "built by convention, not grammar" case: the grammar
contributes exactly one token's worth of receiver-passing shorthand, and
the class, the parent link, and even the name `self` are all runtime
convention.

**Erlang: a paradigm-based absence, like Haskell.** The grammar is rooted
at `forms ::= (form)+ EOF` with `form ::= (attribute | function |
ruleClauses) "."`. Module-level structure is entirely generic attributes —
`attribute ::= "-" tokAtom attrVal | ...` — so `-module(dog).`,
`-export([...]).`, `-record(...)`, and `-behaviour(gen_server).` are not
keywords at all, just atoms after a dash. Functions are
`functionClause ::= tokAtom clauseArgs clauseGuard clauseBody` with every
argument explicit; there is no `this`/`self`, no `new`, and the only `:` in
call position is `expr800 ::= exprMax [(":" exprMax)]`, a
*module-qualified* call (`lists:map(...)`), not dispatch on a receiver.
Records (`recordExpr ::= [exprMax] "#" tokAtom ("." tokAtom | recordTuple)`)
are named tuples with field access, not objects. What Erlang has instead
is processes: `receiveExpr ::= "receive" crClauses ... "end"` and the send
operator in `expr100 ::= expr150 (("=" | "!") expr150)*`. (From general
language knowledge, a process looping on `receive` with private state is
often described as Erlang's "object," with `Pid ! Msg` as the message send
— closer to Smalltalk's original message-passing metaphor than any
class-based language here, but with no class, inheritance, or shared
implementation anywhere in the grammar.) The one interface-like construct
is `AttrName ::= "-" ("spec" | "callback")`: a behaviour module declares
`-callback` signatures that any module claiming `-behaviour(...)` must
implement — a contract between *modules*, checked (from general language
knowledge) by the compiler as a warning, with no type or object involved.

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
invented for the interface case. Swift's flat `type_inheritance_clause`
can't be explained the same way — it was designed in one piece, not
layered on — and is better read as a deliberate choice to use one
"conforms to" notation for every kind of type (class, struct, protocol,
extension), with the superclass treated as just one more thing a class
conforms to. C#'s nominally-split-but-ambiguous `class-base` sits between
the two: it states the Java rule in its productions while sharing Delphi's
one-colon, one-list surface syntax, inherited from C++'s `:` base list.

**VB6 having no implementation inheritance at all.** COM, the platform
VB6 was built around, was deliberately designed around interface-based
polymorphism rather than implementation inheritance (a well-documented COM
design principle — COM objects communicate purely through interfaces, and
COM itself has no notion of inheriting an existing object's code). VB6's
`Implements`-only, no-`Inherits` object model is a direct reflection of
the platform it was designed to be a thin, approachable layer over, not an
arbitrary limitation of the language's own grammar design.

**Why Haskell has no class/object model at all, and why `class`/`instance`
exist anyway.** This is a paradigm-level decision, not an oversight or a
dating artifact: Haskell's entire design commits to values that never
mutate and functions with no hidden state, which removes the one thing an
object-oriented method-dispatch model is fundamentally organized around —
a persistent, mutable, identity-bearing receiver that a method call is
"sent to." With no such receiver, there is nothing for `this`/`self`, for
a dot-call operator, or for an inheritance-of-implementation mechanism to
attach to. The `class`/`instance` keywords exist to solve a real,
separate problem Haskell still has despite rejecting objects entirely:
ad-hoc polymorphism, i.e. letting one function name (`==`, `show`, `+`)
work differently depending on the type it's applied to, without requiring
every type to be known in advance the way a single global case-dispatch
function would. Reusing the word "class" for this was a deliberate,
if arguably confusing in hindsight, choice by Haskell's designers (the
mechanism was introduced specifically in the paper that coined the term
"type class," by Wadler and Blott) to signal "a classification of types
by shared capability," by analogy with an OOP class's "classification of
objects by shared capability" — the analogy is in what problem the
mechanism addresses, not in how it's built or how it behaves.

**Why Erlang has no classes either.** Same category of reason as Haskell,
reached from a different starting point: Erlang was designed (from general
language knowledge) for fault-tolerant telecom systems, where the unit of
encapsulation that matters is an isolated, separately-failing process
owning its own state, not an object sharing a heap with its callers. Once
state lives inside processes and is reached only by sending messages
(`!`/`receive`), there's nothing left for a class to encapsulate, and
code reuse across modules is handled by behaviours — a module-level
`-callback` contract — rather than by inheriting implementation.

**Why Smalltalk's grammar has no class syntax.** Smalltalk takes "everything
is an object, all computation is message sending" literally enough that
classes are themselves objects, and making a new one is a message to an
existing class (`subclass:...`). A dedicated class-declaration production
would be redundant with the expression grammar — so the language that
most fully commits to OO ends up, at the grammar level, looking more like
Lua than like Java. (Smalltalk's image-based development model, where
classes and methods are created and edited through a browser rather than
written as a linear source file, is also why a file-level grammar like
this one only needs to cover method bodies and expressions — general
language knowledge, not something the grammar itself shows.)

**Why Lua stops at the colon.** Lua's design (from general language
knowledge) aims at a small embeddable core offering *mechanisms*, not
policies: tables, metatables, and first-class functions are enough to
build classes, prototypes, or mixins, and choosing one object model in
the grammar would exclude the others. The `:` sugar is the single
concession — the one piece of OO boilerplate (passing the receiver
explicitly) common to every object model a Lua programmer might build.

**The constructor spectrum.** This tracks the same "how much does the
grammar encode vs. leave to convention" axis seen throughout this whole
analysis. C#, Dart, and Swift's fully dedicated constructor productions reflect
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
(attribute existence, method resolution) the same dynamic way. Smalltalk
and Lua take that one step further: with no class in the grammar, a
constructor is just whatever message or function a programmer chooses to
call `new`.

## Summary of cross-cutting patterns

- **The single-base-plus-multiple-interfaces shape is the strongest
  convergent signal in this analysis** — five unrelated languages across
  four decades (Ada 1995/2005, Java 1995, PHP, C# 2000s, Dart 2010s)
  arrived at the identical rule for the same underlying problem, using
  entirely different keywords each time (and Swift, from general language
  knowledge, enforces it too). The rule converges more than the grammar
  does, though: only Java, Dart, Ada, and PHP give base and interfaces
  separate syntactic slots, while Delphi, Swift, and — despite appearances —
  C# all use one list the grammar alone can't split (§3).
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
  caveat already established for lambdas. Haskell's and Erlang's absence
  of classes are the genuine exceptions to "always check the era" here:
  Haskell 98 is contemporaneous with Java and early C#, and the Erlang
  R16B01 grammar (2013) with C# 4.0 and Dart, all unambiguously
  object-oriented languages by then, so there is no vintage story
  available — the absence is a direct consequence of paradigm, confirmed
  by §7's and §9's structural evidence (no dot-call production, no
  `"new"`, no implicit receiver), not a feature the grammar simply
  predates. Lua 5.2 (2011) is a third kind of exception: neither too old
  nor a different paradigm, but a deliberate choice to leave the object
  model out of the grammar.
- **Grammar-level class syntax doesn't track how object-oriented a
  language is.** Smalltalk, the reference point for pure OO, has no
  class-declaration production in this grammar at all, because defining a
  class is just a message send (§9); Lua builds objects entirely by
  convention around one `:` shorthand. Class syntax measures how much of
  the object model a language chose to make *declarative*, not how central
  objects are to it.
- **A superficial keyword match (`class`) is weaker evidence than a
  structural one** — the single clearest instance across all four of
  these companion analyses of why "grep the grammar for a familiar word"
  isn't the same as "the same mechanism is present." Haskell's `class` and
  `instance` solve ad-hoc polymorphism, a real and recognizable problem
  from the OOP survey above, but do so with open, retroactive, receiver-
  free dictionary-passing rather than inheritance, dispatch, or object
  identity — every grammar production that would evidence an actual object
  model is the one that's missing. The same lesson shows up in smaller form
  twice more: COBOL's `"CLASS"` clause names a character set, and this JS
  grammar's `"class"` is a stray reserved atom in `js_primary_expn` — a
  grep hit for "class" in both, and no classes in either.
