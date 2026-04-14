#!/usr/bin/env bash
# Download integration test data from Zenodo into tests/data/.
#
# Usage (run from the repo root):
#   bash tests/download_test_data.sh
#
# Data source: https://zenodo.org/records/19557419 (restart-test.zip)

set -euo pipefail

# Resolve tests/data relative to this script so it works from any cwd
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_DIR="${SCRIPT_DIR}/data"
ZIP_FILE="restart-test.zip"
ZENODO_URL="https://zenodo.org/records/19557419/files/${ZIP_FILE}"

mkdir -p "${LOCAL_DIR}"

if [ -f "${LOCAL_DIR}/DINO_00576000_restart.nc" ] && \
   [ -f "${LOCAL_DIR}/mesh_mask.nc" ] && \
   [ -f "${LOCAL_DIR}/ocean_terms.yaml" ] && \
   [ -d "${LOCAL_DIR}/simu_predicted" ] && \
   [ -d "${LOCAL_DIR}/reconstructed-restarts" ]; then
    echo "Test data already present in ${LOCAL_DIR}/; skipping download."
    exit 0
fi

echo "Downloading ${ZIP_FILE} from Zenodo..."
curl -L -o "${ZIP_FILE}" "${ZENODO_URL}"
unzip -o "${ZIP_FILE}" -d "${LOCAL_DIR}"
rm "${ZIP_FILE}"

echo "Done. Test data available in ${LOCAL_DIR}/"
ls -lh "${LOCAL_DIR}/"
