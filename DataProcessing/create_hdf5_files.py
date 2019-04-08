# ==================================================================
# create_hdf5_files.py
# Convert individual MANGO *.png files to a single *.h5 file for a
#   given night with latitude/longitude arrays and site information
# Created by: L. Lamarche - 2019-3-14
# Based on MANGO_HDF_convert.py
# Updated:
#   2019-4-8  LLamarche
#
# Notes:
#   - file paths read from config file, config.ini
#   - requires glob - may not be Windows compatible?
# ==================================================================

from PIL import Image
import numpy as np
import glob
import os
import h5py
import csv
import datetime as dt
import configparser


# read file paths from config file
config = configparser.ConfigParser()
config.read('config.ini')
sitefile = config.get('DEFAULT','SITEFILE')
datadir = config.get('DEFAULT','DATADIR')
latlondir = config.get('DEFAULT','LATLONDIR')


date = dt.date(2017,5,29)


# read in site list from sitefile
site_list = []
with open(sitefile,'r') as f:
    next(f)         # skip header line
    reader = csv.reader(f)
    for row in reader:
        site_list.append({'name':row[0],'code':row[1],'lon':float(row[2]),'lat':float(row[3])})


# generate hdf5 file for each site
for site in site_list:
    # read in image files
    # Note: This filepath will probably change
    imagename = os.path.join(datadir,'{0:%b%d%y}/{1}{0:%b%d%y}/Processed/Difference/{1}*.png'.format(date,site['code']))
    pimages = glob.glob(imagename)
    if not pimages:
        continue
    pimages.sort()
    images = []
    times = []
    for pimageaddress in pimages:
        img = Image.open(pimageaddress)
        arrimg = np.array(img)
        images.append(arrimg[:,:,0])
        timestring = pimageaddress[-11:-5]
        t = dt.datetime.strptime(timestring,'%H%M%S').replace(year=date.year,month=date.month,day=date.day)
        times.append(t)
    tstmp = np.array([(t-dt.datetime.utcfromtimestamp(0)).total_seconds() for t in times])
    images = np.array(images)


    # read in latitude and longitude arrays
    latitude = np.genfromtxt(os.path.join(latlondir, '{}/Latitudes.csv'.format(site['name'].replace(' ',''))), dtype=float, delimiter=',')
    longitude = np.genfromtxt(os.path.join(latlondir, '{}/Longitudes.csv'.format(site['name'].replace(' ',''))), dtype=float, delimiter=',')
    # correct longitude to range from 0 to 360
    # Note: this is nessisary for the gridding that happens in mosaic.py - may be more appropriate to move this adjustment there
    longitude[longitude<0] += 360.


    # save hdf5 file
    filename = os.path.join(datadir, '{0:%b%d%y}/{1}{0:%b%d%y}/Processed/Difference/{1}{0:%b%d%y}.h5'.format(date,site['code']))
    print(filename)
    f = h5py.File(filename, 'w')
    f.create_group('SiteInfo')
    N = f.create_dataset('SiteInfo/Name', data=site['name'])
    N.attrs['Description'] = 'site name'
    C = f.create_dataset('SiteInfo/Code', data=site['code'])
    C.attrs['Description'] = 'one letter site abbreviation/code'
    L = f.create_dataset('SiteInfo/Lon', data=site['lon'])
    L.attrs['Description'] = 'geodetic longitude of site'
    L.attrs['Unit'] = 'degrees'
    L = f.create_dataset('SiteInfo/Lat', data=site['lat'])
    L.attrs['Description'] = 'geodetic latitude of site'
    L.attrs['Unit'] = 'degrees'
    T = f.create_dataset('Time', data=tstmp, compression='gzip', compression_opts=1)
    T.attrs['Description'] = 'unix time stamp'
    T.attrs['Unit'] = 'seconds'
    T.attrs['Size'] = 'Nrecords'
    I = f.create_dataset('ImageData', data=images, compression='gzip', compression_opts=1)
    I.attrs['Description'] = 'pixel values for images'
    I.attrs['Size'] = 'Nrecords x Ipixels x Jpixels'
    Lon = f.create_dataset('Longitude', data=longitude, compression='gzip', compression_opts=1)
    Lon.attrs['Description'] = 'geodetic longitude of each pixel projected to 250 km'
    Lon.attrs['Size'] = 'Ipixels x Jpixels'
    Lon.attrs['Unit'] = 'degrees'
    Lat = f.create_dataset('Latitude', data=latitude, compression='gzip', compression_opts=1)
    Lat.attrs['Description'] = 'geodetic latitude of each pixel projected to 250 km'
    Lat.attrs['Size'] = 'Ipixels x Jpixels'
    Lat.attrs['Unit'] = 'degrees'

    f.close()

