"""CLI smoke tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lffa import cli
from lffa import config


class CliTests(unittest.TestCase):
    def test_version_command(self) -> None:
        code = cli.main(["version"])
        self.assertEqual(code, 0)

    def test_doctor_json(self) -> None:
        from lffa import slm

        with patch.object(slm, "ollama_reachable", return_value=False):
            config.reset_config_cache()
            with patch("sys.stdout") as out:
                # doctor prints to real stdout in json mode via print_json
                import io
                from contextlib import redirect_stdout

                buf = io.StringIO()
                with redirect_stdout(buf):
                    code = cli.main(["doctor", "--json"])
                payload = json.loads(buf.getvalue())
        self.assertIn("checks", payload)
        self.assertFalse(payload["all_ok"])  # ollama unreachable in test

    def test_export_import_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "ledger.db")
            cli.main(["add", "--db", db, "Item", "-100", "--category", "misc"])
            out_file = Path(tmp) / "out.json"
            code = cli.main(["export", "--db", db, "-o", str(out_file)])
            self.assertEqual(code, 0)
            db2 = str(Path(tmp) / "ledger2.db")
            code = cli.main(["import", "--db", db2, str(out_file)])
            self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
