"""Checks of the labelling choices of `simulate_sample`, kept apart from the declarations.

(The installer ships `setup.py` only when `src/` holds more than `__init__.py` files, and this keeps the declaration module short.)
"""

from labconstrictor_tools import ToolError

# Each probe template names the structures it can label (`known_targets` in its VLab4Mic configuration file):
# "Generic" labels any structure, "Mock" is a template (antibody, nanobody, tag...) that binds a sequence of the structure
# (VLab4Mic picks a random one when none is given), and a structure ID is a probe made for that structure.
# tests/test_lc_tools_declaration.py checks this table against the configuration files of the installed VLab4Mic.
_MOCK_PROBES = ("Antibody", "Nanobody", "GFP", "GFP_w_nanobody", "SNAP-tag", "mMaple", "Linker")
_PROBE_FOR_STRUCTURE = {
    "CCP_heavy_chain_Cterminal": "1XI5",
    "HIV_capsid_p24_direct": "3J3Y",
    "anti-p24_primary_antibody_HIV": "3J3Y",
    "NPC_Nup96_Cterminal_direct": "7R5K",
}


def check_labelling(structure, probe, target_sequence):
    if structure is not None and probe in _PROBE_FOR_STRUCTURE and structure != _PROBE_FOR_STRUCTURE[probe]:  # structure=None: a structure file is used (see check_structure_source)
        raise ToolError(
            "probe_structure_mismatch",
            "The probe '%s' was made for the structure %s, not %s: choose %s, or a probe such as NHS_ester that labels any structure."
            % (probe, _PROBE_FOR_STRUCTURE[probe], structure, _PROBE_FOR_STRUCTURE[probe]),
        )
    if target_sequence and probe not in _MOCK_PROBES:
        raise ToolError(
            "target_not_used",
            "'Target sequence' is only used by antibodies, nanobodies and tags (%s); the probe '%s' has its own target. Leave it unset."
            % (", ".join(_MOCK_PROBES), probe),
        )


def check_structure_source(structure, structure_file, probe):
    """A structure file replaces the PDB ID, so a probe that was made for one particular structure cannot be used with it."""
    if structure_file and probe in _PROBE_FOR_STRUCTURE:
        raise ToolError(
            "probe_structure_mismatch",
            "The probe '%s' was made for the structure %s, which a structure file replaces: choose a probe such as NHS_ester that labels any structure."
            % (probe, _PROBE_FOR_STRUCTURE[probe]),
        )


def parse_numbers(text, name, count=None, integers=False):
    """'10, 20, 30' -> [10, 20, 30]. Anything that is not a list of numbers (or not `count` of them) is an error that names the field."""
    kind = "whole numbers" if integers else "numbers"
    parts = [part.strip() for part in text.split(",")]
    try:
        numbers = [int(part) if integers else float(part) for part in parts]
    except ValueError:
        raise ToolError("bad_list", "'%s' must be %s separated by commas, for example 0, 90, 180; got %r" % (name, kind, text)) from None
    if count is not None and len(numbers) != count:
        raise ToolError("bad_list", "'%s' needs exactly %d %s separated by commas; got %d" % (name, count, kind, len(numbers)))
    return numbers
