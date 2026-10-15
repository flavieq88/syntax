from pathlib import Path
import tempfile
import unittest

from bgf_mining import mine_corpus, terminal_class


class BGFMiningTests(unittest.TestCase):
    def test_terminal_classification_preserves_identity_in_report(self):
        self.assertEqual(terminal_class("while"), "keyword")
        self.assertEqual(terminal_class("("), "punctuation")
        self.assertEqual(terminal_class("+="), "punctuation")

    def test_mines_subtrees_and_structural_relations_with_provenance(self):
        xml = '''<grammar xmlns="http://planet-sl.org/bgf">
          <production><nonterminal>A</nonterminal><expression><sequence>
            <expression><terminal>(</terminal></expression>
            <expression><selectable><selector>x</selector><expression><nonterminal>B</nonterminal></expression></selectable></expression>
            <expression><terminal>)</terminal></expression>
          </sequence></expression></production>
          <production><nonterminal>C</nonterminal><expression><seplistplus>
            <expression><nonterminal>D</nonterminal></expression>
            <expression><terminal>,</terminal></expression>
          </seplistplus></expression></production>
        </grammar>'''
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "sample.bgf")
            source.write_text(xml, encoding="utf-8")
            report = mine_corpus((source,), minimum_frequency=1, example_limit=2)

        subtree = next(item for item in report["subtrees"] if item["shape"] == 'sequence("(", N, ")")')
        self.assertEqual(subtree["frequency"], 1)
        self.assertEqual(subtree["languages"], ["sample"])
        self.assertEqual(
            subtree["terminals"],
            [{"value": "(", "class": "punctuation"}, {"value": ")", "class": "punctuation"}],
        )
        relations = {(item["relation"], item["shape"]) for item in report["motifs"]}
        self.assertIn(("sequence(T1, subtree, T2)", 'sequence("(", N, ")")'), relations)
        self.assertIn(("separated-repetition(subtree, T)", 'seplistplus(N, ",")'), relations)
        separated = next(item for item in report["subtrees"] if item["shape"] == 'seplistplus(N, ",")')
        self.assertEqual(separated["containing_structures"], [])
        nonterminal = next(item for item in report["subtrees"] if item["shape"] == "N")
        parent_shapes = {item["shape"] for item in nonterminal["containing_structures"]}
        self.assertIn('sequence("(", N, ")")', parent_shapes)
        adjacent = next(
            item for item in report["motifs"]
            if item["relation"] == "sequence(N, T)" and item["shape"] == 'sequence(N, ")")'
        )
        self.assertIn(
            'sequence("(", N, ")")',
            {item["shape"] for item in adjacent["containing_structures"]},
        )


if __name__ == "__main__":
    unittest.main()
