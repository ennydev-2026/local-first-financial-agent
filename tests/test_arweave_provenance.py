"""Tests for Arweave provenance stub and wallet configuration."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lffa import config
from lffa.arweave_provenance import build_artifact, upload_artifact


class ArweaveProvenanceTests(unittest.TestCase):
    def test_upload_without_wallet_is_stub(self) -> None:
        with patch.dict(
            os.environ,
            {
                "LFFA_ARWEAVE_WALLET_JWK_PATH": "",
                "ARWEAVE_WALLET_JWK_PATH": "",
            },
            clear=False,
        ):
            os.environ.pop("LFFA_ARWEAVE_WALLET_JWK_PATH", None)
            os.environ.pop("ARWEAVE_WALLET_JWK_PATH", None)
            config.reset_config_cache()
            artifact = build_artifact("test", {"a": 1})
            result = upload_artifact(artifact, {"a": 1})
        self.assertEqual(result["status"], "stub_not_uploaded")

    def test_upload_with_wallet_honest_not_implemented(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            jwk = Path(tmp) / "wallet.json"
            jwk.write_text(json.dumps({"kty": "RSA", "n": "x"}), encoding="utf-8")
            with patch.dict(
                os.environ,
                {"LFFA_ARWEAVE_WALLET_JWK_PATH": str(jwk)},
                clear=False,
            ):
                config.reset_config_cache()
                artifact = build_artifact("test", {"b": 2})
                result = upload_artifact(artifact, {"b": 2})
        self.assertEqual(result["status"], "upload_not_implemented")
        self.assertNotIn("tx_id", result)


if __name__ == "__main__":
    unittest.main()
