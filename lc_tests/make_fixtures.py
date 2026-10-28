"""Host-side fixture generator (numpy + scipy + tifffile only) for the `compare_images` cases.

A reference image of bright spots at 20 nm per pixel, the same field at half the resolution (40 nm per pixel), a version of
it with an offset background, an unrelated noise image, and a small structure file (`mini_ring.cif`) for the
`structure_file` cases. No simulation is needed.

    python lc_tests/make_fixtures.py lc_tests/fixtures
"""

import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter, zoom
from tifffile import imwrite

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(11)

size = 160
field = np.zeros((size, size), np.float64)
for y, x in rng.uniform(15, size - 15, (14, 2)):
    field[int(y), int(x)] = rng.uniform(0.6, 1.0)
reference = gaussian_filter(field, 3.0)
reference = (reference / reference.max() * 4000).astype(np.uint16)

half = zoom(reference.astype(np.float64), 0.5, order=3)  # the same field, imaged with 40 nm pixels
half = np.clip(half, 0, None).astype(np.uint16)
noise = rng.integers(0, 4000, (size, size)).astype(np.uint16)  # nothing in common with the reference

imwrite(out / "reference_20nm.tif", reference)
imwrite(out / "same_field_40nm.tif", half)
imwrite(out / "unrelated_20nm.tif", noise)
imwrite(out / "flat_20nm.tif", np.full((size, size), 100, np.uint16))
imwrite(out / "stack.tif", np.stack([reference, reference]))
imwrite(out / "zero_20nm.tif", np.zeros((size, size), np.uint16))  # an all-zero image: nothing to compare
(out / "not_a_structure.csv").write_text("x,y,z\n1,2,3\n")  # a file that is not a structure (refused by its type)


def mini_ring_cif(n_atoms: int = 24, radius_a: float = 60.0) -> str:
    """Return a minimal mmCIF text: `n_atoms` lysine CA atoms (the target of the default probe, an NHS ester) on a ring of `radius_a` angstroms in one chain (a stand-in structure)."""
    lines = [
        "data_MINIRING",
        "_entity.id 1",  # VLab4Mic reads the entity names and strands of the file: it fails when they are missing
        "_entity.pdbx_description 'mini ring'",
        "_entity_poly.pdbx_strand_id A",
        "loop_",
        "_atom_site.group_PDB",
        "_atom_site.id",
        "_atom_site.type_symbol",
        "_atom_site.label_atom_id",
        "_atom_site.label_alt_id",
        "_atom_site.label_comp_id",
        "_atom_site.label_asym_id",
        "_atom_site.label_entity_id",
        "_atom_site.label_seq_id",
        "_atom_site.pdbx_PDB_ins_code",
        "_atom_site.Cartn_x",
        "_atom_site.Cartn_y",
        "_atom_site.Cartn_z",
        "_atom_site.occupancy",
        "_atom_site.B_iso_or_equiv",
        "_atom_site.auth_seq_id",
        "_atom_site.auth_asym_id",
        "_atom_site.pdbx_PDB_model_num",
    ]
    for i in range(n_atoms):
        angle = 2 * np.pi * i / n_atoms
        x, y = radius_a * np.cos(angle), radius_a * np.sin(angle)
        lines.append(f"ATOM {i + 1} C CA . LYS A 1 {i + 1} ? {x:.3f} {y:.3f} 0.000 1.00 20.00 {i + 1} A 1")
    return "\n".join(lines) + "\n"


(out / "mini_ring.cif").write_text(mini_ring_cif(), encoding="utf-8")
print("wrote 5 images and mini_ring.cif to", out)
