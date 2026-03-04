#!/usr/bin/env bash
# Download integration test data from spirit1.ipsl.fr into tests/data/.
#
# Usage (locally, assuming SSH access to spirit1 is configured):
#   bash scripts/download_test_data.sh
#
# In CI the workflow sets up the SSH key before calling this script.
#
# NOTE: Once the NEMO-SPINUP THREDDS quota is restored and the data is published,
# this script will be updated to use curl instead of scp:
#   https://thredds-su.ipsl.fr/thredds/catalog/NEMO-SPINUP/restart/simple/
#   Data will be moved to /projsu/nemo-rd/SPINUP/
#   SSH key will be deleted

set -euo pipefail

REMOTE_USER="marcher"
REMOTE_HOST="spirit1.ipsl.fr"
REMOTE_DIR="/scratchu/marcher/restart/examples/simple"
LOCAL_DIR="tests/data"

mkdir -p "$LOCAL_DIR"

echo "Downloading test data from ${REMOTE_HOST}:${REMOTE_DIR} -> ${LOCAL_DIR}/"

# Compressed NetCDF files
for file in DINO_00576000_restart.nc.xz mesh_mask.nc.xz NEW_DINO_00576000_restart.nc.xz; do
    if [ ! -f "${LOCAL_DIR}/${file%.xz}" ]; then
        echo "  Fetching ${file}..."
        scp "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/${file}" "${LOCAL_DIR}/"
        xz -d -v "${LOCAL_DIR}/${file}"
    else
        echo "  ${file%.xz} already exists, skipping."
    fi
done

# Config file
if [ ! -f "${LOCAL_DIR}/ocean_terms.yaml" ]; then
    echo "  Fetching ocean_terms.yaml..."
    scp "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/ocean_terms.yaml" "${LOCAL_DIR}/"
else
    echo "  ocean_terms.yaml already exists, skipping."
fi

# Prediction directory
if [ ! -d "${LOCAL_DIR}/simus_predicted" ]; then
    echo "  Fetching simus_predicted/..."
    scp -r "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/simus_predicted" "${LOCAL_DIR}/"
else
    echo "  simus_predicted/ already exists, skipping."
fi

echo "Done. Test data available in ${LOCAL_DIR}/"
ls -lh "${LOCAL_DIR}/"
