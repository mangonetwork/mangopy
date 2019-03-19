# mango.py
# Basic data and plotting utilities for MANGO network
#
# created 2019-3-19 by LLamarche

import numpy as np
import datetime as dt
import h5py
import csv
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature


class Mango(object):

    def __init__(self,sitename):

        sitefile = '/Users/e30737/Desktop/Projects/InGeO/MANGO/Data/SiteInformation.csv'
        self.site = self.get_site_info(sitename, sitefile)

    def plot(self,targtime):
        # plot single mango image
        img, __, __, truetime = self.get_data(targtime)
        plt.imshow(img, cmap=plt.get_cmap('gist_heat'))
        plt.title('{:%Y-%m-%d %H:%M}'.format(truetime))
        plt.show()

    def map(self,targtime):
        # map single mango image
        img, lat, lon, truetime = self.get_data(targtime)

        # set up map
        fig = plt.figure()
        map_proj = ccrs.LambertConformal(central_longitude=np.nanmean(lon),central_latitude=np.nanmean(lat))
        ax = fig.add_subplot(111,projection=map_proj)
        ax.coastlines()
        ax.gridlines()
        ax.add_feature(cfeature.STATES)
        ax.set_extent([np.nanmin(lon),np.nanmax(lon),np.nanmin(lat),np.nanmax(lat)])

        # plot image on map
        ax.scatter(lon, lat, c=img, s=0.7, cmap=plt.get_cmap('gist_heat'), transform=ccrs.Geodetic())

        # add time as title of plot
        ax.set_title('{:%Y-%m-%d %H:%M}'.format(truetime))

        plt.show()

    def get_data(self,targtime):
        # read mango data file
        datadir = '/Users/e30737/Desktop/Projects/InGeO/MANGO/Data/'
        filename = datadir + '{}/{:%b%d%y}/Processed/{:%b%d%y}{}.h5'.format(self.site['name'].replace(' ',''),targtime,targtime,self.site['code'])

        with h5py.File(filename, 'r') as file:
            tstmp0 = (targtime-dt.datetime.utcfromtimestamp(0)).total_seconds()
            tstmp = file['Time'][:]
            t = np.argmin(np.abs(tstmp-tstmp0))
            truetime = dt.datetime.utcfromtimestamp(tstmp[t])

            img_array = file['ImageData'][t,:,:]
            lat = file['Latitude'][:]
            lon = file['Longitude'][:]

        return img_array, lat, lon, truetime

    def fetch_data(self, save_directory='./MANGOData/'):
        # fetch mango data from online repository
        # Curtesy of AReimer's url_fetcher() function
        import os
        import urllib2
        from contextlib import closing
        # takes in a dictionary of format:
        # dict = {'URL':'some url','time':utctimestamp in unix epoch seconds}

        # first check the file at the link and look/compare with archived.

        filename = os.path.basename(url)

        output_filename = os.path.join(save_directory,filename)

        with closing(urllib2.urlopen(url)) as d:
            url_size = int(d.info()['Content-Length'])

            download = True
            if os.path.exists(output_filename):
                output_size = os.stat(output_filename).st_size
                if output_size == url_size:
                    print("    Already have file: %s" % filename)
                    download = False

            if download:
                with open(output_filename,'w') as f:
                    f.write(d.read())

        if download:
            output_size = os.stat(output_filename).st_size
            if not output_size == url_size:
                print("Problem downloading file from: %s" % url)
                try:
                    os.remove(output_filename)
                except Exception:
                    pass
            else:
                print("    Successfully downloaded: %s" % filename)

    def get_site_info(self,sitename, sitefile):
        # get site info from sitefile based on site name provided
        with open(sitefile,'r') as f:
            next(f)         # skip header line
            reader = csv.reader(f)
            for row in reader:
                if sitename == row[0]:
                    site = {'name':row[0],'code':row[1],'lon':float(row[2]),'lat':float(row[3])}
                    return site


def main():

    m = Mango('Rainwater Observatory')
    m.map(dt.datetime(2017,5,28,5,35))

if __name__ == '__main__':
    main()