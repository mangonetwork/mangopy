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
#
# Requires config.ini, which specifies data file locations
# ; config.ini
#  
# [DEFAULT]
# SITEFILE = ???
# DATADIR = ???
# LATLONDIR = ???
#
# To Run:
#  > python create_hdf5_files.py [sites]
#  - the optional sites argument is a list of codes for sites you would
#	 like to process
#  - if no sites are given, default is to process all sites
# e.g.
#  > python create_hdf5_files.py
#	will create *.h5 files for all sites in SiteInformation.csv
#  > python create_hdf5_files.py M R B
#	will create *.h5 fiels for Madison, Rainwater Observatory, and Bridger
# ==================================================================

from PIL import Image
import numpy as np
import glob
import h5py
import csv
import datetime as dt
import os
import configparser
import sys

# read file paths from config file
config = configparser.ConfigParser()
config.read('config.ini')
sitefile = config.get('DEFAULT','SITEFILE')
datadir = config.get('DEFAULT','DATADIR')
latlondir = config.get('DEFAULT','LATLONDIR')


# create site list from the site file and user input
site_list = []
with open(sitefile,'r') as f:
    next(f)         # skip header line
    reader = csv.reader(f)
    for row in reader:
        site_list.append({'name':row[0],'code':row[1],'lon':float(row[2]),'lat':float(row[3])})

# if sites were given in input, only process those sites
sites_to_process = sys.argv[1:]
if sites_to_process:
	site_list = [site for site in site_list if site['code'] in sites_to_process]

for site in site_list:
	code = site['code']
	site_name = site['name']
	site_lon = site['lon']
	site_lat = site['lat']


	# read lat/lon from where ever Latitude.csv and Longitude.csv are for that site
	try:
		latitude = np.genfromtxt(os.path.join(latlondir,'{}/calibration/Latitudes.csv'.format(site_name)), dtype=float, delimiter=',')
		longitude = np.genfromtxt(os.path.join(latlondir,'{}/calibration/Longitudes.csv'.format(site_name)), dtype=float, delimiter=',')
		longitude[longitude<0] += 360.
	except IOError:
		print('Could not process {}!'.format(site_name))
		continue

	# from MANGO_HDF_convert.py
	sitepath = os.path.join(datadir, site_name)
	print(sitepath)
	if not os.path.exists(sitepath):
		print('Could not find data directory for {}!'.format(site_name))
		continue

	for procFolder in next(os.walk(sitepath))[1]:
		print(procFolder)
		date = dt.datetime.strptime(procFolder[0:3]+' '+procFolder[3:5]+ ' 20'+ procFolder[5:7], '%b %d %Y')
		
		datapath = os.path.join(datadir, site_name, procFolder)
		pimages = glob.glob(os.path.join(datapath, '{}*.png'.format(code)))
		print(len(pimages))
		pimages.sort()
		images = []
		times = []
		filename = os.path.join(datapath, '{}{}.h5'.format(code,procFolder))
		if not os.path.isfile(filename):

			for pimageaddress in pimages:
				img = Image.open(pimageaddress)
				arrimg = np.array(img)
				images.append(arrimg[:,:,0])
				timestring = pimageaddress[-11:-5]
				t = dt.datetime.strptime(timestring,'%H%M%S').replace(year=date.year,month=date.month,day=date.day)
				times.append(t)

			tstmp = np.array([(t-dt.datetime.utcfromtimestamp(0)).total_seconds() for t in times])
			images = np.array(images)



	# save hdf5 file
			print(filename)
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

