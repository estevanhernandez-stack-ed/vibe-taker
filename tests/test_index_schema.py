"""
Index-schema conformance tests.

`index.schema.json` governs ~/.vibe-taker/library/index.json — the shelf
manifest read by `:list` (Phase 1.4) and `:plant` (Phase 1.2), validated on
every read; a corrupt/invalid index is a class-2 outcome. An empty library is a
*valid* index (`bundles: []`), not an error — list/SKILL.md is explicit.
"""
import copy

import pytest


# --- Schema is itself well-formed -----------------------------------------

def test_index_schema_is_valid_draft202012(index_schema):
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.Draft202012Validator.check_schema(index_schema)


def test_index_schema_declares_2020_12(index_schema):
    assert index_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_index_schema_forbids_additional_properties(index_schema):
    assert index_schema["additionalProperties"] is False


# --- Positive -------------------------------------------------------------

def test_valid_index_passes(make_validator, index_schema, valid_index):
    make_validator(index_schema).validate(valid_index)


def test_multiversion_index_passes(make_validator, index_schema, multiversion_index):
    make_validator(index_schema).validate(multiversion_index)


def test_empty_library_index_is_valid(make_validator, index_schema):
    """An empty shelf is a clean state, not a failure (list/SKILL.md Phase 1)."""
    assert make_validator(index_schema).is_valid({"schema_version": "1.0", "bundles": []})


def test_bundle_framework_null_is_valid(make_validator, index_schema, valid_index):
    valid_index["bundles"][0]["framework"] = None
    assert make_validator(index_schema).is_valid(valid_index)


def test_bundle_optional_fields_omitted(make_validator, index_schema, valid_index):
    for opt in ("tags", "summary", "framework"):
        valid_index["bundles"][0].pop(opt, None)
    assert make_validator(index_schema).is_valid(valid_index)


# --- Negative -------------------------------------------------------------

def _b0_drop(field):
    return lambda x: x["bundles"][0].pop(field, None)


def _b0_set(field, value):
    return lambda x: x["bundles"][0].__setitem__(field, value)


def _v0_drop(field):
    return lambda x: x["bundles"][0]["versions"][0].pop(field, None)


def _v0_set(field, value):
    return lambda x: x["bundles"][0]["versions"][0].__setitem__(field, value)


INDEX_NEGATIVES = {
    "missing bundles": lambda x: x.pop("bundles"),
    "missing schema_version": lambda x: x.pop("schema_version"),
    "wrong schema_version const": lambda x: x.__setitem__("schema_version", "1.1"),
    "unknown top-level property": lambda x: x.__setitem__("extra", 1),
    "bundle missing versions": _b0_drop("versions"),
    "bundle missing latest_version": _b0_drop("latest_version"),
    "bundle missing language": _b0_drop("language"),
    "bundle missing name": _b0_drop("name"),
    "bundle unknown property": _b0_set("color", "red"),
    "bundle name uppercase": _b0_set("name", "Bad-Name"),
    "latest_version bad pattern": _b0_set("latest_version", "2"),
    "versions empty (minItems 1)": _b0_set("versions", []),
    "versions not array": _b0_set("versions", {"version": "v1"}),
    "version entry missing source_repo": _v0_drop("source_repo"),
    "version entry missing source_path": _v0_drop("source_path"),
    "version entry missing captured_at": _v0_drop("captured_at"),
    "version entry missing version": _v0_drop("version"),
    "version entry bad version pattern": _v0_set("version", "ver1"),
    "version entry unknown property": _v0_set("note", "x"),
}


@pytest.mark.parametrize("label,mutate", list(INDEX_NEGATIVES.items()), ids=list(INDEX_NEGATIVES))
def test_invalid_index_rejected(make_validator, index_schema, valid_index, label, mutate):
    broken = copy.deepcopy(valid_index)
    mutate(broken)
    assert not make_validator(index_schema).is_valid(broken), f"schema wrongly accepted: {label}"
