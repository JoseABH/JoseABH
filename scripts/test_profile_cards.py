import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


spec = importlib.util.spec_from_file_location("cards", Path(__file__).with_name("generate-profile-cards.py"))
cards = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cards)


class ProfileCardsTests(unittest.TestCase):
    profile = {"followers": 4, "created_at": "2022-10-25T00:00:00Z"}

    def repo(self, **overrides):
        return dict(fork=False, private=False, stargazers_count=3, forks_count=2, language="Python") | overrides

    def test_only_public_originals_contribute_to_totals(self):
        result = cards.summarize(self.profile, [self.repo(), self.repo(language=None),
                                              self.repo(fork=True), self.repo(private=True)])
        self.assertEqual((result["repos"], result["stars"], result["forks"]), (2, 6, 4))
        self.assertEqual(result["languages"], {"Python": 1})

    def test_fetches_all_repository_pages(self):
        with patch.object(cards, "github", side_effect=[self.profile, [self.repo()] * 100, [self.repo()]]) as api:
            _, repos = cards.fetch_profile()
        self.assertEqual(len(repos), 101)
        self.assertIn("page=2", api.call_args.args[0])

    def test_empty_language_data_produces_valid_svg(self):
        rendered = cards.render_cards(cards.summarize(self.profile, []))
        for svg in rendered.values():
            ET.fromstring(svg)
        self.assertIn("No public language data", rendered["github-languages.svg"])

    def test_language_chart_groups_overflow_and_escapes_labels(self):
        repos = [self.repo(language="A&B")] * 2
        repos += [self.repo(language=f"Language {i}") for i in range(9)]
        rendered = cards.render_cards(cards.summarize(self.profile, repos))
        svg = rendered["github-languages.svg"]
        ET.fromstring(svg)
        self.assertIn("A&amp;B", svg)
        self.assertIn("Other", svg)
        # 2 repositories in A&B, 6 named groups, 3 grouped as Other: 11 total.
        self.assertIn("27%", svg)

    def test_failed_fetch_preserves_previous_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "assets" / "generated"
            output.mkdir(parents=True)
            existing = output / "github-stats.svg"
            existing.write_text("previous successful card", encoding="utf-8")
            with patch.object(cards, "ROOT", root), patch.object(cards, "github", side_effect=OSError("API unavailable")):
                with self.assertRaises(OSError):
                    cards.main()
            self.assertEqual(existing.read_text(encoding="utf-8"), "previous successful card")


if __name__ == "__main__":
    unittest.main()
