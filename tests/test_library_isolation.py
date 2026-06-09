"""
Library-path isolation guards.

The real shelf lives at ~/.vibe-taker/library/. The suite must NEVER read or
write it. Every library operation under test routes through the `temp_library`
fixture (pytest tmp_path). These tests prove the isolation holds and exercise a
full index read/write/validate cycle entirely inside the temp shelf — the
`:capture` (index update) and `:list`/`:plant` (index read) data path, sandboxed.
"""
from pathlib import Path

REAL_SHELF = Path.home() / ".vibe-taker"


def test_temp_library_is_under_tmp_not_home(temp_library):
    resolved = temp_library.resolve()
    # The fixture's shelf is not the real one...
    assert REAL_SHELF.resolve() not in resolved.parents
    assert resolved != (REAL_SHELF / "library").resolve()
    # ...and it does live somewhere under a temp root.
    assert any("tmp" in part.lower() or "temp" in part.lower() or "pytest" in part.lower()
               for part in resolved.parts), f"temp_library not under a tmp root: {resolved}"


def test_temp_library_seeded_with_valid_empty_index(temp_library, make_validator, index_schema, jsonio):
    index = jsonio.read(temp_library / "index.json")
    assert index == {"schema_version": "1.0", "bundles": []}
    make_validator(index_schema).validate(index)


def test_index_write_read_cycle_in_temp_shelf(temp_library, make_validator, index_schema, valid_index, jsonio):
    """Simulate `:capture`'s index update + `:list`'s index read, sandboxed."""
    index_path = temp_library / "index.json"
    jsonio.write(index_path, valid_index)
    reloaded = jsonio.read(index_path)
    assert reloaded == valid_index
    make_validator(index_schema).validate(reloaded)
    # The write stayed inside the temp shelf.
    assert index_path.resolve().is_relative_to(temp_library.resolve())


def test_bundle_dir_layout_in_temp_shelf(temp_library, valid_contract, jsonio):
    """A captured bundle's six-artifact directory lands under the temp shelf,
    never the real one (bundle-schema.md layout)."""
    bundle = temp_library / valid_contract["name"] / valid_contract["version"]
    jsonio.write(bundle / "contract.json", valid_contract)
    (bundle / "prompts").mkdir(parents=True, exist_ok=True)
    (bundle / "prompts" / "empty.txt").write_text(
        "(no prompts extracted from this feature)", encoding="utf-8", newline="\n"
    )
    assert (bundle / "contract.json").is_file()
    assert bundle.resolve().is_relative_to(temp_library.resolve())
    assert REAL_SHELF.resolve() not in bundle.resolve().parents


def test_suite_uses_no_path_under_real_shelf(temp_library):
    """Belt-and-suspenders: nothing the fixture produced resolves under ~/.vibe-taker."""
    assert REAL_SHELF.resolve() not in temp_library.resolve().parents
