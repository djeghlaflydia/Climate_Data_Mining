"""Shared helpers for the Algeria ERA5 climate-mining notebooks."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely import contains_xy

RAW_FILENAME = "era5_algeria_raw.nc"
BOUNDARY_FILENAME = "dz.json"


def find_project_root(start: str | Path | None = None) -> Path:
    """Find the project root regardless of whether Jupyter starts in root or notebooks/."""
    here = Path(start or Path.cwd()).resolve()
    candidates = [here, *here.parents]
    for candidate in candidates:
        if (candidate / "data" / "raw" / RAW_FILENAME).exists():
            return candidate
    raise FileNotFoundError(
        f"Could not find data/raw/{RAW_FILENAME}. Start Jupyter from the project root "
        "or from its notebooks/ directory."
    )


def load_boundary(project_root: str | Path | None = None):
    """Read and merge Algeria GeoJSON geometries (coordinates are lon/lat, WGS84)."""
    root = Path(project_root) if project_root else find_project_root()
    with (root / "data" / "raw" / BOUNDARY_FILENAME).open(encoding="utf-8") as f:
        geojson = json.load(f)
    geometries = [
        shape(feature["geometry"])
        for feature in geojson.get("features", [])
        if feature.get("geometry") is not None
    ]
    if not geometries:
        raise ValueError("The boundary GeoJSON does not contain any geometries.")
    geometry = unary_union(geometries)
    if geometry.is_empty or not geometry.is_valid:
        raise ValueError("The Algeria boundary geometry is empty or invalid.")
    return geometry


def make_algeria_mask(ds: xr.Dataset, project_root: str | Path | None = None):
    """Build a Boolean grid mask using strict polygon containment at grid-cell centers."""
    geometry = load_boundary(project_root)
    lon2d, lat2d = np.meshgrid(ds["longitude"].values, ds["latitude"].values)
    mask = contains_xy(geometry, lon2d, lat2d)
    mask_da = xr.DataArray(
        mask,
        dims=("latitude", "longitude"),
        coords={"latitude": ds["latitude"], "longitude": ds["longitude"]},
        name="algeria_polygon_mask",
        attrs={
            "description": "True when the grid-cell center is strictly inside the Algeria GeoJSON polygon",
            "boundary_rule": "strict contains; cells whose centers lie exactly on the boundary are excluded",
            "coordinate_reference": "WGS84 longitude/latitude (GeoJSON convention)",
        },
    )
    return mask_da, geometry


def load_masked_dataset(project_root: str | Path | None = None):
    """Open the raw NetCDF, create the country mask, and mask cells outside Algeria.

    The returned Dataset remains lazy until values are accessed or loaded.
    Returns (dataset, mask, boundary_geometry).
    """
    root = Path(project_root) if project_root else find_project_root()
    ds = xr.open_dataset(root / "data" / "raw" / RAW_FILENAME)
    mask, geometry = make_algeria_mask(ds, root)
    return ds.where(mask), mask, geometry


def area_weights(latitude: xr.DataArray) -> xr.DataArray:
    """Approximate relative grid-cell area weights for a regular lon/lat grid."""
    weights = np.cos(np.deg2rad(latitude))
    return weights.clip(min=0)


def area_weighted_mean(da: xr.DataArray, mask: xr.DataArray) -> xr.DataArray:
    """Compute a time-aware cosine(latitude)-weighted average over masked grid cells.

    The denominator is calculated separately for each time step and excludes cells
    that are missing for that variable, avoiding bias from a fixed missing-value count.
    """
    weights = area_weights(da["latitude"]).broadcast_like(mask).where(mask)
    valid_weights = weights.where(da.notnull())
    numerator = (da * weights).sum(dim=("latitude", "longitude"), skipna=True)
    denominator = valid_weights.sum(dim=("latitude", "longitude"), skipna=True)
    result = numerator / denominator
    result.attrs = dict(da.attrs)
    result.attrs["spatial_aggregation"] = "cos(latitude)-weighted mean over polygon mask"
    return result


def regional_time_series(ds: xr.Dataset, mask: xr.DataArray) -> pd.DataFrame:
    """Return an area-weighted monthly regional time series for each data variable."""
    columns = {}
    for name, da in ds.data_vars.items():
        if {"latitude", "longitude"}.issubset(da.dims):
            columns[name] = area_weighted_mean(da, mask).values
    frame = pd.DataFrame(columns, index=pd.to_datetime(ds["valid_time"].values))
    frame.index.name = "valid_time"
    return frame


def to_analysis_units(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert selected variables to convenient units without changing raw data."""
    out = frame.copy()
    for name in ("t2m", "d2m"):
        if name in out:
            out[name] = out[name] - 273.15  # Kelvin -> degrees Celsius
    for name in ("tp", "ro"):
        if name in out:
            out[name] = out[name] * 1000.0  # meters of water -> millimeters
    if {"u10", "v10"}.issubset(out.columns):
        out["wind10_speed"] = np.hypot(out["u10"], out["v10"])
    return out
