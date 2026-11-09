# Keywords across `grammar-zoo-flavie-adapted`

An analysis of the word-shaped tokens — keywords — in the 20 grammars of
`grammar-zoo-flavie-adapted`: how many each language has, which words the
languages share, what those shared words mean in each, and what the
different choices cost or buy in terms of the three classic language
evaluation criteria — **readability** (how easily a program can be
understood), **writability** (how easily one can be written), and
**reliability** (how well the language keeps programs correct) — as
framed by Sebesta (see References).

**How the keywords were counted.** A keyword here is any terminal in a
grammar that is shaped like a word (a letter, then letters, digits, `_`
or `-`, plus Fortran's dotted `.and.`-style operators), taken from
`grammar-zoo-flavie/` — before `adapt_lexical_grammar.py` added lexical
rules, so that letters such as the `e` in an exponent or the `x` in `0x`
don't count as keywords. Some non-keyword words were removed by hand:
Python's `INDENT`/`DEDENT` layout markers and string-prefix spellings,
the HTML tag names in PHP's inline-HTML rules, Modula-3's `DQUOTE`, and
Ada's attribute names (`Access`, `Range`, …). C99's `_Bool` and
`_Complex` are added back. Two consequences follow:

- The counts are **words the grammar uses**, not official reserved-word
  lists. They include literal words (`true`, `null`, `nil`), contextual
  keywords, and words that only matter in one construct. Where the two
  happen to agree (Lua 5.2's 22, Python 2's 31), that's a good sign the
  grammar is complete; where they differ, the grammar's own scope is
  usually why.
- With three exceptions (§2), these grammars don't say which words are
  *reserved* — a CFG lists what may appear where, not what may never be a
  name. Reservation normally lives in the lexer.

## 1. How many keywords?

| Language | Keywords | What makes up the count |
|---|---|---|
| Smalltalk | 5 | `nil true false self super` — and nothing else |
| Lua 5.2 | 22 | control flow, `local`, `function`, logical operators as words |
| Haskell 98 | 23 | declarations (`data`, `class`, `instance`, `module`, …) and a handful of expression words |
| Erlang | 27 | expression forms (`case`, `receive`, `fun`, `try`), word operators (`div`, `rem`, `band`, `bsl`, …) |
| Python 2 | 31 | statement keywords, `and`/`or`/`not`/`is`/`in` |
| JavaScript | 34 | C-style statements, `function`, `typeof`, `instanceof` |
| C99 | 36 | statements, types, storage classes, qualifiers |
| Dart | 44 | C-style plus class vocabulary |
| Java 5 | 51 | C-style plus modifiers and class vocabulary |
| Swift | 57 | declarations, statements, 21 context-sensitive words |
| Modula-3 | 57 | all uppercase; types, modules, `LOCK`, `TYPECASE`, `UNTRACED` |
| C++98 | 61 | C plus classes, templates, casts, exceptions |
| Eiffel | 62 | contracts (`require`, `ensure`, `invariant`, `variant`), inheritance clauses |
| PHP | 72 | C-style plus alternative syntax (`endif`, `endwhile`, …) and built-in language constructs (`echo`, `isset`, `unset`, `include`) |
| Ada 2005 | 73 | statements, types, packages, tasking (`accept`, `entry`, `select`, `requeue`) |
| C# 4.0 | 105 | 77 reserved + 28 contextual (§2) |
| Fortran-90 | 111 | statements, type and attribute words, `end`-forms, dotted operators |
| Delphi 2006 | 136 | Pascal plus built-in type names (`integer`, `cardinal`, `ansistring`, …), calling conventions (`cdecl`, `stdcall`, `safecall`), class directives |
| VB6 | 137 | statements, plus file and system commands as keywords (`beep`, `chdir`, `kill`, `mkdir`, `filecopy`, `savepicture`, …) |
| COBOL | 321 | English verbs, clause words, `END-xxx` terminators, data-format words |

The range is a factor of 64, from Smalltalk to COBOL. Three different
things drive a count up:

- **Library as syntax.** VB6 gives operations that other languages put in a
  library (`kill` a file, `mkdir`, `beep`) their own keyword and statement
  form; Delphi makes predefined type names keywords; PHP does the same for
  `echo`, `isset`, `unset`, `include`. Compare Python 2, where only `print`
  and `exec` get that treatment.
- **English as syntax.** COBOL writes almost everything in words, including
  arithmetic (`ADD x TO y`, `MULTIPLY`, `DIVIDE … GIVING`) and comparison
  (`GREATER THAN OR EQUAL TO`), and closes each statement kind with its
  own `END-xxx`.
- **One keyword per feature.** C#'s 105 come from the language having many
  distinct features (unsafe code, events, properties, LINQ), each with its
  own word.

The low end is driven by the opposite choice: put the work somewhere other
than keywords. Smalltalk's five reserved words are all *values* — there is
not a single control-flow keyword, because conditionals and loops are
messages sent to objects (`x > 0 ifTrue: [...]`; see
`dangling-else-analysis.md`). Haskell and Erlang use symbols and layout
(`->`, `|`, `<-`, `::`) and make most constructs expressions; Lua keeps
one form per job and reuses `end` and `do` for every block.

## 2. Reserved, contextual, or neither

A reserved word can never be a name; a contextual keyword is a keyword
only in certain positions and an ordinary name everywhere else. Three
grammars show the difference directly:

- **Swift** splits the two in the grammar itself:
  `keyword ::= "class" | "deinit" | "enum" | … | "Self" | "Type"` (37
  words) versus `context_sensitive_keyword ::= "associativity" | "didSet" |
  "get" | … | "willSet"` (21 words), and then
  `identifier ::= Identifier | context_sensitive_keyword` — so `get`, `set`,
  `left`, `weak` and the rest are legal variable names, while `class` is
  not.
- **Dart** does the same with what it calls built-in identifiers:
  `identifier ::= IDENTIFIER_NO_DOLLAR | IDENTIFIER | ABSTRACT | ASSERT |
  CLASS | EXTENDS | FACTORY | GET | …`. Words like `get`, `set`, `import`
  and `static` can be names. (`CLASS` appearing in that list is odd —
  `class` is fully reserved in Dart as generally documented — so this
  looks like a quirk of this early grammar.)
- **C#** in its extracted tier has one `keyword` rule with 105
  alternatives, but its order gives the split away: the first 77, `abstract`
  through `while`, are C#'s reserved words, and the last 28 — `group`,
  `by`, `join`, `let`, `get`, `set`, `yield`, `partial`, `var`, `where`,
  `from`, `select`, … — are its contextual keywords (general knowledge for
  the split itself). C# also has an escape hatch in the grammar:
  `identifier ::= available-identifier | "@" identifier-or-keyword`, so
  `@class` is a legal name.

Everywhere else, the grammar's identifier rule simply doesn't exclude
keywords — reservation is left to the lexer. The one language where that
gap is the real language is **Fortran**, which has no reserved words at
all (general knowledge): `IF`, `END` and `REAL` are all legal variable
names, and the parser works out from context which is meant.

**Why contextual keywords exist: evolution.** Most of C#'s 28
contextual words — `yield`, `partial` and `where` in C# 2.0, `var` and the
LINQ words in 3.0, `dynamic` in 4.0 — were added after the language
shipped (general knowledge). Making them reserved would have broken every
existing program that used `var`, `where` or `select` as a name. The same pressure explains Swift's and
Dart's split. A reserved word is safest to *read* — it can only mean one
thing — but it is a one-way door for language designers, so new keywords
get added as contextual ones.

## 3. How keywords are spelled

**Case.** Modula-3 writes every keyword in uppercase (`IF`, `PROCEDURE`,
`END`), as does COBOL. Eiffel capitalizes its value-like words (`True`,
`False`, `Current`, `Result`, `NONE`, `TUPLE`), and Swift its type-level
ones (`Self`, `Type`, `Protocol`). Everyone else uses lowercase. Ada,
Pascal, Fortran, VB6 and COBOL are case-insensitive languages, so their
grammars' casing is a convention of the source, not a rule (general
knowledge); Modula-3's uppercase is a rule.

**Multi-word keywords.** Several grammars build one keyword out of two
words:

- Ada: `and then`, `or else` (short-circuit forms), `end if`, `end loop`,
  `end select`.
- Eiffel: `and then`, `or else`.
- COBOL: `GREATER THAN OR EQUAL TO`, `NEXT SENTENCE`.
- Fortran accepts **both** the spaced and the joined form: `EndIfStmt ::=
  … "endif" … | … "end" "if" …`, and likewise `go` `to` / `goto`,
  `double` `precision` / `doubleprecision`, `select` `case` / `selectcase`.
- COBOL uses hyphens instead: `END-IF`, `DATE-WRITTEN`, `ALPHABETIC-LOWER`.

**Optional noise words.** COBOL has keywords whose only job is to make a
statement read like English, and they're optional. In this grammar, `IS`
appears 60 times and is optional in 48 of them; `THAN` (7 of 7), `WITH`
(14 of 14), `ON` (17 of 21) and `TO` (13 of 28) are often optional too.
`relational_operator ::= [("IS" | "NOT" | ("IS" "NOT") | ("NOT" "IS"))]
(("GREATER" ["THAN"]) | ">" | …)` alone admits `X > Y`, `X GREATER Y`,
`X IS GREATER THAN Y`, `X GREATER THAN Y` and more, all meaning the same
thing.

## 4. Same word, different meaning

Twenty-three words appear in at least nine of the twenty grammars (`if`,
`else`, `do`, `return`, `case`, `for`, `while`, `in`, `class`, `default`,
`continue`, `and`, `or`, `break`, `try`, `new`, `then`, `not`, `end`,
`const`, `static`, `true`, `false`). Most of the control-flow ones (`if`,
`else`, `while`, `return`, `break`, `continue`) mean nearly the same thing
everywhere. The interesting ones are those that don't.

### `in`

| Meaning | Languages and productions |
|---|---|
| element of a `for` loop | Python `for_stmt`, JS `js_for_statement`, Lua `stat`, Swift `for_in_statement`, VB6 `for_each_statement`, C# `foreach-statement`, Ada `loop_parameter_specification`, Delphi `loop_stm` |
| membership test (operator) | Python `comp_op` (`"in" \| "not" "in"`), JS `js_equality_op`, Modula-3 `Relop`, Delphi `infix_opr` |
| end of local bindings | Haskell `exp10n` (`let … in …`) |
| parameter mode (input) | Ada `mode`, Fortran `IntentSpec` (`intent(in)`) |
| start of a closure body | Swift `closure_signature` (`{ x in … }`) |
| source of a query | C# `from-clause`, `join-clause` (LINQ) |

Six meanings for a two-letter word. Swift alone uses it two ways (`for x
in xs` and `{ x in x * 2 }`), and Python two ways (`for x in xs` and
`if x in xs`) — in Python's case the grammar has to tell them apart by
position, since `for x in xs` contains an `in` that is not an operator.

### `case`

| Meaning | Languages |
|---|---|
| a label inside `switch` | C99, C++98, C#, Java, JS, Dart, PHP, Swift (`case_label`) |
| the multi-way statement itself | Ada `case_statement`, Modula-3 `CaseStmt`, Fortran `CaseConstruct`, Delphi `selection_stm`, VB6 `select_case_statement` |
| a pattern-matching *expression* | Haskell `exp10n` (`case e of …`), Erlang `caseExpr` (`case e of … end`) |
| a variant inside a record type | Ada `variant_part`, Delphi `variant_section` |
| declaring an enum member | Swift `raw_value_style_enum_case_clause` (`case red, green`) |

In the C family `case` marks one *branch*; in the Algol/Pascal family it
names the *whole construct*. Haskell's and Erlang's `case` returns a value.
Swift is the only one where `case` also *declares* something.

### `class`

Object-oriented class in C++, C#, Java, Dart, Python, PHP, Delphi, VB6,
Eiffel, Swift; **type class** in Haskell (`topdecl`), which is closer to an
interface (`classes-and-inheritance-analysis.md` §7); **character class**
in COBOL (`class_clause`, a named set of characters for a condition
test). Delphi adds two more: `class` before a method for a class-level
method, and `class of T` for a metaclass type (`class_reference_type`).

### `do`

A loop body opener (Lua, Modula-3, Delphi `while … do`), the start of a
post-tested loop (C99, C++, C#, Java, JS, PHP `do … while`; Swift
`do_while_statement`), Fortran's counting loop (`DO i = 1, n`), Eiffel's
routine body (`Routine_mark`), an Ada `accept … do` rendezvous body — and
Haskell's `do`, which has nothing to do with loops: it sequences monadic
actions (`exp10n`). Delphi also uses `do` after `with` and in exception
handlers (`on E: Exception do`).

### `is`

Ada uses `is` to introduce a declaration's body (`procedure P is …`,
`type T is …`) — it carries no operation at all. Python's `is` is object
identity (`comp_op`), C#'s and Delphi's a type test (`x is string`), and
Swift's a type-test *pattern* (`is_pattern`). In COBOL it is a noise word
(§3).

### `with`

| Meaning | Languages |
|---|---|
| open a record's fields as plain names | Delphi `with_stm`, VB6 `with_statement`, JS `js_with_statement` |
| alias a value for a block | Modula-3 `WithStmt` |
| context manager (setup/teardown) | Python `with_stmt` |
| import a library unit; extend a record | Ada (`with` clause; `extension_aggregate`, `… with private`) |
| a filler word in a statement | COBOL (`CLOSE … WITH LOCK`, `DISPLAY … WITH NO ADVANCING`) |

### `select`

Ada's `select` is concurrency (choosing among task rendezvous —
`selective_accept`, `timed_entry_call`); VB6's and Fortran's is a
multi-way branch (`select case`); C#'s ends a LINQ query (`select-clause`);
Eiffel's resolves a name clash under repeated inheritance (`Select`);
COBOL's assigns a file (`select_clause`).

### `new`

Object creation in C++, C#, Java, JS, Dart, PHP, VB6. In Ada, `new` is
also used for **type derivation** — `type Celsius is new Float;` makes a
new, incompatible type (`derived_type_definition`) — and for allocation
(`allocator`). C# adds a third meaning: `new` as a member modifier that
hides an inherited member (`class-modifier`).

### `static`

The word with the most meanings *inside* one language. In C99 the grammar
shows it in `storage-class-specifier` (internal linkage at file level,
persistent storage inside a function) and also in `direct-declarator`
(`int a[static 10]` — a guarantee that a parameter array has at least 10
elements). In Java it marks class members and also appears in
`importDeclaration` (`import static`). In VB6, PHP, Swift, C#, Dart it
marks class-level or persistent members. Delphi uses it for class methods.

### `let`, `where`, `when`, `of`, `end`

- `let`: a local binding scope in Haskell (`let … in`), an immutable
  binding in Swift (`constant_declaration`), the optional assignment word
  in VB6 (`Let x = 5`), a query variable in C# LINQ (`let-clause`).
- `where`: local definitions in Haskell (`wheredecls`), generic
  constraints in C# (`type-parameter-constraints-clause`) and Swift
  (`requirement_clause`), a filter in C# LINQ and Swift's `case … where`
  (`guard_clause`), and a masked array assignment in Fortran
  (`WhereConstructStmt`).
- `when`: an alternative in Ada `case` and exception handlers, a guard in
  Ada entries (`entry_barrier`) and Erlang (`clauseGuard`), an `inspect`
  branch in Eiffel (`When_part`).
- `of`: element type in Ada/Modula-3/Pascal arrays (`array … of`), the
  branch list in Haskell/Erlang/Modula-3/Pascal `case … of`.
- `end`: closes a block in nine grammars (Ada, VB6, COBOL, Eiffel, Erlang,
  Fortran, Lua, Modula-3, Delphi), but how much it says varies: Lua's,
  Eiffel's and Modula-3's bare `end` closes anything, Ada's and VB6's `end
  if`/`end loop` names what it closes, and COBOL's `END-IF`/`END-READ`
  fuses the two into one word.

### `and` and `or` — same word, different precedence

This is where shared words cause real bugs, and the grammars show
exactly how:

- **PHP has both `and` and `&&`, at different precedence.**
  `LogicalAndAssignmentExpr ::= "and" AssignmentExpr` places `and` *below*
  assignment, while `ConditionalAndBitOrExpr ::= "&&" BitOrExpr` places
  `&&` above it. So `$ok = true and false;` assigns `true` to `$ok` and
  then discards the `and` (general knowledge for the resulting value; the
  grammar shows the precedence).
- **Erlang's `and`/`or` are not the short-circuit operators.**
  `multOp ::= "/" | "*" | "div" | "rem" | "band" | "and"` and
  `addOp ::= … | "or" | "xor"` put them at the same precedence as `*` and
  `+`; the short-circuit forms are separate words at the bottom of the
  precedence ladder: `expr150 ::= expr160 ("orelse" expr160)*`,
  `expr160 ::= expr200 ("andalso" expr200)*`.
- **Ada forbids mixing them without parentheses.**
  `expression ::= (relation ("and" relation)*) | (relation ("or"
  relation)*) | (relation ("xor" relation)*) | (relation ("and" "then"
  relation)*) | (relation ("or" "else" relation)*)` — each alternative
  repeats only *one* operator, so `a and b or c` doesn't parse at all; it
  has to be written `(a and b) or c`. Ada also reuses `and` in
  `interface_list` (`new T and I1 and I2`), and `or` between alternatives
  of a `select`.
- Python, Lua, Delphi, VB6, Modula-3, Eiffel and COBOL use only the word
  forms; Fortran writes them as dotted words (`.and.`, `.or.`, `.not.`,
  `.eqv.`); the C family and Haskell use only symbols; Eiffel adds
  `implies`.

Similarly, `mod` is an operator in VB6, Modula-3 and Delphi, but in Ada it
also appears in type definitions (`type Byte is mod 256` — a modular,
wrap-around integer type, `modular_type_definition`); `rem` is the
remainder operator in both Ada and Erlang.

## 5. Readability, writability, and reliability

The three criteria pull against each other, and keywords are one of the
clearest places to see it.

### More keywords versus fewer

**Many keywords favour readability for newcomers and hurt writability.**
COBOL's `ADD PRICE TO TOTAL` and VB6's `kill "file.txt"` can be read
aloud and understood with no knowledge of the language. The cost is
paid by the writer — more words to type, and more to memorize — and by
the language's consistency: 137 VB6 keywords include commands that
would be ordinary library calls elsewhere, so the boundary between
"language" and "library" is wherever the designers happened to draw it.

**Few keywords favour writability and orthogonality.** Smalltalk's five
words and Lua's 22 are learnable in an afternoon, and in Smalltalk every
construct follows the same message-send rule. The cost moves elsewhere:
more meaning is carried by symbols and position (`[ ]` blocks, `^`
return, Haskell's `->`, `<-`, `|`), which is concise to write but harder
to read for anyone who doesn't already know the conventions.

### Optional words and alternative spellings

COBOL's optional `IS`/`THAN`/`TO` and Fortran's `endif`/`end if`,
`goto`/`go to` are **writability features** — the writer may choose — and
**readability costs**: a reader of a large codebase meets the same
construct spelled several ways, and searching for it means searching for
every spelling. They don't affect reliability directly, since every
spelling means the same thing.

### Reserved words versus contextual keywords versus none

- **Reserved words** are the most **reliable** and **readable** choice:
  `if` can never be a variable, so a reader never has to wonder. The cost
  falls on the language's future, since every new reserved word breaks
  existing programs that used it as a name.
- **Contextual keywords** (C#, Swift, Dart) trade a little readability —
  `var where = select;` is legal C# — for the ability to grow the language
  without breaking old code.
- **No reserved words** (Fortran) maximizes backward compatibility and
  writability (any name is available) at a large readability and
  reliability cost: `IF (IF .EQ. THEN) THEN = ELSE` is legal Fortran
  (general knowledge), and a misspelling can silently turn a statement
  into an assignment.

### Overloaded words within a language

`static` in C (three meanings), `in` in Swift and Python (two each), `do`
in Delphi (three), `new` in Ada (two), `and`/`or` in Ada (operator and
list separator): reusing a word saves the language a keyword, which is a
small **writability** gain, and costs **readability**, because the
reader has to work out from position which meaning applies. Usually the
position makes it obvious; C's `static` is the standard example of where
it doesn't (general knowledge).

### Shared words across languages

This is the biggest **reliability** risk in the whole analysis, because
the errors it causes are silent. A programmer who carries a meaning from
one language to another gets code that compiles and does the wrong thing:

- `and` in PHP binds below `=`; in Erlang it doesn't short-circuit.
- `is` in Python is identity, not equality (general knowledge: `x is 1000`
  can be false even when `x == 1000`).
- `case` in C falls through to the next label without `break`; in Ada,
  Pascal, Haskell, Erlang and Swift it doesn't (general knowledge; C's
  `labeled-statement` is just a label, which is *why* it falls through).
- `static`, `with`, `select` and `new` mean different things in different
  languages, though most of those mismatches give a compile error rather
  than wrong behaviour.

Designers have three responses visible in this corpus. **Two words**:
Erlang's `andalso`/`orelse` and Ada's and Eiffel's `and then`/`or else`
give the short-circuit operators names that can't be mistaken for the
non-short-circuit ones. **A grammar rule**: Ada's `expression` makes
`a and b or c` unparsable, forcing the writer to state the intended
grouping — a direct trade of writability for reliability, enforced by
the grammar itself. **Uniformity**: Smalltalk avoids the problem by
having almost no keywords to misunderstand.

### Word terminators versus symbols

The nine grammars that close blocks with `end` sit at one end of a
three-way trade. A bare `end` (Lua, Eiffel, Modula-3) is easy to write
but, in a deep nest, hard to match by eye. A named terminator (`end if`,
`END-IF`, Fortran's `endif`) is longer to write but tells the reader what
is closing, and lets the compiler report *which* block is unclosed — a
reliability gain, and the same mechanism that removes the dangling-else
ambiguity (`dangling-else-analysis.md`, strategy 1). Braces (the C
family) are the most writable and the least self-describing.

### Case conventions

Modula-3's mandatory uppercase keywords make the structure of a program
visible at a glance, since `IF`, `WHILE` and `END` stand out from
lowercase names — good for readability, and cheap for reliability since
a keyword can never clash with a lowercase name. The cost is writability:
constant shifting, and the visual weight critics call shouting. Most
later languages chose lowercase keywords and left highlighting to the
editor.

## Summary

- **Keyword counts range from 5 (Smalltalk) to 321 (COBOL).** High counts
  come from library-as-syntax (VB6, Delphi, PHP), English-as-syntax
  (COBOL), or many features (C#); low counts from pushing control flow
  into messages (Smalltalk), symbols and expressions (Haskell, Erlang), or
  a minimal construct set (Lua).
- **Most grammars don't say which words are reserved.** Swift, Dart and C#
  show the reserved/contextual split in the grammar; Fortran has no
  reserved words at all.
- **Common words drift in meaning.** `in` has six meanings across the
  corpus, `case` five, `class` three; `static` has several inside C alone.
- **The dangerous overlaps are the silent ones.** PHP's `and`, Erlang's
  `and`, and Python's `is` look familiar and do something else. Two-word
  operators (`andalso`, `and then`) and Ada's no-mixing rule are the
  grammar-level defences.
- **The trade-off is consistent.** More words and more optional words buy
  readability for newcomers at a writability cost; fewer words buy
  writability and uniformity at a readability cost; reserved words buy
  reliability at the cost of the language's ability to evolve, which is
  why newer keywords are contextual.

## References

Keyword counts and productions are taken from `grammar-zoo-flavie/` and
`normalized-ebnf-flavie-adapted/`. Remarks marked as general knowledge are
not cited claim by claim.

- Sebesta, R. W. (2019). *Concepts of Programming Languages* (12th ed.). Pearson. — the readability / writability / reliability evaluation criteria used in §5, and the discussion of reserved words versus keywords.
- Hoare, C. A. R. (1973). *Hints on Programming Language Design* (Stanford AI Lab Memo AIM-224 / STAN-CS-73-403). Stanford University, Computer Science Department. — readability and reliability as design goals.
- Stefik, A., & Siebert, S. (2013). An empirical investigation into programming language syntax. *ACM Transactions on Computing Education*, 13(4), 1–40. https://doi.org/10.1145/2534973 — measured how intuitive novices find different keyword choices.
- Zaytsev, V. (2015). Grammar Zoo: A corpus of experimental grammarware. *Science of Computer Programming*, 98, 28–51. https://doi.org/10.1016/j.scico.2014.07.010 — the source corpus every grammar here comes from.
