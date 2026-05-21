from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PluginManifestTests(unittest.TestCase):
    def test_plugin_manifest_and_marketplace_are_valid_json(self):
        plugin = json.loads((ROOT / ".agents" / "plugins" / "kodeximi" / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin["name"], "kodeximi")
        self.assertEqual(plugin["skills"], "./skills/")
        self.assertEqual(marketplace["plugins"][0]["name"], "kodeximi")

    def test_plugin_skill_mentions_strict_mode(self):
        skill = (ROOT / ".agents" / "plugins" / "kodeximi" / "skills" / "kodeximi-strict-mode" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Small tasks are not exceptions", skill)
        self.assertIn("inventory", skill)


if __name__ == "__main__":
    unittest.main()

