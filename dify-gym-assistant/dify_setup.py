#!/usr/bin/env python3
"""Configure a running Dify stack for the Ironbark gym assistant, with no clicking.

Creates the admin account, installs the OpenAI model-provider plugin, stores the
OpenAI key, imports the app from app/ironbark-gym-assistant.yml, turns on Dify's
built-in Opik tracing for the app and mints a service API key for demo.py. Every step checks before it creates, so re-running
is safe. Standard library only.
"""

import base64
import http.cookiejar
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
STATE = HERE / ".dify-state.json"
DSL = HERE / "app" / "ironbark-gym-assistant.yml"
APP_NAME = "Ironbark Gym Assistant"
OPENAI_PROVIDER = "langgenius/openai/openai"
OPENAI_PLUGIN = "langgenius/openai"
MARKETPLACE = "https://marketplace.dify.ai/api/v1/plugins/langgenius/openai"

ADMIN_EMAIL = os.environ.get("DIFY_ADMIN_EMAIL", "desk@ironbark.example")
ADMIN_PASSWORD = os.environ.get("DIFY_ADMIN_PASSWORD", "IronbarkDesk2026")


def step(msg: str) -> None:
    print(f"  * {msg}", flush=True)


class Console:
    """Dify's console API, authenticated the way the web UI is: session cookies
    plus an X-CSRF-Token header echoing the csrf_token cookie on every call."""

    def __init__(self, base_url: str):
        self.api = base_url.rstrip("/") + "/console/api"
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def call(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        req = urllib.request.Request(
            self.api + path,
            data=json.dumps(body).encode() if body is not None else None,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        csrf = next((c.value for c in self.jar if c.name == "csrf_token"), None)
        if csrf:
            req.add_header("X-CSRF-Token", csrf)
        try:
            with self.opener.open(req, timeout=120) as resp:
                return resp.status, json.loads(resp.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            raw = e.read().decode() or "{}"
            try:
                return e.code, json.loads(raw)
            except json.JSONDecodeError:
                return e.code, {"raw": raw}

    def must(self, method: str, path: str, body: dict | None = None) -> dict:
        status, payload = self.call(method, path, body)
        if status not in (200, 201):
            sys.exit(f"ERROR: {method} {path} -> {status}: {payload}")
        return payload


def wait_until_up(console: Console, timeout_s: int = 900) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            status, body = console.call("GET", "/setup")
            if status == 200 and body.get("step") in ("not_started", "finished"):
                step("Dify console is answering")
                return
        except OSError:
            pass
        time.sleep(5)
    sys.exit("ERROR: Dify did not come up in time; check `docker compose ps` in dify-docker/.")


def admin_and_login(console: Console) -> None:
    _, body = console.call("GET", "/setup")
    if body.get("step") != "finished":
        console.must("POST", "/setup", {"email": ADMIN_EMAIL, "name": "Ironbark Desk", "password": ADMIN_PASSWORD})
        step(f"Created admin {ADMIN_EMAIL}")
    # The console expects the password base64-encoded, as the web UI sends it.
    body = console.must("POST", "/login", {
        "email": ADMIN_EMAIL,
        "password": base64.b64encode(ADMIN_PASSWORD.encode()).decode(),
        "remember_me": True,
    })
    if body.get("result") != "success":
        sys.exit(f"ERROR: login failed: {body}")
    step("Logged in")


def openai_plugin(console: Console) -> None:
    body = console.must("GET", "/workspaces/current/plugin/list")
    if any(p.get("plugin_id") == OPENAI_PLUGIN for p in body.get("plugins", [])):
        step("OpenAI plugin already installed")
        return
    # The marketplace answers 403 to urllib's default User-Agent.
    req = urllib.request.Request(MARKETPLACE, headers={"User-Agent": "ironbark-gym-setup"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        identifier = json.loads(resp.read().decode())["data"]["plugin"]["latest_package_identifier"]
    task = console.must("POST", "/workspaces/current/plugin/install/marketplace",
                        {"plugin_unique_identifiers": [identifier]})
    task_id = task.get("task_id")
    deadline = time.time() + 300
    while task_id and not task.get("all_installed") and time.time() < deadline:
        time.sleep(3)
        status = (console.must("GET", f"/workspaces/current/plugin/tasks/{task_id}").get("task") or {}).get("status")
        if status == "success":
            break
        if status == "failed":
            sys.exit("ERROR: OpenAI plugin install failed")
    step(f"Installed {identifier.split('@')[0]}")


def openai_credential(console: Console, key: str) -> None:
    path = f"/workspaces/current/model-providers/{OPENAI_PROVIDER}/credentials"
    status, body = console.call("GET", path)
    if status == 200 and body.get("credentials"):
        step("OpenAI credential already stored")
        return
    console.must("POST", path, {"credentials": {"openai_api_key": key}, "name": "default"})
    step("Stored the OpenAI key as the provider credential")


def import_app(console: Console) -> str:
    for app in console.must("GET", "/apps?page=1&limit=100").get("data", []):
        if app.get("name") == APP_NAME:
            step(f"App already imported ({app['id']})")
            return app["id"]
    body = console.must("POST", "/apps/imports", {"mode": "yaml-content", "yaml_content": DSL.read_text()})
    step(f"Imported {APP_NAME} from the DSL ({body['app_id']})")
    return body["app_id"]


def opik_tracing(console: Console, app_id: str) -> None:
    # Dify's built-in Opik integration: the same four fields as the app's
    # Monitoring panel. Dify's API and worker containers send the traces, so a
    # local Opik on the host must be addressed as host.docker.internal.
    url = os.environ.get("OPIK_URL_OVERRIDE", "http://localhost:5173/api/")
    url = url.replace("//localhost", "//host.docker.internal").replace("//127.0.0.1", "//host.docker.internal")
    config = {
        "api_key": os.environ.get("OPIK_API_KEY", ""),  # empty for a local Opik
        "workspace": os.environ.get("OPIK_WORKSPACE", "default"),
        "project": "dify-gym-assistant",  # every trace lands in this Opik project
        "url": url,
    }
    status, body = console.call("GET", f"/apps/{app_id}/trace-config?tracing_provider=opik")
    exists = status == 200 and not body.get("has_not_configured")
    # Saving the config makes Dify call Opik once to validate it.
    console.must("PATCH" if exists else "POST", f"/apps/{app_id}/trace-config",
                 {"tracing_provider": "opik", "tracing_config": config})
    # Saving is not enough: tracing stays off until it is switched on.
    console.must("POST", f"/apps/{app_id}/trace", {"enabled": True, "tracing_provider": "opik"})
    step(f"Opik tracing on: project dify-gym-assistant at {url}")


def service_key(console: Console, app_id: str) -> str:
    if STATE.exists():
        state = json.loads(STATE.read_text())
        if state.get("app_id") == app_id:
            return state["service_key"]
    return console.must("POST", f"/apps/{app_id}/api-keys", {})["token"]


def main() -> None:
    openai_key = os.environ.get("OPENAI_API_KEY") or sys.exit("ERROR: OPENAI_API_KEY is not set")
    base_url = os.environ.get("DIFY_URL", "http://localhost:8090")
    console = Console(base_url)
    print(f"Configuring Dify at {base_url}")
    wait_until_up(console)
    admin_and_login(console)
    openai_plugin(console)
    openai_credential(console, openai_key)
    app_id = import_app(console)
    opik_tracing(console, app_id)
    key = service_key(console, app_id)
    STATE.write_text(json.dumps({"dify_url": base_url, "app_id": app_id, "service_key": key}, indent=2) + "\n")
    print(f"Done. App: {base_url}/app/{app_id}/configuration  (state in {STATE.name}, git-ignored)")


if __name__ == "__main__":
    main()
