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

MAX_SIMULATION_GB = 2.0  # memory a simulation may need


@tool("Simulate imaging of a virtual sample")
def simulate_sample(
    structure: Annotated[
        Literal["1XI5", "7R5K", "3J3Y", "8GMO"],
        Group("Sample"),
        Description(
            "Structure to image (PDB ID): 1XI5 clathrin coat, 7R5K nuclear pore complex (constricted), 3J3Y HIV-1 capsid, 8GMO bacteriophage T4 capsid. The first run with a structure downloads it."
        ),
    ] = "1XI5",
    number_of_particles: Annotated[
        int, Min(1), Max(20), Group("Sample"), Description("Copies of the structure placed in the field (fewer are placed when they would not fit)")
    ] = 1,
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
            "NHS_ester labels lysines of any structure; antibodies, nanobodies and tags bind a sequence of the structure (a random one unless you set 'Target sequence'). The last four are made for one structure (7R5K, 1XI5, 3J3Y)."
        ),
    ] = "NHS_ester",
    target_sequence: Annotated[
        Optional[str],
        Group("Labelling"),
        Description("Amino-acid sequence of the structure that an antibody, nanobody or tag binds, e.g. ELAVGSL (Nup96 C-terminus of 7R5K); unset = VLab4Mic picks one"),
    ] = None,
    fluorophore: Annotated[Literal["AF647", "AF488"], Group("Labelling")] = "AF647",
    labelling_efficiency: Annotated[
        float, Min(0), Max(1), Group("Labelling"), Description("Fraction of the binding sites that carry a probe")
    ] = 1.0,
    distance_from_epitope_angstrom: Annotated[
        Optional[float],
        Min(0),
        Max(1000),
        Unit("angstrom"),
        Label("Distance from epitope"),
        Group("Labelling"),
        Advanced(),
        Description("Distance between the epitope and the probe; unset = the probe's own value"),
    ] = None,
    wobble_cone_degrees: Annotated[
        Optional[float],
        Min(0),
        Max(45),
        Unit("deg"),
        Label("Wobble cone"), Group("Labelling"),
        Advanced(),
        Description("Half-angle of the cone in which the probe wobbles; unset = no wobble"),
    ] = None,
    degree_of_labelling: Annotated[
        Optional[int], Min(0), Max(1000), Group("Labelling"), Advanced(), Description("Fluorophores per probe (DOL); unset = the probe's own value")
    ] = None,
    structural_integrity: Annotated[
        Optional[float],
        Min(0),
        Max(1),
        Group("Labelling"),
        Advanced(),
        Description("Fraction of the complex that is intact; unset = intact. Uses the two cluster distances below"),
    ] = None,
    small_cluster_distance_angstrom: Annotated[
        float, Min(0), Unit("angstrom"), Label("Small cluster distance"), Group("Labelling"), Advanced(), Description("Distance that groups epitopes into multimers (with 'Structural integrity')")
    ] = 100.0,
    large_cluster_distance_angstrom: Annotated[
        float, Min(0), Unit("angstrom"), Label("Large cluster distance"), Group("Labelling"), Advanced(), Description("Distance within multimers to consider neighbours (with 'Structural integrity')")
    ] = 200.0,
    sample_size_xy_nm: Annotated[
        int, Min(100), Max(20000), Unit("nm"), Label("Sample size XY"), Group("Sample"), Advanced(), Description("Side of the square sample; the image has this size divided by the pixel size, per side")
    ] = 1000,
    sample_size_z_nm: Annotated[int, Min(1), Max(20000), Unit("nm"), Label("Sample size Z"), Group("Sample"), Advanced(), Description("Thickness of the sample")] = 100,
    minimal_distance_nm: Annotated[
        Optional[int],
        Min(1),
        Max(1000),
        Unit("nm"),
        Label("Minimal distance between particles"), Group("Sample"),
        Advanced(),
        Description("Minimal distance between particles; unset = from the size of the labelled structure"),
    ] = None,
    random_positions: Annotated[bool, Group("Sample"), Advanced(), Description("Place the particles at random (always the case with more than one)")] = True,
    axial_offset_nm: Annotated[Optional[float], Unit("nm"), Label("Axial offset"), Group("Sample"), Advanced(), Description("Height of the particles above the bottom of the sample; unset = standard")] = None,
    random_orientations: Annotated[bool, Group("Sample"), Advanced(), Description("Give each particle a random orientation")] = True,
    random_rotations: Annotated[bool, Group("Sample"), Advanced(), Description("Rotate each particle randomly in the plane")] = True,
    expansion_factor: Annotated[float, Min(0.1), Max(100), Group("Sample"), Advanced(), Description("Expansion of the structure (expansion microscopy); 1 = none")] = 1.0,
    modality: Annotated[
        Literal["STED", "Widefield", "Confocal", "AiryScan", "SMLM"],
        Group("Imaging"),
        Description("Imaging modality; it sets the resolution and the pixel size (Widefield 100 nm, Confocal 70 nm, AiryScan 40 nm, STED 15 nm, SMLM 2 nm)"),
    ] = "STED",
    exposure_time_s: Annotated[
        float, Min(0), Max(10), Unit("s"), Label("Exposure time"), Group("Imaging"), Description("Exposure time of the acquisition. The memory needed grows with it: about 2.6 GB at 0.1 s for one clathrin particle")
    ] = 0.001,
    noise: Annotated[bool, Group("Imaging"), Description("Add detector noise to the simulated image")] = True,
    pixel_size_nm: Annotated[
        Optional[int], Min(1), Max(1000), Unit("nm"), Label("Pixel size"), Group("Modality"), Advanced(), Description("Pixel size; unset = the modality's. It must be a multiple of the PSF sampling rate")
    ] = None,
    psf_sigma_xy_nm: Annotated[
        Optional[float], Min(0), Max(1000), Unit("nm"), Label("PSF sigma in XY"), Group("Modality"), Advanced(), Description("Unset = the modality's")
    ] = None,
    psf_sigma_z_nm: Annotated[
        Optional[float], Min(0), Max(1000), Unit("nm"), Label("PSF sigma in Z"), Group("Modality"), Advanced(), Description("Unset = the modality's")
    ] = None,
    depth_of_field_nm: Annotated[
        Optional[int], Min(10), Max(1000), Unit("nm"), Label("Depth of field"), Group("Modality"), Advanced(), Description("Unset = the modality's")
    ] = None,
    psf_sampling_nm: Annotated[
        Optional[int], Min(1), Max(1000), Unit("nm"), Label("PSF sampling rate"), Group("Modality"), Advanced(), Description("Unset = the modality's")
    ] = None,
    lateral_precision_nm: Annotated[
        Optional[float], Min(0), Max(1000), Unit("nm"), Label("Lateral precision"), Group("Localisations (SMLM)"), Advanced(), Description("Precision of the localisations in XY; unset = the modality's")
    ] = None,
    axial_precision_nm: Annotated[
        Optional[float], Min(0), Max(1000), Unit("nm"), Label("Axial precision"), Group("Localisations (SMLM)"), Advanced(), Description("Precision of the localisations in Z; unset = the modality's")
    ] = None,
    localisations_per_emitter: Annotated[
        Optional[int], Min(1), Max(1000), Group("Localisations (SMLM)"), Advanced(), Description("Unset = the modality's")
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
    sample = {}
    for key, value in (
        ("probe_distance_to_epitope", distance_from_epitope_angstrom),
        ("probe_wobble_theta", wobble_cone_degrees),
        ("probe_DoL", degree_of_labelling),
        ("minimal_distance", minimal_distance_nm),
        ("axial_offset", axial_offset_nm),
    ):
        if value is not None:
            sample[key] = value
    if structural_integrity is not None:
        sample.update(
            structural_integrity=float(structural_integrity),
            structural_integrity_small_cluster=float(small_cluster_distance_angstrom),
            structural_integrity_large_cluster=float(large_cluster_distance_angstrom),
        )
    try:
        _, _, experiment = experiments.image_vsample(
            structure=structure,
            probe_template=probe,
            probe_target_type="Sequence" if target_sequence else None,
            probe_target_value=target_sequence or None,
            probe_fluorophore=fluorophore,
            labelling_efficiency=float(labelling_efficiency),
            sample_dimensions=[int(sample_size_xy_nm), int(sample_size_xy_nm), int(sample_size_z_nm)],
            random_placing=bool(random_positions),
            random_orientations=bool(random_orientations),
            random_rotations=bool(random_rotations),
            expansion_factor=float(expansion_factor),
            modality=modality,
            number_of_particles=int(number_of_particles),
            random_seed=random_seed,
            clear_experiment=True,
            run_simulation=False,
            **sample,
        )
    except OSError as error:  # no internet, or the structure database is unreachable (requests' errors derive from OSError)
        raise ToolError(
            "structure_unavailable",
            "Could not get the structure %s (%s: %s). The first use of a structure downloads it from RCSB: check the internet connection and try again."
            % (structure, type(error).__name__, error),
        ) from error
    check_cancel()
    overrides = {
        key: value
        for key, value in (
            ("pixelsize_nm", pixel_size_nm),
            ("lateral_resolution_nm", psf_sigma_xy_nm),
            ("axial_resolution_nm", psf_sigma_z_nm),
            ("depth_of_field_nm", depth_of_field_nm),
            ("psf_voxel_nm", psf_sampling_nm),
            ("lateral_precision", lateral_precision_nm),
            ("axial_precision", axial_precision_nm),
            ("nlocalisations", localisations_per_emitter),
        )
        if value is not None
    }
    if overrides:  # only what was set: update_modality simulates localisations unless told otherwise
        experiment.update_modality(modality, simulate_localistations=(modality == "SMLM"), **overrides)
    experiment.set_modality_acq(modality, exp_time=float(exposure_time_s), noise=bool(noise), nframes=1)
    detector = experiment.imaging_modalities[modality]["detector"]
    pixel_nm = float(detector["pixelsize"]) * float(detector["scale"]) * 1e9
    sampling_nm = float(experiment.imaging_modalities[modality]["psf_params"]["voxelsize"][0])
    if sampling_nm > 0 and abs(pixel_nm / sampling_nm - round(pixel_nm / sampling_nm)) > 1e-6:
        raise ToolError(
            "pixel_size_not_multiple",
            "The pixel size (%g nm) must be a multiple of the PSF sampling rate (%g nm): change one of them under 'Modality'."
            % (pixel_nm, sampling_nm),
        )
    # VLab4Mic draws every photon of every emitter as a coordinate (3 floats): the memory grows with exposure x emitters x particles
    # (about 1e5 photons per emitter and second; calibrated on 1XI5, 1 particle, 1 s = 26 GB). Refuse what cannot fit.
    emitters = sum(len(v) for v in experiment.particle.emitters.values()) * int(number_of_particles)
    needed_gb = emitters * 1e5 * float(exposure_time_s) * 24 / 1e9
    if needed_gb > MAX_SIMULATION_GB:
        raise ToolError(
            "exposure_too_long",
            "With %d emitters, an exposure of %g s needs about %.0f GB of memory in VLab4Mic. Use at most %.3g s (or fewer particles, or a lower labelling efficiency)."
            % (emitters, exposure_time_s, needed_gb, exposure_time_s * MAX_SIMULATION_GB / needed_gb),
        )
    progress(0.5, "simulating the %s image" % modality)
    images, noiseless = experiment.run_simulation()
    progress(0.95, "collecting the image")
    channel = next(iter(images[modality]))
    simulated = np.asarray(images[modality][channel])
    clean = np.asarray(noiseless[modality][channel], dtype=np.float32)
    if simulated.ndim == 3:  # one frame is acquired; keep the declared YX output
        simulated, clean = simulated[0], clean[0]
    placed = int(experiment.coordinate_field.get_molecule_param("nMolecules"))
    return (
        simulated,
        clean,
        {
            "modality": modality,
            "pixel_size_nm": round(pixel_nm, 3),
            "pixel_size_um": round(pixel_nm / 1000.0, 6),
            "image_size_px": "%d x %d" % (simulated.shape[1], simulated.shape[0]),
            "particles_requested": int(number_of_particles),
            "particles_placed": placed,
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
