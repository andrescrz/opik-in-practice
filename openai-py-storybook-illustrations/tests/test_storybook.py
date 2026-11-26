import base64
from types import SimpleNamespace

import pytest

from storybook import illustrate as illustrate_mod
from storybook.briefs import BRIEF_V1, BRIEF_V2, load_scenes, render
from storybook.library import brief_diff, ensure_brief_versions


def test_scenes_fill_every_placeholder_of_both_briefs():
    for scene in load_scenes():
        for brief in (BRIEF_V1, BRIEF_V2):
            text = render(brief, **scene)
            assert "{{" not in text
            assert scene["action"] in text


def test_render_fails_loudly_on_missing_variable():
    with pytest.raises(KeyError):
        render(BRIEF_V1, page=1)


def test_v2_only_adds_rules():
    assert BRIEF_V2.startswith(BRIEF_V1)
    assert "No text" in BRIEF_V2 and "No text" not in BRIEF_V1


class FakePrompt:
    def __init__(self, text, version):
        self.prompt, self.version = text, version


class FakeLibrary:
    """Mimics create_prompt: a new version only when text differs from the latest."""

    def __init__(self):
        self.versions: list[FakePrompt] = []

    def get_prompt(self, name, version=None, project_name=None):
        if not self.versions:
            return None
        if version is None:
            return self.versions[-1]
        return next(v for v in self.versions if v.version == version)

    def get_prompt_history(self, name, project_name=None):
        return list(self.versions)

    def create_prompt(self, name, prompt, **kwargs):
        if not self.versions or self.versions[-1].prompt != prompt:
            self.versions.append(FakePrompt(prompt, f"v{len(self.versions) + 1}"))


def test_prompt_creation_is_idempotent():
    lib = FakeLibrary()
    for _ in range(3):
        v1, v2 = ensure_brief_versions(lib, "demo")
    assert len(lib.versions) == 2
    assert (v1.version, v2.version) == ("v1", "v2")
    assert "+- No text, letters" in brief_diff(v1, v2)


def test_traced_functions_run_with_tracking_disabled(tmp_path):
    png = b"\x89PNG fake"
    image_api = SimpleNamespace(
        generate=lambda **kw: SimpleNamespace(
            data=[SimpleNamespace(b64_json=base64.b64encode(png).decode())],
            usage=SimpleNamespace(input_tokens=10, output_tokens=20, total_tokens=30),
        )
    )
    client = SimpleNamespace(images=image_api)
    brief = SimpleNamespace(version="v1", format=lambda **kw: render(BRIEF_V1, **kw))
    path = illustrate_mod.illustrate(client, brief, load_scenes()[0], tmp_path)
    assert path.read_bytes() == png
    assert path.name == "v1-lantern-hill.png"
