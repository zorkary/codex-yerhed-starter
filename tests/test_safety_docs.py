from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]


class SafetyDocsTests(unittest.TestCase):
    def test_public_safety_docs_are_explicit(self) -> None:
        readme = (REPO / "README.md").read_text()
        security = (REPO / "SECURITY.md").read_text()
        threat = (REPO / "THREAT_MODEL.md").read_text()
        combined = "\n".join([readme, security, threat])
        self.assertIn("THREAT_MODEL.md", readme)
        self.assertIn("THREAT_MODEL.md", security)
        for phrase in [
            "No Send / No Network",
            "best-effort",
            "not DLP",
            "No Warranty",
            "YERHED_DISABLED=1",
            "unset YERHED_DISABLED",
            "codex mcp remove yerhed",
            "do not use it with data you cannot afford to expose",
        ]:
            self.assertIn(phrase, combined)
        self.assertIn("Egress helpers classify drafts", combined)
        self.assertIn("they do not send, post, publish", combined)

    def test_static_bootstrap_docs_defer_to_disabled_mode(self) -> None:
        agents = (REPO / "AGENTS.md").read_text()
        global_boot = (REPO / "config" / "global-bootstrap.md").read_text()
        for text in [agents, global_boot]:
            self.assertIn("YERHED_DISABLED=1", text)
            self.assertIn("overrides", text)
            self.assertIn("closeout", text)
