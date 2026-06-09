"""
Contract-schema conformance tests.

`contract.schema.json` is the load-bearing artifact of vibe-taker: every
`:capture` writes against it and every `:plant` validates against it before
touching the target repo (capture/SKILL.md Phase 7.3, plant/SKILL.md Phase 1.6,
error-contract.md class-2). If the schema stops constraining what the SKILL
prose assumes it constrains, every command silently drifts.

These tests prove the schema (a) is itself a valid Draft 2020-12 schema,
(b) accepts the documented bundle shapes, and (c) actually rejects the
malformations the prose layer would otherwise let through.
"""
import copy

import pytest


# --- Schema is itself well-formed -----------------------------------------

def test_contract_schema_is_valid_draft202012(contract_schema):
    jsonschema = pytest.importorskip("jsonschema")
    # Raises SchemaError if the schema document itself is malformed.
    jsonschema.Draft202012Validator.check_schema(contract_schema)


def test_contract_schema_declares_2020_12(contract_schema):
    assert contract_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"


def test_contract_schema_forbids_additional_properties(contract_schema):
    assert contract_schema["additionalProperties"] is False


# --- Positive: documented shapes validate ---------------------------------

def test_valid_full_contract_passes(make_validator, contract_schema, valid_contract):
    make_validator(contract_schema).validate(valid_contract)


def test_valid_minimal_contract_passes(make_validator, contract_schema, minimal_contract):
    make_validator(contract_schema).validate(minimal_contract)


def test_emdash_contract_passes(make_validator, contract_schema, emdash_contract):
    make_validator(contract_schema).validate(emdash_contract)


def test_framework_null_is_valid(make_validator, contract_schema, valid_contract):
    valid_contract["framework"] = None
    assert make_validator(contract_schema).is_valid(valid_contract)


def test_optional_fields_may_be_omitted(make_validator, contract_schema, valid_contract):
    for opt in ("tags", "summary", "notes_completeness"):
        valid_contract.pop(opt, None)
    assert make_validator(contract_schema).is_valid(valid_contract)


@pytest.mark.parametrize(
    "io_type",
    ["path", "string", "int", "float", "bool", "stdin", "flag", "other",
     "enum:a|b|c", "enum:fast|accurate"],
)
def test_valid_input_type_variants(make_validator, contract_schema, valid_contract, io_type):
    valid_contract["inputs"] = [{"name": "x", "type": io_type}]
    assert make_validator(contract_schema).is_valid(valid_contract)


@pytest.mark.parametrize("kind", ["cli", "library", "skill", "script", "service", "bot", "other"])
def test_valid_interface_kinds(make_validator, contract_schema, valid_contract, kind):
    valid_contract["interface_kind"] = kind
    assert make_validator(contract_schema).is_valid(valid_contract)


# --- Negative: malformations are rejected ---------------------------------

def _drop(field):
    def mut(c):
        c.pop(field, None)
    return mut


def _set(path, value):
    def mut(c):
        node = c
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
    return mut


def _add_unknown(value="boom"):
    def mut(c):
        c["definitely_not_in_schema"] = value
    return mut


CONTRACT_NEGATIVES = {
    "missing required name": _drop("name"),
    "missing required schema_version": _drop("schema_version"),
    "missing required captured_at": _drop("captured_at"),
    "missing required entry_points": _drop("entry_points"),
    "unknown top-level property": _add_unknown(),
    "wrong schema_version const": _set(["schema_version"], "2.0"),
    "slug with uppercase": _set(["name"], "Bad_Name"),
    "slug with leading dash": _set(["name"], "-bad"),
    "slug with space": _set(["name"], "bad name"),
    "version without v prefix": _set(["version"], "1"),
    "version v-only no digit": _set(["version"], "v"),
    "interface_kind not in enum": _set(["interface_kind"], "webapp"),
    "language wrong type": _set(["language"], 7),
    "framework wrong type": _set(["framework"], 7),
    "dependencies item not string": _set(["dependencies"], ["ok", 5]),
    "input type not allowed": _set(["inputs", 0, "type"], "date"),
    "input missing name": (lambda c: c["inputs"][0].pop("name")),
    "input unknown property": _set(["inputs", 0, "color"], "red"),
    "output type not allowed": _set(["outputs", 0, "type"], "timestamp"),
    "env_var name lowercase": _set(["env_vars", 0, "name"], "openai_key"),
    "env_var missing load_bearing": (lambda c: c["env_vars"][0].pop("load_bearing")),
    "env_var unknown property": _set(["env_vars", 0, "secret"], True),
    "notes_completeness missing field": (lambda c: c["notes_completeness"].pop("interview_fired")),
    "notes_completeness unknown property": _set(["notes_completeness", "extra"], 1),
    "notes_completeness negative count": _set(["notes_completeness", "substantive_count"], -1),
    "inputs not an array": _set(["inputs"], {"name": "x"}),
}


@pytest.mark.parametrize("label,mutate", list(CONTRACT_NEGATIVES.items()), ids=list(CONTRACT_NEGATIVES))
def test_invalid_contract_rejected(make_validator, contract_schema, valid_contract, label, mutate):
    broken = copy.deepcopy(valid_contract)
    mutate(broken)
    validator = make_validator(contract_schema)
    assert not validator.is_valid(broken), f"schema wrongly accepted: {label}"
