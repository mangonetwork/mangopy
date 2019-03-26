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
import os


class Mango(object):

    def __init__(self):

        self.sitefile = 'SiteInformation.csv'
        self.datadir = './MANGOData/'
        # self.site = self.get_site_info(sitename, sitefile)

        # self.datadir = datadir + '{}/'.format(self.site['name'])

    def plot(self,site,targtime):
        # plot single mango image
        img, __, __, truetime = self.read_data(site,targtime)
        plt.imshow(img, cmap=plt.get_cmap('gist_heat'))
        plt.title('{:%Y-%m-%d %H:%M}'.format(truetime))
        plt.show()

    def map(self,site,targtime):
        # map single mango image
        img, lat, lon, truetime = self.read_data(site,targtime)

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

    def read_data(self,site,targtime):
        # read mango data file
        # self.datadir = datadir + '{}/'.format(self.site['name'])

        filename = self.datadir + '{}/{}{:%b%d%y}.h5'.format(site['name'],site['code'],targtime)

        with h5py.File(filename, 'r') as file:
            tstmp0 = (targtime-dt.datetime.utcfromtimestamp(0)).total_seconds()
            tstmp = file['Time'][:]
            t = np.argmin(np.abs(tstmp-tstmp0))
            truetime = dt.datetime.utcfromtimestamp(tstmp[t])

            img_array = file['ImageData'][t,:,:]
            lat = file['Latitude'][:]
            lon = file['Longitude'][:]

        return img_array, lat, lon, truetime

    def fetch_data(self, site, date, save_directory=None):
        # fetch mango data from online repository
        # Curtesy of AReimer's url_fetcher() function
        import os
        # NOTE: urllib2 does not work with python 3.  I've modified this so that it's python 3 complatible,
        #   but I havn't tested it with python 2. (2019-03-19 LL)
        # import urllib2
        from urllib.request import urlopen
        from contextlib import closing

        # form url
        url = 'ftp://isr.sri.com/pub/earthcube/provider/asti/MANGOProcessed/{}/{:%b%d%y}/{}{:%b%d%y}.h5'.format(self.site['name'],date,self.site['code'],date)

        # make sure save directory exists
        # self.datadir = datadir + '{}/'.format(self.site['name'])
        if not save_directory:
            save_directory = self.datadir + '{}/'.format(site['name'])
        try:
            os.mkdir(save_directory)
        except:
            pass

        # first check the file at the link and look/compare with archived.

        filename = os.path.basename(url)

        output_filename = os.path.join(save_directory,filename)
        # print(output_filename)

        # with closing(urllib2.urlopen(url)) as d:
        with closing(urlopen(url)) as d:
            url_size = int(d.info()['Content-Length'])

            download = True
            if os.path.exists(output_filename):
                output_size = os.stat(output_filename).st_size
                if output_size == url_size:
                    print("    Already have file: %s" % filename)
                    download = False

            if download:
                with open(output_filename,'wb') as f:
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


    def get_site_info(self,sites):
        # create site list from the site file and user input
        site_list = []
        with open(self.sitefile,'r') as f:
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