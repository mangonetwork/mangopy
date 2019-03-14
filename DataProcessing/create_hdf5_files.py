# ==================================================================
# create_hdf5_files.py
# Convert individual MANGO *.png files to a single *.h5 file for a
#   given night with latitude/longitude arrays and site information
# Created by: L. Lamarche - 2019-3-14
# Based on MANGO_HDF_convert.py
# Updated:
#
# Notes:
#   - hard-coded file paths need to be updated
#   - requires glob - may not be Windows compatible?
# ==================================================================

from PIL import Image
import numpy as np
import glob
import h5py
import csv
import datetime as dt

#date = dt.date(2017,5,28)
code = 'R'

# create site list from the site file and user input
sitefile = '/Users/e30737/Desktop/Projects/InGeO/MANGO/Data/SiteInformation.csv'
with open(sitefile,'r') as f:
    next(f)         # skip header line
    reader = csv.reader(f)
    for row in reader:
        if row[1] == code:
            site_name = row[0]
            site_lon = row[2]
            site_lat = row[3]


# from MANGO_HDF_convert.py
datadir = '/Users/e30737/Desktop/Projects/InGeO/MANGO/Data/{}/{:%b%d%y}/Processed/'.format(site_name.replace(' ',''),date)
pimages = glob.glob(datadir + code + '*.png')
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



# Generate Latitude and Longitude files
configdir = '/Users/e30737/Desktop/Projects/InGeO/MANGO/Data/{}/'.format(site_name.replace(' ',''))
# read lat/lon from where ever Latitude.csv and Longitude.csv are for that site
latitude = np.genfromtxt(configdir+'Latitudes.csv', dtype=float, delimiter=',')
longitude = np.genfromtxt(configdir+'Longitudes.csv', dtype=float, delimiter=',')

longitude[longitude<0] += 360.


# save hdf5 file
filename = datadir + '{:%b%d%y}{}.h5'.format(date,code)
f = h5py.File(filename, 'w')
f.create_group('SiteInfo')
N = f.create_dataset('SiteInfo/Name', data=site_name)
N.attrs['Description'] = 'site name'
C = f.create_dataset('SiteInfo/Code', data=code)
C.attrs['Description'] = 'one letter site abbreviation/code'
L = f.create_dataset('SiteInfo/Lon', data=site_lon)
L.attrs['Description'] = 'geodetic longitude of site'
L.attrs['Unit'] = 'degrees'
L = f.create_dataset('SiteInfo/Lat', data=site_lat)
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

