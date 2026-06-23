# nemo-spinup-restart

Update NEMO ocean model restart files with machine learning predictions.

## Installation
Start by installing a virtual environment and then:

```bash
pip install .
```

## Usage

```bash
nemo-restart 
  --restart_path /path/to/restarts \
  --radical RESTART_NAME \
  --mask_file /path/to/mask.nc \
  --prediction_path /path/to/predictions \
  --ocean_terms ocean_terms.yaml

nemo-upscale upscale \\
  --predictions-dir ./predictions \
  --coarse-template ./1deg/restart_template.nc \
  --coarse-mask ./1deg/mesh_mask.nc \
  --coarse-namelist ./1deg/namelist_cfg \
  --fine-template ./025deg/restart_template.nc \
  --fine-mask ./025deg/mesh_mask.nc \
  --output-dir ./generated \
  --name C2
```

### Required Arguments

- `--restart_path`: Directory containing restart files
- `--radical`: Restart filename pattern/radical
- `--mask_file`: Path to NEMO mesh mask file
- `--prediction_path`: Directory containing prediction numpy files

### Optional Arguments

- `--ocean_terms`: Path to ocean terms YAML configuration (default: `ocean_terms.yaml`)

## License

MIT License - Adapted from [Spinup-NEMO](https://github.com/maudtst/Spinup-NEMO) by Maud Tissot
