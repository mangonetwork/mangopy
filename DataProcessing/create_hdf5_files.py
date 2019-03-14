# create_hdf5_files.py
# convert individual *.png files to a *.h5 file for a given night
# requires glob - may not be Windows compatible?

# import matplotlib
# from matplotlib import pylab
# import matplotlib.pyplot as plt
from PIL import Image
# from mpl_toolkits.basemap import Basemap
import numpy as np
# from numpy import *
import glob
# import os
import h5py
import datetime as dt

date = dt.date(2017,5,28)
site_name = 'Rainwater Observatory'
code = 'R'

DIRN = '/Users/e30737/Desktop/Projects/InGeO/MANGO/Data/{}/{:%b%d%y}/Processed/'.format(site_name.replace(' ',''),date)
# pimages = glob.glob(DIRN + 'R*.png')
pimages = glob.glob(DIRN + code + '*.png')
# print(pimages)
pimages.sort()
# himagesdirn = DIRN + 'HDF/'
himagesdirn = DIRN
#print pimages
images = []
times = []
for pimageaddress in pimages:
#    print pimageaddress[-12:-5]
    img = Image.open(pimageaddress)
    arrimg = np.array(img)
    # print(arrimg.shape)
    images.append(arrimg[:,:,0])
    timestring = pimageaddress[-11:-5]
    t = dt.datetime.strptime(timestring,'%H%M%S').replace(year=2017,month=5,day=28)
    # print(timestring, tstmp)
    times.append(t)

# print(times)

tstmp = np.array([(t-dt.datetime.utcfromtimestamp(0)).total_seconds() for t in times])
images = np.array(images)

print(tstmp.shape,images.shape)

    # fname = himagesdirn + pimageaddress[-12:-5] + '.h5'
    # f = h5py.File(fname, 'w')
    # f.create_dataset('imageData', data=arrimg[:,:,0])
    # f.close()

filename = DIRN + '{}{:%Y%m%d}.h5'.format(code,date)
print(filename)
f = h5py.File(filename, 'w')
f.create_group('SiteInfo')
f.create_dataset('SiteInfo/SiteName', data=site_name)
f.create_dataset('SiteInfo/SiteCode', data=code)
f.create_dataset('Time', data=tstmp)
f.create_dataset('ImageData', data=images)
f.close()
