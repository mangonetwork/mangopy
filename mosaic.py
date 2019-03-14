# mosaic.py
# create mosaic plot from multiple MANGO sites
# 
# created 2019-03-13 by LLamarche
# - paths to SiteInfomation.csv and data files are currently hard coded
#   - adjust these in __init__() and get_data()


import sys
sys.path.append('/Users/e30737/Desktop/Research/General')


import numpy as np
import tables
import h5py
import csv
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy import interpolate
import os
import datetime as dt



class Mosaic(object):

    def __init__(self,sites='all'):

        self.site_list = self.get_sites('/Users/e30737/Desktop/Projects/InGeO/MANGO/Data/SiteInformation.csv',sites)

    def create_mosaic(self,time,edges=False):

        # create base background grid
        latmin = 25.
        latmax = 55.
        latstp = 0.1
        lonmin = 225.
        lonmax = 300.
        lonstp = 0.1
        grid_lon, grid_lat = np.meshgrid(np.arange(lonmin,lonmax,lonstp),np.arange(latmin,latmax,latstp))
        grid_shape = grid_lon.shape
        flat_grid = np.array([grid_lon.ravel(),grid_lat.ravel()]).T

        # get data from each site and interpolate it to background grid
        grid_img = []
        truetime = []
        for site in self.site_list:

            # get data
            try:
                img, lat, lon, ttime = self.get_data(site,time)
                # img, lat, lon, ttime = self.get_data_h5(site,time)
            except FileNotFoundError as e:
                print(e)
                truetime.append('')
                grid_img.append(np.full(grid_shape,np.nan))
                continue

            print(site['name'], ttime)
            truetime.append(ttime)
            print(img.shape, lat.shape, lon.shape)
            print(img[np.isfinite(img)].shape, lat[np.isfinite(lat)].shape, lon[np.isfinite(lon)].shape)

            # flatten arrays and remove NAN points outside the camera FoV
            flat_lat = lat[np.isfinite(lon)].ravel()
            flat_lon = lon[np.isfinite(lon)].ravel()
            flat_points = np.array([flat_lon,flat_lat]).T
            flat_img = img[np.isfinite(lon)].ravel()

            # interpolate to background grid
            img_interp = interpolate.griddata(flat_points,flat_img,flat_grid)
            img_interp = img_interp.reshape(grid_shape)

            grid_img.append(img_interp)

        grid_img = np.array(grid_img)

        # find site hiarchy for background grid
        hiarchy = self.site_hiarchy(np.array([grid_lat,grid_lon]))

        # create combined grid of all sites based on site hiarchy
        combined_grid = np.empty(grid_shape)
        for i in range(grid_shape[0]):
            for j in range(grid_shape[1]):
                v = np.nan
                for k in range(len(self.site_list)):
                    v = grid_img[int(hiarchy[k,i,j]),i,j]
                    if np.isfinite(v):
                        break
                combined_grid[i,j] = v

        if edges:
            edge_lon, edge_lat = np.meshgrid(np.arange(lonmin-0.5*lonstp,lonmax,lonstp),np.arange(latmin-0.5*latstp,latmax,latstp))
            return combined_grid, grid_lat, grid_lon, edge_lat, edge_lon, truetime
        else:
            return combined_grid, grid_lat, grid_lon

    def plot_mosaic(self,time):

        # get background grid image and coordinates
        img, grid_lat, grid_lon, edge_lat, edge_lon, truetime = self.create_mosaic(time, edges=True)

        # set up map
        # ax = plt.axes(projection=ccrs.PlateCarree())
        ax = plt.axes(projection=ccrs.LambertConformal(central_longitude=-110.,central_latitude=40.0))
        # ax = plt.axes(projection=ccrs.Mollweide())
        ax.coastlines()
        ax.gridlines()
        ax.add_feature(cfeature.STATES)
        ax.set_extent([225,300,25,50])

        # plot image on map
        plt.pcolormesh(edge_lon, edge_lat, img, cmap=plt.get_cmap('gist_heat'),transform=ccrs.PlateCarree())

        # # plot sites on map
        # asi_az = np.linspace(0,360,50)*np.pi/180.
        # asi_el = np.full(50,15.)*np.pi/180.
        # for site in self.site_list:
        #     lat, lon, alt = self.projected_beam(site['lat'],site['lon'],0,asi_az,asi_el,proj_alt=250.)
        #     plt.plot(lon,lat,transform=ccrs.Geodetic())

        # print actual image times below plot
        img_times = ['{} - {:%H:%M:%S}'.format(site['name'],ttime) for site, ttime in zip(self.site_list, truetime) if ttime]
        img_times = '\n'.join(img_times)
        plt.text(0.05,-0.5,img_times,transform=ax.transAxes)

        # add target time as title of plot
        plt.title('{:%Y-%m-%d %H:%M}'.format(time))

        plt.show()



    def get_sites(self,sitefile,sites):
        # create site list from the site file and user input
        site_list = []
        with open(sitefile,'r') as f:
            next(f)         # skip header line
            reader = csv.reader(f)
            for row in reader:
                site_list.append({'name':row[0],'code':row[1],'lon':float(row[2]),'lat':float(row[3])})

        # if particular sites are given, only include those sites in the site list
        if sites != 'all':
            site_list = [s for s in site_list if s['name'] in sites]

        return site_list

    def site_hiarchy(self,grid_points):
        # calculate site hiarcy for common grid based on the distance of each point from each site
        grid_distance = []
        for site in self.site_list:
            dist = self.haversine(site['lat'],site['lon'],grid_points[0],grid_points[1])
            grid_distance.append(dist)
        grid_distance = np.array(grid_distance)

        hiarchy = np.argsort(grid_distance,axis=0)

        return hiarchy

    def haversine(self,lat0,lon0,lat,lon):
        # calculates distance (in km) between two points on earth assuming spherical Earth

        # convert decimal degrees to radians 
        lon0 = lon0*np.pi/180.
        lat0 = lat0*np.pi/180.
        lon = lon*np.pi/180.
        lat = lat*np.pi/180.

        # Haversine formula (https://en.wikipedia.org/wiki/Haversine_formula)
        dlon = lon - lon0 
        dlat = lat - lat0 
        a = np.sin(dlat/2)**2 + np.cos(lat0) * np.cos(lat) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a)) 
        # Radius of earth in kilometers is 6371
        km = 6371* c
        return km

    def get_data_h5(self,site,targtime):
        datadir = '/Users/e30737/Desktop/Projects/InGeO/MANGO/Data/'
        filename = datadir + '{}/{:%b%d%y}/Processed/{:%b%d%y}{}.h5'.format(site['name'].replace(' ',''),targtime,targtime,site['code'])

        file = h5py.File(filename, 'r')

        tstmp0 = (targtime-dt.datetime.utcfromtimestamp(0)).total_seconds()
        tstmp = file['Time'][:]
        t = np.argmin(np.abs(tstmp-tstmp0))
        truetime = dt.datetime.utcfromtimestamp(tstmp[t])

        img_array = file['ImageData'][t,:,:]
        lat = file['Latitude'][:]
        lon = file['Longitude'][:]

        return img_array, lat, lon, truetime

    def get_data(self,site,targtime):

        # find the file corresponding to the event time given
        # filedir = '/Users/e30737/Desktop/Projects/InGeO/MANGO/MANGO/Data/{}/May2817/'.format(site['name'].replace(' ',''))
        datadir = '/Users/e30737/Desktop/Projects/InGeO/MANGO/Data/'
        filedir = datadir+'{}/{:%b%d%y}/Processed/'.format(site['name'].replace(' ',''),targtime)
        filesuffix = '.h5'
        # extract a list of times from the timestamps on file names in the data directory
        filetimes = []
        for file in os.listdir(filedir):
            if file.startswith(site['code']) and file.endswith(filesuffix):
                # print(file)
                filetimes.append(dt.datetime.strptime(file[1:7],'%H%M%S').replace(year=2017,month=5,day=28))
        # find the time that's closest to the target time
        tstmp =  min(filetimes, key=lambda t: abs(t-targtime))
        # raise error if no file is found within 10 minutes of the requested time
        if abs((tstmp-targtime).total_seconds())>300.:
            raise FileNotFoundError('No file found for {} at {:%Y-%m-%d %H:%M}'.format(site['name'],targtime))
        # form filename
        filename = filedir+'{}{:%H%M%S}'.format(site['code'],tstmp)+filesuffix


        # open hdf5 file and read image array
        with tables.open_file(filename,'r') as h5file:
            img_array = h5file.get_node('/imageData').read()

        # read in latitude file
        latfile = datadir+'{}/Latitudes.csv'.format(site['name'].replace(' ',''))
        # if site['name'] == 'Bridger':
        #     latfile = 'Data/{}/Bridger400/Latitudes.csv'.format(site['name'].replace(' ',''))
        with open(latfile,'r') as f:
            reader = csv.reader(f)
            lat = np.array([[float(v) for v in row] for row in reader])

        # read in longitude file
        lonfile = datadir+'{}/Longitudes.csv'.format(site['name'].replace(' ',''))
        # if site['name'] == 'Bridger':
        #     latfile = 'Data/{}/Bridger400/Longitudes.csv'.format(site['name'].replace(' ',''))
        with open(lonfile,'r') as f:
            reader = csv.reader(f)
            lon = np.array([[float(v) for v in row] for row in reader])
        # adjust longitude coordinates so that they are in the range [0,360] (nessisary for grid interpolation)
        lon[lon<0]+=360.

        return img_array, lat, lon, tstmp


    # def projected_beam(self,lat0,lon0,alt0,azimuth,elevation,proj_alt=300.):
    #     import coord_convert as cc

    #     points = np.arange(0.,proj_alt/np.sin(min(elevation)),1.)*1000.
    #     x0, y0, z0 = cc.geodetic_to_cartesian(lat0,lon0,alt0)

    #     latitude = []
    #     longitude = []
    #     altitude = []

    #     for el, az in zip(elevation,azimuth):

    #         ve = np.cos(el)*np.sin(az)
    #         vn = np.cos(el)*np.cos(az)
    #         vu = np.sin(el)

    #         vx, vy, vz = cc.vector_geodetic_to_cartesian(vn,ve,vu,lat0,lon0,alt0)

    #         lat, lon, alt = cc.cartesian_to_geodetic(x0+vx*points,y0+vy*points,z0+vz*points)

    #         idx = (np.abs(alt-proj_alt)).argmin()

    #         latitude.append(lat[idx])
    #         longitude.append(lon[idx])
    #         altitude.append(alt[idx])

    #     latitude = np.array(latitude)
    #     longitude = np.array(longitude)
    #     altitude = np.array(altitude)

    #     return latitude, longitude, altitude


def main():
    # m = Mosaic(sites=['Rainwater Observatory'])
    m = Mosaic()
    m.plot_mosaic(dt.datetime(2017,5,28,5,35))

if __name__ == '__main__':
    main()