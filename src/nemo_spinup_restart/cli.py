# Adapted from code by Maud Tissot (Spinup-NEMO)
# Original source: https://github.com/maudtst/Spinup-NEMO
# Licensed under the MIT License
#
# Modifications in this version by ICCS, 2025
import argparse
import xarray as xr

from nemo_spinup_restart.restart import (
    get_restart_files,
    get_mask_file,
    load_predictions,
    propagate_pred,
    record_full_restart,
    record_pieced_restart,
)


def main():
    """Main CLI entry point for nemo-spinup-restart."""
    parser = argparse.ArgumentParser(
        description="Update NEMO restart files with ML predictions"
    )
    parser.add_argument(
        "--restart_path", type=str, required=True, help="path of restart file directory"
    )
    parser.add_argument(
        "--radical", type=str, required=True, help="radical of restart filename"
    )
    parser.add_argument(
        "--mask_file", type=str, required=True, help="address of mask file"
    )
    parser.add_argument(
        "--prediction_path",
        type=str,
        required=True,
        help="path of prediction directory",
    )
    parser.add_argument(
        "--ocean_terms",
        type=str,
        default="ocean_terms.yaml",
        help="path to ocean_terms.yaml file (default: ocean_terms.yaml)",
    )
    args = parser.parse_args()

    print(f"Loading restart file from {args.restart_path}...")
    restart = xr.open_dataset(
        get_restart_files(args.restart_path, args.radical), decode_times=False
    )

    print(f"Loading mask file from {args.mask_file}...")
    mask = get_mask_file(args.mask_file, restart)

    print(f"Loading predictions from {args.prediction_path}...")
    restart = load_predictions(
        restart, dirpath=args.prediction_path, ocean_terms_file=args.ocean_terms
    )

    print("Propagating predictions to derived variables...")
    restart = propagate_pred(restart, mask)

    print("Recording full restart file...")
    record_full_restart(args.restart_path, args.radical, restart)

    print("Recording pieced restart file...")
    record_pieced_restart(args.restart_path, args.radical, restart)

    print("""
✓ All done! Next steps:
    1. Back transform the coordinates of the pieced restart files using ncks
       (see bash script xarray_to_CMIP.sh)
    2. Rename/Overwrite the "NEW_" restart files to their old version if you're happy with them
       (see bash script rewrite.sh)
    3. Point to the restart directory in your simulation config.card
       You might need to reorganize them in a ./OCE/Restart/CM....nc structure
       instead of ./OCE_CM...nc (there's the rename.sh bash script for that)

See the example script Jumper.sh for reference.
""")


if __name__ == "__main__":
    main()
