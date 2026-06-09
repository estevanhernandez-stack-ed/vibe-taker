"""
Bundle serialization round-trips + Windows UTF-8 encoding guards.

vibe-taker has no serializer *code* — the SKILL prose instructs the agent to
write contract.json / index.json in a documented shape. The faithful analog of
"round-trip every serializer (capture -> library -> list -> plant read)" is:
the documented shapes survive a write -> read cycle byte-faithfully, still
validate, and preserve the fields that `:list` / `:plant` mirror between
contract.json and index.json.

The encoding guards are the real Windows surface for a prose plugin: summaries
and descriptions carry em-dashes, smart quotes, and non-Latin text. If a write
or read ever drops `encoding="utf-8"`, those corrupt (cp1252 mojibake). These
tests pin real UTF-8 bytes on disk.
"""
import json
from pathlib import Path

import pytest

# Mirror fields: contract.json values that index.json copies (bundle-schema.md
# "Mirrored in index.json"). The capture -> list/plant chain relies on these
# staying identical across the two artifacts.
MIRROR_FIELDS = ("summary", "tags", "language", "framework")

NON_ASCII_SAMPLES = [
    "em-dash — here",
    "smart quotes “quoted” and ’apostrophe’",
    "arrow flow A → B → C",
    "accented café façade señal",
    "cjk 中文测试 テスト",
    "mixed — “café” → 测试",
]


# --- contract round-trip ---------------------------------------------------

def test_contract_roundtrip_preserves_content(jsonio, make_validator, contract_schema, valid_contract, tmp_path):
    path = jsonio.write(tmp_path / "contract.json", valid_contract)
    reloaded = jsonio.read(path)
    assert reloaded == valid_contract
    make_validator(contract_schema).validate(reloaded)


def test_minimal_contract_roundtrip(jsonio, make_validator, contract_schema, minimal_contract, tmp_path):
    path = jsonio.write(tmp_path / "contract.json", minimal_contract)
    reloaded = jsonio.read(path)
    assert reloaded == minimal_contract
    make_validator(contract_schema).validate(reloaded)


def test_emdash_contract_roundtrip_preserves_unicode(jsonio, make_validator, contract_schema, emdash_contract, tmp_path):
    path = jsonio.write(tmp_path / "contract.json", emdash_contract)
    reloaded = jsonio.read(path)
    assert reloaded == emdash_contract
    # The specific non-ASCII codepoints survived as real characters.
    assert "—" in reloaded["summary"]
    assert "→" in reloaded["summary"]
    assert "中文测试" in reloaded["summary"]
    assert "señal" in reloaded["tags"]
    make_validator(contract_schema).validate(reloaded)


# --- index round-trip ------------------------------------------------------

def test_index_roundtrip_preserves_content(jsonio, make_validator, index_schema, valid_index, tmp_path):
    path = jsonio.write(tmp_path / "index.json", valid_index)
    reloaded = jsonio.read(path)
    assert reloaded == valid_index
    make_validator(index_schema).validate(reloaded)


def test_multiversion_index_roundtrip(jsonio, make_validator, index_schema, multiversion_index, tmp_path):
    path = jsonio.write(tmp_path / "index.json", multiversion_index)
    reloaded = jsonio.read(path)
    assert reloaded == multiversion_index
    make_validator(index_schema).validate(reloaded)


# --- encoding: real UTF-8 bytes on disk (the mojibake guard) --------------

def test_emdash_written_as_real_utf8_bytes(jsonio, emdash_contract, tmp_path):
    """Em-dash must land on disk as UTF-8 (0xE2 0x80 0x94), not a \\u2014 escape
    and not a cp1252 single byte. This is the exact failure the family's
    recurring mojibake bug produces when encoding is left to the platform default.
    """
    path = jsonio.write(tmp_path / "contract.json", emdash_contract)
    raw = Path(path).read_bytes()
    assert b"\xe2\x80\x94" in raw, "em-dash not stored as UTF-8 bytes"
    assert b"\\u2014" not in raw, "em-dash was ASCII-escaped (ensure_ascii leaked)"
    # CJK present as UTF-8 too.
    assert "中文测试".encode("utf-8") in raw


def test_roundtrip_rejects_cp1252_misread(jsonio, emdash_contract, tmp_path):
    """Reading a UTF-8 file as cp1252 must NOT silently reproduce the原 content —
    proves the corruption is real and that reading with encoding='utf-8'
    (as the helper does) is load-bearing, not incidental.
    """
    path = jsonio.write(tmp_path / "contract.json", emdash_contract)
    raw = Path(path).read_bytes()
    mis = raw.decode("cp1252", errors="replace")
    correct = Path(path).read_text(encoding="utf-8")
    assert mis != correct
    assert "—" in correct and "—" not in mis


@pytest.mark.parametrize("sample", NON_ASCII_SAMPLES, ids=[s[:12] for s in NON_ASCII_SAMPLES])
def test_summary_non_ascii_roundtrips(jsonio, make_validator, contract_schema, valid_contract, tmp_path, sample):
    valid_contract["summary"] = sample
    path = jsonio.write(tmp_path / "contract.json", valid_contract)
    reloaded = jsonio.read(path)
    assert reloaded["summary"] == sample
    make_validator(contract_schema).validate(reloaded)


# --- shape chain: capture -> library -> list/plant read -------------------

def test_contract_mirror_fields_carry_into_index(jsonio, make_validator, contract_schema, index_schema, valid_contract, tmp_path):
    """Build an index entry from a contract the way `:capture` Phase 8.5 does,
    then assert the mirrored fields are identical across both artifacts and both
    validate. This is the round-trip `:list`/`:plant` rely on: the index is the
    discovery surface, the contract is the source of truth, and the mirror must hold.
    """
    contract_path = jsonio.write(tmp_path / "bundle" / "contract.json", valid_contract)
    contract = jsonio.read(contract_path)

    entry = {
        "name": contract["name"],
        "latest_version": contract["version"],
        "versions": [{
            "version": contract["version"],
            "captured_at": contract["captured_at"],
            "source_repo": contract["source_repo"],
            "source_path": contract["source_path"],
        }],
        "tags": contract.get("tags", []),
        "summary": contract.get("summary", ""),
        "language": contract["language"],
        "framework": contract["framework"],
    }
    index = {"schema_version": "1.0", "bundles": [entry]}
    index_path = jsonio.write(tmp_path / "library" / "index.json", index)
    reloaded_index = jsonio.read(index_path)

    make_validator(contract_schema).validate(contract)
    make_validator(index_schema).validate(reloaded_index)

    listed = reloaded_index["bundles"][0]
    for field in MIRROR_FIELDS:
        assert listed[field] == contract[field], (
            f"mirror field '{field}' drifted between contract and index"
        )
    # latest_version actually resolves to a real version entry (plant Phase 1.4).
    assert listed["latest_version"] in {v["version"] for v in listed["versions"]}


def test_pretty_printed_two_space_indent(jsonio, valid_index, tmp_path):
    """bundle-schema.md pins index.json to 2-space indent. A future reader/diff
    tool depends on it; lock the convention the helper writes."""
    path = jsonio.write(tmp_path / "index.json", valid_index)
    text = jsonio.read_text(path)
    lines = text.splitlines()
    # Top-level keys sit at exactly 2 spaces under the opening brace.
    assert any(line.startswith('  "bundles"') for line in lines)
    assert not any(line.startswith("\t") for line in lines), "tabs leaked into JSON output"
