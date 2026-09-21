"""Tests for Ollama SLM client and stub fallback."""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import MagicMock, patch

from lffa import config
from lffa import slm


class SlmFallbackTests(unittest.TestCase):
    def test_complete_local_unreachable_uses_stub(self) -> None:
        with patch.object(slm, "ollama_reachable", return_value=False):
            result = slm.complete_local("hello", embedding_model="stub-sha256-local-v0")
        self.assertEqual(result.backend, "stub")
        self.assertIsNotNone(result.notice)
        self.assertIn("stub local SLM", result.text)

    def test_complete_local_missing_model_uses_stub(self) -> None:
        with patch.object(slm, "ollama_reachable", return_value=True):
            with patch.object(slm, "ollama_model_available", return_value=False):
                result = slm.complete_local("hello", embedding_model="stub-sha256-local-v0")
        self.assertEqual(result.backend, "stub")
        self.assertIn("not pulled", result.notice or "")

    def test_complete_local_success(self) -> None:
        payload = json.dumps({"response": "Budget looks fine."}).encode()

        def fake_urlopen(req, timeout=0):  # noqa: ARG001
            resp = MagicMock()
            resp.status = 200
            resp.read.return_value = payload
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        with patch.object(slm, "ollama_reachable", return_value=True):
            with patch.object(slm, "ollama_model_available", return_value=True):
                with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                    result = slm.complete_local("User: hi", embedding_model="stub-sha256-local-v0")
        self.assertEqual(result.backend, "ollama")
        self.assertEqual(result.text, "Budget looks fine.")
        self.assertIsNone(result.notice)

    def test_default_model_env(self) -> None:
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("LFFA_OLLAMA_MODEL", None)
            config.reset_config_cache()
            self.assertEqual(slm.ollama_model(), slm.DEFAULT_OLLAMA_MODEL)


if __name__ == "__main__":
    unittest.main()
