import matplotlib
from matplotlib import pylab
import matplotlib.pyplot as plt
from PIL import Image
# from mpl_toolkits.basemap import Basemap
import numpy as np
from numpy import *
import glob
import os
import h5py

DIRN = "/Users/e30737/Desktop/Projects/InGeO/MANGO/MANGO/Data/RainwaterObservatory/May2817/Processed/"
pimages = glob.glob(DIRN + 'R*.png')
pimages.sort()
# himagesdirn = DIRN + 'HDF/'
himagesdirn = DIRN
#print pimages
for pimageaddress in pimages:
#    print pimageaddress[-12:-5]
    img = Image.open(pimageaddress)
    arrimg = array(img)
    fname = himagesdirn + pimageaddress[-12:-5] + '.h5'
#    print fname
    f = h5py.File(fname, 'w')
    f.create_dataset('imageData', data=arrimg[:,:,0])
    f.close()
