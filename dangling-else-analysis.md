# The dangling-else problem across `grammar-zoo-flavie-adapted`

The dangling-else problem: in `if a then if b then s1 else s2`, it is unclear
whether `else s2` belongs to the inner `if b` or the outer `if a`. This
analyzes how each grammar in `grammar-zoo-flavie-adapted` resolves it, based
on the actual `if`/`then`/`else` productions in
`normalized-ebnf-flavie-adapted/`, not just general language knowledge.

This covers all **20 languages** in the corpus, all of them full language
syntax. Nineteen have a real conditional production; the twentieth,
Smalltalk, has no conditional syntax at all, which turns out to be its own
answer to the problem (strategy 5). COBOL here is
`cobol-vscobolii-lammel-gdk.bgf` (IBM VS COBOL II).

## Five resolution strategies, cleanly split

### 1. Mandatory closing delimiter — ambiguity structurally impossible

| Language | Production |
|---|---|
| Ada | `"if" cond "then" seq (elsif...)* [else seq] "end" "if" ";"` |
| Eiffel | `"if" Then_part_list [Else_part] "end"` |
| Modula-3 | `"IF" Expr "THEN" Stmts (ELSIF...)* [ELSE Stmts] "END"` |
| Lua 5.2 | `"if" exp "then" block ("elseif" exp "then" block)* ["else" block] "end"` (an alternative of `stat`) |
| Fortran-90 (block form) | `IfConstruct ::= IfThenStmt ConditionalBody (ElseIfConstruct)* [ElseConstruct] EndIfStmt` — mandatory `END IF`/`ENDIF` |
| Basic/VB6 (block form) | `full_if_statement` requires `end if` |
| Erlang | `ifExpr ::= "if" ifClauses "end"`, `ifClauses ::= ifClause (";" ifClause)*`, `ifClause ::= guard clauseBody` |
| Swift | `if_statement ::= "if" if_condition code_block [else_clause]`, `else_clause ::= ("else" code_block) \| ("else" if_statement)`, `code_block ::= "{" [statements] "}"` |

Every nested `if` consumes its own terminator, so
`if a then if b then s1 else s2 end if end if` can only parse one way
regardless of nesting depth — no grammar-level or parser-level tie-breaking
is needed.

Two of these rows need a note:

- **Erlang** has no `else` keyword anywhere in the grammar. An `if` is a
  `;`-separated list of `guard -> body` clauses, and the "otherwise" branch
  is just one more clause (by convention `true -> ...`; that idiom and the
  runtime `if_clause` error when no guard matches are general Erlang
  knowledge, not something the grammar shows). The trailing optional part
  is therefore the `(";" ifClause)*` repetition rather than an `else`, and
  it would have exactly the same dangling problem without a terminator: in
  a hypothetical `end`-less `if A -> if B -> x; C -> y`, the `C -> y`
  clause could belong to either `if`. The mandatory `end` is what settles
  it, exactly as in Ada.
  `caseExpr ::= "case" expr "of" crClauses "end"` has the same shape, and
  both are expressions (alternatives of `exprMax`), not statements.
- **Swift** gets the same guarantee from braces instead of a keyword:
  the `then` branch is always a `code_block`, so an `else` can only ever
  appear right after a `}` that closes exactly one `if`. The one unbraced
  form, `"else" if_statement`, is only allowed *after* `else`, where it is
  harmless: the nested `if_statement` again requires its own braced block.
  Swift is the only language in the corpus that keeps C's
  `if`-plus-condition shape but makes the body's delimiter mandatory.

### 2. Layout as the delimiter, not a keyword

- **Python**: `if test : suite (elif)* [else]`, where `suite` is either an
  indented block bounded by INDENT/DEDENT tokens or a single-line statement
  list. The indentation level itself plays the role of `end if` — the
  `else`'s column tells the parser which `if` it closes. Same effect as
  strategy 1, different mechanism (whitespace instead of a lexeme).

### 3. Genuinely ambiguous grammar, resolved outside the CFG

| Language | Production |
|---|---|
| C99 | `"if" ( expr ) statement \| "if" ( expr ) statement "else" statement` |
| C++98 | identical shape |
| C# 4.0 | identical shape |
| Java 5 | same language, written with an optional `["else" statement]` tail |
| Dart | same language, written with an optional `[ELSE statement]` tail |
| JavaScript (Synytskyy/Cordy) | same language, written with an optional `[js_else_clause]` tail |
| Pascal/Delphi | `"if" expr "then" nested_stm [else_stm]`, where `nested_stm` recurses straight back to `statement` with no bracketing |

Strictly, only C99, C++98, and C# 4.0 write it as the textbook pair of
alternatives (`if-statement` in C# uses `embedded-statement` for the body).
Java, Dart, and JavaScript write the same language as one alternative with
an optional tail, e.g. Java's `"if" parExpression statement ["else"
statement]` and JavaScript's `"if" "(" js_expn ")"
js_declaration_or_statement [js_else_clause]`. The two spellings generate
identical strings and have the identical ambiguity. All seven lack any
"matched/open-statement" split (the classical Algol-60-revised fix isn't used
anywhere in this corpus). The BGF files can't show *how* it's resolved —
that information isn't part of a context-free grammar — but by
convention/spec prose it's always "attach `else` to the nearest `if` still
missing one," enforced in real parsers as a shift preference (LALR default)
or hand-coded lookahead. No BGF file in the corpus carries any
disambiguation annotation (the format has no precedence/priority markup), so
this really is invisible at the grammar level for all seven.

### 4. No optional clause to dangle — the ambiguity precondition itself is absent

- **Haskell**:
  `exp10n ::= ... | ("if" exp "then" exp "else" exp) | ...`
  — a Haskell `if` is an *expression*, not a statement, and critically
  `else` is not bracketed as `[else exp]` anywhere in this production. It is
  mandatory, full stop. Nested `if`s absolutely still recurse (`then`'s and
  `else`'s own slots are both plain `exp`, which can itself expand back to
  `exp10n` and another `if`), so
  `if a then if b then s1 else s2 else s3` is perfectly legal and perfectly
  unambiguous — there is no dangling clause because there is no optional
  clause. This isn't strategy 1 wearing a different keyword either: Ada's
  `end if` is a *terminator*, something added specifically to close off an
  otherwise-open construct; Haskell's `else` was never an optional add-on to
  begin with; it's exactly as mandatory as `then`. The reason this works at
  all without feeling restrictive is semantic, not syntactic: since `if` must
  produce a value usable in surrounding context, a branch that silently does
  nothing (what an omitted `else` would mean) isn't a coherent option in the
  first place — unlike C's `if (x) foo();`, where "do nothing otherwise" is
  a perfectly normal thing for a *statement* to mean.

### 5. No conditional syntax at all — conditionals are ordinary messages

- **Smalltalk** (Redline grammar): the grammar has no `if`, `then`,
  `else`, or any other control-flow keyword. There is no `ifTrue:` either;
  it isn't a token in the grammar. A Smalltalk conditional (by general
  language knowledge, `x > 0 ifTrue: [...] ifFalse: [...]`) is just an
  instance of the generic keyword-message rules:

  ```
  keywordSend    ::= binarySend keywordMessage
  keywordMessage ::= ws (keywordPair ws)+
  keywordPair    ::= KEYWORD ws binarySend ws
  KEYWORD        ::= IDENTIFIER COLON
  block          ::= BLOCK_START [blockParamList] ws [sequence] BLOCK_END
  ```

  Two things in these rules keep the dangling-else shape from arising.
  First, a keyword argument is a `binarySend`, which can't itself be a
  `keywordSend`, so a nested keyword message has to go inside `( ... )`
  (`subexpression`) or `[ ... ]` (`block`). Second,
  `(keywordPair ws)+` means every consecutive `keyword:` part belongs to
  the same, outermost message: `a ifTrue: b ifTrue: [s1] ifFalse: [s2]`
  parses as one send of a three-part selector `ifTrue:ifTrue:ifFalse:` to
  `a` (which would just fail at runtime as an unknown message), never as a
  nested conditional. To nest, you have to write the brackets:
  `a ifTrue: [b ifTrue: [s1] ifFalse: [s2]]`, and the `]` marks where the
  inner conditional ends. So Smalltalk denies condition (2) of the
  generalization below, but for every keyword message at once and with no
  conditional-specific grammar at all.

## Mixed/hybrid cases

- **Fortran-90** also has a single-line form,
  `IfStmt ::= "if" ( Expr ) ActionStmt`, and `ActionStmt` recursively
  includes `IfStmt` — so single-line ifs *can* nest — but `ActionStmt` never
  includes the block `IfConstruct`/`else`, so no path through this rule can
  ever produce a dangling `else`. It's a third, subtler way of avoiding the
  ambiguity: not by delimiting, but by making the compact form syntactically
  incapable of carrying an `else` at all.
- **VB6 (Basic)** and **PHP** each offer *two* forms side by side: a
  C-style compact one (`short_if_statement` in Basic; the brace-based form
  in PHP) that's ambiguous and resolved by nearest-if convention, plus a
  fully delimited alternative (`end if` in Basic; the
  `if (...): ... endif;` alt-syntax in PHP) that sidesteps the problem
  entirely. These read as "give the ambiguous form for convenience, but
  provide an unambiguous one too."
- **COBOL** has the same duality, but far more systematically than VB6 or
  PHP's one-off exception: `statements ::= ... | (if_statement
  [("END-IF" [statements])]) | ...`, where `if_statement` itself is
  `"IF" condition [THEN] (statements | "NEXT" "SENTENCE") [("ELSE"
  (statements | "NEXT" "SENTENCE"))]`. `END-IF` is bracketed — fully
  optional — so a nested, unterminated `IF` inside an `IF` is exactly as
  ambiguous as C's, resolved the same "nearest if" way; adding `END-IF`
  removes the ambiguity completely for that one `IF`, the same trade a
  VB6 programmer makes with `end if`. What makes COBOL distinct is that
  this exact `[END-XXX [statements]]` shape isn't special-cased for `IF`
  at all — it's the *uniform* pattern `statements` uses for seventeen
  different statement kinds alike (`END-ADD`, `END-CALL`, `END-COMPUTE`,
  `END-DELETE`, `END-DIVIDE`, `END-EVALUATE`, `END-IF`, `END-MULTIPLY`,
  `END-READ`, `END-RETURN`, `END-REWRITE`, `END-SEARCH`, `END-START`,
  `END-STRING`, `END-SUBTRACT`, `END-UNSTRING`, `END-WRITE`), all
  independently optional. (`END-PERFORM` is the exception: it lives inside
  the in-line forms of `perform_statement_format_*` themselves and is
  mandatory there.) COBOL doesn't give `IF` a special
  carve-out the way VB6/PHP do — it applies the identical "ambiguous by
  default, opt into an explicit terminator" trade-off everywhere a
  compound statement can embed another one.

## The pattern

The split runs along **language lineage, not decade**:

- **Wirth/Ada-family "structured programming" languages** (Ada, Eiffel,
  Modula-3, Fortran-90's block form) all independently chose explicit
  termination — likely a direct reaction to Pascal's dangling-else being the
  field's canonical cautionary example. **Lua** belongs here too: its
  `if ... then ... elseif ... else ... end` is the Modula-3 production
  almost token for token, and Lua uses the same `... end` closing for
  `while`/`for`/`do` blocks (general knowledge: Lua's designers cite
  Modula as a syntactic influence).
- **C-lineage languages** (C, C++, C#, Java, Dart, JavaScript) all inherited
  the exact same ambiguous production across 40+ years (in two equivalent
  spellings), and all inherited the same "nearest if" folk-rule to resolve
  it. **Swift** is the one exception in the corpus: it keeps the C-family
  look (no `then`, no `end`, braces) but makes the braces mandatory, which
  is enough to remove the ambiguity. So "C-like syntax" and "dangling else"
  are separable after all; the other six just never chose to separate them.
- **Pascal itself** is the odd one out: Wirth fixed the problem a few years
  later in Modula, yet classic/Delphi Pascal keeps the ambiguous form.
- **Python** is the only language here that solves it via layout rather
  than an explicit token (keyword or brace), consistent with it dropping block delimiters everywhere
  else in the grammar.
- Languages that give programmers a **choice of two if-forms** (VB6, PHP)
  tend to pair a delimited one with a C-style compact one, suggesting
  compact-but-ambiguous and safe-but-verbose are seen as a deliberate
  trade-off, not just a legacy accident.
- **COBOL (1959)**, the oldest language in this corpus after Fortran, shows the
  "give both forms" accommodation in its most systematic version —
  optional `END-IF` alongside the ambiguous fallback, applied uniformly
  to nearly every compound statement rather than as a special exception
  carved out just for `IF`. `END-IF` itself (like most of COBOL's
  `END-XXX` scope terminators) was a later standard addition, retrofitted
  onto a language whose original 1959 design relied on the terminating
  period and "nearest if" convention alone — directly parallel to
  Fortran's own later `END IF` retrofit in strategy 1 above.
- **Haskell** is a fourth lineage entirely, and it solves the problem for a
  reason none of the other three groups share: `if` is an *expression*
  there, not a *statement*. Once every branch of a conditional has to
  produce a usable value, "what if one branch is just skipped" stops being
  a sensible question to ask, and the mandatory-`else` shape falls out as a
  consequence of that choice rather than a dangling-else fix bolted on
  separately.
- **Erlang** shows that being expression-oriented doesn't settle it on its
  own: its `ifExpr` and `caseExpr` are expressions too, but their clause
  lists are open-ended, so Erlang needs the mandatory `end` anyway. Its
  `if` is closer to Dijkstra's guarded commands (a list of `guard -> body`
  clauses with no privileged `else`) than to either Haskell's or Ada's
  `if`; the guarded-command connection is general knowledge, not something
  the grammar states.
- **Smalltalk** sits outside all of these: with no conditional syntax at
  all, there is nothing language-specific to fix. Conditionals inherit
  whatever the general message-send rules give them, and those rules
  already require `( )` or `[ ]` around any nested keyword message.

## Pros, cons, and design motivation for each strategy

### 1. Mandatory closing delimiter (Ada, Eiffel, Modula-3, Lua, Fortran block-`IF`, VB6 full form, Erlang; Swift via mandatory braces)

**Pros**

- Ambiguity is eliminated *provably*, by construction — no shift-reduce
  conflict exists in the grammar, so any correct parser (yours or a third
  party's) gets the same answer.
- Self-documenting scope: a reader (or a diff, or a static analyzer) can see
  exactly where a conditional ends without tracking indentation or braces.
- Editing safety: inserting or deleting a nested `if` can't silently
  reattach an `else` to the wrong branch — the compiler will reject a
  mismatched `end if` rather than quietly changing behavior.
- Fits naturally with a "structured programming" design where every
  compound construct (loop, procedure, block) already gets its own explicit
  terminator — no special-casing `if` differently from the rest of the
  grammar.

**Cons**

- Verbose — `end if` (or `end`) on every conditional adds real boilerplate,
  especially painful for short guard-clauses (`if x then return; end if;`
  vs. C's `if (x) return;`).
- Where the terminator is generic (`end` in Modula-3/Eiffel/Lua/Erlang, or
  `}` in Swift, rather than a construct-specific keyword), a misplaced `end` during refactoring can
  silently close the wrong block — you trade the dangling-`else` bug for a
  milder version of the same class of mistake.
- Extra tokens to type/parse for the overwhelmingly common one-line-body
  case, which is a real ergonomic cost even though it's the rare deeply
  nested case that actually needed the safety. Swift's braces are the
  cheapest version of this cost (two characters), which is likely part of
  why it is the variant a C-family language could adopt.

**Why it was chosen this way**: Ada, Modula-3, and Eiffel all descend from
the "structured programming" / correctness-first tradition (Wirth,
Dijkstra, Ichbiah). Dangling-else was already a textbook example of grammar
ambiguity by the time these languages were designed (1970s–80s) — Algol 60
and Pascal had already made it infamous — so their designers had no excuse
to repeat it. Ada in particular was a DoD-funded language for
safety-critical/embedded systems (avionics, defense), where a class of bug
caused by "which branch does this else belong to" is not an acceptable
risk. Fortran's block `IF`/`END IF` was added later (FORTRAN 77/90) as a
retrofit once the community wanted ALGOL-like structured control flow
instead of `GOTO`-and-labels — its addition is a direct historical
acknowledgment that the old style was error-prone. The three newer entries
are general-knowledge cases too: Lua (1993) took its block syntax from the
Modula/Pascal tradition and simply used `end` for every block; Erlang
closes every multi-clause construct with `end` (the grammar shows this for
`ifExpr`, `caseExpr`, `receiveExpr`, and the clause form of `funExpr`), so
`if` is not special-cased; and Swift (2014) is a late C-family design that
adopted mandatory braces outright, as Go and Rust also did, after decades
of the C-family style guides already demanding them.

### 2. Layout/indentation as the delimiter (Python)

**Pros**

- Zero punctuation overhead — no braces, no closing keyword, and it's
  "free" since you're indenting for readability anyway.
- Eliminates an entire real-world bug class: code that *looks* nested one
  way to a human reading indentation but actually parses another way (this
  is the exact shape of several infamous C bugs, e.g. mis-indented
  `if`/`else` chains that fooled reviewers). In Python, what you see
  indented *is* the parse, by definition.
- Forces one consistent style across every codebase — no brace-placement
  debates, no reformatting tools needed to reveal true structure.

**Cons**

- Whitespace becomes semantically load-bearing: mixed tabs/spaces,
  copy-pasting from a browser or chat window, or an aggressive
  auto-formatter can change meaning or break the file, in a way a
  brace/keyword language would just shrug off.
- Moving a block to a different nesting depth requires careful, consistent
  re-indentation of every line — you can't just paste and let the compiler
  figure out the boundaries.
- Machine-generated code (templates, codegen) needs to track indentation
  depth explicitly, which is more bookkeeping than emitting a delimiter
  token.

**Why it was chosen this way**: Guido van Rossum built Python's block
syntax directly on his earlier work with ABC, a language explicitly
designed for teaching, where reducing visual noise and enforcing a single
"obvious" layout was a stated goal. Making indentation *mean* something was
a deliberate reaction against exactly the C-family bug class above — if
indentation is forced to match structure, that whole category of "looks
right, parses wrong" bug simply can't exist. This tracks with Python's
general design ethos ("there should be one obvious way to do it").

### 3. Ambiguous grammar + "nearest if" convention (C, C++, C#, Java, Dart, JavaScript, Pascal)

**Pros**

- Maximum brevity for the common case: `if (x) return;` needs nothing
  extra, and `if`/`while`/`for` all uniformly take "a single embedded
  statement" with no special-cased grammar just for `if`.
- The fix-up rule itself is trivial to state and learn ("`else` binds to
  the nearest `if` without one"), and in an LALR parser it's *already* the
  default shift-over-reduce behavior — Yacc/Bison resolve it correctly with
  zero extra grammar rules, so historically there was no implementation
  cost to leaving it ambiguous.
- Preserves syntactic familiarity across generations of the family — C++,
  Java, C#, Dart, and JS all kept it so programmers moving between them
  don't have to relearn a control-flow construct.

**Cons**

- It's a genuine ambiguity in the formal grammar, not just a style
  question — any tool built independently of "the" reference parser (a
  linter, a formatter, a verifier, a from-scratch implementation) has to
  know to special-case it, since the CFG alone doesn't disambiguate.
- It's a real, historically-documented source of bugs, which is precisely
  why "dangling else" became the canonical textbook example of grammar
  ambiguity in the first place — style guides in every C-family language
  now mandate always-braced `if`/`else` specifically to compensate for this
  grammar weakness by convention, in effect re-adding by policy what a
  delimiter-based grammar would have given for free.
- A learner reading un-braced, indented code can be misled into the wrong
  parse if their indentation doesn't match the real attachment — the
  language doesn't protect them the way Python's grammar does.

**Why it was chosen this way**: C descends from B/BCPL, designed for terse
systems programming on very constrained 1970s hardware and compilers, where
every extra keyword had a real compiler-complexity and typing cost. Since
the ambiguity resolves for free as a parser-generator default, there was no
practical pressure to fix it — and once the convention was established, it
became a shared idiom. Every later C-family language (C++, Java, C#, Dart,
JS) was designed decades afterward, by which point the flaw was well
understood, but each deliberately prioritized syntactic familiarity for the
huge existing pool of C-trained programmers over a small theoretical
hygiene fix — a "least surprise, easy migration" trade-off over "fix a
well-known but low-real-world-impact wart." Pascal is the interesting
outlier: it inherited the same ambiguous shape from Algol 60, and Wirth
only fixed it in his *later* languages (Modula-2/3) once he was willing to
break from Pascal/Algol compatibility — suggesting it was seen as a real
but minor flaw, worth correcting only when a clean break was already on the
table.

### 4. Mandatory `else` via expression-oriented design (Haskell)

**Pros**

- The ambiguity doesn't need fixing because it structurally cannot arise —
  stronger even than strategy 1's guarantee, since there isn't even an
  optional terminator to forget or mismatch during a refactor.
- Forces every conditional to actually decide both outcomes, which rules
  out an entire class of "forgot the else branch" logic bugs for free,
  as a side effect of the type system rather than a style-guide rule.

**Cons**

- A guard-clause idiom that's one line in C (`if (x) return;`) has no
  direct equivalent — you're always writing both branches, even when one
  of them is semantically "do nothing," which in an expression language has
  to be spelled out as some explicit value (`Nothing`, `()`, the `do`-block
  it was already in) rather than simply omitted.
- Only works because the language made conditionals expressions in the
  first place; it isn't a strategy retrofittable onto a statement-oriented
  language without that deeper design commitment.

**Why it was chosen this way**: this isn't a dangling-else fix at all — it's
a side effect of Haskell committing, from first principles, to "everything
is an expression, nothing is a statement" (the same commitment C/Java/Dart
make only for calls, per `function-analysis.md` §2, Haskell makes for
control flow itself). Once a language goes that far, a conditional that
could silently produce nothing in one branch isn't just stylistically
risky, it's not well-typed — the fix is a consequence of the type
discipline, not a grammar patch aimed at this specific ambiguity the way
Ada's `end if` or Python's layout rule are.

### 5. No conditional syntax; conditionals are messages (Smalltalk)

**Pros**

- Nothing to get wrong in the grammar: conditionals get the same
  bracketing rules as every other keyword message, so the dangling-else
  shape can't arise for them specifically.
- Extremely small grammar. The Redline grammar has no statement-level
  control flow at all, and new control structures can be added as library
  methods without touching the parser (general knowledge: this is how
  Smalltalk implements loops like `whileTrue:` and `to:do:` as well).

**Cons**

- Every branch body has to be written as a block (`[ ... ]`), even a
  one-expression one, because only a block delays evaluation until the
  receiver picks a branch.
- The grammar can't tell a conditional from any other message send, so
  tools that want to see control flow (or compilers that want to optimize
  it) have to recognize `ifTrue:ifFalse:` by selector name. (General
  knowledge: real Smalltalk compilers do inline these selectors as a
  special case, which is a semantic rule the grammar doesn't record.)
- An accidental missing bracket doesn't produce a nested conditional with
  the wrong attachment, it produces a single message with a longer,
  usually nonexistent selector, so the mistake shows up at runtime rather
  than at parse time.

**Why it was chosen this way**: this isn't a dangling-else fix either.
Smalltalk's design goal (general knowledge: Kay and Ingalls at Xerox PARC)
was "everything is an object, all computation is message sends," and
conditionals are just `ifTrue:`/`ifFalse:` methods on the Boolean classes.
The absence of the ambiguity is a side effect of how keyword messages are
parsed, in the same way that Haskell's mandatory `else` is a side effect of
its type discipline.

## Generalizing the pattern: what actually causes this class of ambiguity

Dangling-else is one instance of a broader, precise phenomenon: it is
**not** caused by "having an optional trailing construct" alone. It
requires two things at once — (1) a trailing optional clause, and (2) a
body slot that can recursively contain another instance of the *same*
construct with no delimiter marking where that inner instance ends. When
both hold, a parser genuinely cannot tell which enclosing instance the
trailing clause binds to. Two more real cases of exactly this shape turn
up elsewhere in `grammar-zoo-flavie-adapted` — one resolved, one not — plus a
useful counter-example that pins down why some optional trailing clauses
never cause this problem at all.

### Case 1: Python's `while`/`for` ... `else` — the identical ambiguity, the identical fix

```
while_stmt ::= "while" test ":" suite [else_clause]
for_stmt   ::= "for" exprlist "in" testlist ":" suite [else_clause]
```

Both loops have an optional trailing `else` (Python's little-known "runs if
the loop completes without `break`" clause), and `suite` can recursively
contain another `while`/`for`. `while a: while b: pass` followed by an
`else:` is structurally identical to the if/else case — and it is resolved
the same way: indentation. The `else`'s column tells you which loop it
belongs to. This confirms that Python's layout-as-delimiter strategy isn't
a one-off fix for `if` specifically — it's a general solution that happens
to cover every construct in the language with this shape at once, which is
a real structural advantage over fixing the ambiguity construct-by-construct.

### Case 2: VB6's single-line `if` — genuinely ambiguous, and left unresolved

```
short_if_statement ::= "if" expn "then" single_declaration_or_statement [short_else_clause]
short_else_clause   ::= "else" single_declaration_or_statement
```

Tracing the recursion: `single_declaration_or_statement` expands to
`statement`, `statement` includes `if_statement`, and
`if_statement ::= full_if_statement | short_if_statement` — so a
`short_if_statement` can genuinely contain another `short_if_statement`
directly, with no `end if` anywhere in this form.
`If a Then If b Then s1 Else s2` is exactly as ambiguous in VB6's one-line
form as it is in C.

This qualifies the strategy-1 table above, which lists VB6 only on the
strength of its `full_if_statement`/`end if` block form. What's actually
true is VB6 has **both** forms side by
side — the safe, delimited one and the ambiguous, undelimited one — the
same "keep the old mechanism, add the new one, never retire either"
pattern already documented for VB6 in the companion analyses (its
name-assignment-plus-bare-`Return` duplication and its
`Optional`-plus-independent-default-value duplication in
`function-analysis.md`). This is now a third confirmed instance of that
same VB6 signature.

### Case 3: Haskell — the same rule, broken from the *other* side

Every case above fixes the ambiguity by denying condition (2): giving the
body its own unambiguous delimiter (`end if`, braces, layout). Haskell
instead denies condition (1) directly — there never was an optional
trailing clause to misattach, since `else` in
`"if" exp "then" exp "else" exp` is mandatory. The recursive containment
(condition 2) is still fully present — `exp` can absolutely contain another
`if` — but with no optionality on the outer construct's own trailing
clause, there's nothing for the recursion to create ambiguity *about*.
Together with the counter-example just below (which denies condition 2
while leaving an optional clause fully in place), these two cases confirm
the "two necessary conditions" framing from opposite directions: break
either one, and the ambiguity provably cannot occur, regardless of what
happens to the other.

### The counter-example that sharpens the rule: `try`/`catch`/`finally` and `switch`/`default`

Java's `try` statement has an optional `finally`, and every `switch` has
an implicit "does this have a `default`" question — both trailing-optional,
structurally similar to `else`. Neither is ambiguous, and the grammar
shows exactly why:

```
"try" block ((catches "finally" block) | catches | ("finally" block))
"switch" parExpression "{" switchBlockStatementGroups "}"
```

`block` and `"{" ... "}"` are *mandatorily* brace-delimited — never the
bare, unbraced `statement` that `if`/`while`/`for` bodies are allowed to be
in C-family languages. Because the body's boundary is always explicit,
there is no nesting ambiguity for a trailing clause to be confused about.
For `try`, this holds uniformly across C++ (`"try" compound-statement
handler-seq`), C#, Java, and Dart: every `try`, `catch`, and `finally`
body is a braced block. For `switch` it holds in C#, Java, and Dart, but
not in C99 or C++98, whose `"switch" "(" ... ")" statement` takes a bare
statement just like `if`. That doesn't reintroduce the problem there,
though, because C/C++ `switch` has no trailing optional clause of its own
(`default` is a label inside the body, not a clause after it), so only
condition (2) holds. It confirms the
precise condition above: the problem is not "has an optional trailing
clause," it is "optional trailing clause *plus* a body that is allowed to
omit its own delimiter."

### A genuinely different ambiguity, worth not conflating with this one

C and C++ have a well-known *different* ambiguity class: whether `T * x;`
is a pointer declaration or a multiplication expression, and C++'s "most
vexing parse" (`Foo f(Bar());` parsing as a function declaration rather
than an object construction). Neither is caused by an optional construct
at all — both come from one token sequence being derivable by two
*unrelated* grammar rules, resolvable only with symbol-table information
(is `T` a typedef name?) that a pure context-free grammar cannot carry.
This is well-documented compiler-theory knowledge rather than something
directly verified against a specific production in this corpus, but it is
worth keeping distinct: "ambiguity in a grammar" is a larger category than
just the dangling-else shape, and this document is specifically about the
latter.
