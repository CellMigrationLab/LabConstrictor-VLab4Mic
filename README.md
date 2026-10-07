<div align="center">

<img src="src/logo/logo.png" width="420" alt="VLab4Mic logo"/>

# VLab4Mic Desktop App

**Download and install VLab4Mic on your computer. A friendly toolkit to simulate fluorescence microscopy images, no coding required.**

[VLab4Mic website](https://vlab4mic.henriqueslab.org/) · [Main project repository](https://github.com/HenriquesLab/VLab4Mic) · [Releases](https://github.com/HenriquesLab/LabConstrictor-VLab4Mic/releases)

</div>

---

## What is VLab4Mic?

VLab4Mic is a virtual laboratory that lets you explore, test, and design imaging experiments before stepping into the microscope room. You build virtual samples from molecular structures, apply fluorescent labelling, and simulate image acquisition across microscopy modalities, all without writing code. It works equally well for newcomers learning the basics and for experienced researchers benchmarking probes, PSFs, or reconstruction methods.

With VLab4Mic you can:

- Build virtual samples from PDB/CIF structures
- Apply direct or indirect fluorescent labelling
- Add structural variation and molecular crowding
- Simulate image acquisition across multiple modalities
- Run parameter sweeps to explore experimental conditions
- Compare noiseless versus realistic acquisitions

## What this repository gives you

This repository is the desktop-app distribution of VLab4Mic, built with [LabConstrictor](https://github.com/CellMigrationLab/LabConstrictor). It provides one-click installers for **Windows, macOS, and Linux**, so you can run VLab4Mic locally with no Python setup. The installers are published on the [Releases page](https://github.com/HenriquesLab/LabConstrictor-VLab4Mic/releases).

## Download and install

Full step-by-step instructions for each operating system are in the [installation guide](.tools/docs/download_executable.md).

| Platform | Installer | Notes |
|----------|-----------|-------|
| Windows | `.exe` | Double-click to install. Approve via `More info` then `Run anyway` if Windows warns. |
| macOS | `.pkg` (ARM64 or Intel) or `.sh` | Pick ARM64 for Apple silicon, Intel otherwise. |
| Linux | `.sh` | Run `bash VLab4Mic-<version>-Linux-x86_64.sh`, or mark executable and run. |

Installation takes around 6 to 8 minutes and is only needed once. After installing, launch VLab4Mic from your desktop, Start Menu, or Applications folder.

## Use VLab4Mic from Napari and Fiji (experimental)

The installer also registers two VLab4Mic tools for the [LabConstrictor tools bridge](https://github.com/CellMigrationLab/LabConstrictor-Tools), so that [Napari](https://github.com/CellMigrationLab/napari-labconstrictor) and [Fiji](https://github.com/CellMigrationLab/LabConstrictor-Fiji) show them as forms, and so that the command line can run them:

| Tool | What it does |
|---|---|
| **Simulate imaging of a virtual sample** | Builds a virtual sample of a structure (clathrin, nuclear pore, HIV capsid, ...), labels it with a probe and returns the simulated and the noiseless image, plus the pixel size. |
| **Compare an image with a reference** | Measures the structural similarity (SSIM) and the Pearson correlation of two images after matching their pixel sizes. |

Example from a terminal (use the Python of the installed app):

```
<install folder>/bin/python -m labconstrictor_tools run VLab4Mic simulate_sample modality=STED random_seed=1
<install folder>/bin/python -m labconstrictor_tools run VLab4Mic simulate_sample structure=7R5K probe=NPC_Nup96_Cterminal_direct modality=Widefield field_of_view_nm=3000
```

Good to know:
- The first run with a structure downloads it, and a run takes from about 10 seconds (small structure, STED) to over a minute (nuclear pore, SMLM). Stopping a run takes effect between its stages.
- The image covers a square field (1000 nm by default, *Field of view* under advanced settings). A widefield image at 100 nm per pixel has only 10 x 10 pixels in the default field: use a larger field for the coarser modalities.
- The pixel size is reported in the results (Napari and Fiji do not read it from the image): enter it as the pixel size of the layer or window when you compare images.
- SSIM is high for sparse images even when they do not match (an image full of background looks alike); read it together with the Pearson correlation.
- The notebooks are unchanged.

Developers: `src/vlab4mic_lc_tools` holds the declarations, `lc_tests/` the tests (see `lc_tests/README.md`).

## Other ways to use VLab4Mic

Prefer not to install anything, or want full scripting control? The [main VLab4Mic repository](https://github.com/HenriquesLab/VLab4Mic) covers the alternatives:

- **Google Colab** notebooks, no installation needed
- **Local Jupyter notebooks** with the same widget interface
- **Python library** for scripting and automation

## Documentation and support

- Website and tutorials: https://vlab4mic.henriqueslab.org/
- Main project repository: https://github.com/HenriquesLab/VLab4Mic
- Questions and bug reports: [open an issue](https://github.com/HenriquesLab/LabConstrictor-VLab4Mic/issues)

## Citation

If you use VLab4Mic in your research, please cite:

```bibtex
@article{martinez_2026_vlab4mic,
  title={VLab4Mic: prediction of structural resolvability in super-resolution microscopy},
  author={Mart{\'i}nez, Dami{\'a}n and Saraiva, Bruno M. and Shakespeare, Tayla and
          Bates, Mark and Owen, Dylan M. and Leterrier, Christophe and
          Del Rosario, Mario and Henriques, Ricardo},
  year={2026},
  journal={bioRxiv},
  doi={10.64898/2026.06.02.729521},
  url={https://www.biorxiv.org/content/10.64898/2026.06.02.729521v1}
}
```

## License

Released under the [MIT License](LICENSE).

## 🔄 Automatic Template Updates

LabConstrictor can prepare pull requests that keep this repository aligned with improvements in the main template, including updates to GitHub Actions workflows. Complete the one-time [automatic synchronization setup](.tools/docs/template_synchronization.md) to enable these updates.
