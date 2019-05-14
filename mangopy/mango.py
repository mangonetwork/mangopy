# mango.py
# Basic data and plotting utilities for MANGO network
#
# created 2019-3-19 by LLamarche
# Notes:
# - Default data directory is TEMP/MANGOData/, where TEMP is defined by tempfile.gettempdir() (https://docs.python.org/3/library/tempfile.html)
# - TODO: Data files availabe at ftp://isr.sri.com/pub/earthcube/provider/asti/MANGOProcessed/

import numpy as np
import datetime as dt
import h5py
import csv
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os
import urllib
from contextlib import closing
import tempfile


class Mango(object):

    def __init__(self, datadir=None):

        self.mangopy_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        # if no data directory specified, use a default temp directory
        if datadir is None:
            datadir = os.path.join(tempfile.gettempdir(),'MANGOData')
            print('No data directory has been specified!  If data is downloaded, it will be saved to {}.  This is also where mangopy will look for existing data files.'.format(datadir))
        self.datadir = datadir


    def plot(self,site,targtime):
        # plot single mango image
        img, __, __, truetime = self.get_data(site,targtime)
        plt.imshow(img, cmap=plt.get_cmap('gist_heat'))
        plt.title('{:%Y-%m-%d %H:%M}'.format(truetime))
        plt.show()

    def map(self,site,targtime):
        # map single mango image
        img, lat, lon, truetime = self.get_data(site,targtime)

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

    def get_data(self,site,targtime):
        # read mango data file
        filename = os.path.join(self.datadir,'{0}/{1:%b%d%y}/{2}{1:%b%d%y}.h5'.format(site['name'],targtime,site['code']))

        # first try to read data file locally
        try:
            img_array, lat, lon, truetime = self.read_datafile(filename,targtime)
        # if that fails, try to download, then read the data file
        except OSError:
            print('Attempting to download {0}{1:%b%d%y}.h5 from FTP server.'.format(site['code'],targtime))
            self.fetch_datafile(site, targtime.date())
            img_array, lat, lon, truetime = self.read_datafile(filename,targtime)

        return img_array, lat, lon, truetime


    def read_datafile(self,filename,targtime):
        with h5py.File(filename, 'r') as file:
            tstmp0 = (targtime-dt.datetime.utcfromtimestamp(0)).total_seconds()
            tstmp = file['Time'][:]
            t = np.argmin(np.abs(tstmp-tstmp0))
            truetime = dt.datetime.utcfromtimestamp(tstmp[t])

            # raise error if the closest time is more than 5 minutes from targtime
            if np.abs((targtime-truetime).total_seconds())>5.*60.:
                raise ValueError('Requested time {:%H:%M:%S} not included in {}'.format(targtime,filename))

            img_array = file['ImageData'][t,:,:]
            lat = file['Latitude'][:]
            lon = file['Longitude'][:]

        return img_array, lat, lon, truetime

    def fetch_datafile(self, site, date, save_directory=None):
        # fetch mango data from online repository
        # Curtesy of AReimer's url_fetcher() function
        # import os
        # NOTE: urllib2 does not work with python 3.  I've modified this so that it's python 3 complatible,
        #   but I havn't tested it with python 2. (2019-03-19 LL)

        # form url
        url = 'ftp://isr.sri.com/pub/earthcube/provider/asti/MANGOProcessed/{0}/{1:%b%d%y}/{2}{1:%b%d%y}.h5'.format(site['name'],date,site['code'])

        # make sure save directory exists
        if not save_directory:
            # define file directory path for this date
            save_directory = os.path.join(self.datadir,site['name'],'{:%b%d%y}'.format(date))
        try:
            # try and create directory path for this date
            os.makedirs(save_directory)
        except FileExistsError:
            # if directory already exists, don't do anything
            pass

        # define filename and output filename
        filename = os.path.basename(url)
        output_filename = os.path.join(save_directory,filename)

        try:
            # with closing(urllib2.urlopen(url)) as d:  # THIS IS A PYTHON2 REMINENT
            with closing(urllib.request.urlopen(url)) as d:
                url_size = int(d.info()['Content-Length'])

                # if file already exists, return without downloading anything
                if os.path.exists(output_filename):
                    output_size = os.stat(output_filename).st_size
                    if output_size == url_size:
                        print('    Already have file: {}'.format(filename))
                        return

                # download file
                with open(output_filename,'wb') as f:
                    f.write(d.read())

        # if the requested URL doesn't exist, raise an error
        except urllib.error.URLError:
            download = False
            raise ValueError('No data available for {} on {}.'.format(site['name'],date))

        # check to make sure download was completed sucessfully
        else:
            output_size = os.stat(output_filename).st_size
            if output_size == url_size:
                # if download sucessful, print success message
                print('    Successfully downloaded: {}'.format(filename))
            else:
                # if download not sucessful, print failure message and raise error
                print('    Problem downloading file from: {}'.format(url))
                try:
                    os.remove(output_filename)
                except Exception:
                    pass
                raise ValueError('Error downloading data!')



    def get_site_info(self,sites):
        # create site list from the site file and user input
        sitefile = os.path.join(self.mangopy_path,'SiteInformation.csv')

        site_list = []
        with open(sitefile,'r') as f:
            next(f)         # skip header line
            reader = csv.reader(f)
            for row in reader:
                site_list.append({'name':row[0],'code':row[1],'lon':float(row[2]),'lat':float(row[3])})

        # if particular sites are given, only include those sites in the site list
        if sites != 'all':
            site_list = [s for s in site_list if s['name'] in sites]

        if len(site_list) == 1:
            return site_list[0]
        else:
            return site_list



def main():

    m = Mango()
    site = m.get_site_info('Hat Creek Observatory')
    time = dt.datetime(2017,5,28,5,35)
    m.plot(site,time)
    m.map(site,time)

if __name__ == '__main__':
    main()