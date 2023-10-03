import stitches

import pandas as pd
import pkg_resources
import xarray as xr
import numpy as np
import seaborn as sns

import intake
import fsspec


def get_template_arr(full_arr: xr.DataArray):
    """
    Returns a xarray in with the same coords, dims and chunks as the output from the map_blocks function
    in conjunction with `annual_area_weighted_mean`. This is done so that Dask can pre-specify the
    output specifications.

    :param full_arr: xr.DataArray
        What will be passed to `map_blocks`, a chunked xr.DataArray with coords lat, lon, time, region
    :return: template: xr.DataArray
        An empty xarray of the form of the output of `map_blocks`
    """
    # Get example of the output after doing the coarsening and getting annual values
    template = full_arr[dict(region=1)].mean(("lon", "lat")).coarsen(time=12).mean()['pr'].chunk({'time': -1})

    # Particularly need the time array, and we know there are 43 regions 0-43
    # Also want one chunk per region as is input to the map_blocks func
    template = xr.DataArray(dims = ['time', 'region'],
                            coords = {
                                'time': template['time'],
                                'region': np.arange(0,43)
                            }).chunk({'time': -1, 'region': 1})

    # Return template
    return template


def annual_area_weighted_mean(grid_data: xr.Dataset, variable_name: str):
    """
    Takes a dataset with coordinates for latitude, longitude and time, and returns the weighted
    average of every grid cell over the globe, for each year. This is generally used when the grid
    is masked by region.

    :param grid_data: xr.Dataset
        An xr.Dataset with lat, lon, time
    :param variable_name: str
        The name of the variable of interest in the data
    :return: annual_weighted_mean: xr.DataArray
        The weighted average of every grid cell per year as a xr.DataArray with dims time
    """
    # Latitude coordinates vector
    lats = grid_data['lat']

    # Grid cell area estimation by latitude. Used as weighting
    area = np.cos(np.deg2rad(lats))
    area.name = 'weights'

    # Return weighted aggregation in the given region, and for each year
    return grid_data.weighted(area).mean(("lon", "lat")).coarsen(time=12).mean()[variable_name]


def format_aoi_values(aoi_arr: xr.DataArray, file_list, file_index: int, aoi_labels):
    # Convert to pd.Dataframe
    aoi_arr.name = 'pr'
    aoi_yearly_df = aoi_arr.to_dataframe().reset_index().copy()

    # Keep Year from the time column
    aoi_yearly_df['year'] = aoi_yearly_df['time'].apply(lambda t: t.year).copy()
    aoi_yearly_df = aoi_yearly_df.drop('time', axis=1).copy()

    # Label ESM, experiment, ensemble ID and variable
    aoi_yearly_df['esm'] = file_list.iloc[file_index].model
    aoi_yearly_df['experiment'] = file_list.iloc[file_index].experiment
    aoi_yearly_df['ensemble'] = file_list.iloc[file_index].ensemble
    aoi_yearly_df['variable'] = file_list.iloc[file_index].variable

    # Convert 0-43 region number to actual region name and ID
    aoi_yearly_df = aoi_yearly_df.merge(aoi_labels, on='region', how='left').drop(['region'], axis=1).copy()

    # Return result
    return aoi_yearly_df
