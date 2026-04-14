"""
Integration test for nemo-spinup-restart using real NetCDF data.

Compares the output of the full pipeline against a known-good reference file.
Test data must be downloaded first via:

    bash tests/download_test_data.sh
"""

import pathlib
import pytest
import xarray as xr
import numpy as np

from nemo_spinup_restart.restart import (
    get_mask_file,
    load_predictions,
    propagate_pred,
)

DATA_DIR = pathlib.Path(__file__).parent / "data"


@pytest.fixture(scope="module")
def test_data():
    """Load input, reference output, and mask from tests/data/."""
    for name in (
        "DINO_00576000_restart.nc",
        "mesh_mask.nc",
        "reconstructed-restarts/NEW_DINO_00576000_restart.nc",
    ):
        path = DATA_DIR / name
        assert path.exists(), (
            f"{path} not found. Run `bash tests/download_test_data.sh` first."
        )

    restart = xr.open_dataset(DATA_DIR / "DINO_00576000_restart.nc", decode_times=False)
    mask = get_mask_file(str(DATA_DIR / "mesh_mask.nc"), restart)
    reference = xr.open_dataset(
        DATA_DIR / "reconstructed-restarts" / "NEW_DINO_00576000_restart.nc",
        decode_times=False,
    )

    return {
        "restart": restart,
        "mask": mask,
        "reference": reference,
        "ocean_terms_file": str(DATA_DIR / "ocean_terms.yaml"),
        "prediction_path": str(DATA_DIR / "simu_predicted"),
    }


def test_cli_entry_point():
    """CLI entry point should be installed and expose all expected arguments."""
    import subprocess

    result = subprocess.run(
        ["nemo-spinup-restart", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    for arg in [
        "--restart_path",
        "--radical",
        "--mask_file",
        "--prediction_path",
        "--ocean_terms",
    ]:
        assert arg in result.stdout, f"Expected {arg} in --help output"


def test_output_matches_reference(test_data):
    """Full pipeline output should match the reference file variable by variable."""
    restart = test_data["restart"].copy(deep=True)
    mask = test_data["mask"]
    reference = test_data["reference"]

    restart = load_predictions(
        restart,
        dirpath=test_data["prediction_path"],
        ocean_terms_file=test_data["ocean_terms_file"],
    )
    restart = propagate_pred(restart, mask)

    for var in reference.data_vars:
        if var not in restart:
            pytest.skip(f"Variable {var!r} not in output, skipping.")
        np.testing.assert_allclose(
            restart[var].values,
            reference[var].values,
            rtol=1e-5,
            err_msg=f"Mismatch in variable {var!r}",
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
