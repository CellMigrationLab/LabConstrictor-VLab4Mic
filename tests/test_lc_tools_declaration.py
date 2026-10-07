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


def test_choices_match_the_notebook_and_the_configuration_files_of_vlab4mic():
    tool = _tools()["simulate_sample"]
    # the notebook offers four structures and the five modalities of the configuration folder (minus the "Reference" one)
    assert set(_choices(tool, "structure")) == {"1XI5", "7R5K", "3J3Y", "8GMO"} <= _config_names("structures")
    assert set(_choices(tool, "modality")) == _config_names("modalities") - {"Reference"}
    assert set(_choices(tool, "probe")) == _config_names("probes")
    assert set(_choices(tool, "fluorophore")) == _config_names("fluorophores")


def test_probe_rules_match_the_known_targets_of_the_probes():
    pytest.importorskip("vlab4mic")
    import yaml
    from vlab4mic_lc_tools import _labelling

    import vlab4mic

    folder = Path(vlab4mic.__file__).parent / "configs" / "probes"
    for name in _config_names("probes"):
        known = yaml.safe_load((folder / (name + ".yaml")).read_text())["known_targets"]
        if known == ["Generic"]:
            assert name not in _labelling._MOCK_PROBES and name not in _labelling._PROBE_FOR_STRUCTURE, name
        elif known == ["Mock"]:
            assert name in _labelling._MOCK_PROBES, name
        else:
            assert known == [_labelling._PROBE_FOR_STRUCTURE.get(name)], name


@pytest.mark.parametrize(
    "structure, probe, sequence, code",
    [
        ("1XI5", "NPC_Nup96_Cterminal_direct", None, "probe_structure_mismatch"),
        ("1XI5", "NHS_ester", "ELAVGSL", "target_not_used"),
        ("7R5K", "NPC_Nup96_Cterminal_direct", "ELAVGSL", "target_not_used"),
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
    [
        ("1XI5", "NHS_ester", None),
        ("7R5K", "NPC_Nup96_Cterminal_direct", None),
        ("7R5K", "Antibody", "ELAVGSL"),
        ("1XI5", "Antibody", None),  # VLab4Mic picks a target sequence at random
    ],
)
def test_valid_labellings_are_accepted(structure, probe, sequence):
    from vlab4mic_lc_tools._labelling import check_labelling

    check_labelling(structure, probe, sequence)


def test_ranges_match_the_notebook_widgets():
    inputs = {p["name"]: p for p in _tools()["simulate_sample"]["inputs"]}
    assert (inputs["number_of_particles"]["minimum"], inputs["number_of_particles"]["maximum"], inputs["number_of_particles"]["default"]) == (1, 20, 1)
    assert (inputs["sample_size_xy_nm"]["default"], inputs["sample_size_z_nm"]["default"]) == (1000, 100)
    assert inputs["exposure_time_s"]["default"] == 0.001
    assert inputs["random_orientations"]["default"] is True and inputs["random_rotations"]["default"] is True


def test_a_new_simulation_replaces_the_previous_images():
    outputs = {o["name"]: o for o in _tools()["simulate_sample"]["outputs"]}
    assert outputs["simulated"]["replace"] and outputs["noiseless"]["replace"]
    assert "replace" not in outputs["values"]
