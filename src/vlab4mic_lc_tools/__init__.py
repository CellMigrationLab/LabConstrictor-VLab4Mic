"""VLab4Mic tools for Napari, Fiji and the command line (LabConstrictor tools bridge, experimental).

This module only *declares* the tools: it imports `labconstrictor_tools` and the standard library at the top, and numpy and
VLab4Mic inside the functions. Keep it that way: hosts import it to list the tools, and `import vlab4mic` takes several seconds.
It lives in its own package (not inside `vlab4mic`) for the same reason, and its name must be `<package>_lc_tools` for the
installer to register it.

    labconstrictor-tools check --module vlab4mic_lc_tools
    labconstrictor-tools test  --module vlab4mic_lc_tools --cases lc_tests/cases.json
"""

from typing import Annotated, Literal, Optional

from labconstrictor_tools import (
    Advanced,
    Axes,
    Description,
    Group,
    Image,
    ImageOut,
    Label,
    Max,
    Min,
    Name,
    PixelSizeOf,
    Scalars,
    ToolError,
    Unit,
    check_cancel,
    progress,
    tool,
)

from ._labelling import check_labelling


@tool("Simulate imaging of a virtual sample")
def simulate_sample(
    structure: Annotated[
        Literal["1XI5", "7R5K", "1HZH", "2RCJ", "3J3Y", "8GMO"],
        Group("Sample"),
        Description(
            "Structure to image (PDB ID): 1XI5 clathrin coat, 7R5K nuclear pore complex, 1HZH IgG antibody, 2RCJ IgM, 3J3Y HIV capsid, 8GMO bacteriophage T4 capsid. The first run with a structure downloads it."
        ),
    ] = "1XI5",
    number_of_particles: Annotated[
        int, Min(1), Max(200), Group("Sample"), Description("Copies of the structure placed at random in the field (fewer are placed when they would overlap)")
    ] = 3,
    probe: Annotated[
        Literal[
            "NHS_ester",
            "Antibody",
            "Nanobody",
            "GFP",
            "GFP_w_nanobody",
            "SNAP-tag",
            "mMaple",
            "Linker",
            "NPC_Nup96_Cterminal_direct",
            "CCP_heavy_chain_Cterminal",
            "HIV_capsid_p24_direct",
            "anti-p24_primary_antibody_HIV",
        ],
        Group("Labelling"),
        Description(
            "NHS_ester labels lysines of any structure. Antibodies, nanobodies and tags need a 'Target sequence'. The last four are made for one structure (7R5K, 1XI5, 3J3Y)."
        ),
    ] = "NHS_ester",
    target_sequence: Annotated[
        Optional[str],
        Group("Labelling"),
        Description("Amino-acid sequence of the structure that the probe binds, e.g. ELAVGSL (Nup96 C-terminus of 7R5K). Only for antibodies, nanobodies and tags; unset otherwise"),
    ] = None,
    fluorophore: Annotated[Literal["AF647", "AF488"], Group("Labelling")] = "AF647",
    labelling_efficiency: Annotated[
        float, Min(0), Max(1), Group("Labelling"), Description("Fraction of the binding sites that carry a probe")
    ] = 1.0,
    modality: Annotated[
        Literal["STED", "Widefield", "Confocal", "AiryScan", "SMLM", "Reference"],
        Group("Imaging"),
        Description("Imaging modality; it sets the resolution and the pixel size (Widefield 100 nm, Confocal 70 nm, AiryScan 40 nm, STED 15 nm, Reference 5 nm, SMLM 2 nm)"),
    ] = "STED",
    field_of_view_nm: Annotated[
        Optional[int],
        Min(200),
        Max(20000),
        Unit("nm"),
        Group("Sample"),
        Advanced(),
        Description("Side of the square field in nm; unset = the standard 1000 nm. The image has field / pixel size pixels per side"),
    ] = None,
    exposure_time_s: Annotated[
        Optional[float],
        Min(1e-6),
        Max(1000),
        Unit("s"),
        Label("Exposure time"),
        Group("Imaging"),
        Advanced(),
        Description("Exposure time of the acquisition; unset = the modality's default"),
    ] = None,
    random_seed: Annotated[
        Optional[int], Min(0), Group("Imaging"), Advanced(), Description("Seed for reproducible positions, orientations and noise; unset = a different sample every run")
    ] = None,
) -> tuple[
    Annotated[ImageOut, Name("simulated"), Axes("YX")],
    Annotated[ImageOut, Name("noiseless"), Axes("YX")],
    Scalars,
]:
    """Build a virtual sample of a molecular structure, label it with a probe and simulate how a microscope images it."""
    check_labelling(structure, probe, target_sequence)
    progress(0.03, "loading VLab4Mic")
    import numpy as np
    from vlab4mic import experiments

    check_cancel()
    progress(0.08, "building the virtual sample (the first run with a structure downloads it)")
    options = {}
    if field_of_view_nm is not None:
        options["sample_dimensions"] = [int(field_of_view_nm), int(field_of_view_nm), 100]
    if exposure_time_s is not None:
        options[modality] = {"exp_time": float(exposure_time_s)}
    try:
        _, _, experiment = experiments.image_vsample(
            structure=structure,
            probe_template=probe,
            probe_target_type="Sequence" if target_sequence else None,
            probe_target_value=target_sequence or None,
            probe_fluorophore=fluorophore,
            labelling_efficiency=float(labelling_efficiency),
            modality=modality,
            number_of_particles=int(number_of_particles),
            random_seed=random_seed,
            clear_experiment=True,
            run_simulation=False,
            **options,
        )
    except OSError as error:  # no internet, or the structure database is unreachable (requests' errors derive from OSError)
        raise ToolError(
            "structure_unavailable",
            "Could not get the structure %s (%s: %s). The first use of a structure downloads it from RCSB: check the internet connection and try again."
            % (structure, type(error).__name__, error),
        ) from error
    check_cancel()
    progress(0.5, "simulating the %s image" % modality)
    images, noiseless = experiment.run_simulation()
    progress(0.95, "collecting the image")
    channel = next(iter(images[modality]))
    simulated = np.asarray(images[modality][channel])
    clean = np.asarray(noiseless[modality][channel], dtype=np.float32)
    frames = int(simulated.shape[0]) if simulated.ndim == 3 else 1
    if simulated.ndim == 3:  # one frame is acquired; a stack would not fit the declared YX output
        simulated, clean = simulated[0], clean[0]
    detector = experiment.imaging_modalities[modality]["detector"]
    pixel_size_nm = float(detector["pixelsize"]) * float(detector["scale"]) * 1e9
    placed = int(experiment.coordinate_field.get_molecule_param("nMolecules"))
    return (
        simulated,
        clean,
        {
            "modality": modality,
            "pixel_size_nm": round(pixel_size_nm, 3),
            "pixel_size_um": round(pixel_size_nm / 1000.0, 6),
            "image_size_px": "%d x %d" % (simulated.shape[1], simulated.shape[0]),
            "particles_requested": int(number_of_particles),
            "particles_placed": placed,
            "frames_acquired": frames,
        },
    )


@tool("Compare an image with a reference")
def compare_images(
    reference: Annotated[
        Image, Axes("YX"), Group("Images"), Description("Reference image, for example an experimental acquisition")
    ],
    simulated: Annotated[
        Image, Axes("YX"), Group("Images"), Description("Image to compare with it, for example a simulation; it is rescaled to the pixel size of the reference")
    ],
    reference_pixel_size_um: Annotated[float, Unit("um/px"), Min(0), PixelSizeOf("reference"), Group("Images")],
    simulated_pixel_size_um: Annotated[float, Unit("um/px"), Min(0), PixelSizeOf("simulated"), Group("Images")],
) -> Scalars:
    """Measure how similar two images are: structural similarity (SSIM) and Pearson correlation, after matching the pixel sizes."""
    progress(0.05, "loading VLab4Mic")
    import numpy as np
    from vlab4mic.analysis import metrics

    for name, image in (("Reference", reference), ("Simulated", simulated)):
        if image.ndim != 2:
            raise ToolError("bad_input", "%s must be a 2D (YX) image; got %d dimensions" % (name, image.ndim))
        if not np.isfinite(image.astype(np.float64)).all():
            raise ToolError("bad_input", "%s contains NaN or infinite values" % name)
    if reference_pixel_size_um <= 0 or simulated_pixel_size_um <= 0:
        raise ToolError("invalid_pixel_size", "Both pixel sizes must be greater than 0 (they are in micrometres per pixel).")
    if float(simulated.max()) == float(simulated.min()):
        raise ToolError("flat_image", "The simulated image has the same value everywhere: similarity cannot be measured.")
    check_cancel()
    progress(0.3, "matching the pixel sizes")
    ref = reference.astype(np.float64)
    sim = simulated.astype(np.float64)
    # The VLab4Mic metrics work on a mask of the compared pixels; all pixels of both images count.
    ref_mask = np.ones(ref.shape, dtype=bool)
    sim_mask = np.ones(sim.shape, dtype=bool)
    arguments = dict(
        reference_image=ref,
        reference_image_pixelsize_nm=float(reference_pixel_size_um) * 1000.0,
        reference_image_mask=ref_mask,
        simulated_image=sim,
        simulated_image_pixelsize_nm=float(simulated_pixel_size_um) * 1000.0,
        simulated_image_mask=sim_mask,
    )
    progress(0.6, "measuring similarity")
    ssim_value = float(metrics.structural_similarity(**arguments))
    pearson_value = float(metrics.pearson_correlation(**arguments))
    return {
        "ssim": round(ssim_value, 6),
        "pearson": round(pearson_value, 6),
        "reference_pixel_size_nm": round(float(reference_pixel_size_um) * 1000.0, 3),
        "simulated_pixel_size_nm": round(float(simulated_pixel_size_um) * 1000.0, 3),
    }
