"""Offline tests for dify_setup.py: no Dify, no Opik, no keys. Run: python3 -m unittest discover tests"""

import os
import pathlib
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import dify_setup  # noqa: E402

APP_ID = "app-123"


class FakeConsole:
    """Records console calls and answers GETs from a canned table."""

    def __init__(self, gets: dict | None = None):
        self.gets = gets or {}
        self.calls = []

    def call(self, method, path, body=None):
        self.calls.append((method, path, body))
        return self.gets.get(path, (200, {}))

    def must(self, method, path, body=None):
        return self.call(method, path, body)[1]

    def writes(self):
        return [(m, p, b) for m, p, b in self.calls if m != "GET"]


def run_opik_tracing(console, env):
    with mock.patch.dict(os.environ, env, clear=True), redirect_stdout(StringIO()):
        dify_setup.opik_tracing(console, APP_ID)
    return console.writes()


NOT_CONFIGURED = {f"/apps/{APP_ID}/trace-config?tracing_provider=opik": (200, {"has_not_configured": True})}


class OpikTracingTest(unittest.TestCase):
    def test_local_opik_is_addressed_from_inside_the_containers(self):
        for host in ("localhost", "127.0.0.1"):
            with self.subTest(host=host):
                writes = run_opik_tracing(FakeConsole(NOT_CONFIGURED), {"OPIK_URL_OVERRIDE": f"http://{host}:5173/api/"})
                self.assertEqual(writes[0][2]["tracing_config"]["url"], "http://host.docker.internal:5173/api/")

    def test_remote_opik_url_is_left_alone(self):
        url = "https://opik.example.org/api/"
        writes = run_opik_tracing(FakeConsole(NOT_CONFIGURED), {"OPIK_URL_OVERRIDE": url, "OPIK_API_KEY": "k"})
        config = writes[0][2]["tracing_config"]
        self.assertEqual(config["url"], url)
        self.assertEqual(config["api_key"], "k")

    def test_defaults_target_a_local_opik_and_this_examples_project(self):
        writes = run_opik_tracing(FakeConsole(NOT_CONFIGURED), {})
        self.assertEqual(writes[0][2], {
            "tracing_provider": "opik",
            "tracing_config": {
                "api_key": "",
                "workspace": "default",
                "project": "dify-gym-assistant",
                "url": "http://host.docker.internal:5173/api/",
            },
        })

    def test_first_run_creates_the_config_then_switches_tracing_on(self):
        writes = run_opik_tracing(FakeConsole(NOT_CONFIGURED), {})
        self.assertEqual([(m, p) for m, p, _ in writes], [
            ("POST", f"/apps/{APP_ID}/trace-config"),
            ("POST", f"/apps/{APP_ID}/trace"),
        ])
        self.assertEqual(writes[1][2], {"enabled": True, "tracing_provider": "opik"})

    def test_rerun_updates_the_existing_config(self):
        configured = {f"/apps/{APP_ID}/trace-config?tracing_provider=opik": (200, {"tracing_provider": "opik"})}
        writes = run_opik_tracing(FakeConsole(configured), {})
        self.assertEqual(writes[0][:2], ("PATCH", f"/apps/{APP_ID}/trace-config"))
        self.assertEqual(writes[1][:2], ("POST", f"/apps/{APP_ID}/trace"))


class ImportAppTest(unittest.TestCase):
    def test_existing_app_is_reused(self):
        console = FakeConsole({"/apps?page=1&limit=100": (200, {"data": [{"name": dify_setup.APP_NAME, "id": "existing"}]})})
        with redirect_stdout(StringIO()):
            self.assertEqual(dify_setup.import_app(console), "existing")
        self.assertEqual(console.writes(), [])

    def test_missing_app_is_imported_from_the_dsl(self):
        console = FakeConsole({"/apps/imports": (200, {"app_id": "new"})})
        with redirect_stdout(StringIO()):
            self.assertEqual(dify_setup.import_app(console), "new")
        method, path, body = console.writes()[0]
        self.assertEqual((method, path, body["mode"]), ("POST", "/apps/imports", "yaml-content"))
        self.assertIn(f"name: {dify_setup.APP_NAME}", body["yaml_content"])


if __name__ == "__main__":
    unittest.main()
