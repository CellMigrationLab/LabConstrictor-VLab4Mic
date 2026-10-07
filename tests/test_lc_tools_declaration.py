"""The tool declarations must stay valid, cheap to import, and in step with the installed VLab4Mic.

    pip install pytest labconstrictor-tools vlab4mic
    pytest tests
"""

import sys
from pathlib import Path

import pytest

pytest.importorskip("labconstrictor_tools")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def _tools():
    import importlib

    from labconstrictor_tools.introspection import describe_tools

    importlib.import_module("vlab4mic_lc_tools")  # the declarations register their tools when imported
    return {t["id"]: t for t in describe_tools("vlab4mic_lc_tools")["tools"]}


def _choices(tool, name):
    return next(p["choices"] for p in tool["inputs"] if p["name"] == name)


def test_declarations_are_valid_and_light():
    tools = _tools()
    assert set(tools) == {"simulate_sample", "compare_images"}
    assert {o["name"] for o in tools["simulate_sample"]["outputs"]} == {"simulated", "noiseless", "values"}
    assert [p["name"] for p in tools["compare_images"]["inputs"][:2]] == ["reference", "simulated"]
    assert "vlab4mic" not in sys.modules, "importing the declarations must not import VLab4Mic (several seconds)"


def test_defaults_work_without_any_input():
    inputs = {p["name"]: p for p in _tools()["simulate_sample"]["inputs"]}
    required = [name for name, p in inputs.items() if "default" not in p and not p.get("nullable")]
    assert required == [], "a run with all defaults must be possible: %s have no default" % required


def _config_names(kind):
    vlab4mic = pytest.importorskip("vlab4mic")
    folder = Path(vlab4mic.__file__).parent / "configs" / kind
    return {f.stem for f in folder.glob("*.yaml") if not f.stem.startswith("_")}


@pytest.mark.parametrize(
    "name, kind",
    [("structure", "structures"), ("probe", "probes"), ("modality", "modalities"), ("fluorophore", "fluorophores")],
)
def test_choices_match_the_configuration_files_of_vlab4mic(name, kind):
    assert set(_choices(_tools()["simulate_sample"], name)) == _config_names(kind)


def test_probe_rules_match_the_known_targets_of_the_probes():
    pytest.importorskip("vlab4mic")
    import yaml
    from vlab4mic_lc_tools import _labelling

    import vlab4mic

    folder = Path(vlab4mic.__file__).parent / "configs" / "probes"
    for name in _config_names("probes"):
        known = yaml.safe_load((folder / (name + ".yaml")).read_text())["known_targets"]
        if known == ["Generic"]:
            assert name not in _labelling._NEEDS_SEQUENCE and name not in _labelling._PROBE_FOR_STRUCTURE, name
        elif known == ["Mock"]:
            assert name in _labelling._NEEDS_SEQUENCE, name
        else:
            assert known == [_labelling._PROBE_FOR_STRUCTURE.get(name)], name


@pytest.mark.parametrize(
    "structure, probe, sequence, code",
    [
        ("1XI5", "Antibody", None, "probe_needs_target"),
        ("1XI5", "NPC_Nup96_Cterminal_direct", None, "probe_structure_mismatch"),
        ("1XI5", "NHS_ester", "ELAVGSL", "target_not_used"),
    ],
)
def test_labelling_mistakes_are_explained(structure, probe, sequence, code):
    from labconstrictor_tools import ToolError
    from vlab4mic_lc_tools._labelling import check_labelling

    with pytest.raises(ToolError) as caught:
        check_labelling(structure, probe, sequence)
    assert code in str(caught.value) or getattr(caught.value, "code", None) == code


@pytest.mark.parametrize(
    "structure, probe, sequence",
    [("1XI5", "NHS_ester", None), ("7R5K", "NPC_Nup96_Cterminal_direct", None), ("7R5K", "Antibody", "ELAVGSL")],
)
def test_valid_labellings_are_accepted(structure, probe, sequence):
    from vlab4mic_lc_tools._labelling import check_labelling

    check_labelling(structure, probe, sequence)
