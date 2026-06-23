# Diffusion state restart file generation and evaluation

## Data setup 

TODO: Host data on spiritx

## Regrid and upscale

We need 1-degree, 0.25-degree restart file and mesh mask references. 

```bash

REFERENCE=./data/reference

nemo-upscale upscale \
    --predictions-dir $REFERENCE/diffusion_states/chamon_C2_clean/ \
    --coarse-template $REFERENCE/1deg_restart/DINO_00000002_restart.nc \
    --coarse-mask     $REFERENCE/1deg_restart/mesh_mask.nc \
    --coarse-namelist $REFERENCE/1deg_restart/namelist_cfg \
    --fine-template   $REFERENCE/025deg_restart/restart25_arch/DINO_10800000_restart.nc \
    --fine-mask       $REFERENCE/025deg_restart/restart25_arch/mesh_mask.nc \
    --name            C2 \
    --time-index      4 \
    --output-dir      ./generated
```

## Evaluate using spinup-evaluation

Install spinup-evaluation as normal and create a gen-setup.yaml that looks as so:

```gen-setup.yaml

mesh_mask: $REFERENCE/025deg_restart/restart25_arch/mesh_mask.nc
restart_files: 'generated_restart_C2'
```

```bash
spinup-eval \
  --sim-path ./generated/ \
  --config ./gen-setup.yaml \
  --mode restart
```
