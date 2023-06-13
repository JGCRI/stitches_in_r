import stitches

import sys

from dask.distributed import Client, LocalCluster
import dask

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

    # Task index from SLURM array to run specific model
    task_id = int(sys.argv[1])

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
    esms = ['ACCESS-CM2',
       'AWI-CM-1-1-MR',
       'AWI-ESM-1-1-LR',
       'BCC-CSM2-HR',
       'BCC-CSM2-MR',
       'BCC-ESM1',
       'CESM1-1-CAM5-CMIP5',
       'CESM1-WACCM-SC',
       'CESM2',
       'CESM2-FV2',
       'CESM2-WACCM-FV2',
       'CIESM',
       'CMCC-CM2-HR4',
       'CMCC-CM2-SR5',
       'CMCC-CM2-VHR4',
       'CMCC-ESM2',
       'CNRM-CM6-1',
       'CNRM-CM6-1-HR',
       'CNRM-ESM2-1',
       'CanESM5-CanOE',
       'E3SM-1-0',
       'E3SM-1-1',
       'E3SM-1-1-ECA',
       'EC-Earth3',
       'EC-Earth3-AerChem',
       'EC-Earth3-CC',
       'EC-Earth3-LR',
       'EC-Earth3-Veg',
       'EC-Earth3-Veg-LR',
       'EC-Earth3P',
       'EC-Earth3P-HR',
       'EC-Earth3P-VHR',
       'ECMWF-IFS-HR',
       'ECMWF-IFS-LR',
       'FGOALS-f3-H',
       'FGOALS-f3-L',
       'FIO-ESM-2-0',
       'GFDL-AM4',
       'GFDL-CM4',
       'GFDL-CM4C192',
       'GFDL-ESM2M',
       'GFDL-OM4p5B',
       'GISS-E2-1-G',
       'GISS-E2-1-G-CC',
       'GISS-E2-1-H',
       'GISS-E2-2-G',
       'GISS-E2-2-H',
       'HadGEM3-GC31-HM',
       'HadGEM3-GC31-LL',
       'HadGEM3-GC31-LM',
       'HadGEM3-GC31-MM',
       'ICON-ESM-LR',
       'IITM-ESM',
       'INM-CM4-8',
       'INM-CM5-0',
       'INM-CM5-H',
       'IPSL-CM5A2-INCA',
       'IPSL-CM6A-ATM-HR',
       'IPSL-CM6A-LR-INCA',
       'KACE-1-0-G',
       'KIOST-ESM',
       'MCM-UA-1-0',
       'MIROC-ES2H',
       'MIROC-ES2L',
       'MPI-ESM-1-2-HAM',
       'MPI-ESM1-2-XR',
       'MRI-AGCM3-2-H',
       'MRI-AGCM3-2-S',
       'MRI-ESM2-0',
       'NESM3',
       'NorCPM1',
       'NorESM1-F',
       'NorESM2-MM',
       'SAM0-UNICON',
       'TaiESM1'
       'HadGEM3-GC31-LL',
       'NorESM2-LM'
       ]
    esm = esms[task_id]
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
    pangeo_data = pangeo_data[(pangeo_data['source_id'].isin(esms)) &
                            (pangeo_data['variable_id'].isin(vars)) &
                            (pangeo_data['table_id'] == 'Amon') &
                            (pangeo_data['experiment_id'].isin(exps))].copy()

    # reshape to look like package data but with the ESMs we want to include
    pangeo_data = pangeo_data[["source_id", "experiment_id", "member_id", "variable_id", "grid_label",
                                                            "zstore", "table_id"]].copy()
    pangeo_data = pangeo_data.rename(columns={"source_id": "model", "experiment_id": "experiment",
                                                    "member_id": "ensemble", "variable_id": "variable",
                                                    "zstore": "zstore", "table_id": "domain"}).reset_index(drop = True).copy()


    # keep only p1 runs:
    # Except for UK model only does f2 runs for some reason
    if esm.contains('UKESM'):
        pangeo_data = pangeo_data[pangeo_data['ensemble'].str.contains('i1p1f2')].copy().reset_index(drop=True).copy()
    else:
        pangeo_data = pangeo_data[pangeo_data['ensemble'].str.contains('i1p1f1')].copy().reset_index(drop=True).copy()


    # List of possible ensemble members
    ensembles = np.unique(pangeo_data.ensemble.values)

    # Formatting regions
    aoi = land_main_gdf.reset_index(drop=True).copy()
    # Getting rid of oceans and polar regions
    aoi = aoi[aoi['Type']!= 'Ocean'].copy()
    aoi = aoi[aoi['Continent'] != 'POLAR'].reset_index(drop=True).copy()
    aoi_labels = aoi[['Continent', 'Type', 'Name', 'Acronym']].copy()
    aoi_labels = aoi_labels.rename(columns={'Continent':'continent',
                                            'Type':'type',
                                            'Name':'name',
                                            'Acronym':'acronym'}).copy()
    aoi_labels['region'] = aoi_labels.index.copy()

    # Helper functions

    # Get template output
    def get_template_arr(full_arr: xr.DataArray, variable: str):
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
        template = full_arr[dict(region=1)].mean(("lon", "lat")).coarsen(time=12).mean()[variable].chunk({'time': -1})

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

        # Remove random extra height coordinate in some datasets which does nothing
        try:    
            matched_data = matched_data.drop_vars('height')
        except:
            pass
        matched_data

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
            template = get_template_arr(matched_data, variable)

            # For each region (which is a single chunk), get the annual mean values (weighted by area) for each year
            mean_by_year_region_arr = xr.map_blocks(annual_area_weighted_mean, matched_data, kwargs={'variable_name': variable}, template = template)
            mean_by_year_region_arr.compute()

            # Format resulting data
            mean_by_year_region_df = format_aoi_values(mean_by_year_region_arr, variable, file_list, 0, aoi_labs)

        matched_data.close()
        del matched_data

        mean_by_year_region_df = mean_by_year_region_df.rename(columns={variable: 'value'})

        return mean_by_year_region_df

    # Getting tas
    # Iterate over all combinations and get time series
    results = [get_time_series(esm, b, c, 'tas', aoi, aoi_labels) for b in exps for c in ensembles]

    # Concatenate output
    comb_results = pd.concat(results).reset_index(drop=True)

    # Write out result
    comb_results.to_csv((f'extracted_timeseries/IPCC_all_regions_tas_{esm}_{ref_start}-{ref_end}.csv'), index=False)

    # Iterate over all combinations and get time series
    results = [get_time_series(esm, b, c, 'pr', aoi, aoi_labels) for b in exps for c in ensembles]

    # Concatenate output
    comb_results = pd.concat(results).reset_index(drop=True)

    # Write out result
    comb_results.to_csv((f'extracted_timeseries/IPCC_all_regions_pr_{esm}_{ref_start}-{ref_end}.csv'), index=False)