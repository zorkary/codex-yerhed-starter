from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_GRAPH_FIELDS = [
    "broken links",
    "duplicate/near-duplicate entity pages",
    "missing entity pages",
    "missing resolver entries",
    "stale aliases",
    "stale salience / Active Anchor promotion-demotion candidates",
    "graph hygiene warnings",
    "new wikilink candidates",
    "ambiguous/sensitive link candidates requiring operator approval",
    "applied safe link/entity updates",
    "skipped link/entity updates with reason",
]


class DreamCycleProtocolTests(unittest.TestCase):
    def test_protocol_requires_auditable_graph_gardening_sections(self) -> None:
        text = (REPO_ROOT / "automations" / "dream-cycle.md").read_text(encoding="utf-8")
        for field in REQUIRED_GRAPH_FIELDS:
            self.assertIn(field, text)
        self.assertIn("suggest_links_for_review_set", text)
        self.assertIn("Minimum review set", text)

    def test_automation_template_mentions_new_wikilink_candidates(self) -> None:
        text = (REPO_ROOT / "automations" / "codex-automation-specs.md").read_text(encoding="utf-8")
        self.assertIn("new wikilink candidates", text)
        self.assertIn("suggest_links_for_review_set", text)


if __name__ == "__main__":
    unittest.main()
