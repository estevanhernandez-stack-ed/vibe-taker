"""
Bundle template tests.

`:capture` Phase 7.2 renders three markdown templates by substituting
`{{placeholder}}` tokens. If a template grows a placeholder the capture SKILL
does not know how to fill, the bundle ships with a literal `{{foo}}` in it. These
tests lock each template's placeholder set and prove a full substitution leaves
no residual token, plus a UTF-8 render round-trip.

The expected sets below are the contract between the templates and capture
Phase 7.2 — editing a template should fail these until the SKILL prose is
updated to match (and vice versa).
"""
import re
from pathlib import Path

import pytest

TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent
    / "plugins" / "vibe-taker" / "skills" / "guide" / "templates"
)

PLACEHOLDER_RE = re.compile(r"\{\{([a-z0-9_]+)\}\}")

EXPECTED_PLACEHOLDERS = {
    "README.md.template": {
        "name", "summary", "what_it_is", "when_to_reach",
        "version", "captured_at", "source_repo", "source_path", "schema_version",
    },
    "architecture.md.template": {
        "name", "summary_paragraph", "components_block",
        "data_flow_block", "key_files_block", "captured_at",
    },
    "notes.md.template": {
        "name", "why_block", "gotchas_block", "tradeoffs_block", "captured_at",
    },
}

# Every placeholder the capture SKILL (Phase 7.2 + the contract.json fields it
# carries) is documented to fill. The union of all template placeholders must be
# a subset of this — a template may not introduce an unfillable token.
KNOWN_FILLABLE = set().union(*EXPECTED_PLACEHOLDERS.values())


def _read_template(name):
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")


def _placeholders(text):
    return set(PLACEHOLDER_RE.findall(text))


@pytest.mark.parametrize("name", list(EXPECTED_PLACEHOLDERS))
def test_template_file_exists(name):
    assert (TEMPLATES_DIR / name).is_file()


@pytest.mark.parametrize("name,expected", list(EXPECTED_PLACEHOLDERS.items()), ids=list(EXPECTED_PLACEHOLDERS))
def test_template_placeholder_set_is_locked(name, expected):
    found = _placeholders(_read_template(name))
    assert found == expected, (
        f"{name} placeholder drift: "
        f"unexpected={found - expected}, missing={expected - found}"
    )


@pytest.mark.parametrize("name", list(EXPECTED_PLACEHOLDERS))
def test_no_unfillable_placeholder(name):
    found = _placeholders(_read_template(name))
    unfillable = found - KNOWN_FILLABLE
    assert not unfillable, f"{name} references placeholders capture cannot fill: {unfillable}"


@pytest.mark.parametrize("name", list(EXPECTED_PLACEHOLDERS))
def test_full_substitution_leaves_no_residual(name):
    text = _read_template(name)
    rendered = text
    for token in _placeholders(text):
        rendered = rendered.replace("{{" + token + "}}", f"value-for-{token}")
    assert "{{" not in rendered and "}}" not in rendered, f"{name} left a residual token after render"


def test_rendered_template_roundtrips_utf8(tmp_path):
    """Render the README template with non-ASCII fills and confirm it survives a
    UTF-8 write/read — bundle README summaries routinely carry em-dashes."""
    text = _read_template("README.md.template")
    fills = {
        "name": "relay-bot",
        "summary": "Relay Slack events → a webhook — “fire-and-forget”.",
        "what_it_is": "A façade over the message bus.",
        "when_to_reach": "When you need señal routing.",
        "version": "v1",
        "captured_at": "2026-04-15T12:00:00Z",
        "source_repo": "https://github.com/626labs/relay",
        "source_path": "services/relay/",
        "schema_version": "1.0",
    }
    rendered = text
    for token, value in fills.items():
        rendered = rendered.replace("{{" + token + "}}", value)

    out = tmp_path / "README.md"
    out.write_text(rendered, encoding="utf-8", newline="\n")
    back = out.read_text(encoding="utf-8")

    assert back == rendered
    assert "→" in back and "—" in back and "façade" in back
    # The literal plant command renders intact.
    assert "/vibe-taker:plant relay-bot" in back
    assert "{{" not in back
