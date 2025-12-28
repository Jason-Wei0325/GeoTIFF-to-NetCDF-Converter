"""
Convert daily GeoTIFF files into yearly NetCDF files.

This script:
1. Reads daily GeoTIFF ET raster files.
2. Groups files by year based on filename prefix (YYYY).
3. Stacks daily rasters into a 3D array (time, lat, lon).
4. Writes one NetCDF file per year using CF-style conventions.

Assumptions:
- GeoTIFF filenames start with YYYYDDD (year + day of year).
- All GeoTIFFs within the same year share identical spatial
  resolution, extent, and projection.
- The raster represents daily evapotranspiration (ET).

Dependencies:
- GDAL
- netCDF4
- NumPy
"""

import os
import glob
import numpy as np
from osgeo import gdal
import netCDF4 as nc

# Enable GDAL exceptions for clearer error reporting
gdal.UseExceptions()

# =============================================================================
# Path configuration
# =============================================================================
tif_dir = r"***"
out_dir = r"***"
os.makedirs(out_dir, exist_ok=True)

# =============================================================================
# Collect all GeoTIFF files
# =============================================================================
tif_files = sorted(glob.glob(os.path.join(tif_dir, "*.tif")))

# =============================================================================
# Group GeoTIFF files by year (YYYY from filename)
# =============================================================================
files_by_year = {}
for f in tif_files:
    year = int(os.path.basename(f)[:4])
    files_by_year.setdefault(year, []).append(f)

# =============================================================================
# Process each year independently
# =============================================================================
for year, files in files_by_year.items():
    files = sorted(files)
    ndays = len(files)
    print(f"Processing {year}, {ndays} files")

    # -------------------------------------------------------------------------
    # Read spatial reference from the first GeoTIFF
    # -------------------------------------------------------------------------
    ds0 = gdal.Open(files[0])
    band0 = ds0.GetRasterBand(1)

    nlon = ds0.RasterXSize
    nlat = ds0.RasterYSize
    geotrans = ds0.GetGeoTransform()
    proj = ds0.GetProjection()

    # Compute 1D longitude and latitude coordinates (cell centers)
    x0, dx, _, y0, _, dy = geotrans
    lon = x0 + dx * (np.arange(nlon) + 0.5)
    lat = y0 + dy * (np.arange(nlat) + 0.5)

    ds0 = None

    # -------------------------------------------------------------------------
    # Pre-allocate arrays for performance
    # -------------------------------------------------------------------------
    data_all = np.empty((ndays, nlat, nlon), dtype=np.float32)
    time_vals = np.empty(ndays, dtype=np.int32)

    # -------------------------------------------------------------------------
    # Read daily GeoTIFFs into memory
    # -------------------------------------------------------------------------
    for i, tif in enumerate(files):
        fname = os.path.basename(tif)

        # Extract day-of-year (DDD) directly from filename
        doy = int(fname[4:7])

        ds = gdal.Open(tif)
        data_all[i, :, :] = ds.ReadAsArray()
        time_vals[i] = doy
        ds = None

    # -------------------------------------------------------------------------
    # Create NetCDF file for the current year
    # -------------------------------------------------------------------------
    out_nc = os.path.join(out_dir, f"ET_{year}.nc")
    ds = nc.Dataset(out_nc, "w", format="NETCDF4")

    # Define dimensions
    ds.createDimension("time", ndays)
    ds.createDimension("lat", nlat)
    ds.createDimension("lon", nlon)

    # Coordinate variables
    lat_var = ds.createVariable("lat", "f8", ("lat",))
    lon_var = ds.createVariable("lon", "f8", ("lon",))
    time_var = ds.createVariable("time", "i4", ("time",))

    lat_var[:] = lat
    lon_var[:] = lon
    time_var[:] = time_vals

    lat_var.units = "degrees_north"
    lon_var.units = "degrees_east"
    time_var.calendar = "standard"
    time_var.long_name = "day of year"

    # -------------------------------------------------------------------------
    # Main data variable: ET
    # -------------------------------------------------------------------------
    et = ds.createVariable(
        "ET",
        "f4",
        ("time", "lat", "lon"),
        zlib=True,
        complevel=4,
        chunksizes=(1, nlat, nlon),
    )

    et[:, :, :] = data_all
    et.units = "mm/day"
    et.long_name = "Daily Evapotranspiration"
    et.grid_mapping = "crs"

    # -------------------------------------------------------------------------
    # Coordinate reference system (CRS)
    # -------------------------------------------------------------------------
    crs = ds.createVariable("crs", "i1")
    crs.spatial_ref = proj

    # -------------------------------------------------------------------------
    # Global attributes
    # -------------------------------------------------------------------------
    ds.title = "Daily Evapotranspiration"
    ds.year = str(year)
    ds.unit = "mm/d"

    ds.close()
    print(f"Saved: {out_nc}")

print("All years finished.")