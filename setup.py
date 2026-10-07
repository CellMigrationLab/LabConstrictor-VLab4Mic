"""Packages the tool declarations of VLab4Mic for Napari, Fiji and the command line (LabConstrictor tools bridge).

The installer builds this folder with `pip install --no-deps --no-build-isolation`: VLab4Mic itself comes from PyPI
(requirements.txt), and `vlab4mic_lc_tools` only declares the tools, so it needs nothing else.
"""

from setuptools import setup

setup(
    name="vlab4mic-lc-tools",
    version="0.1.0",
    description="VLab4Mic tools for Napari, Fiji and the command line (LabConstrictor tools bridge)",
    package_dir={"": "src"},
    packages=["vlab4mic_lc_tools"],
    python_requires=">=3.10",
)
