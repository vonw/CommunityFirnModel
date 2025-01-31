#!/usr/bin/env python
'''
writer.py
=========

Functions for writing model outputs.
'''

import csv
import os
import numpy as np
import h5py
from constants import *
import xarray as xr

def write_nospin_hdf5(self,Mout_dict,forcing_dict=None):
    '''
    Write the results fromt the main model run to hdf file.

    Parameters
    ----------
    Mout_dict: dict
        contains all of the model outputs; each key is the name of the output 
    '''

    f4 = h5py.File(os.path.join(self.c['resultsFolder'], self.c['resultsFileName']),'w')

    for VW in Mout_dict.keys():

        if VW == 'rho': 
            wn = 'density'
        elif VW == 'Tz':
            wn = 'temperature'
        elif VW == 'z':
            wn = 'depth'
        elif VW == 'age':
            Mout_dict[VW] = Mout_dict[VW]/S_PER_YEAR
            wn = 'age'
        elif VW == 'climate':
            wn = 'Modelclimate'
        elif VW == 'Hx':
            wn = 'temp_Hx'
        else:
            wn = VW

        f4.create_dataset(wn, data = Mout_dict[VW])

    if forcing_dict:
        ks = list(forcing_dict)
        ll = len(forcing_dict[ks[0]])
        forcing_out = np.zeros([ll,5])
        forcing_out[:,0] = forcing_dict['dectime']
        forcing_out[:,1] = forcing_dict['TSKIN']
        forcing_out[:,2] = forcing_dict['BDOT']
        try:
            forcing_out[:,3] = forcing_dict['SMELT']
        except:
            forcing_out[:,3] = -9999* np.ones_like(forcing_dict['dectime'])
        try:
            forcing_out[:,4] = forcing_dict['RAIN']
        except:
            forcing_out[:,4] = -9999* np.ones_like(forcing_dict['dectime'])
        f4.create_dataset('forcing',data=forcing_out,dtype='float64')

    f4.close()


def write_spin_hdf5(self):
    '''
    Write the model outputs to hdf file at the end of spin up.
    '''

    f5 = h5py.File(os.path.join(self.c['resultsFolder'], self.c['spinFileName']), 'w')

    f5.create_dataset('densitySpin', data = self.rho_time)
    f5.create_dataset('tempSpin', data = self.Tz_time)
    f5.create_dataset('ageSpin', data = self.age_time)
    f5.create_dataset('depthSpin', data = self.z_time)
    if self.c['physGrain']:
        f5.create_dataset('r2Spin', data = self.r2_time)
    if self.THist:
        f5.create_dataset('HxSpin', data = self.Hx_time)
    if self.c['isoDiff']:
        for isotope in self.c['iso']:
            f5.create_dataset('IsoSpin_{}'.format(isotope), data = self.iso_out[isotope])
            f5.create_dataset('iso_sig2_{}'.format(isotope), data = self.iso_sig2_out[isotope])
    if self.doublegrid:
        f5.create_dataset('gridSpin', data = self.grid_time)
    if self.c['MELT']: #VV
        f5.create_dataset('LWCSpin', data = self.LWC_time)
    # if self.write_bdot:
        # f5.create_dataset('bdot_meanSpin', data = self.bdot_mean_time)
    f5.close()

def SpinUpdate(self,mtime):
    '''
    Overwrite the variables in the spin file to whatever they are 
    at time = mtime

    Parameters
    ----------
    mtime: float
        Time (model time) at which the 
    '''

    spin_results = h5py.File(os.path.join(self.c['resultsFolder'], self.c['spinFileName']),'r+')
    
    spin_results['densitySpin'][:] = np.append(mtime,self.rho)
    spin_results['tempSpin'][:]    = np.append(mtime,self.Tz)
    spin_results['ageSpin'][:]     = np.append(mtime,self.age)
    spin_results['depthSpin'][:]   = np.append(mtime,self.z)

    try:
        spin_results.create_dataset('bdot_meanSpin',data = np.append(mtime,self.bdot_mean))
    except:
        spin_results['bdot_meanSpin'][:] = np.append(mtime,self.bdot_mean)

    if self.c['MELT']:
        try:
            spin_results.create_dataset('LWCSpin',data = np.append(mtime,self.LWC))
        except:
            spin_results['LWCSpin'][:] = np.append(mtime,self.LWC)

    if self.c['physGrain']:
        try:
            spin_results['r2Spin'][:] = np.append(mtime,self.r2)
        except:
            pass

    if self.c['physRho']=='Morris2014':
        spin_results['HxSpin'][:] = np.append(mtime,self.Hx)

    if self.c['isoDiff']:
        for isotope in self.c['iso']:
            spin_results['IsoSpin_{}'.format(isotope)][:]  = np.append(mtime, self.Isoz[isotope])
            spin_results['iso_sig2_{}'.format(isotope)][:] = np.append(mtime, self.Iso_sig2_z[isotope])

    if self.doublegrid:
        spin_results['gridSpin'][:] = np.append(mtime,self.gridtrack)

    spin_results.close()
    
def write_nospin_netcdf(self,Mout_dict,forcing_dict=None):
    '''
    Write the results from the main model run to netCDF file.

    Parameters
    ----------
    Mout_dict: dict
        contains all of the model outputs; each key is the name of the output 
    '''
    time  = Mout_dict['climate'][:,0]
    depth = Mout_dict['z']
    
    ds    = xr.Dataset(data_vars = {
                        'age':           (['time', 'depth'], Mout_dict['age']),
                        'density':       (['time', 'depth'], Mout_dict['rho']),
                        'temperature':   (['time', 'depth'], Mout_dict['Tz']),
                        'LWC':           (['time', 'depth'], Mout_dict['LWC']),
                        'iso_sig2_d18O': (['time', 'depth'], Mout_dict['iso_sig2_d18O']),
                        'iso_sig2_dD':   (['time', 'depth'], Mout_dict['iso_sig2_dD']),
                        'isotopes_d18O': (['time', 'depth'], Mout_dict['isotopes_d18O']),
                        'isotopes_dD':   (['time', 'depth'], Mout_dict['isotopes_dD']),
                        },
                       coords={
                         'time':  time,
                         'depth': depth,  
                        })

    ds.to_netcdf(os.path.join(self.c['resultsFolder'], self.c['resultsFileName']))
    
    return
