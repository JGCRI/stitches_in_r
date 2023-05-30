import stitches

import pandas as pd
import pkg_resources
import xarray as xr
import numpy as np
import seaborn as sns

import geopandas as gpd
# Spatial subsetting of netcdf files:
import regionmask
import intake
import fsspec

if __name__ == "__main__":

    warnings.filterwarnings("ignore")

    # Time slices
    ref_start = 1980
    ref_end =  2014
    comp_start = 2015
    comp_end =  2099

    # IPCC Regions
    url = 'IPCC-WGI-reference-regions-v4_shapefile.zip'
    land_main_gdf = gpd.read_file(url)
    IPCC_names  = land_main_gdf['Acronym'].unique()

    # Lists of models, variables and experiments to extract
    # Models
    esms = ['CAMS-CSM1-0', 'MIROC6', 'GFDL-ESM4', 'FGOALS-g3',
    'MPI-ESM1-2-HR', 'MPI-ESM1-2-LR', 'MRI-ESM2-0',
    'ACCESS-ESM1-5', 'IPSL-CM6A-LR', 'CESM2-WACCM',
    'UKESM1-0-LL',
    'CanESM5']
    # variables
    vars = ['pr', 'tas']
    # experiments
    exps = ['historical',
            'ssp126', 'ssp245', 'ssp370',  'ssp585',
            'ssp460', 'ssp119',   'ssp434', 'ssp534-over']

    # Pangeo table
    url = "https://storage.googleapis.com/cmip6/pangeo-cmip6.json"
    out = intake.open_esm_datastore(url)
    # Initial pangeo table of ESMs for reference
    pangeo_data = stitches.fx_pangeo.fetch_pangeo_table()

    # Extracting just the desired models, variables, scenarios we want
    pangeo_data = pangeo_data[(pangeo_data['source_id'].isin(esm)) &
                            (pangeo_data['variable_id'].isin(vars1)) &
                            (pangeo_data['table_id'] == 'Amon') &
                            (pangeo_data['experiment_id'].isin(exps))].copy()

    # reshape to look like package data but with the ESMs we want to include
    pangeo_data = pangeo_data[["source_id", "experiment_id", "member_id", "variable_id", "grid_label",
                                                            "zstore", "table_id"]].copy()
    pangeo_data = pangeo_data.rename(columns={"source_id": "model", "experiment_id": "experiment",
                                                    "member_id": "ensemble", "variable_id": "variable",
                                                    "zstore": "zstore", "table_id": "domain"}).reset_index(drop = True).copy()

    # keep only p1 runs:
    # UK model only does f2 runs for some reason
    # What are f2 vs f1 runs?
    ukesm_data =  pangeo_data[pangeo_data['model'].str.contains('UKESM')].copy()
    ukesm_data = ukesm_data[ukesm_data['ensemble'].str.contains('i1p1f2')].copy()

    # everyone else does f1 runs
    pangeo_data = pangeo_data[pangeo_data['ensemble'].str.contains('i1p1f1')].copy()

    # combine UKESM with other models
    pangeo_data = pd.concat([pangeo_data, ukesm_data]).reset_index(drop=True).copy()

    # List of possible ensemble members
    ensembles = np.unique(pangeo_data.ensemble.values)

    # Formatting regions
    aoi = land_main_gdf.reset_index(drop=True).copy()
    aoi_labels = aoi[['Continent', 'Type', 'Name', 'Acronym']].copy()
    aoi_labels = aoi_labels.rename(columns={'Continent':'continent',
                                            'Type':'type',
                                            'Name':'name',
                                            'Acronym':'acronym'}).copy()
    aoi_labels['region'] = aoi_labels.index.copy()

    # Helper functions

    # Get template output
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
                                    'region': np.arange(0,len(aoi))
                                }).chunk({'time': -1, 'region': 1})

        # Return template
        return template

    # Get annual weighted mean
    def annual_area_weighted_mean(grid_data: xr.Dataset, variable_name: str):
        lats = grid_data['lat']
        area = np.cos(np.deg2rad(lats))
        area.name = 'weights'
        # I don't think it's off by a factor of 10, but I think technically we should be weighting months by their length
        # Not sure how much it will change but 31 != 30 != 29 != 28 which are all possible days in a month. Plus there
        # are the strange calendars with different month numbers, so we should try to be consistent.
        return grid_data.weighted(area).mean(("lon", "lat")).coarsen(time=12).mean()[variable_name]

    # Dataframe format of output
    def format_aoi_values(aoi_arr: xr.DataArray, variable, file_list, file_index: int, labels):
        # Convert to pd.Dataframe
        aoi_arr.name = variable
        aoi_yearly_df = aoi_arr.to_dataframe().reset_index().copy()

        # Keep Year from the time column
        aoi_yearly_df['year'] = aoi_yearly_df['time'].apply(lambda t: t.year).copy()
        aoi_yearly_df = aoi_yearly_df.drop('time', axis=1).copy()

        # Label ESM, experiment, ensemble ID and variable
        aoi_yearly_df['esm'] = file_list.iloc[file_index].model
        aoi_yearly_df['experiment'] =  file_list.iloc[file_index].experiment
        aoi_yearly_df['ensemble'] = file_list.iloc[file_index].ensemble
        aoi_yearly_df['variable'] = file_list.iloc[file_index].variable

        # Convert 0-43 region number to actual region name and ID
        aoi_yearly_df = aoi_yearly_df.merge(labels, on ='region', how ='left').drop(['region'], axis=1).copy()

        # Return result
        return aoi_yearly_df

    # Primary function for extracting time series
    def get_time_series(model, experiment, ensemble, variable, aois, aoi_labs):
        # Get url for given inputs
        file_list = pangeo_data[(pangeo_data['model'] == model) &
                                (pangeo_data['experiment'] == experiment) &
                                (pangeo_data['ensemble'] == ensemble) &
                                (pangeo_data['variable'] == variable)]

        # Empty result
        mean_by_year_region_df = pd.DataFrame(columns=[variable, 'year', 'esm', 'experiment', 'ensemble', 'variable', 'continent', 'type', 'name', 'acronym'])

        # If no matches return empty
        if file_list.empty:
            return mean_by_year_region_df

        # The url now that we know it exists
        file_url = file_list.iloc[0].zstore

        # Open data
        matched_data = stitches.fx_pangeo.fetch_nc(file_url)
        matched_data = matched_data.sortby('time').copy()

        # Get masks for regions
        region_masks = regionmask.mask_3D_geopandas(aois, matched_data.lon, matched_data.lat)
        matched_data = matched_data.where(region_masks).copy()

        # If the experiment is historical, further slice to reference years.
        # Otherwise, slice to comparison years:
        # What is with this UKESM1-0-LL ESM?
        # Why are we doing this weird slicing?
        win_len = comp_end - comp_start + 1
        if experiment == 'historical':
            win_len = ref_end - ref_start + 1
            if model == 'UKESM1-0-LL':
                matched_data = matched_data.sel(time=slice(str(ref_start) + '-01-01',
                                    '2014-12-30')).copy()
            if model != 'UKESM1-0-LL':
                matched_data = matched_data.sel(time=slice(str(ref_start) + '-01-01',
                                                        str(ref_end) +'-12-31')).copy()

        if experiment != 'historical':
            if model == 'UKESM1-0-LL':
                matched_data = matched_data.sel(time=slice(str(comp_start) + '-01-01',
                                    '2099-12-30')).copy()
            if model != 'UKESM1-0-LL':
                matched_data = matched_data.sel(time=slice(str(comp_start) + '-01-01',
                                                        str(comp_end) +'-12-31')).copy()

        if len(matched_data.time) >= 12 * win_len:

            # Force download of data and set each region to one chunk
            matched_data = matched_data.persist().chunk({'lon': -1, 'lat': -1, 'time': -1, 'region': 1}).copy()

            # Template for map_blocks
            template = get_template_arr(matched_data)

            # For each region (which is a single chunk), get the annual mean values (weighted by area) for each year
            mean_by_year_region_arr = xr.map_blocks(annual_area_weighted_mean, matched_data, kwargs={'variable_name': 'pr'}, template = template)
            mean_by_year_region_arr.compute()

            # Format resulting data
            mean_by_year_region_df = format_aoi_values(mean_by_year_region_arr, variable, file_list, 0, aoi_labs)

        matched_data.close()
        del matched_data

        return mean_by_year_region_df

    # Iterate over all combinations and get time series
    results = [get_time_series(a, b, c, d, aoi, aoi_labels) for a in esms for b in exps for c in ensembles for d in vars]

    # Concatenate output
    comb_results = pd.concat(results).reset_index(drop=True)

    # Write out result
    comb_results.to_csv(('extracted_timeseries/IPCC_all_regions_and_data.csv'), index=False)