# Integration Tests for nemo-spinup-restart

This directory contains integration tests that validate the full pipeline against
a known-good reference output using real NEMO data files.

## Test Data

Test data lives in `tests/data/` (gitignored — not committed to the repo):

| File | Description |
|------|-------------|
| `DINO_00576000_restart.nc` | Input restart file |
| `mesh_mask.nc` | Ocean mask file |
| `NEW_DINO_00576000_restart.nc` | Reference output for comparison |
| `ocean_terms.yaml` | Configuration file for ocean terms |
| `simus_predicted/` | Directory containing ML prediction files |

## Downloading Test Data

Test data is stored on `spirit1` and downloaded via:

```bash
bash scripts/download_test_data.sh
```

This requires SSH access to `spirit1`. Files are skipped if already present,
so the script is safe to re-run.

> **Note:** Once the NEMO-SPINUP THREDDS quota is restored and the data is
> published, the script will be updated to use `curl` and SSH access will no
> longer be required:
> <https://thredds-su.ipsl.fr/thredds/catalog/NEMO-SPINUP/restart/simple/>

## Running Tests Locally

```bash
# Install the package with dev dependencies
pip install -e ".[dev]"

# Download test data (requires SSH access to spirit1)
bash scripts/download_test_data.sh

# Run the integration test
pytest tests/test_integration.py -v
```

## What the Test Does

`test_output_matches_reference` runs the full pipeline:

1. Loads the input restart file and mask
2. Loads ML predictions via `load_predictions`
3. Propagates predictions to derived variables via `propagate_pred`
4. Compares every variable in the output against the reference file using `np.testing.assert_allclose`

This means the test catches any regression in the physics, not just crashes.

## CI/CD Setup

The workflow `.github/workflows/integration_test.yml` runs on every PR. It:

1. Sets up SSH using the `SSH_PRIVATE_KEY` GitHub Secret
2. Calls `scripts/download_test_data.sh` to fetch data into `tests/data/`
3. Runs `pytest tests/test_integration.py -v`

To configure: add the private key for `spirit1` as a GitHub Secret named `SSH_PRIVATE_KEY`.

## Troubleshooting

- **File not found**: Run `bash scripts/download_test_data.sh` first
- **Import errors**: Ensure the package is installed with `pip install -e ".[dev]"`
- **SSH issues**: Check that the SSH key has access to `spirit1` and that `ssh-keyscan spirit1` resolves correctly in your environment
