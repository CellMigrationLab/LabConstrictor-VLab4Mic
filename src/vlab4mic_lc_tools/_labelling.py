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
    if probe in _PROBE_FOR_STRUCTURE and structure != _PROBE_FOR_STRUCTURE[probe]:
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
