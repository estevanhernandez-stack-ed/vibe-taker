"""
Pytest configuration + shared fixtures for the vibe-taker test suite.

vibe-taker is a prose-driven (markdown-SKILL) plugin — it ships NO executable
layer (no scripts/, no Python/JS, no subprocess calls). See the suite-level
docstring in each test module. The only deterministic, machine-checkable,
load-bearing artifacts are:

  - plugins/vibe-taker/skills/guide/schemas/contract.schema.json
  - plugins/vibe-taker/skills/guide/schemas/index.schema.json
  - plugins/vibe-taker/skills/guide/templates/*.md.template

These tests lock those contract artifacts. Schema validation uses
`jsonschema.Draft202012Validator` — the exact validator the plugin documents in
skills/guide/references/bundle-schema.md. It is already installed in this repo's
environment; tests that need it skip gracefully (importorskip) if it is ever
absent, while the structural / encoding / isolation tests run on stdlib alone.

Every file write/read in the suite is UTF-8 explicit and isolated to pytest's
tmp_path — the real ~/.vibe-taker/ shelf is never touched.
"""
import copy
import json
from pathlib import Path

import pytest

# --- Paths -----------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = REPO_ROOT / "plugins" / "vibe-taker"
SCHEMAS_DIR = PLUGIN_ROOT / "skills" / "guide" / "schemas"
TEMPLATES_DIR = PLUGIN_ROOT / "skills" / "guide" / "templates"
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

CONTRACT_SCHEMA_PATH = SCHEMAS_DIR / "contract.schema.json"
INDEX_SCHEMA_PATH = SCHEMAS_DIR / "index.schema.json"


# --- UTF-8 JSON helpers (mirror the plugin's "pretty-printed, 2-space" shape) -

def write_json_utf8(path, obj):
    """Write JSON the way the plugin documents: 2-space indent, real UTF-8.

    ensure_ascii=False is deliberate — it forces non-ASCII (em-dashes, smart
    quotes, CJK) onto disk as real UTF-8 bytes rather than \\uXXXX escapes, so
    the round-trip tests actually exercise the Windows mojibake surface.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
    return path


def read_json_utf8(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def read_text_utf8(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


# --- Fixtures --------------------------------------------------------------

@pytest.fixture
def jsonio():
    """Expose the UTF-8 read/write helpers to tests as a single handle."""
    class _IO:
        write = staticmethod(write_json_utf8)
        read = staticmethod(read_json_utf8)
        read_text = staticmethod(read_text_utf8)
    return _IO


@pytest.fixture(scope="session")
def contract_schema():
    return read_json_utf8(CONTRACT_SCHEMA_PATH)


@pytest.fixture(scope="session")
def index_schema():
    return read_json_utf8(INDEX_SCHEMA_PATH)


@pytest.fixture
def make_validator():
    """Return a factory producing a Draft 2020-12 validator for a schema.

    Uses the same validator the plugin's bundle-schema.md prescribes. Skips the
    requesting test cleanly if jsonschema is unavailable.
    """
    jsonschema = pytest.importorskip("jsonschema")

    def _factory(schema):
        return jsonschema.Draft202012Validator(schema)

    return _factory


@pytest.fixture
def valid_contract():
    """A fresh deep copy of the full valid contract — safe to mutate."""
    return copy.deepcopy(read_json_utf8(FIXTURES_DIR / "contract_valid_full.json"))


@pytest.fixture
def minimal_contract():
    """Only-required-fields contract (framework null, empty arrays)."""
    return copy.deepcopy(read_json_utf8(FIXTURES_DIR / "contract_valid_minimal.json"))


@pytest.fixture
def emdash_contract():
    """Contract loaded with heavy non-ASCII content (encoding stress)."""
    return copy.deepcopy(read_json_utf8(FIXTURES_DIR / "contract_emdash.json"))


@pytest.fixture
def valid_index():
    """A fresh deep copy of the valid index — safe to mutate."""
    return copy.deepcopy(read_json_utf8(FIXTURES_DIR / "index_valid.json"))


@pytest.fixture
def multiversion_index():
    """A multi-bundle index (mixed languages, a null framework, 2 versions)."""
    return copy.deepcopy(read_json_utf8(FIXTURES_DIR / "index_multiversion.json"))


@pytest.fixture
def temp_library(tmp_path):
    """An isolated fake ~/.vibe-taker/library/ under pytest's tmp_path.

    Never the real shelf. Seeds an empty-but-valid index.json and returns the
    library directory Path.
    """
    lib = tmp_path / ".vibe-taker" / "library"
    lib.mkdir(parents=True, exist_ok=True)
    write_json_utf8(lib / "index.json", {"schema_version": "1.0", "bundles": []})
    return lib
