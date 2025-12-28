# GeoTIFF-to-NetCDF-Converter
This repository provides a Python-based workflow for converting daily GeoTIFF evapotranspiration (ET) products into yearly NetCDF files. The implementation is designed for geospatial raster time series and emphasizes correctness, performance, and compatibility with common scientific data standards.

## Overview

The script reads daily GeoTIFF files, groups them by year, and stacks them along a time dimension to produce one NetCDF file per year. Spatial reference information, resolution, and extent are preserved. Temporal information is derived directly from the GeoTIFF filenames using day-of-year (DOY), allowing for non-continuous time series.

## Input Data

### File Naming Convention

Input GeoTIFF files must follow this naming pattern:

YYYYDDD.tif

Where:
- `YYYY` is the four-digit year
- `DDD` is the day of year (001–366)

Non-continuous DOY sequences are supported.

### Spatial Requirements

All GeoTIFF files within the same year must share:
- The same coordinate reference system (CRS)
- The same spatial resolution
- The same raster extent

## Output Data

### NetCDF File

One NetCDF file is generated per year:

ET_YYYY.nc

### Dimensions

- `time`: number of available days in the year
- `lat`: latitude
- `lon`: longitude

### Variables

- `ET (time, lat, lon)`  
  Daily evapotranspiration values, units: `mm/day`
- `lat (lat)`  
  Latitude coordinate, units: `degrees_north`
- `lon (lon)`  
  Longitude coordinate, units: `degrees_east`
- `time (time)`  
  Day of year (DOY)
- `crs`  
  Coordinate reference system information (CF-style)
