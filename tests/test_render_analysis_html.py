import unittest

from render_analysis_html import render_report


class RenderAnalysisHTMLTests(unittest.TestCase):
    def test_renders_self_contained_safe_report(self):
        record = {
            "frequency": 2, "language_count": 1, "languages": ["c"],
            "production_count": 1, "productions": ["c:0:X"],
            "shape": 'sequence("</script>", N)',
            "terminals": [{"value": "</script>", "class": "punctuation"}],
            "examples": [{"language": "c", "production": "c:0:X", "text": "example"}],
            "containing_structures": [{"frequency": 2, "language_count": 1,
                "production_count": 1, "shape": 'sequence("(", sequence("</script>", N), ")")'}],
        }
        report = {"grammar_count": 1, "production_count": 1, "subtrees": [record], "motifs": []}
        document = render_report(report)
        self.assertIn("How to read this report", document)
        self.assertIn("Recurring subtrees", document)
        self.assertNotIn('sequence("</script>", N)', document)
        self.assertIn(r"<\/script>", document)
        self.assertIn(r".join('\n')", document)
        self.assertNotIn(".join('\n')", document)
        self.assertIn('<option value="present" selected>Has at least one terminal</option>', document)
        self.assertIn("tc==='present'?x.terminals.length>0", document)
        self.assertIn("Recurring containing structures", document)
        self.assertIn('class="shape-link"', document)
        self.assertIn("rows.filter(x=>x.shape===exactShape)", document)
        self.assertIn("switchSection('subtrees')", document)


if __name__ == "__main__":
    unittest.main()
