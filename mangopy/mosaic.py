# mosaic.py
# create mosaic plot from multiple MANGO sites
# 
# created 2019-03-13 by LLamarche
# - SiteInfomation.csv must be in the running directory
#    and data files are in ./MANGOData/<site>
#   - adjust these in mango.py __init__()
# - site regridding is stored in regrid_image_index.h5
#   - this file can be removed, but it will be recreated
#     every time the program is run



import numpy as np
import tables
import h5py
# import csv
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy import interpolate
import os
import datetime as dt
from scipy.spatial import ConvexHull
from .mango import Mango
# from mango import mango


class Mosaic(Mango):

    def __init__(self,sites='all'):

        super(Mosaic, self).__init__()
        self.site_list = self.get_site_info(sites)


    def generate_grid(self,time):

        rewrite_file = False
        regrid_file = 'regrid_image_index.h5'
        if rewrite_file:
            os.remove(regrid_file)

        # create base background grid
        # original images have the following approximate resolution:
        # lat_res ~ 0.025 degrees
        # lon_res ~ 0.035 degrees
        latmin = 25.
        latmax = 55.
        latstp = 0.02
        # latstp = 1.
        lonmin = 225.
        lonmax = 300.
        lonstp = 0.03
        # lonstp = 1.
        lat_arr = np.arange(latmin,latmax,latstp)
        lon_arr = np.arange(lonmin,lonmax,lonstp)

        grid_lon, grid_lat = np.meshgrid(lon_arr,lat_arr)
        edge_lon, edge_lat = np.meshgrid(np.arange(lonmin-0.5*lonstp,lonmax,lonstp),np.arange(latmin-0.5*latstp,latmax,latstp))
        grid_shape = grid_lon.shape
        flat_grid = np.array([grid_lon.ravel(),grid_lat.ravel()]).T

        # get data from each site and interpolate it to background grid
        grid_img = []
        truetime = []
        for site in self.site_list:

            print(site['name'])
            # get data
            try:
                img, lat, lon, tt = self.read_data(site,time)
                # print(site['name'], tt)
                truetime.append(tt)
            except OSError as e:
                print(e)
                truetime.append('')
                grid_img.append(np.full(grid_shape,np.nan))
                continue
            except IOError as e:
                print(e)
                truetime.append('')
                grid_img.append(np.full(grid_shape,np.nan))
                continue
            except ValueError as e:
                print(e)
                truetime.append('')
                grid_img.append(np.full(grid_shape,np.nan))
                continue


            flat_img = img.ravel()
    

            try:
                with h5py.File(regrid_file,'r') as f:
                    nearest_idx = f[site['name']][:]
            except:
                flat_lat = lat.ravel()
                flat_lon = lon.ravel()
                flat_idx = np.arange(len(flat_lat))

                flat_idx = flat_idx[np.isfinite(flat_lat)]
                flat_lon = flat_lon[np.isfinite(flat_lat)]
                flat_lat = flat_lat[np.isfinite(flat_lat)]
                flat_points = np.array([flat_lon,flat_lat]).T

                fov = flat_points[ConvexHull(flat_points).vertices].T
                # print(fov)
                center_lon = site['lon']
                if center_lon<0:
                    center_lon += 360.
                # find points west of site
                fovW = fov[:,fov[0,:]<center_lon]
                # find points east of site
                fovE = fov[:,fov[0,:]>center_lon]
                # find longitude limits for each latitude row in the grid
                limits = []
                for f in [fovW,fovE]:
                    f = f[:,np.argsort(f[1,:])]
                    limits.append(np.interp(lat_arr,f[1,:],f[0,:],left=np.nan,right=np.nan))
                # create flag array identifying points in grid within fov
                flags = np.all(np.array([lon_arr>=limits[0][:,None],lon_arr<=limits[1][:,None]]),axis=0)

                # find index of image cell that is closest to each grid cell in the fov
                nearest_idx = np.full(grid_shape,np.nan)
                nearest_idx[flags] = interpolate.griddata(flat_points,flat_idx,flat_grid[flags.ravel()],method='nearest')

                with h5py.File(regrid_file, 'a') as f:
                    f.create_dataset(site['name'], data=nearest_idx, compression='gzip', compression_opts=1)

            # interpolate image to grid
            img_interp = np.full(grid_shape,np.nan)
            img_interp[np.isfinite(nearest_idx)] = flat_img[nearest_idx[np.isfinite(nearest_idx)].astype('int32')]

            # add interpolated image to the list of interpolated images from all sites
            grid_img.append(img_interp)

        grid_img = np.array(grid_img)

        return grid_img, grid_lat, grid_lon, edge_lat, edge_lon, truetime


    def create_mosaic(self,time,edges=False):

        grid_img, grid_lat, grid_lon, edge_lat, edge_lon, truetime = self.generate_grid(time)

        # find site hiarchy for background grid
        hiarchy = self.site_hiarchy(np.array([grid_lat,grid_lon]))

        # create combined grid of all sites based on site hiarchy
        grid_shape = grid_lat.shape
        combined_grid = np.full(grid_shape,np.nan)
        J, I = np.meshgrid(np.arange(grid_shape[1]),np.arange(grid_shape[0]))
        for lev in range(hiarchy.shape[0]):
            nans = np.isnan(combined_grid)
            combined_grid[nans] = grid_img[hiarchy[lev][nans].astype('int32'),I[nans],J[nans]]


        if edges:
            # edge_lon, edge_lat = np.meshgrid(np.arange(lonmin-0.5*lonstp,lonmax,lonstp),np.arange(latmin-0.5*latstp,latmax,latstp))
            return combined_grid, grid_lat, grid_lon, edge_lat, edge_lon, truetime
        else:
            return combined_grid, grid_lat, grid_lon

    def plot_mosaic(self,time,dpi=300):

        # get background grid image and coordinates
        img, grid_lat, grid_lon, edge_lat, edge_lon, truetime = self.create_mosaic(time, edges=True)

        # set up map
        fig = plt.figure(figsize=(15,10))
        map_proj = ccrs.LambertConformal(central_longitude=-110.,central_latitude=40.0)
        ax = fig.add_subplot(111,projection=map_proj)
        ax.coastlines()
        ax.gridlines()
        ax.add_feature(cfeature.STATES)
        ax.set_extent([225,300,25,50])

        # plot image on map
        ax.pcolormesh(edge_lon, edge_lat, img, cmap=plt.get_cmap('gist_heat'),transform=ccrs.PlateCarree())

        # add target time as title of plot
        ax.set_title('{:%Y-%m-%d %H:%M}'.format(time))

        # print actual image times below plot
        img_times = ['{} - {:%H:%M:%S}'.format(site['name'],ttime) for site, ttime in zip(self.site_list, truetime) if ttime]
        img_times = '\n'.join(img_times)
        ax.text(0.05,-0.03,img_times,verticalalignment='top',transform=ax.transAxes)



        plt.savefig('mosaic_{:%Y%m%d_%H%M}'.format(time), dpi=dpi)
        plt.show()



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



def main():
    # m = Mosaic(sites=['Rainwater Observatory','Hat Creek Observatory'])
    m = Mosaic()
    m.plot_mosaic(dt.datetime(2017,5,28,5,35))

if __name__ == '__main__':
    main()