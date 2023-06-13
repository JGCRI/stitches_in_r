#!/usr/bin/env python
# coding: utf-8

# # curating  data for an area of interest
# 
# - easy to do a for a single AOI, just update and re-run script for different AOI.
# Inefficient as we start wanting to look at more.
# - Update code relative to `aoi_calculations.ipynb` to try to keep things grouped
# by region
# 
# 
# # Import general packages
# 

# In[1]:


import stitches as stitches


import pandas as pd
import pkg_resources
import xarray as xr
import numpy as np
import seaborn as sns

# Plotting options
sns.set(font_scale=1.3)
sns.set_style("white")
# For help with plotting
from matplotlib import pyplot as plt
get_ipython().run_line_magic('matplotlib', 'inline')
get_ipython().run_line_magic('config', "InlineBackend.figure_format = 'retina'")
plt.rcParams['figure.figsize'] = 12, 6
pd.set_option('display.max_columns', None)


# # import packages for spatial masking

# In[2]:


import geopandas as gpd
# Spatial subsetting of netcdf files:
import regionmask


# #  Set up time slices and area of interest (AOI) to focus on
# 
# - require ensemble average PR values over the ref period and comparison period
# for an area of interest
# - Do spatial aggregation for each ensemble member, take the time average in the
# time window, calculate average across ensemble members

# In[3]:


# Time slices
ref_start = 1980
ref_end =  2014

comp_start = 2015
comp_end =  2099



# In[4]:


# AOI
# working off https://www.earthdatascience.org/courses/use-data-open-source-python/hierarchical-data-formats-hdf/subset-netcdf4-climate-data-spatially-aoi/

# # physical land polygon files:
# url =  (    "https://naturalearth.s3.amazonaws.com/"
# "10m_physical/ne_10m_land.zip")

# # country URL
# url =  (    "https://naturalearth.s3.amazonaws.com/"
#             "10m_cultural/ne_10m_admin_0_countries.zip")

# # state/province URL
# url =  (    "https://naturalearth.s3.amazonaws.com/"
#             "10m_cultural/ne_10m_admin_1_states_provinces.zip")

# IPCC ar6 reference regions - including ocean regions
# actually have to download locally from
# https://github.com/IPCC-WG1/Atlas/blob/main/reference-regions/IPCC-WGI-reference-regions-v4_shapefile.zip
url =  (   'IPCC-WGI-reference-regions-v4_shapefile.zip')

land_main_gdf = gpd.read_file(url)


# In[5]:


IPCC_names  = land_main_gdf['Acronym'].unique()

land_main_gdf.plot()


# # specify ESMs, variables, experiments

# In[6]:


# The CMIP6 ESM we want to emulate and the variables we want to
# emulate
# NOTE IPSL and GFDL submitted results under grids labeled not `gn` so they
# are not included in the stitches patches data. To pull their ESMs, we have to
# source the pangeo table directly from pangeo and reshape it instead of using
# the stitches package data.

# # training ESMs
# esm = ['CAMS-CSM1-0', 'MIROC6', 'GFDL-ESM4', 'FGOALS-g3',
# 'MPI-ESM1-2-HR', 'MPI-ESM1-2-LR', 'MRI-ESM2-0',
# 'ACCESS-ESM1-5', 'IPSL-CM6A-LR', 'CESM2-WACCM',
# 'UKESM1-0-LL',
# 'CanESM5']

# out of sample ESMs
esm = [#'ACCESS-CM2',
       #'AWI-CM-1-1-MR',
       #'AWI-ESM-1-1-LR',
       #'BCC-CSM2-HR',
       #'BCC-CSM2-MR',
       #'BCC-ESM1',
       #'CESM1-1-CAM5-CMIP5',
       #'CESM1-WACCM-SC',
       #'CESM2',
       #'CESM2-FV2',
       #'CESM2-WACCM-FV2',
       #'CIESM',
       #'CMCC-CM2-HR4',
       #'CMCC-CM2-SR5',
       #'CMCC-CM2-VHR4',
       #'CMCC-ESM2',
       #'CNRM-CM6-1',
       #'CNRM-CM6-1-HR',
       #'CNRM-ESM2-1',
       #'CanESM5-CanOE',
       #'E3SM-1-0',
       #'E3SM-1-1',
       #'E3SM-1-1-ECA',
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
       #'HadGEM3-GC31-LL',
       # 'NorESM2-LM'
       ]

vars1 = ['tas']

exps = ['historical',
        'ssp126', 'ssp245', 'ssp370',  'ssp585',
        'ssp460', 'ssp119',   'ssp434', 'ssp534-over']


# # Pull pangeo dataframe with netcdf addresses for above

# In[7]:


# pangeo table of ESMs for reference
pangeo_data = stitches.fx_pangeo.fetch_pangeo_table()


# In[8]:


pangeo_data.sort_values('source_id').source_id.unique()


# In[9]:


pangeo_data = pangeo_data[(pangeo_data['source_id'].isin(esm)) &
                           (pangeo_data['variable_id'].isin(vars1)) &(pangeo_data['table_id'] == 'Amon')&
                           ((pangeo_data['experiment_id'].isin(exps)))].copy()

# reshape to look like package data but with the ESMs we want to include
pangeo_data = pangeo_data[["source_id", "experiment_id", "member_id", "variable_id", "grid_label",
                                                        "zstore", "table_id"]].copy()
pangeo_data = pangeo_data.rename(columns={"source_id": "model", "experiment_id": "experiment",
                                                "member_id": "ensemble", "variable_id": "variable",
                                                "zstore": "zstore", "table_id": "domain"}).reset_index(drop = True).copy()

 # keep only p1 runs:
# UK model only does f2 runs for some reason
ukesm_data =  pangeo_data[pangeo_data['model'].str.contains('UKESM')].copy()
ukesm_data = ukesm_data[ukesm_data['ensemble'].str.contains('i1p1f2')].copy()

# everyone else does f1 runs
pangeo_data = pangeo_data[pangeo_data['ensemble'].str.contains('i1p1f1')].copy()

# combine UKESM with other models
pangeo_data = pd.concat([pangeo_data, ukesm_data]).reset_index(drop=True).copy()


# # loop over files and do calculations

# In[10]:


aoi = land_main_gdf.reset_index(drop=True).copy()
aoi = aoi[aoi['Type']!= 'Ocean'].copy()
aoi = aoi[aoi['Continent'] != 'POLAR'].reset_index(drop=True).copy()

aoi_labels = aoi[['Continent', 'Type', 'Name', 'Acronym']].copy()
aoi_labels = aoi_labels.rename(columns={'Continent':'continent',
                                        'Type':'type',
                                        'Name':'name',
                                        'Acronym':'acronym'}).copy()
aoi_labels['region'] = aoi_labels.index.copy()


# In[ ]:


#Updated

varname = vars1[0]

for esmname in esm:
  timeseries_holder = pd.DataFrame()
  for exp in exps:

    print(esmname)
    print(exp)

    filelist1 = pangeo_data[(pangeo_data['model'] ==esmname)].copy()
    filelist = filelist1[(filelist1['experiment'] == exp)].copy()

    if filelist.empty:
        print('no ensemble members for this exp')
        annual_aoi = pd.DataFrame()
        # end if no files for experiment

    if (not filelist.empty) & (len(filelist1['experiment'].unique()) > 1): #if an ESM only did historical, then this won't be >1 and we don't care, skip
        for i in range(len(filelist)):
            print(i)

            annual_aoi = pd.DataFrame()

            # Load data:
            x = stitches.fx_pangeo.fetch_nc(filelist.iloc[i].zstore)
            x = x.sortby('time').copy()

            # If it's the first ensemble member, set up the mask
            if (i==0):
                aoi_mask = regionmask.mask_3D_geopandas(aoi,
                                                        x.lon,
                                                        x.lat)
                # end if i==0 set up aoi_mask

            # mask the file
            x = x.where(aoi_mask).copy()

            # If the experiment is historical, further slice to reference years.
            # Otherwise, slice to comparison years:
            if (exp == 'historical'):
                window_length = ref_end-ref_start+1
                if(esmname == 'UKESM1-0-LL'):
                    x = x.sel(time=slice(str(ref_start)+'-01-01',
                                         '2014-12-30')).copy()
                if(esmname != 'UKESM1-0-LL'):
                    x = x.sel(time=slice(str(ref_start)+'-01-01',
                                         str(ref_end)+'-12-31')).copy()

            if (exp!='historical'):
                window_length = comp_end-comp_start +1
                if(esmname == 'UKESM1-0-LL'):
                    x = x.sel(time=slice(str(comp_start)+'-01-01',
                                         '2099-12-30')).copy()
                if(esmname != 'UKESM1-0-LL'):
                    x = x.sel(time=slice(str(comp_start)+'-01-01',
                                         str(comp_end)+'-12-31')).copy()

                # end if checks for time slicing

            # Check if there are the correct number of time steps in this
            # sliced data:
            # Very rough QC for checking complete netcdfs and assumes
            # comparison window and reference window same length.
            if (len(x.time) >= 12*window_length):

                for name, group in x.groupby('region'):
                    # aggregate to the region for each month, then calculate annual avg and reshape
                    lat = group['lat']
                    area = np.cos(np.deg2rad(lat))
                    area.name = 'weights'
                    group = group.weighted(area).mean(("lon", "lat")).coarsen(time=12).mean()\
                        [varname].to_dataframe().reset_index().copy()
                    if 'height' in group.columns:
                        group = group.drop(columns='height').copy()
                    annual_aoi = pd.concat([annual_aoi, group]).reset_index(drop=True).copy()
                    del(lat)
                    del(area)
                    # end for loop over regions

                # add labeling
                annual_aoi = annual_aoi.rename(columns={'tas':'ann_agg'}).copy()
                annual_aoi['year'] = annual_aoi['time'].apply(lambda x: x.year).copy()
                annual_aoi = annual_aoi.drop('time', axis=1).copy()
                annual_aoi['esm'] = filelist.iloc[i].model
                annual_aoi['experiment'] =  filelist.iloc[i].experiment
                annual_aoi['ensemble'] = filelist.iloc[i].ensemble
                annual_aoi['variable'] = filelist.iloc[i].variable
                annual_aoi = annual_aoi.merge(aoi_labels, on = 'region', how = 'left').drop(['region'], axis=1).copy()
                timeseries_holder = pd.concat([timeseries_holder, annual_aoi]).reset_index(drop=True).copy()
                # end check if is complete data file and subsequent aggregations
                del(annual_aoi)
                del(window_length)

            # end for loop over file list

    del(filelist)

    # end loop over experiments
  timeseries_holder.to_csv(('extracted_timeseries/IPCC_land_regions_'+ varname+ '_' + esmname +'_timeseries_' + str(ref_start) + '_' + str(comp_end) +'.csv'), index=False)

# end loop over esms



# In[ ]:


# df = pd.read_csv('IPCC_land_regions_tas_allesms_timeseries_1980_2099.csv')
# df = pd.read_csv('xarray_test.csv')
#
# compare = timeseries_holder.merge(df,
#                                   on = ['year', 'esm', 'experiment', 'ensemble', 'variable',
#                                         'continent',	'type',	'name',	'acronym'],
#                                   how = 'left').copy()
#
# np.max(np.abs(compare.ann_agg_x-compare.ann_agg_y))

