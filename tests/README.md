# Integration Tests for nemo-spinup-restart

This directory contains integration tests that validate the full pipeline against
a known-good reference output using real NEMO data files.

## Test Data

Test data lives in `tests/data/` (gitignored — not committed to the repo):

| File | Description |
|------|-------------|
| `DINO_00576000_restart.nc` | Input restart file |
| `mesh_mask.nc` | Ocean mask file |
| `ocean_terms.yaml` | Configuration file for ocean terms |
| `simu_predicted/` | Directory containing ML prediction files (`toce.npy`, `soce.npy`, `ssh.npy`) |
| `reconstructed-restarts/NEW_DINO_00576000_restart.nc` | Reference output for comparison |

## Downloading Test Data

Test data is published on Zenodo and downloaded via:

```bash
bash tests/download_test_data.sh
```

The script fetches `restart-test.zip` from
[Zenodo record 19557419](https://zenodo.org/records/19557419) and extracts it
into `tests/data/`. It is safe to re-run — if the expected files are already
present, the download is skipped.

## Running Tests Locally

```bash
# Install the package with dev dependencies
pip install -e ".[dev]"

# Download test data from Zenodo
bash tests/download_test_data.sh

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

1. Installs the package with dev dependencies
2. Calls `tests/download_test_data.sh` to fetch data from Zenodo into `tests/data/`
3. Runs `pytest tests/test_integration.py -v`

No secrets or SSH configuration are required — the data is fetched over HTTPS.

## Troubleshooting

- **File not found**: Run `bash tests/download_test_data.sh` first
- **Import errors**: Ensure the package is installed with `pip install -e ".[dev]"`
