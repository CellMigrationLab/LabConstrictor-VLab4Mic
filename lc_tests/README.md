# Tests for the tools exposed to Napari / Fiji

Declarations: `src/vlab4mic_lc_tools/`. The tools run in the app's own environment through the LabConstrictor tools worker.

    python lc_tests/make_fixtures.py lc_tests/fixtures      # images for the comparison cases (numpy, scipy, tifffile)
    labconstrictor-tools check --module vlab4mic_lc_tools --pythonpath src
    labconstrictor-tools test  --module vlab4mic_lc_tools --pythonpath src --cases lc_tests/cases.json

`cases.json` has 20 cases: a simulation with the defaults and with every modality (pixel size and image size checked), the two nuclear-pore examples from the VLab4Mic README, a different field of view and exposure time, the errors that are explained (probe without target, probe for another structure, target on a probe that has its own, out-of-range values), and the comparison tool (identical images, the same field at half the resolution, unrelated noise, a flat image, a stack, a zero pixel size).
The simulation cases take about 5 minutes together (SMLM and the nuclear-pore structure are the slow ones) and need internet the first time, to download the structures.
The unit tests (`pytest tests`) check the declarations against the configuration files of the installed VLab4Mic, so they fail when VLab4Mic adds or removes a structure, probe or modality.
