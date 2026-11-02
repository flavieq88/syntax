# Functions across `grammar-zoo-flavie-adapted`: definitions, calls, and parameters

An analysis of how each of the 20 languages in the curated corpus handles
function definition, invocation, parameter passing, and return values,
based on the actual productions in `normalized-ebnf-flavie-adapted/`.
COBOL here is `cobol-vscobolii-lammel-gdk`; "Basic" and "VB6" both refer
to the single grammar `basic-visual-concrete`. Two of the 20 have no
user-defined function *definition* syntax at all in their grammar —
COBOL (§1) and Smalltalk, whose `smalltalk-redline-ladd` grammar covers
only statements and expressions (message sends and blocks), with no
method-definition production — so they appear below mainly in the call,
return, and anonymous-function sections.

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
| Swift | `function_declaration ::= function_head function_name [generic_parameter_clause] function_signature function_body`, with `function_head ::= [attributes] [declaration_specifiers] "func"` and `function_signature ::= parameter_clauses [function_result]` — one keyword (`func`), the `-> Type` (`function_result ::= "->" [attributes] type`) simply optional, Modula-3's shape with an arrow in place of the colon. Initializers and deinitializers are separate productions (`"init"`, `"deinit"`), not variants of `func` |
| Lua | `"function" funcname funcbody` and `"local" "function" NAME funcbody` (both alternatives of `stat`), sharing `funcbody ::= "(" [parlist] ")" block "end"` — one keyword, and no return-type slot at all (dynamically typed) |
| Haskell | goes a full step further: there isn't even a definition keyword to drop. `decl ::= gendecl \| (funlhs rhs) \| (pat0n rhs)` — a multi-parameter binding (`funlhs ::= (var apat ...) \| ...`, at least one `apat`) and a zero-parameter binding (`pat0n rhs`, an ordinary pattern binding) are two alternatives of the *same* `decl` production, with no keyword anywhere distinguishing "this introduces a function" from "this introduces a value." `add x y = x + y` and `pi = 3.14159` are grammatically the same kind of thing, differing only in whether the left-hand side happens to carry parameters |
| Erlang | also no definition keyword: `function ::= functionClause (";" functionClause)*`, `functionClause ::= tokAtom clauseArgs clauseGuard clauseBody`, `clauseBody ::= "->" exprs`, and the whole `form` ends in `"."`. A function is just one or more `name(Args) [when Guard] -> Body` clauses, with the atom name *repeated on every clause*. Unlike Haskell, `clauseArgs ::= argumentList ::= "(" [exprs] ")"` always carries parentheses, so a zero-argument function is still written `f() -> ...` and stays grammatically distinct from a value |

**COBOL doesn't fit either camp — it has no user-defined function/procedure
concept at this grammar version at all.** The closest things COBOL has are
`paragraph`/`section` (a named label followed by a run of statements,
invoked via `PERFORM` — see §2) and whole separate, independently-compiled
*programs* invoked via `CALL`; neither takes a formal parameter list the
way every other language in this section does (`CALL` passes data via
`USING`, covered in §3, but a paragraph has no parameter list
whatsoever — see §2). `cobol_source_program`'s `PROCEDURE DIVISION
USING ...` also has no `RETURNING` clause in this grammar, consistent
with VS COBOL II (1985) predating COBOL 2002's `FUNCTION` and
intrinsic-function additions — another instance of this analysis's
recurring "absence is often a dating artifact" theme (§6).

**Smalltalk doesn't fit either camp for a different reason: this grammar
has no definition syntax to classify.** `smalltalk-redline-ladd`'s root is
`script ::= ws sequence EOF`, and nothing reachable from it defines a
named method — there is no message-pattern/selector-header production at
all. The only callable thing the grammar can create is a block,
`block ::= BLOCK_START [blockParamList] ws [sequence] BLOCK_END` (§6). As
general language knowledge, Smalltalk methods are traditionally written
in a class browser one at a time rather than in a file, so a
statement-level grammar like this one simply never needs a method header;
the absence is a scope choice of the grammar, not a missing feature.

This is a real lineage signal: every language on the "two keywords" side
(Ada, Fortran, Pascal, Basic) predates or was contemporaneous with the
early structured-programming era and inherited the distinction from Algol
60's own `procedure` (Algol only had procedures; a "function" was a
procedure whose body assigns to its own name). Modula-3 — designed by
Wirth's collaborators specifically as a cleanup of Pascal-family clutter —
is the one member of that lineage that deliberately *dropped* the
distinction. Every other language in the corpus (all younger, and outside
that direct lineage) never had it to drop. Haskell sits a further step
beyond even Modula-3: Modula-3 still spells `PROCEDURE` on every
definition, it simply doesn't fork into two keyword categories; Haskell has
no definition keyword at all for this, callable or not. That's not a small
difference in degree — it's only possible because a Haskell function
*body* is a single expression (`rhs ::= "=" exp wheredecls | ...`), so a
"function" is, structurally, nothing but a named value whose left-hand
side happens to pattern-match some arguments before yielding that
expression; there's no separate grammatical machinery for "callable thing"
to need its own keyword in the first place. Erlang reaches the same "no
keyword" outcome by a slightly different route: its body is a
comma-separated sequence (`clauseBody ::= "->" exprs`) rather than a single
expression, but every top-level `form` is already either an `attribute`
(introduced by `-`) or a function/rule clause (introduced by an atom), so
the leading token is enough to tell them apart without a keyword.

## 2. Function calls: a dedicated node, or folded into expression grammar?

Splits almost exactly along "does the language have a separate statement
form for calls used only for their side effect" vs. "a call is just one
more kind of expression."

**Dedicated call production**

| Language | Production |
|---|---|
| Ada | `procedure_call_statement ::= procedure_name ";" \| procedure_prefix actual_parameter_part ";"` — note this is a genuinely distinct rule from `function_call`, because Ada's grammar-level procedure/function split (§1) carries all the way through to call sites |
| Fortran-90 | `CallStmt ::= (LblDef "call" SubroutineNameUse EOS) \| (LblDef "call" SubroutineNameUse "(" SubroutineArgList ")" EOS)` — the `call` *keyword* itself is required, unlike every other language's subroutine call (COBOL's `CALL`/`PERFORM`, below, are the only other mandatory call keywords) |
| Modula-3 | `CallStmt ::= Expr "(" [(Actual ("," Actual)*)] ")"` |
| Lua | `functioncall ::= varOrExp (nameAndArgs)+`, reachable only from `stat` — the expression side builds calls separately through `prefixexp ::= varOrExp (nameAndArgs)*`. `nameAndArgs ::= [":" NAME] args` folds in the `obj:method(...)` colon-call form, and `args ::= ("(" [explist] ")") \| tableconstructor \| string` lets a single table or string literal stand in for the parenthesized list (`f{...}`, `f"..."`) |
| Basic (VB6) | `call_statement ::= ["call"] reference [subroutine_bracketless_params]` — keyword is *optional*, a vestige of older Basic dialects that required it |
| Eiffel | `Call ::= Object_call \| Non_object_call`, further split into `Unqualified_call`/`Explicit_creation_call`/`Non_object_call` — the richest call taxonomy in the corpus, reflecting Eiffel's object-call-centric design (every call is conceptually "send a message to a target") |
| PHP | `CallParams ::= "(" CallParam,* ")"` as its own node, referenced from a general `VariableOrFunctionCall` |

**A fourth variant: a dedicated call keyword that genuinely has no
argument list at all**

| Language | Production |
|---|---|
| COBOL | `perform_statement_format_i ::= "PERFORM" ((procedure_name [(("THROUGH" \| "THRU") procedure_name)]) \| ([series_of_imperative_statements] "END-PERFORM"))` |

Every language in the first table above at least has an argument list in
its dedicated call node, even the ones with mandatory keywords (Fortran's
`CallStmt`). COBOL's `PERFORM procedure-name` has none —
not optional, genuinely absent from the production — because a COBOL
paragraph or section isn't a subroutine with its own parameters at all;
it's a named label that operates directly on whatever `DATA DIVISION`
variables are already in scope, closer to a structured `GOSUB` than a
call in the sense every other language in this document means it. Real
parameter passing in COBOL exists, but only one level up, at the
`CALL ... USING` statement that invokes an entirely separate, independently
compiled *program* (§3) — COBOL keeps "jump to a label within this
program" and "invoke another program with data" as two structurally
unrelated mechanisms, rather than one generalized function-call concept
covering both.

**No dedicated call node — folded into the primary/postfix expression chain**

| Language | Where the call lives |
|---|---|
| C99/C++98 | `postfix-expression ::= postfix-expression "(" [argument-expression-list] ")" \| ...` — a call is just one more postfix operator, alongside `[]`, `.`, `->`, `++` |
| C# | `invocation-expression ::= primary-expression "(" [argument-list] ")"`, one alternative of `primary-no-array-creation-expression` |
| Java | folded into `identifierSuffix`/`arguments` off of `primary` |
| Dart | folded into `selector`/`arguments` off of `postfixExpression` |
| Python | `trailer ::= "(" arglist ")" \| "[" ... "]" \| "." id` — a call is one of three possible *trailers* on an atom, exactly parallel to indexing and attribute access |
| JS | `js_selector ::= js_arguments \| js_subscripts \| js_field_selector`, chained by `js_member_expn ::= js_primary_expn (js_selector)*` — the same three-way call/index/member parallel as Python |
| Swift | `expression ::= ... \| (expression parenthesized_expression [trailing_closure]) \| (expression "." identifier ...) \| (expression "[" expression_list "]") \| ...` — call, member access, and subscript are sibling left-recursive alternatives of one `expression` rule; the optional `trailing_closure` lets a closure argument follow the `)` |
| Erlang | `functionCall ::= expr800 argumentList`, one alternative of `expr700 ::= functionCall \| recordExpr \| expr800`, where `expr800 ::= exprMax [":" exprMax]` supplies the optional `module:` qualifier. It has its own nonterminal name, like C#'s `invocation-expression`, but sits inside the operator-precedence chain rather than at statement level — Erlang has no statements to put it in |

**No delimiter at all — a call is bare juxtaposition**

| Language | Production |
|---|---|
| Haskell | `fexp ::= (fexp aexp) \| aexp` |

This is a third category, structurally distinct from both groups above —
not "its own dedicated node" and not "folded in as one more postfix
operator alongside `[]`/`.`" either, since there's no operator token at
all. `f x y` parses, by this left-recursive production alone, as
`(f x) y`: an expression immediately followed by another expression *is* a
call, with nothing — no parenthesis, no comma — marking it as one.
This is exactly the "whitespace-only, no delimiter" pattern §7 below
predicted conceptually but couldn't verify against a real grammar in this
corpus before Haskell was added — it is now directly confirmed. It's also the clean mechanical reason Haskell
functions are curried by default rather than by special-casing: `f x y` is
not "one call with two arguments" grammatically, it's two single-argument
applications in a row, which is precisely why partial application
(`map (add 1) xs`) needs no special syntax of its own — `add 1` is already
a complete, ordinary `fexp`.

**No call at all — only message sends, with arguments interleaved into the
selector**

| Language | Production |
|---|---|
| Smalltalk | `expression ::= assignment \| cascade \| keywordSend \| binarySend \| primitive`; `unarySend ::= operand ws [unaryTail]`, `binarySend ::= unarySend [binaryTail]`, `keywordSend ::= binarySend keywordMessage`, `keywordMessage ::= ws (keywordPair ws)+`, `keywordPair ::= KEYWORD ws binarySend ws`, `KEYWORD ::= IDENTIFIER COLON` |

This is yet another shape, distinct from all of the above. There is no
function-call construct whatsoever: every operation, including arithmetic
(`binarySend`), is a message sent to a receiver, and the three message
kinds (unary, binary, keyword) are what fix precedence — unary binds
tighter than binary, binary tighter than keyword, purely by which
nonterminal nests inside which. A keyword message has no argument list
either: `dict at: k put: v` splits the selector `at:put:` into
`keywordPair`s, each `KEYWORD` immediately followed by its own argument,
so each argument is labeled by the selector piece in front of it and no
parenthesis or comma is involved. `cascade ::= ws (keywordSend |
binarySend) ((ws SEMI_COLON ws message))+` adds one more call-site form no
other grammar here has: `;` sends further messages to the *same* receiver
as the previous send. Eiffel's "every call is conceptually sending a
message to a target" (first table) is a semantic framing; Smalltalk is the
one grammar where it is literally the only syntax.

The second group is a genuine convergent pattern across otherwise unrelated
lineages (C, Java, Dart, Python, JS, Swift) — all of them model "call", "index", and
"member access" as the *same kind of grammatical thing* (a postfix operator
chained onto a primary expression), which is precisely why `f(x)[0].y(z)`
parses uniformly in all of them. The first group (Ada, Fortran, Modula-3,
Eiffel, PHP, Basic, Lua) is exactly the same set of languages that also keep a
strict statement/expression distinction elsewhere in their grammars. Lua
is a clean confirmation from outside the Algol lineage: its `stat`
alternatives admit `functioncall` but no general expression, so a call is
the only expression-like thing allowed to stand alone as a statement, and
the grammar needs a separate call production to say so. Erlang is the
mirror image — with no statement category at all, its `functionCall`
could only ever live inside the expression chain.

## 3. Parameter-passing mode: explicit in the grammar, or left implicit?

A parameter's passing convention (by value vs. by reference) is either a
first-class grammatical annotation on the parameter, or entirely absent
from the syntax (left to semantics/typing rules the BGF-level grammar
doesn't capture).

| Language | Mechanism |
|---|---|
| Ada | `mode ::= ["in"] \| ("in" "out") \| "out"` — three-way mode is mandatory grammar, directly on `parameter_specification` |
| Modula-3 | `Formal ::= [("VALUE" \| "VAR" \| "READONLY")] IDList ":" Type ...` — same three-way idea (by-value / by-reference / read-only-reference), inherited straight from Modula-3's Ada-adjacent design lineage |
| Pascal/Delphi | `formal_parameter ::= [parm_qual] parameter`, `parm_qual ::= "var" \| "const" \| "out"` — the same three-way idea again (by-reference / read-only / output-only), with plain by-value as the unmarked default |
| Basic (VB6) | `byref_or_byval ::= "byref" \| "byval"` — binary choice, appears on `subprogram_argument`, `event_argument`, and `property_argument` alike |
| C# | `parameter-modifier ::= "ref" \| "out" \| "this"` — binary reference modifiers, plus the C#-specific `this` marking an extension-method receiver. The mode is repeated at the call site too: `argument-value ::= expression \| ("ref" variable-reference) \| ("out" variable-reference)` |
| Swift | `parameter ::= (["inout"] ["let"] ["#"] parameter_name [local_parameter_name] type_annotation [default_argument_clause]) \| (["inout"] "var" ...) \| ...` — a single `inout` keyword (copy-in/copy-out, per general language knowledge), plus `let`/`var` choosing whether the callee's local copy is mutable. Like C#, the call site must mark it as well: `in_out_expression ::= "&" identifier`, an alternative of `expression` |
| COBOL | `call_using_phrase ::= "USING" ((([(["BY"] "REFERENCE")] (identifier \| ("ADDRESS" "OF" identifier) \| file_name)+) \| (["BY"] "CONTENT" (([("LENGTH" "OF")] identifier) \| ("ADDRESS" "OF" identifier) \| literal)+))+` — `BY REFERENCE` (the default, and the whole phrase is optional) and `BY CONTENT` (pass a copy) are explicit per-group modifiers on `CALL ... USING`'s argument list, textually closest in spirit to Ada's/Modula-3's mode keywords despite COBOL predating both — note this is only ever on the separate-program `CALL`, never on a parameterless `PERFORM` (§2), since paragraphs have no parameters to mark a mode on in the first place |
| C99, C++98, Java, JS, Python, PHP, Dart, Eiffel, Haskell, Erlang, Lua, Smalltalk | **no such production at all** — parameter passing convention isn't expressed in the syntax; it's a fixed, non-negotiable semantic rule of the language (C/Java/JS: always by value, or by reference-to-object for objects; Python, Lua, Smalltalk: same; PHP has an explicit `&` reference-sigil, see below). Haskell's case is the most settled of the group: under lazy evaluation every argument is passed as an unevaluated thunk regardless of type, so there is nothing a by-value/by-reference distinction could even apply to at the call site. Erlang is similarly settled for a different reason (general language knowledge): all data is immutable, so by-value and by-reference are observationally identical. Smalltalk's block parameters (`BLOCK_PARAM ::= COLON IDENTIFIER`) carry nothing but a name |

PHP is a partial exception worth calling out on its own: `Param ::= (
[TypeHint] ["&"] TVariable [EqualsStaticScalar] ) | ...` — the `&` here
*is* a by-reference marker, but it's a lone optional token bolted onto an
otherwise ordinary parameter, not a first-class mode system like Ada's.
The same `&` also appears on the caller's side, `CallParam ::= ["&"]
Expr` (call-time pass-by-reference, which later PHP versions removed —
general language knowledge).

Fortran-90 is a second partial exception, structurally unlike everything
in the table above: `IntentStmt ::= "intent" "(" IntentSpec ")" [ColonColon] IntentParList`
and `OptionalStmt ::= "optional" [ColonColon] OptionalParList` exist, but
as their own free-standing declarative *statements* inside the
specification part, naming already-declared dummy arguments by reference —
not as an inline annotation on the parameter list itself the way Ada's
`x : in out Integer` or Basic's `ByRef x` are. Fortran-90 genuinely has
both concepts (mode and optionality); it just can't attach them at the
parameter-list production the way the others do.

The pattern: **only Ada, Modula-3, Pascal/Delphi, Basic, C#, Swift, and
COBOL make parameter-passing mode syntactically explicit on the parameter
itself** (COBOL's case is on `CALL`'s argument group rather than a
function's own parameter list, since that's the only place COBOL has
arguments to mark at all — §2), and most of those are again the
"two-keyword" structured-programming lineage from §1 (Ada, Pascal, Basic)
or its direct descendant Modula-3 — a language family that consistently
treats things other languages leave to convention as worth spelling out in
the grammar itself. C# and Swift are the interesting outliers, reaching
for the same idea for entirely different, much later reasons (interop
with unmanaged code and LINQ extension methods for C#; for Swift, general
language knowledge suggests Objective-C/C interop, where pointer
out-parameters are common) — and they are also the only two grammars in
this table with a call-site counterpart to the parameter mode (`ref x`/`out
x`, `&x`), so a reader of the call can see which arguments may be mutated
(PHP's optional call-site `&`, above, is the only other call-site
reference marker in the corpus).

## 4. Variadic and default parameters

**Variadic (arbitrary-arity) parameters**

| Language | Form |
|---|---|
| C99 | `parameter-type-list ::= parameter-list \| parameter-list "," "..."` — trailing literal `...` |
| C++98 | identical `... ` form, plus it's also legal as a parameter list *by itself* with nothing before it |
| Java 5 | `formalParameterDeclsRest ::= ... \| "..." variableDeclaratorId` — Java 5's newly-added varargs, deliberately reusing C's `...` spelling for familiarity |
| Python | (from the base grammar, confirmed via `varargslist`) `"*" id` / `"**" id` — single- and double-star forms, for positional- and keyword-variadic respectively; entirely different spelling from the C lineage despite the same purpose |
| PHP (this Cordy grammar) | no variadic form present — `func_get_args()` was the only mechanism at the PHP version this grammar targets |
| C# | `parameter-array ::= [attributes] "params" array-type identifier` — variadic via a keyword (`params`) plus an ordinary array type, not special punctuation |
| Basic (VB6) | `property_argument ::= ["optional"] [byref_or_byval] ["paramarray"] id ...` — a keyword form like C#'s, but in this grammar only on `property_argument`; `subprogram_argument` has no `paramarray` slot (real VB6 allows `ParamArray` on ordinary `Sub`/`Function` parameters too, so this looks like a gap in the extraction) |
| Lua | `parlist ::= (namelist [("," "...")]) \| "..."` — C's trailing `...` again, and `"..."` is also one of the alternatives of `exp` itself, so the variadic values are read back in the body through the same token rather than through a named parameter |
| Swift | `parameter_clause ::= ("(" ")") \| ("(" parameter_list ["..."] ")")` — trailing `...`, but placed after the *whole* parameter list rather than attached to one parameter (as general language knowledge, real Swift writes it after the last parameter's type, `xs: Int...`, which this grammar's placement also happens to accept as text) |
| Pascal/Delphi | no parameter-level slot, but the *type* grammar has `array_type ::= ("array" of_const) \| ...` with `of_const ::= "of" "const"` — Delphi's `array of const`, which (general language knowledge) is legal only as a parameter type and is how routines like `Format` take arbitrary argument lists: C#'s "ordinary array type" approach without even the `params` keyword |
| Ada, Modula-3, Fortran-90, Eiffel, JS (this grammar), Dart, Haskell, Erlang, Smalltalk | none |

Three different notations for the same concept — trailing `...` (C
lineage, also Lua and Swift), a leading sigil (Python's `*`/`**`), and a
keyword plus an array type (C#, Basic's `paramarray`) — is a clean
three-way split with no clear convergence. Erlang's absence is principled
rather than a dating artifact (general language knowledge): a function's
arity is part of its identity (`fun name/2` in `funExpr ::= "fun" tokAtom
"/" tokInteger ...` names one specific arity), so `f/2` and `f/3` are
simply different functions. Its type language does have a
"variable-arity" spelling, `funType100 ::= ("(" "..." ")" "->" topType) |
funType`, but only for *describing* fun types in `-spec`s, never in a
clause head.

**Default parameter values**

| Language | Form |
|---|---|
| Ada | `parameter_specification ::= ... [":=" default_expression]` |
| C++98 | `parameter-declaration ::= decl-specifier-seq declarator ["=" assignment-expression] \| ...` — present since C++98 itself (corrected from an earlier version of this analysis, which missed it) |
| C# | `fixed-parameter ::= ... [default-argument]` |
| Dart | `defaultFormalParameter ::= normalFormalParameter ["=" constantExpression]` — but only inside `namedFormalParameters` (Dart's bracketed optional-parameter group), not on ordinary positional parameters |
| PHP | `Param ::= ... [EqualsStaticScalar]` |
| Pascal/Delphi | `parameter ::= sep*(id, ",") [parameter_type]`, `parameter_type ::= colon_type [param_init]`, `param_init ::= equal expr` |
| Python | `fpdef_test ::= (endofline)* fpdef [is_test] [endofline]`, `is_test ::= "=" (endofline)* test` |
| Swift | `parameter ::= ... type_annotation [default_argument_clause]`, `default_argument_clause ::= "=" expression` |
| Basic (VB6) | `subprogram_argument ::= ["optional"] ... [equals_expn]` — notably requires an explicit `optional` keyword *in addition to* the default value, where every other language treats "has a default" as sufficient by itself to make a parameter optional |
| Modula-3 | grammar has `Formal ::= [mode] IDList ":" Type "&" ":=" ConstExpr` — but the `":=" ConstExpr` is *not* bracketed optional, and the literal `"&"` immediately before it doesn't correspond to any real Modula-3 syntax. The same `"&" ":="` pair also appears verbatim in `VariableDecl`, `Field`, and `Method`, which strongly suggests a bug introduced by the Grammar Zoo's automated "connect" mutation (see `upstream-fixes/README.md`) rather than a real language feature captured correctly — real Modula-3 *does* allow `x: T := default` on formals, so this looks like a corpus defect, not a design choice |
| C99, Java, JS (this grammar), Fortran-90, Eiffel, Lua, Erlang, Smalltalk | none |

VB6's `["optional"] ... [equals_expn]` is the one genuine oddity here: it's
the only grammar in the corpus where the optionality and the default value
are two independently-optional grammatical slots rather than one implying
the other (`Optional x`, `Optional y = 5`, and `Optional z` are all
syntactically valid). Because the two slots are independent, this grammar
also accepts a default *without* `Optional` (`x = 5`); real VB6 rejects
that combination (general language knowledge), so the "default requires
`Optional`" rule lives in the compiler's semantic checks, not in this
CFG.

**Haskell has neither** — `funlhs`'s parameter list is a flat sequence of
`apat`s with no `...`-style or sigil-based variadic form and no `[... =
default]` slot anywhere in sight. This isn't a gap so much as a
consequence of §2's juxtaposition model: since `f x y` is really `(f x)
y`, there's no single "parameter list" node for a variadic marker or a
default value to attach to in the first place, only a chain of
one-argument applications. Both of the problems variadics and defaults
usually solve are instead handled at the *type* level in idiomatic
Haskell — a variable number of values becomes an ordinary list argument
(`sum :: [Int] -> Int`), and an "optional" argument becomes a `Maybe`-typed
one — pushing what other languages treat as a syntax feature into
Haskell's general-purpose algebraic-data-type mechanism instead (the same
move shows up again for nullable types in `types-and-generics-analysis.md`
§3).

## 5. Returning a value: explicit statement vs. implicit convention

This is the sharpest three-way split in the whole analysis.

**Explicit `return` keyword, a real statement production**

Ada (`simple_return_statement`/`extended_return_statement`), C99, C++98,
C#, Java, JS, Dart, PHP, Python, Modula-3, Swift (`return_statement ::=
"return" [expression]`, one alternative of `control_transfer_statement`),
Lua, Fortran-90, and VB6 (which *also* has a bare `return_statement ::=
"return"`, with no expression slot at all — because VB6 uses the mechanism
below for the value itself and `Return` alone only unwinds control) all
have a dedicated statement node containing the literal keyword
`return`/`RETURN`.

Fortran-90's case is closer to VB6's than the list suggests: its
`ReturnStmt ::= LblDef "return" [Expr] EOS` does have an expression slot,
but (general language knowledge) that expression is an *alternate-return*
index selecting which label the caller resumes at, not the function's
value. The value itself is produced by assignment, either to the
function's own name or to the variable named in the `"result" "(" Name
")"` clause that `FunctionRange` optionally carries — so Fortran also
belongs, for the value, with the assign-to-name languages below.

**Return allowed only as the final statement of a block**

Two grammars restrict *where* the explicit form may appear, not just
whether it exists:

- **Lua**: `block ::= (stat)* [retstat]`, `retstat ::= "return"
  [explist] [";"]`. `retstat` isn't one of the `stat` alternatives at all —
  it can only be the last thing in a block, so code after a `return` is a
  parse error rather than dead code. (An early return is written by
  wrapping it in its own block, `do return end` — general language
  knowledge, but directly implied by `"do" block "end"` being a `stat`.)
  `explist` also makes multiple return values (`return a, b`) ordinary
  syntax rather than a tuple-building special case.
- **Smalltalk**: `statements ::= answer | (expressions ws PERIOD ws
  answer) | (expressions [PERIOD])`, `answer ::= CARROT ws expression ws
  [PERIOD]`, `CARROT ::= "^"`. The return marker is a single punctuation
  character rather than a keyword, and like Lua's `retstat` it can only
  close a statement sequence. A `sequence` that ends without `^` simply
  has no answer in the grammar; per general language knowledge, a method
  then returns `self` and a block returns its last expression's value.

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
- **Haskell**: grepping the entire grammar for the literal terminal
  `"return"` turns up nothing at all — not even as a keyword, because
  there's no keyword to be. A function's body is `rhs ::= "=" exp
  wheredecls | gdrhs wheredecls` — simply an expression, full stop. There
  is no statement sequence for a `return` to jump out of, and so,
  structurally, no exit point for a keyword to mark: the body doesn't
  *compute and then return* a value, it *is* the value. This is a step
  further than Eiffel's and Pascal's implicit convention below — both of
  those still have an ordinary statement sequence and a magic name you
  assign into partway through it; Haskell has no statement sequence at
  all for a value to escape from early. (Haskell programmers do write
  something spelled `return` inside `do`-blocks, but it is an ordinary
  value of the `Monad` typeclass looked up like any other identifier — in
  this grammar it is just a `qvar`, reached through the completely generic
  `aexp`/`fexp` chain, with zero special-cased syntax of its own.)
- **Erlang**: no `"return"` terminal anywhere in the grammar either, but
  for a slightly different reason from Haskell's. A clause body *is* a
  sequence — `clauseBody ::= "->" exprs`, `exprs ::= expr ("," expr)*` —
  and the clause's value is (general language knowledge) simply the value
  of the last `expr` in it. There is no magic variable as in Eiffel or
  Pascal, and no way to leave the sequence early: since every element of
  `exprs` is an expression, there is no statement form a `return` could
  even be. Erlang therefore sits between Haskell (single expression) and
  the explicit-`return` languages (statement sequence with exit points): a
  sequence, but with the exit fixed at its end.
- **COBOL**: no value-returning construct at all, consistent with §1. The
  grammar's exits are `goback_statement ::= "GOBACK"`,
  `exit_program_statement ::= "EXIT" "PROGRAM"` (both leave a called
  program), and a bare `exit_statement ::= "EXIT"`; results flow back only
  through the `BY REFERENCE` arguments of §3.
- **VB6** actually straddles both camps: it has *both* a bare `Return`
  keyword (control-only, no value) *and* the classic Basic convention of
  assigning to the function's own name via the fully generic
  `assignment_statement ::= ["let"] reference "=" expn` — the same
  duplication pattern already seen in VB6's if-statement (§ dangling-else
  analysis) and default-parameter handling above: give the modern explicit
  form *and* keep the old implicit one working side by side.

The implicit-convention languages (Eiffel, Pascal) are a direct
illustration of *why* the explicit-`return` design eventually won almost
everywhere else, and Haskell is worth keeping distinct from both of them
even though it also lacks `return`: Eiffel and Pascal lack a keyword
because their designers left an older convention in place or chose not to
flag an exit point explicitly; Haskell lacks one because the thing a
keyword would mark — a mid-body exit from a sequence of statements —
doesn't exist in its grammar at all once every function body is a single
expression. One is an absence of marking; the other is an absence of the
thing being marked. a return value that's just "whatever a magic variable
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
| Haskell | `exp10n ::= ("\\" pat (pat)+ "->" exp) \| ("\\" pat "->" exp) \| ...` | not weaker than a named binding at all — a named function's body is `rhs ::= "=" exp ...` and a lambda's is `"->" exp`; both terminate in the identical bare `exp`. A lambda and a top-level definition differ only in whether there's a name and an `=` or a `->` immediately before that shared expression, which is the purest version of the JS convergence in the row below: here the two forms aren't just *structurally parallel*, they share one actual nonterminal |
| C# 4.0 | `lambda-expression ::= anonymous-function-signature "=>" anonymous-function-body`, plus a *separate*, older `anonymous-method-expression ::= "delegate" [signature] block` | C# 4.0 grammar preserves **two** anonymous-function forms side by side — the pre-3.0 `delegate { }` syntax and the newer `=>` lambda — rather than replacing one with the other |
| Dart | `functionExpression ::= [([returnType] identifier)] formalParameterList functionExpressionBody`, `functionExpressionBody ::= ("=>" expression) \| block` | the name (and return type) is an *optional* prefix of the same production, exactly as in JS below; the `=>` short form is shared with named functions (`functionBody ::= ("=>" expression ";") \| block`) |
| JS (this Cordy grammar) | `js_function_expn ::= "function" [id] "(" ... ")" ... "{" ... "}"` | the *same* production optionally takes a name — JS's function-expression and named-function-declaration are one grammar rule apart, differing only in whether `id` is present |
| Lua | `functiondef ::= "function" funcbody`, an alternative of `exp` | shares `funcbody ::= "(" [parlist] ")" block "end"` with both named forms in `stat` (`"function" funcname funcbody`, `"local" "function" NAME funcbody`) — like Haskell, the anonymous and named forms bottom out in one literal nonterminal, here a full statement block rather than a single expression. (As general language knowledge, the named statement form is defined as sugar for assigning a `functiondef` to a variable) |
| Erlang | `funExpr ::= ("fun" tokAtom "/" tokInteger) \| ("fun" atomOrVar ":" atomOrVar "/" integerOrVar) \| ("fun" funClauses "end")`, `funClause ::= argumentList clauseGuard clauseBody` | two kinds in one production: `fun name/arity` and `fun Mod:name/arity` are first-class references to existing named functions (the role Eiffel's `Call_agent` plays), while `fun ... end` is a true anonymous function. Its `funClause` is a named `functionClause` (`tokAtom clauseArgs clauseGuard clauseBody`, with `clauseArgs ::= argumentList`) minus the leading atom, so anonymous funs get multiple pattern-matched clauses and `when` guards for free; `end` is needed because, unlike a top-level `form`, a fun has no terminating `"."` to close it |
| Smalltalk | `block ::= BLOCK_START [blockParamList] ws [sequence] BLOCK_END`, `blockParamList ::= ((ws BLOCK_PARAM))+ ws [PIPE]`, `BLOCK_PARAM ::= COLON IDENTIFIER` | `[:x :y \| x + y]` — square brackets, colon-prefixed parameters, `\|` before the body, and the body is a full `sequence` (including `[temps]` local declarations). Since the grammar has no method definitions (§1), the block is the only function-forming construct it contains |
| Swift | `closure_expression ::= "{" [closure_signature] statements "}"`, `closure_signature ::= (parameter_clause [function_result] "in") \| (identifier_list [function_result] "in") \| (capture_list ...) ...` | the signature moves *inside* the braces and is closed by `in`, reusing the named-function `parameter_clause`/`function_result` nonterminals; it may be omitted entirely, with `Implicit_parameter_name ::= "$" Decimal_digits` (`$0`, `$1`) standing in for parameters. `capture_list ::= "[" capture_specifier expression "]"` (`weak`/`unowned`) makes capture semantics explicit syntax, and a closure can follow a call's `)` as a `trailing_closure` (§2) |
| Eiffel | `Agent ::= Call_agent \| Inline_agent`, `Call_agent ::= "agent" Call_agent_body`, `Inline_agent ::= "agent" [Formal_arguments] [Type_mark] [Attribute_or_routine] [Agent_actuals]` | two forms: a `Call_agent` is a first-class reference to an existing routine (`agent foo`), built on the same call grammar as an ordinary call, while an `Inline_agent` is a genuine routine literal — it reuses the named routine's own `Formal_arguments` and `Attribute_or_routine` (body) nonterminals, so like Dart and JS it is a named-routine shape with the name removed |
| Ada, C99, C++98, Java 5, Fortran, Modula-3, Pascal/Delphi, PHP, Basic (VB6), COBOL | **none** | |

The absence list is telling for dating: C++98, Java 5, and this PHP/VB6
grammar all predate their respective languages' actual lambda features
(C++11, Java 8, PHP 5.3, VB.NET's `Function(...)`) — the *grammar version*
captured in this corpus is simply from before each language added the
feature, not evidence the feature never existed. Ada, Fortran, Modula-3,
Pascal, and COBOL genuinely never had function-valued expressions at these
grammar versions, consistent with their era and design goals (Delphi's
anonymous methods arrived in Delphi 2009, after this Delphi 2006 grammar —
general language knowledge).

Lua, Erlang, Smalltalk, and Swift all have one, and three of them confirm the Haskell/JS/Dart
observation that the anonymous form tends to *reuse* the named form's
nonterminals: Lua shares `funcbody`, Erlang's `funClause` is
`functionClause` minus the name, and Swift's `closure_signature` reuses
`parameter_clause`/`function_result`. Smalltalk is the exception only
because there's no named form in its grammar to share with.

## Summary of cross-cutting patterns

- **The "two structured-programming keywords" cluster (Ada, Fortran-90,
  Pascal, Basic) is the single strongest recurring signal in this whole
  analysis** — it independently predicts three separate findings: a
  separate procedure/function grammatical category (§1), a dedicated
  call-statement node instead of folding calls into expressions (§2), and
  explicit parameter-passing-mode syntax (§3 — inline for Ada, Pascal, and
  Basic; Fortran-90 via separate `INTENT` statements; Modula-3 keeps the
  modes even though it drops the §1 split). These aren't three unrelated design
  choices — they're one underlying stance (make control- and data-flow
  structure explicit and machine-checkable, sacrificing brevity) showing up
  in three different grammar productions.
- **The call-as-postfix-operator convergence (C, Java, Dart, Python, JS,
  Swift)** is
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
- **Haskell is the corpus's single clearest demonstration that "everything
  is an expression" is a spectrum, not a binary flag** — C/Java/Dart/Python
  commit to it for calls/indexing/member-access (§2) and stop there, still
  keeping a visible call operator (`()`) and a separate definition keyword
  nowhere in sight for Haskell. Haskell pushes the identical commitment one
  level further in three unrelated productions at once — no definition
  keyword (§1), no call operator at all, just juxtaposition (§2), and no
  parameter-list delimiter, also juxtaposition (§7) — which is why its
  lambda and named-function syntax collapse into the same nonterminal
  (§6): once application and the trailing expression are both just "more
  expression, no decoration," there's very little left for distinct
  function-defining syntax to add.
- **Restricting *where* `return` may appear is a separate axis from
  whether it exists.** Lua (`block ::= (stat)* [retstat]`) and Smalltalk
  (`^` only as the last of `statements`) both have an explicit return
  marker but let the grammar, not a style rule, guarantee it closes its
  block; Erlang removes the marker and fixes the exit at the end of
  `exprs`. All three reach Eiffel's "single, predictable exit" goal (§5)
  more strictly than Eiffel's own grammar does.

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

**Why Haskell doesn't even keep one keyword.** Haskell takes the
C/Modula-3 unification argument to its logical end point rather than
stopping at "one keyword for both procedures and functions": if a function
body is simply an expression and functions are ordinary first-class
values (never a separate pointer-like category needing its own notation,
unlike C), there's no grammatical work left for a definition keyword to
do — a name is bound to a value, and whether that value happens to be
something you can apply more arguments to is a property of its type, not
of how it was introduced. This is downstream of Haskell's core design
commitment to purity and first-class functions as the central
abstraction mechanism, rather than a deliberate rejection of Ada-style
machinery for its own sake.

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

**Why Haskell drops the operator token too.** Haskell's `fexp ::= (fexp
aexp) | aexp` is this same "everything is an expression" commitment
pushed one step further than C/Java/Dart/Python go: since every function
of more than one argument is really a chain of single-argument
applications (currying), application needs to be the single most
lightweight, most frequently-written operation in the entire grammar — far
more frequent than any other operator, including ordinary infix ones. Not
even requiring a parenthesis or a dot for it is a direct, deliberate
consequence of committing to curried, higher-order functions as the
language's primary abstraction mechanism from the start, rather than
adding them as a library feature on top of an already-parenthesized call
syntax the way C-family languages with function pointers do.

**Why Smalltalk has message sends instead of calls.** Smalltalk-80's
founding design idea (Alan Kay's, per general language knowledge) is that
computation is objects sending messages to one another, with no
operations outside that model — even `3 + 4` is the message `+ 4` sent to
`3`. A grammar built on that premise has nothing for a separate
function-call construct to do, which is exactly what the
unary/binary/keyword `*Send` productions show. The interleaved keyword
selector (`at:put:`) is a readability choice inherited from that same
lineage: every argument is introduced by a word describing its role, so a
call reads close to an English phrase without needing a separate
named-argument feature — the idea Swift later imported via
Objective-C's identical selector style (§7).

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
split. Pascal/Delphi's `var`/`const`/`out` (§3) is the oldest form of the
same idea in this corpus: Wirth's original Pascal already had `var`
parameters (general language knowledge), and Delphi added `const` and
`out` later, the latter largely for COM interop — the same motivation as
VB6's below.

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
Dart, Eiffel, Lua, Smalltalk, and Erlang leave it unmarked.** Each of these
settled on one single, non-negotiable passing rule for the whole language
(C: always by value; Java/Python/JS/Lua/Smalltalk: object references
passed by value of the reference; Erlang: immutable values, so the
question never arises; similarly for the rest), so there is nothing
per-parameter left to annotate. C++ is a partial exception in spirit if not in this specific
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

**Lua's and Swift's `...`.** Both reuse the C spelling, but Lua's version
makes the most of it grammatically: because `"..."` is also an `exp`, the
extra arguments never need a name — they're spliced straight into a call,
a table constructor (`{...}`), or a multiple assignment. That fits Lua's
general design goal (general language knowledge) of a very small grammar
in which tables and multiple values cover what other languages need
separate features for.

### Default parameter values (§4)

**Why Ada, C++, C#, Dart, PHP, Basic, Pascal/Delphi, Python, and Swift
support them.** All of these are general-purpose or
enterprise/application languages where APIs accumulate many optional,
configuration-style parameters over time. Ada's
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

**Why Lua, Erlang, and Smalltalk have none.** Each makes defaults
unnecessary by other means (general language knowledge): Lua passes `nil`
for any missing argument, so `x = x or default` in the body does the job;
Erlang treats `f/1` and `f/2` as distinct functions, so a "default" is
just a shorter-arity clause that calls the longer one; and Smalltalk's
selectors encode the argument count (`at:` vs. `at:put:`), so the same
overloading-by-name approach applies.

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

**Why Lua and Smalltalk restrict `return` to the end of a block.** Lua's
`block ::= (stat)* [retstat]` is (per Lua's reference manual, general
language knowledge) a parsing convenience: since Lua statements need no
separator, `return f` followed by more code on the next line would be
ambiguous about how much of it the `explist` consumes, and requiring
`return` to be last removes the question. Smalltalk's `^`-only-at-the-end
reads more as a consequence of its terse statement grammar than a stated
goal, but the effect is the same: unreachable code after a return can't
be written at all.

**Why Erlang has no `return`.** Erlang functions are sequences of
expressions with pattern-matched clauses choosing which sequence runs
(general language knowledge); with no statements and single assignment,
"leave early with a value" is expressed by choosing a different clause or
`case` branch instead, so the grammar never needed an exit keyword.

### Lambdas / anonymous functions (§6)

**Why Haskell's lambda and named-function syntax are the same expression
with different dressing.** This isn't really an addition at all, unlike
every other language in this section — it's the base case. Haskell's
theoretical ancestor, the untyped lambda calculus, has exactly one
function-forming construct (`λx. e`) and gets named bindings by convention
(`let`/letrec) on top of it, never the reverse; Haskell's grammar mirrors
that lineage directly, which is exactly why `rhs`'s `"=" exp` and a
lambda's `"->" exp` land on the identical nonterminal (§6's table above).
Every other lambda-supporting language in this list added anonymous
functions to a grammar that already had named-function definitions as the
primary, older construct; Haskell is the one language here where the
historical and grammatical order is reversed.

**Why Python, C#, Dart, JS, Eiffel, Lua, Erlang, Smalltalk, and Swift have
some form.** Each added it for
a distinct, language-specific reason: Python's `lambda` supports its
functional-programming-adjacent idioms (`map`/`filter`/`sorted(key=...)`)
without needing a full `def`; C# 4.0's `=>` lambdas exist to support LINQ,
which relies heavily on passing small inline predicates and projections to
query operators; JS function expressions are central to its
event-driven/callback-oriented design going back to its earliest browser
use; Eiffel's `agent` mechanism is a natural extension of its
message-passing object model — a `Call_agent` is a first-class reference
to a routine call, consistent with "everything is a call to a target,"
and the `Inline_agent` form simply lets that target routine be written in
place. Among the newer additions: Smalltalk's blocks are original to
Smalltalk-80 and are how it expresses all control flow (general language
knowledge — `ifTrue:`/`whileTrue:` are messages taking blocks, which is
why this grammar has no `if` or `while` production at all); Lua's and
Erlang's anonymous functions follow from treating functions as ordinary
first-class values (Erlang additionally uses funs heavily as spawned
process bodies); and Swift's closures, with `$0` shorthand and trailing
closure syntax, were designed in from the start to make callback-heavy
Cocoa APIs and higher-order collection methods short to write.

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

**Flat comma-separated, one entry per parameter.** C99, C++98, C#, Java,
JS, Python, PHP, Dart, Swift, Fortran-90, Basic (VB6), Lua, and Erlang all
use one comma-separated list in which each parameter is its own entry. In
the statically typed ones (C99, C++98, C#, Java, Dart, Swift) every entry
spells out its own type; in JS (`js_formal_parameter ::= id`), Lua
(`namelist ::= NAME ("," NAME)*`), and Fortran-90 (`FunctionPar ::=
DummyArgName`, with types declared afterwards in the body) the entries are
bare names; in Python, PHP, and Basic a type annotation is absent or
optional; and in Erlang (`argumentList ::= "(" [exprs] ")"`) each entry is
a full pattern expression, so a clause head like `f({ok, X}, [H|T])`
destructures its arguments in place:

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
pascal:    formal_parameters ::= "(" formal_parameter (semi_formal_parameter)* ")"   where semi_formal_parameter ::= ";" formal_parameter
           parameter ::= sep*(id, ",") [parameter_type]
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

**Whitespace-only, no delimiter at all — now directly confirmed by
Haskell.** This pattern was previously only a conceptual prediction in
this analysis: the obvious real examples (OCaml/Haskell-style curried
`let add a b = a + b`; Lisp/Scheme `(defn add [a b] ...)`) belonged to
languages not present in `grammar-zoo-flavie` at the time. With Haskell now in the corpus, the
prediction is directly verifiable:
`funlhs ::= (var apat funlhs_2_1) | (var apat) | (pat0n varop pat0n)`
(where the generated helper `funlhs_2_1` is one or more further `apat`s)
— a function's declared parameters
are simply juxtaposed `apat`s, one after another, with no comma, no
parenthesis, nothing. `add a b = a + b` is not "one binding with a
two-element parameter list" grammatically; `funlhs` has no list node at
all, just repeated single patterns, which matches exactly the call-site
juxtaposition already confirmed in §2. There is no "parameter list" node
in the grammar for a delimiter to live in, because each "parameter" really
corresponds to its own separate, nested single-argument function once
curried; juxtaposition is just repeated application, not a list
construct, so there's nothing for a comma to separate on either side of
the definition.

Smalltalk's blocks are a second, uncurried instance of the same
whitespace-only pattern: `blockParamList ::= ((ws BLOCK_PARAM))+ ws
[PIPE]`, `BLOCK_PARAM ::= COLON IDENTIFIER` — `[:a :b | a + b]` separates
parameters only by whitespace, with each one marked by its own leading
`:` instead of by a delimiter between them, and the `|` closing the whole
list. Unlike Haskell, this isn't a consequence of currying (a two-parameter
block takes both arguments at once); the colon prefix alone is enough to
make the list unambiguous.

### A related question: are arguments ever labeled?

Separate from how parameters are delimited is whether the *caller* names
them. Most grammars here have some optional named-argument form at the
call site — Ada's `parameter_association ::= [(formal_parameter_selector_name
"=>")] explicit_actual_parameter`, Modula-3's `Actual ::= ([(Ident ":=")]
Expr) | Type`, Fortran-90's `SubroutineArg ::= (Name "=" Expr) | ...`,
C#'s `argument-name ::= identifier ":"`, Dart's `namedArgument ::= label
expression`, and Python's `argument_value ::= ... | ("=" test)`. Two
grammars go further and make the label part of the routine's declared
signature itself:

- **Swift**: `parameter ::= ([...] ["#"] parameter_name [local_parameter_name]
  type_annotation ...)` gives each parameter two names — an external
  `parameter_name` used by callers and an optional internal
  `local_parameter_name` used in the body — with `"_"` allowed for either
  to suppress it, and `#` (per general language knowledge, Swift 1.x
  shorthand) meaning "use the same name for both." The call site supplies
  the labels through `expression_element ::= expression | (identifier ":"
  expression)`.
- **Smalltalk**: labels aren't an add-on at all — they *are* the selector.
  A `keywordMessage` is `(keywordPair)+`, each `KEYWORD ::= IDENTIFIER
  COLON` immediately followed by its argument (§2), so the "labels" are
  the method's name, split up and interleaved with the arguments. Swift's
  external-name design is, per general language knowledge, a direct
  inheritance of this style via Objective-C, which borrowed Smalltalk's
  keyword selectors.

Swift's grammar also allows *several* parenthesized parameter lists on
one function, `parameter_clauses ::= parameter_clause [parameter_clauses]`
— the curried-function declaration syntax of early Swift (general
language knowledge: removed in Swift 3), and the only grammar in the
corpus besides Haskell where a definition can take its arguments in
separate application steps.

### A related question: are the parens themselves ever optional?

Checking whether the entire `( ... )` group can be dropped for a
zero-parameter routine — not just left empty — turns up a clean split
that lands on the same language cluster yet again.

**Parens are structurally mandatory, even with zero parameters:** C99,
C++98, C#, Java, JS, Python, PHP, Dart, Swift (`parameter_clause ::= ("("
")") | ...`), Lua (`funcbody ::= "(" [parlist] ")" block "end"`), Erlang
(`argumentList ::= "(" [exprs] ")"`), and Modula-3 — Modula-3's
`Signature ::= "(" Formals ")" [":" Type]` requires the literal `(` `)`
even when `Formals` expands to nothing.

**The whole parenthesized group is optional and can vanish entirely:**

```
ada:      parameter_and_result_profile ::= [formal_part] "return" ...
pascal:   procedure_signature ::= ... [formal_parameters] ...
fortran:  FunctionParList ::= ("(" FunctionPars ")") | epsilon
basic:    subprogram_declaration ::= ... [subprogram_argument_description] ...
eiffel:   Declaration_body ::= [Formal_arguments] [Query_mark] [Feature_value]
```

So `function Foo return Integer;`, `procedure Foo;`, and `Sub Foo` are all
valid with no parens anywhere in the text. Apart from Eiffel (below), this
is the same four-language cluster again (Ada, Pascal, Fortran, Basic), and
the reason connects
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

Eiffel, previously missing from this comparison, goes furthest of all in
this group: `Formal_arguments ::= "(" Entity_declaration_list ")"` with
`Entity_declaration_list ::= sep+(Entity_declaration_group, ";")`, and on
the call side `Unqualified_call ::= Feature_name [Actuals]` with
`Actual_list ::= sep+(Expression, ",")` — both lists are one-or-more, so
an *empty* `()` is not merely optional but unparseable, in declarations
and calls alike. A zero-argument routine call and an attribute access are
therefore textually identical (`account.balance`), which is (per general
language knowledge) Meyer's deliberate "uniform access principle": a
client shouldn't be able to tell whether a feature is stored or computed.
This fits the §2 grouping — Eiffel also keeps calls in a dedicated `Call`
production — and adds a design reason beyond parsing for dropping the
parens.

Modula-3 and Lua refine that explanation rather than break it. Both have a
dedicated call *statement* (§2) yet still require parens, and both also
treat a bare procedure name as a meaningful expression value (Modula-3
has procedure types, `ProcedureType ::= "PROCEDURE" Signature`; Lua's
`functiondef` is an `exp`). So the real predictor is first-class procedure
values, of which calls-as-postfix-expressions is the usual symptom: once
`foo` alone can denote the procedure, `foo()` has to look different.
Erlang shows the other side of the same coin: a bare `f` is just an atom,
never the function, and the function value has its own syntax
(`"fun" tokAtom "/" tokInteger`, §6), so its mandatory parens on
definitions are about pattern-matching argument lists rather than
disambiguation. Lua also has a call-site-only escape: `args ::= ("("
[explist] ")") | tableconstructor | string` lets the parens be dropped
when the single argument is a table or string literal (`require "mod"`),
which is unambiguous because a literal can't otherwise directly follow an
expression.

**Haskell makes a third move on this same question**: there is no
parenthesized parameter-list production at all to be optional or
mandatory, since `funlhs` is just juxtaposed `apat`s with nothing
bracketing them (§7 above). And yet Haskell never runs into the
"bare-name-vs-zero-arg-call" ambiguity C/Java/Dart/Python avoid with
mandatory parens, for a more fundamental reason than any grammar rule: a
reference to any value, callable or not, is the identical production
(`aexp ::= qvar | ...`), and there is no such thing as "calling a function
with no arguments" to begin with, since `fexp ::= (fexp aexp) | aexp`
always consumes exactly one more argument per application. A zero-argument
"function" in Haskell isn't a function at all — it's just an ordinary
value — so `f` is never ambiguous between "the function" and "call it with
nothing," because the second reading simply doesn't exist as an operation
in the language. The disambiguation problem the other four languages solve
with mandatory parens doesn't need solving here, because currying removes
the very notion the parens would otherwise be needed to distinguish.

## 8. Function modifiers: how strictly does the grammar constrain them?

The most useful axis here isn't which keywords exist, but *how much of
"which modifier is valid on which kind of declaration" the grammar itself
enforces*, versus leaving that check to a later semantic pass.

**C# is the most granular in the corpus — a separate modifier production
per declaration kind.** Not one `modifier` rule but fourteen for
declarations alone: `class-modifier`, `constant-modifier`,
`method-modifier`, `field-modifier`, `property-modifier`,
`accessor-modifier`, `event-modifier`, `indexer-modifier`,
`operator-modifier`, `constructor-modifier`, `struct-modifier`,
`interface-modifier`, `enum-modifier`, `delegate-modifier` (plus
`parameter-modifier` and `anonymous-function-parameter-modifier` for
parameters, §3). Nearly all of them repeat the shared access-level
keywords (`public`/`protected`/`internal`/`private`) — `operator-modifier
::= "public" | "static" | "extern"` is the exception, admitting only
`public` — but each only admits the kind-specific ones where they're
actually meaningful:
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

**Swift lands on C's side of this axis, not C#'s.** `function_head ::=
[attributes] [declaration_specifiers] "func"` and `variable_declaration_head
::= [attributes] [declaration_specifiers] "var"` (and `constant_declaration`
for `let`) all draw on the one shared `declaration_specifier ::= "class" |
"mutating" | "nonmutating" | "override" | "static" | "unowned" |
"unowned(safe)" | "unowned(unsafe)" | "weak"`. So `weak func f()` and
`mutating var x` are grammatically well-formed even though `weak` only
means anything on a reference-typed variable and `mutating` only on a
method — the same "one vocabulary, checked later" strategy as C. This
grammar also has no access-level keywords at all (`public`/`private`/
`internal` never appear); per general language knowledge, Swift's access
control was added in a beta after the language's first public grammar,
which this one evidently predates.

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
`package_specification ::= "package" defining_program_unit_name "is"
(basic_declarative_item)* [("private" (basic_declarative_item)*)] "end"
...` — one `private` keyword marks
where a package's private section begins; everything declared before it
is visible outside the package, everything after is hidden. Visibility is
a property of *where* something is written, not *what keyword* is
attached to it. Fortran-90 lands halfway between this and a per-declaration
modifier: it has a genuine `AccessSpec ::= "public" | "private"` keyword,
but it names a whole list of module entities in one statement rather than
annotating each subprogram individually.

**Haskell has no per-declaration visibility keyword at all — visibility is
a single module-level whitelist, not a property of the binding itself.**
`modul ::= ("module" modid exportspec "where" body) | ("module" modid
"where" body)` — the *first* alternative's `exportspec ::= "(" exports
")"` names exactly the identifiers a module exposes; everything else
declared inside it is private by omission, with no `private`/`public`
keyword ever attached to the binding in question. The *second*
alternative — the one with no export list at all — is itself a real,
citable design decision: writing `module Foo where ...` with nothing
further exports *everything*, the opposite default from Java's
package-private-unless-marked or C#'s private-unless-marked instinct.
This is one further point on the same axis Ada and Fortran-90 sit on
(visibility as a property of *where*/*whether* something is listed, not
*what keyword* decorates it) but landing on a different mechanism again:
Ada's is purely positional within one file (before/after `private`),
Haskell's is an explicit, named list sitting apart from every declaration
it governs, closer in spirit to Eiffel's whitelist below except coarser —
visible-or-not to everyone, with no per-client targeting.

**Erlang uses the same whitelist idea as Haskell, but its grammar can't
tell it apart from any other module attribute.** Per general language
knowledge, a function is visible outside its module only if listed in
`-export([name/arity, ...])`. In this grammar, though, that is just one
instance of the fully generic `attribute ::= ("-" tokAtom attrVal) | ...`:
`export` is an ordinary atom, no different syntactically from `-module`,
`-author`, or any user-invented attribute. The only attributes the grammar
singles out are `AttrName ::= "-" ("spec" | "callback")`, because those
two are followed by type syntax (`typeSpec`) rather than a plain term.
Visibility is real in Erlang but invisible at the CFG level — the
furthest point on the "checked later" end of this axis.

**Lua and Smalltalk have no function modifiers at all.** Lua's only
related word is `local`, and in `"local" "function" NAME funcbody` it is
about *scope* (lexical vs. global variable), not access control; the
`funcname ::= NAME ("." NAME)* [":" NAME]` form only decides where the
function is stored, with `:` (per general language knowledge) adding an
implicit `self` parameter. Smalltalk's grammar has no definitions to
modify (§1); its one annotation-like construct is `primitive ::= LT ws
KEYWORD ws (DIGIT)+ ws GT` (`<primitive: 60>`), which marks a method
body as implemented by the VM and is reachable only as an ordinary
`expression` in this grammar.

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
