"""Tests for Nosana overflow client and stub fallback."""

from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from lffa import config
from lffa import nosana_overflow


class NosanaOverflowTests(unittest.TestCase):
    def test_no_api_key_uses_stub(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("NOSANA_API_KEY", None)
            os.environ.pop("LFFA_NOSANA_API_KEY", None)
            config.reset_config_cache()
            req = nosana_overflow.build_overflow_job("hello")
            with patch.object(nosana_overflow, "_emit_notice") as notice_mock:
                result = nosana_overflow.submit_overflow_job(req)
        self.assertEqual(result.backend, "stub")
        self.assertIsNotNone(result.notice)
        notice_mock.assert_called_once()

    def test_api_key_balance_ok_prepared_work(self) -> None:
        payload = json.dumps({"balance": 42}).encode()

        def fake_urlopen(req, timeout=0):  # noqa: ARG001
            from unittest.mock import MagicMock

            resp = MagicMock()
            resp.status = 200
            resp.read.return_value = payload
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        env = {"NOSANA_API_KEY": "nos_test_key"}
        with patch.dict(os.environ, env, clear=False):
            config.reset_config_cache()
            req = nosana_overflow.build_overflow_job("long prompt " * 10)
            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                with patch.object(nosana_overflow, "_emit_notice"):
                    result = nosana_overflow.submit_overflow_job(req)
        self.assertEqual(result.backend, "nosana")
        self.assertEqual(result.payload.get("status"), "overflow_work_prepared")

    def test_api_key_job_post_success(self) -> None:
        payload = json.dumps({"job": "job-address-abc"}).encode()

        def fake_urlopen(req, timeout=0):  # noqa: ARG001
            from unittest.mock import MagicMock

            resp = MagicMock()
            resp.status = 200
            resp.read.return_value = payload
            resp.__enter__ = lambda s: s
            resp.__exit__ = MagicMock(return_value=False)
            return resp

        env = {
            "NOSANA_API_KEY": "nos_test_key",
            "NOSANA_IPFS_HASH": "QmExampleHash",
            "NOSANA_MARKET": "market-pubkey",
        }
        with patch.dict(os.environ, env, clear=False):
            config.reset_config_cache()
            req = nosana_overflow.build_overflow_job("overflow")
            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                result = nosana_overflow.submit_overflow_job(req)
        self.assertEqual(result.backend, "nosana")
        self.assertEqual(result.payload.get("status"), "job_posted")
        self.assertEqual(result.payload.get("job"), "job-address-abc")

    def test_api_key_http_failure_falls_back_stub(self) -> None:
        import urllib.error

        def fake_urlopen(req, timeout=0):  # noqa: ARG001
            raise urllib.error.URLError("network down")

        with patch.dict(os.environ, {"LFFA_NOSANA_API_KEY": "nos_x"}, clear=False):
            config.reset_config_cache()
            req = nosana_overflow.build_overflow_job("x")
            with patch("urllib.request.urlopen", side_effect=fake_urlopen):
                with patch.object(nosana_overflow, "_emit_notice"):
                    result = nosana_overflow.submit_overflow_job(req)
        self.assertEqual(result.backend, "stub")

    def test_credentials_present_with_lffa_key(self) -> None:
        with patch.dict(os.environ, {"LFFA_NOSANA_API_KEY": "nos_y"}, clear=False):
            config.reset_config_cache()
            self.assertTrue(nosana_overflow.nosana_credentials_present())

    def test_decide_route_overflow_when_large(self) -> None:
        big = "a" * 5000
        decision = nosana_overflow.decide_route(big, local_max_chars=4000)
        self.assertEqual(decision.route, nosana_overflow.InferenceRoute.NOSANA_OVERFLOW)


if __name__ == "__main__":
    unittest.main()
