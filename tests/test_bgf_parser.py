from pathlib import Path
import unittest

from bgf_parser import (
    BGFParseError,
    Choice,
    Empty,
    Epsilon,
    Marked,
    Nonterminal,
    Optional,
    Selectable,
    SeparatedOneOrMore,
    Sequence,
    Terminal,
    format_grammar,
    parse,
    parse_string,
)


NS = "http://planet-sl.org/bgf"


class BGFParserTests(unittest.TestCase):
    def test_preserves_roots_labels_order_and_expression_structure(self):
        grammar = parse_string(
            f'''<b:grammar xmlns:b="{NS}">
              <root>Start</root><root>Other</root>
              <b:production><label>main</label><nonterminal>Start</nonterminal>
                <b:expression><sequence>
                  <b:expression><terminal>if</terminal></b:expression>
                  <b:expression><optional><b:expression><nonterminal>Other</nonterminal></b:expression></optional></b:expression>
                </sequence></b:expression>
              </b:production>
            </b:grammar>'''
        )
        self.assertEqual(grammar.roots, ("Start", "Other"))
        production = grammar.productions[0]
        self.assertEqual((production.label, production.nonterminal), ("main", "Start"))
        self.assertEqual(
            production.expression,
            Sequence((Terminal("if"), Optional(Nonterminal("Other")))),
        )

    def test_distinguishes_special_and_annotating_constructs(self):
        grammar = parse_string(
            f'''<grammar xmlns="{NS}"><production><nonterminal>X</nonterminal>
              <expression><choice>
                <expression><epsilon/></expression>
                <expression><empty/></expression>
                <expression><selectable><selector>field</selector><expression><terminal> </terminal></expression></selectable></expression>
                <expression><marked><mark>m</mark><expression><seplistplus><expression><nonterminal>X</nonterminal></expression><expression><terminal>,</terminal></expression></seplistplus></expression></marked></expression>
              </choice></expression>
            </production></grammar>'''
        )
        self.assertEqual(
            grammar.productions[0].expression,
            Choice((
                Epsilon(),
                Empty(),
                Selectable("field", Terminal(" ")),
                Marked("m", SeparatedOneOrMore(Nonterminal("X"), Terminal(","))),
            )),
        )

    def test_rejects_unknown_construct_instead_of_losing_it(self):
        with self.assertRaisesRegex(BGFParseError, "unknown BGF expression"):
            parse_string(
                f'<grammar xmlns="{NS}"><production><nonterminal>X</nonterminal>'
                '<expression><future/></expression></production></grammar>'
            )

    def test_canonical_pretty_printer_covers_annotations_and_escaping(self):
        grammar = parse_string(
            f'''<grammar xmlns="{NS}"><root>S</root>
            <production><label>quoted " label</label><nonterminal>S</nonterminal>
              <expression><sequence>
                <expression><terminal>line&#10;break</terminal></expression>
                <expression><star><expression><value>string</value></expression></star></expression>
                <expression><seplistplus><expression><nonterminal>S</nonterminal></expression><expression><terminal>,</terminal></expression></seplistplus></expression>
              </sequence></expression>
            </production></grammar>'''
        )
        self.assertEqual(
            format_grammar(grammar),
            '@root N("S");\n\n'
            'N("S") @label("quoted \\" label") ::= '
            '("line\\nbreak" (value("string"))* sep+(N("S"), ","));\n',
        )

    def test_pretty_printer_rejects_non_ast_objects(self):
        with self.assertRaisesRegex(TypeError, "unsupported expression node"):
            format_grammar(
                # Runtime validation is intentional even though static typing
                # rejects this malformed AST.
                type("G", (), {"roots": (), "productions": (
                    type("P", (), {"nonterminal": "X", "label": None, "expression": object()})(),
                )})()
            )

    def test_entire_grammar_zoo_parses(self):
        corpus = Path(__file__).parents[1] / "grammar-zoo"
        files = sorted(corpus.glob("*.bgf"))
        self.assertEqual(len(files), 588)
        for path in files:
            with self.subTest(path=path.name):
                grammar = parse(path)
                self.assertIsInstance(grammar.productions, tuple)


if __name__ == "__main__":
    unittest.main()
