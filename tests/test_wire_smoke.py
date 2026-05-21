from __future__ import annotations

import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from kodeximi.wire_smoke import run_wire_initialize


class WireSmokeTests(unittest.TestCase):
    def test_initialize_accepts_jsonrpc_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            server = Path(tmp) / "fake_wire_server.py"
            server.write_text(
                textwrap.dedent(
                    """
                    import json
                    import sys

                    line = sys.stdin.readline()
                    request = json.loads(line)
                    assert request["params"]["protocol_version"] == "1.10"
                    assert request["params"]["client"]["name"] == "kodeximi"
                    print(json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": {"protocolVersion": "1.10"}}), flush=True)
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            result = run_wire_initialize([sys.executable, str(server)], cwd=Path(tmp), timeout_seconds=2)
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["response"]["result"]["protocolVersion"], "1.10")

    def test_initialize_reports_non_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            server = Path(tmp) / "fake_bad_wire_server.py"
            server.write_text("print('not json', flush=True)\n", encoding="utf-8")
            result = run_wire_initialize([sys.executable, str(server)], cwd=Path(tmp), timeout_seconds=2)
            self.assertFalse(result["ok"], result)
            self.assertEqual(result["error_code"], "WIRE_NON_JSON_RESPONSE")


if __name__ == "__main__":
    unittest.main()
