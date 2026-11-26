import difflib

import opik

from storybook.briefs import BRIEF_NAME, BRIEF_V1, BRIEF_V2, V2_CHANGE


def ensure_brief_versions(client: opik.Opik, project_name: str) -> tuple[opik.Prompt, opik.Prompt]:
    """Make sure the prompt library holds exactly v1 and v2, however often this runs.

    create_prompt adds a new version whenever the text differs from the *latest*
    version, so blindly re-creating v1 after v2 exists would mint a v3. We only
    create what is missing, then read both versions back from the library.
    """
    # Prompts are project-scoped: pass project_name to create and fetch so the
    # prompt shows up in this example's project rather than "Default Project".
    if client.get_prompt(BRIEF_NAME, project_name=project_name) is None:
        client.create_prompt(
            name=BRIEF_NAME,
            prompt=BRIEF_V1,
            change_description="Initial brief: page, setting, action, mood",
            tags=["image-generation", "storybook"],
            project_name=project_name,
        )
    if len(client.get_prompt_history(BRIEF_NAME, project_name=project_name)) < 2:
        client.create_prompt(
            name=BRIEF_NAME,
            prompt=BRIEF_V2,
            change_description=V2_CHANGE,
            tags=["image-generation", "storybook"],
            project_name=project_name,
        )
    v1 = client.get_prompt(BRIEF_NAME, version="v1", project_name=project_name)
    v2 = client.get_prompt(BRIEF_NAME, project_name=project_name)
    if v1 is None or v2 is None:
        raise RuntimeError(f"prompt {BRIEF_NAME!r} is missing a version in the library")
    return v1, v2


def brief_diff(v1: opik.Prompt, v2: opik.Prompt) -> str:
    return "\n".join(
        difflib.unified_diff(
            v1.prompt.splitlines(), v2.prompt.splitlines(), "v1", "v2", lineterm="", n=0
        )
    )
