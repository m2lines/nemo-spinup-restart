"""
CLI for upscaling NEMO restart files from coarse to fine resolution.
"""

import argparse
from pathlib import Path

from nemo_spinup_restart.regrid import (
    regrid_restart,
    upscale_predictions,
)


def main():
    """Main CLI entry point for nemo-upscale."""
    parser = argparse.ArgumentParser(
        description="Upscale NEMO restart files from coarse to fine resolution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
                Examples:
                # Complete upscaling workflow (predictions -> coarse -> fine)
                nemo-upscale upscale \\
                    --predictions-dir ./predictions \\
                    --coarse-template ./1deg/restart_template.nc \\
                    --coarse-mask ./1deg/mesh_mask.nc \\
                    --coarse-namelist ./1deg/namelist_cfg \\
                    --fine-template ./025deg/restart_template.nc \\
                    --fine-mask ./025deg/mesh_mask.nc \\
                    --output-dir ./generated \\
                    --name C2

                # Regrid existing coarse restart to fine resolution
                nemo-upscale regrid \\
                    --coarse-restart ./generated/restart_coarse.nc \\
                    --fine-template ./025deg/restart_template.nc \\
                    --coarse-mask ./1deg/mesh_mask.nc \\
                    --fine-mask ./025deg/mesh_mask.nc \\
                    --output ./generated/restart_fine.nc
               """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Subcommand: upscale (complete workflow)
    upscale_parser = subparsers.add_parser(
        "upscale",
        help="Complete workflow: numpy predictions -> coarse restart -> fine restart",
    )
    upscale_parser.add_argument(
        "--predictions-dir",
        type=str,
        required=True,
        help="Directory containing pred_thetao.npy, pred_so.npy, pred_zos.npy",
    )
    upscale_parser.add_argument(
        "--coarse-template",
        type=str,
        required=True,
        help="Template restart file at coarse resolution",
    )
    upscale_parser.add_argument(
        "--coarse-mask",
        type=str,
        required=True,
        help="Mesh mask file at coarse resolution",
    )
    upscale_parser.add_argument(
        "--coarse-namelist",
        type=str,
        required=True,
        help="NEMO namelist at coarse resolution (for density calculation)",
    )
    upscale_parser.add_argument(
        "--fine-template",
        type=str,
        required=True,
        help="Template restart file at fine resolution",
    )
    upscale_parser.add_argument(
        "--fine-mask", type=str, required=True, help="Mesh mask file at fine resolution"
    )
    upscale_parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory to save generated restart files",
    )
    upscale_parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Identifier for this generation (e.g., 'C2')",
    )
    upscale_parser.add_argument(
        "--time-index",
        type=int,
        default=-1,
        help="Time index to extract from prediction arrays (default: -1, last timestep)",
    )

    # Subcommand: regrid (coarse -> fine only)
    regrid_parser = subparsers.add_parser(
        "regrid", help="Regrid existing restart file to fine resolution"
    )
    regrid_parser.add_argument(
        "--coarse-restart",
        type=str,
        required=True,
        help="Coarse resolution restart file to regrid",
    )
    regrid_parser.add_argument(
        "--fine-template",
        type=str,
        required=True,
        help="Template restart file at fine resolution",
    )
    regrid_parser.add_argument(
        "--coarse-mask",
        type=str,
        required=True,
        help="Mesh mask file at coarse resolution",
    )
    regrid_parser.add_argument(
        "--fine-mask", type=str, required=True, help="Mesh mask file at fine resolution"
    )
    regrid_parser.add_argument(
        "--output", type=str, required=True, help="Path to save regridded restart file"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    # Execute the appropriate command
    if args.command == "upscale":
        print("Starting complete upscaling workflow...")
        print(f"Predictions: {args.predictions_dir}")
        print(f"Coarse: {args.coarse_template}")
        print(f"Fine: {args.fine_template}")
        print(f"Output: {args.output_dir}")

        import numpy as np

        # Verify predictions exist
        pred_dir = Path(args.predictions_dir)
        if not (pred_dir / "toce.npy").exists():
            raise FileNotFoundError(
                f"toce.npy not found in {args.predictions_dir}"
            )
        if not (pred_dir / "soce.npy").exists():
            raise FileNotFoundError(f"soce.npy not found in {args.predictions_dir}")
        if not (pred_dir / "ssh.npy").exists():
            raise FileNotFoundError(f"ssh.npy not found in {args.predictions_dir}")

        output_file = upscale_predictions(
            args.predictions_dir,
            args.coarse_template,
            args.coarse_mask,
            args.coarse_namelist,
            args.fine_template,
            args.fine_mask,
            args.output_dir,
            args.name,
            args.time_index,
        )

        print(f"\n✓ Upscaling complete!")
        print(f"  Fine resolution restart: {output_file}")

    elif args.command == "regrid":
        print("Regridding restart to fine resolution...")
        print(f"Coarse: {args.coarse_restart}")
        print(f"Fine template: {args.fine_template}")
        print(f"Output: {args.output}")

        regrid_restart(
            args.coarse_restart,
            args.fine_template,
            args.coarse_mask,
            args.fine_mask,
            args.output,
        )

        print(f"\n✓ Regridding complete: {args.output}")


if __name__ == "__main__":
    main()
