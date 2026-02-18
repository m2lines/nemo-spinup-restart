
Key insight: Pre-existing template lat and lon values do not matter. Mesh mask is the authoritative grid definition and we overwrite the coordinates with mask.glamt and mask.gphit values. 

---

## Regrid.py Algorithm

### `upscale_predictions()`
1. Load numpy predictions (toce, soce, ssh) at specified time index
2. Create coarse restart: `create_restart_from_predictions()`
3. Regrid to fine resolution: `regrid_restart()`
4. Return path to fine restart file

### `create_restart_from_predictions()`
1. Load template restart and mesh mask
2. Extract depth from mask (`gdept_0`)
3. Compute potential density using NEMO equation of state
4. Populate restart fields: tb/tn, sb/sn, sshb/sshn, rhop
5. Update metadata and save to NetCDF

### `regrid_restart()`

**Phase 1: Load & Prepare**
1. Load coarse/fine restarts and masks
2. Assign lon/lat coords to restarts from masks (glamt/gphit)
3. Save intermediate: `restart_lr.nc`, `restart_hr_template.nc`

**Phase 2: Extrapolate Coarse**
4. Call `extrapolate_to_land(restart_lr, mask_lr)`
5. Save intermediate: `restart_lr_extrap.nc`

**Phase 3: Regrid**
6. Create xESMF regridder (bilinear, nearest_s2d extrapolation)
7. Apply regridding: `restart_hr = regridder(restart_lr_extrap)`
8. Save intermediate: unmasked fine restart

**Phase 4: Cleanup Coordinates**
9. Rename lat→nav_lat, lon→nav_lon
10. Drop x, y coordinate variables

**Phase 5: Apply Fine Mask**
11. Prepare fine mask (align nav_lev, drop x/y/time)
12. Mask all variables (set land to 0.0)

**Phase 6: Finalize**
13. Zero all velocities (ub/un/vb/vn)
14. Copy time metadata from coarse (kt, ndastp, adatrj, ntime)
15. Copy timestep from fine template (rdt)
16. Reorder variables to match template
17. Update file metadata and save

### `extrapolate_to_land()`
1. Prepare mask (squeeze, drop x/y/time_counter, align nav_lev)
2. Create 2D surface mask
3. Apply mask to set land to NaN (3D and 4D variables)
4. Extrapolate along x-dimension (nearest neighbor)
5. Extrapolate along y-dimension (nearest neighbor)
6. Return extrapolated restart

**Note:** No vertical extrapolation performed (~12k NaNs remain in deep ocean)

### Key Design Choices
- **Coordinates from mask:** Always overwrite restart coords with glamt/gphit  
- **xESMF requirements:** Needs lon/lat named coordinates for geographic interpolation
- **Dimension-based masking:** `.where()` broadcasts on dimension names (y, x), not coord values.
- **Conservative velocities:** Zero out for NEMO to recompute from density
- **Two-stage extrapolation:** Fill land before regridding to avoid NaN propagation

