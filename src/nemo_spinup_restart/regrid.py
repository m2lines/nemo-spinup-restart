"""
Upscale NEMO restart files from coarse to fine resolution.

Uses standard open-source libraries:
- xarray for NetCDF handling
- xnemogcm for NEMO-specific file operations (MIT)
- xesmf for regridding (MIT)
- f90nml for namelist reading (LGPL)
"""

import numpy as np
import xarray as xr
import xesmf as xe
import f90nml
from datetime import datetime
from pathlib import Path


def compute_nemo_density(temperature, salinity, depth, namelist_path):
    """
    Compute potential density using NEMO's simplified linear equation of state.

    Parameters
    ----------
    temperature : np.ndarray
        Ocean temperature (°C), shape (nav_lev, y, x)
    salinity : np.ndarray
        Ocean salinity (PSU), shape (nav_lev, y, x)
    depth : np.ndarray
        Depth levels (m), shape (nav_lev, y, x) or (nav_lev,)
    namelist_path : str
        Path to NEMO namelist file containing equation of state parameters

    Returns
    -------
    rhop : np.ndarray
        Potential density (kg/m³), shape (nav_lev, y, x)
    """
    nml = f90nml.read(namelist_path)
    eos = nml["nameos"]

    rhop = (
        -eos["rn_a0"]
        * (1.0 + 0.5 * eos["rn_lambda1"] * (temperature - 10.0) + eos["rn_mu1"] * depth)
        * (temperature - 10.0)
        + eos["rn_b0"]
        * (1.0 - 0.5 * eos["rn_lambda2"] * (salinity - 35.0) - eos["rn_mu2"] * depth)
        * (salinity - 35.0)
        - eos["rn_nu"] * (temperature - 10.0) * (salinity - 35.0)
    ) + 1026

    return rhop


def create_restart_from_predictions(
    restart_template_path,
    mesh_mask_path,
    namelist_path,
    temperature,
    salinity,
    ssh,
    output_path,
):
    """
    Create a NEMO restart file from ML predictions at template resolution.

    Parameters
    ----------
    restart_template_path : str
        Path to template restart file (defines structure and grid)
    mesh_mask_path : str
        Path to mesh_mask file (for depth levels)
    namelist_path : str
        Path to NEMO namelist (for equation of state parameters)
    temperature : np.ndarray
        Temperature predictions (°C), shape (nav_lev, y, x)
    salinity : np.ndarray
        Salinity predictions (PSU), shape (nav_lev, y, x)
    ssh : np.ndarray
        Sea surface height predictions (m), shape (y, x)
    output_path : str
        Where to save the generated restart file

    Returns
    -------
    restart : xr.Dataset
        The created restart file
    """
    # Load template
    restart = xr.open_dataset(restart_template_path).load()

    # Load mask for depth information
    mask = xr.open_dataset(mesh_mask_path)
    depth = mask.gdept_0.squeeze().data  # Remove extra dimensions

    # Compute density
    rhop = compute_nemo_density(temperature, salinity, depth, namelist_path)

    # Populate restart file
    restart["tb"] = (
        ("time_counter", "nav_lev", "y", "x"),
        np.expand_dims(temperature, axis=0),
    )
    restart["tn"] = (
        ("time_counter", "nav_lev", "y", "x"),
        np.expand_dims(temperature, axis=0),
    )

    restart["sb"] = (
        ("time_counter", "nav_lev", "y", "x"),
        np.expand_dims(salinity, axis=0),
    )
    restart["sn"] = (
        ("time_counter", "nav_lev", "y", "x"),
        np.expand_dims(salinity, axis=0),
    )

    restart["sshb"] = (("time_counter", "y", "x"), np.expand_dims(ssh, axis=0))
    restart["sshn"] = (("time_counter", "y", "x"), np.expand_dims(ssh, axis=0))

    restart["rhop"] = (
        ("time_counter", "nav_lev", "y", "x"),
        np.expand_dims(rhop, axis=0),
    )

    # Update metadata
    restart.attrs["file_name"] = Path(output_path).name
    restart.attrs["TimeStamp"] = (
        datetime.now().astimezone().strftime("%d/%m/%Y %H:%M:%S %z")
    )

    # Save
    Path(output_path).unlink(missing_ok=True)
    restart.to_netcdf(output_path, unlimited_dims="time_counter")
    print(f"Saved {output_path}")

    return restart


def extrapolate_to_land(restart, mask):
    """
    Extrapolate ocean values onto land points for better regridding.

    Parameters
    ----------
    restart : xr.Dataset
        Restart file to extrapolate
    mask : xr.Dataset
        NEMO mask file (mesh_mask.nc)

    Returns
    -------
    restart_extrapolated : xr.Dataset
        Restart with land points filled
    """
    # Create 3D mask matching restart coordinates

    breakpoint()
    # tmask_3d = mask.tmask.rename({"y_c": "y", "x_c": "x", "z_c": "nav_lev"}) 
    tmask_3d = mask.tmask
    tmask_3d = tmask_3d.assign_coords({"nav_lev": restart.nav_lev}).drop_vars(
        ["x", "y"], errors="ignore"
    )

    # 2D mask for surface variables
    tmask_2d = tmask_3d.isel(nav_lev=0)

    # Apply mask (set land to NaN)
    restart_masked = restart.copy()
    for var_name, var_data in restart.items():
        if var_data.ndim == 3:  # 2D variables (+ time)
            restart_masked[var_name] = var_data.where(tmask_2d == 1.0)
        elif var_data.ndim == 4:  # 3D variables (+ time)
            restart_masked[var_name] = var_data.where(tmask_3d == 1.0)

    # Extrapolate NaN values
    restart_filled_x = restart_masked.interpolate_na(
        dim="x", method="nearest", fill_value="extrapolate"
    )
    restart_filled_xy = restart_filled_x.interpolate_na(
        dim="y", method="nearest", fill_value="extrapolate"
    )

    return restart_filled_xy


def regrid_restart(
    restart_coarse_path,
    restart_fine_template_path,
    mesh_mask_coarse_path,
    mesh_mask_fine_path,
    output_path,
):
    """
    Regrid a restart file from coarse to fine resolution.

    Parameters
    ----------
    restart_coarse_path : str
        Path to coarse resolution restart file (e.g., 1°)
    restart_fine_template_path : str
        Path to fine resolution restart template (e.g., 1/4°)
    mesh_mask_coarse_path : str
        Path to coarse resolution mesh_mask
    mesh_mask_fine_path : str
        Path to fine resolution mesh_mask
    output_path : str
        Where to save the regridded restart file

    Returns
    -------
    restart_regridded : xr.Dataset
        The regridded restart file at fine resolution
    """
    # Load files
    restart_lr = xr.open_dataset(restart_coarse_path).load()
    restart_hr_template = xr.open_dataset(restart_fine_template_path).load()
    mask_lr = xr.open_dataset(mesh_mask_coarse_path)
    mask_hr = xr.open_dataset(mesh_mask_fine_path)

    # Extract timestep from template
    timestep_fine = float(restart_hr_template["rdt"].values)
    print(f"Using timestep from template: {timestep_fine}s")

    # Add lon/lat coordinates for xESMF (it needs CF-compliant coordinates)
    # Get lon/lat from mesh_mask files (glamt, gphit are T-point coordinates)
    restart_lr = restart_lr.assign_coords({
        "lon": (["y", "x"], mask_lr.glamt.squeeze().values),
        "lat": (["y", "x"], mask_lr.gphit.squeeze().values)
    })
    restart_hr_template = restart_hr_template.assign_coords({
        "lon": (["y", "x"], mask_hr.glamt.squeeze().values),
        "lat": (["y", "x"], mask_hr.gphit.squeeze().values)
    })

    # Extrapolate coarse restart onto land
    restart_lr_extrap = extrapolate_to_land(restart_lr, mask_lr)
    # Create regridder (bilinear interpolation)
    regridder = xe.Regridder(
        restart_lr_extrap,
        restart_hr_template,
        "bilinear",
        extrap_method="nearest_s2d",
        ignore_degenerate=True,
    )

    # Apply regridding
    restart_hr = regridder(restart_lr_extrap)

    # Apply fine resolution mask
    # Rename mask dimensions to match restart coordinates
    tmask_3d = mask_hr.tmask
    tmask_3d = tmask_3d.assign_coords({"nav_lev": restart_hr.nav_lev})
    
    # Drop time_counter coordinate from mask (it has different value than restart)
    tmask_3d = tmask_3d.drop_vars(["x", "y", "time_counter"], errors="ignore").squeeze()
    tmask_3d = tmask_3d.compute()

    tmask_2d = tmask_3d.isel(nav_lev=0).compute()

    # Mask regridded data (xarray broadcasts mask over time automatically)
    for var_name, var_data in restart_hr.items():
        if var_data.ndim == 3:  # 2D variables (+ time)
            restart_hr[var_name] = var_data.where(tmask_2d == 1.0, 0.0)
        elif var_data.ndim == 4:  # 3D variables (+ time)
            restart_hr[var_name] = var_data.where(tmask_3d == 1.0, 0.0)

    # Zero out velocities (will be recomputed by NEMO)
    restart_hr["ub"].values[:] = 0.0
    restart_hr["un"].values[:] = 0.0
    restart_hr["vb"].values[:] = 0.0
    restart_hr["vn"].values[:] = 0.0

    # Copy metadata from coarse restart and fine template
    restart_hr["kt"] = restart_lr.kt
    restart_hr["ndastp"] = restart_lr.ndastp
    restart_hr["adatrj"] = restart_lr.adatrj
    restart_hr["ntime"] = restart_lr.ntime
    restart_hr["rdt"] = restart_hr_template["rdt"]  # Use timestep from fine resolution

    # Clean up duplicate coordinates (keep template structure)
    # Drop lon/lat that were added for xESMF, and nav_lon/nav_lat from mask
    coords_to_drop = ["lon", "lat", "nav_lon", "nav_lat"]
    restart_hr = restart_hr.drop_vars(coords_to_drop, errors="ignore")

    # Match variable order from template
    restart_hr = restart_hr[list(restart_hr_template.keys())]

    # Update metadata
    restart_hr.attrs["file_name"] = Path(output_path).name
    restart_hr.attrs["TimeStamp"] = (
        datetime.now().astimezone().strftime("%d/%m/%Y %H:%M:%S %z")
    )
    # Save
    Path(output_path).unlink(missing_ok=True)
    restart_hr.to_netcdf(output_path, unlimited_dims="time_counter")
    print(f"Saved {output_path}")

    return restart_hr


def upscale_predictions(
    predictions_dir,
    coarse_restart_template,
    coarse_mesh_mask,
    coarse_namelist,
    fine_restart_template,
    fine_mesh_mask,
    output_dir,
    generation_name,
    time_index=-1,
):
    """
    Complete workflow: numpy predictions → coarse restart → regrid → fine restart.

    Parameters
    ----------
    predictions_dir : str
        Directory containing pred_thetao.npy, pred_so.npy, pred_zos.npy
    coarse_restart_template : str
        Template restart file at coarse resolution
    coarse_mesh_mask : str
        Mesh mask at coarse resolution
    coarse_namelist : str
        Namelist at coarse resolution (for density calculation)
    fine_restart_template : str
        Template restart file at fine resolution
    fine_mesh_mask : str
        Mesh mask at fine resolution
    output_dir : str
        Directory to save generated restart files
    generation_name : str
        Identifier for this generation (e.g., 'C2')
    time_index : int, optional
        Time index to extract from prediction arrays (default: -1, last timestep)

    Returns
    -------
    fine_restart_path : str
        Path to the final upscaled restart file
    """
    # Step 1: Load predictions (select specified time index)
    temp = np.load(Path(predictions_dir) / "toce.npy")[time_index]
    sal = np.load(Path(predictions_dir) / "soce.npy")[time_index]
    ssh = np.load(Path(predictions_dir) / "ssh.npy")[time_index]

    # Ensure ssh is 2D by squeezing if needed
    if ssh.ndim == 3:
        ssh = np.squeeze(ssh)

    print(
        f"Loaded predictions at time index {time_index}: temp {temp.shape}, sal {sal.shape}, ssh {ssh.shape}"
    )

    # Step 2: Create coarse restart
    coarse_output = Path(output_dir) / f"generated_restart_{generation_name}_coarse.nc"
    create_restart_from_predictions(
        coarse_restart_template,
        coarse_mesh_mask,
        coarse_namelist,
        temp,
        sal,
        ssh,
        str(coarse_output),
    )

    # Step 3: Regrid to fine resolution
    fine_output = Path(output_dir) / f"generated_restart_{generation_name}_fine.nc"
    regrid_restart(
        str(coarse_output),
        fine_restart_template,
        coarse_mesh_mask,
        fine_mesh_mask,
        str(fine_output),
    )

    return str(fine_output)
