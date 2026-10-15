import unittest

from bgf_analysis import analyze_production_shapes, format_analysis, production_shape
from bgf_parser import (
    Grammar,
    Nonterminal,
    Production,
    Selectable,
    SeparatedOneOrMore,
    Sequence,
    Terminal,
)


class BGFAnalysisTests(unittest.TestCase):
    def test_ignores_nonterminal_names_and_selectors_but_preserves_terminals(self):
        left = Sequence((
            Selectable("left", Nonterminal("Expression")),
            Terminal("="),
            Nonterminal("Value"),
        ))
        right = Sequence((
            Nonterminal("Target"),
            Terminal("="),
            Selectable("rhs", Nonterminal("Source")),
        ))
        self.assertEqual(production_shape(left), 'sequence(N, "=", N)')
        self.assertEqual(production_shape(left), production_shape(right))

    def test_preserves_separated_list_as_a_distinct_bgf_abstraction(self):
        expression = SeparatedOneOrMore(Nonterminal("Item"), Terminal(","))
        self.assertEqual(production_shape(expression), 'seplistplus(N, ",")')

    def test_counts_and_sorts_complete_production_shapes(self):
        grammar = Grammar((), (
            Production("A", Terminal("z")),
            Production("B", Nonterminal("A")),
            Production("C", Selectable("field", Nonterminal("B"))),
            Production("D", Terminal("a")),
        ))
        analysis = analyze_production_shapes(grammar)
        self.assertEqual(analysis.production_count, 4)
        self.assertEqual(
            [(entry.count, entry.shape) for entry in analysis.frequencies],
            [(2, "N"), (1, '"a"'), (1, '"z"')],
        )
        self.assertIn("2\tN\n", format_analysis(analysis, source="sample.bgf"))


if __name__ == "__main__":
    unittest.main()
