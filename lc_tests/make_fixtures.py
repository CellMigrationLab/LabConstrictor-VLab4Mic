"""Host-side fixture generator (numpy + scipy + tifffile only) for the `compare_images` cases.

A reference image of bright spots at 20 nm per pixel, the same field at half the resolution (40 nm per pixel), a version of
it with an offset background, and an unrelated noise image. No simulation is needed.

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
print("wrote 5 images to", out)
