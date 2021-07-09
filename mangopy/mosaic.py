# mosaic.py
# create mosaic plot from multiple MANGO sites
#
# created 2019-03-13 by LLamarche
# - site regridding is stored in regrid_image_index.h5
#   - this file can be removed, but it will be recreated
#     every time the program is run


import numpy as np
import h5py
import matplotlib.pyplot as plt
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
except ImportError:
    print('WARNING: cartopy is not installed')
from scipy import interpolate
import os
import datetime as dt
from scipy.spatial import ConvexHull
from .mango import Mango


class Mosaic(Mango):
    """
    Object for creating and visualizing mosaics of all cameras in the MANGO network.

    Parameters
    ==========
    sites : list, optional
        Sites to be plotted as mosaic on map.
    datadir : str, optional
        Path to exisiting directory containing MANGO data.

    """

    def __init__(self,sites='all',datadir=None):

        super(Mosaic, self).__init__(datadir=datadir)
        self.site_list = self.get_site_info(sites)


    def generate_grid(self):
        """
        Create base background grid.
        Original images have the following approximate resolution:\n
        lat_res ~ 0.025 degrees\n
        lon_res ~ 0.035 degrees\n

        Returns
        =======
        grid_array : array
            Array of grid latitude and longitude values.
        edge_array : array
            Array of edge latitude and longitude values.

        """
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

        grid_array = np.array([grid_lon, grid_lat])
        edge_array = np.array([edge_lon, edge_lat])
        # return flat_grid
        return grid_array, edge_array


    def site_hierarchy(self,grid_points):
        """
        Calculates site hierarchy for common grid based on the
        distance of each point from each site.  Site hierarchy
        is used to determine which camera to plot in each cell
        of the mosaic.

        Parameters
        ==========
        grid_points : array
            Coordinate points of base background grid.

        Returns
        =======
        hierarchy : array
            Array containing hierarchy of sites.

        """
        grid_distance = []
        for site in self.site_list:
            dist = self.haversine(site['lat'],site['lon'],grid_points[1],grid_points[0])
            grid_distance.append(dist)
        grid_distance = np.array(grid_distance)

        hierarchy = np.argsort(grid_distance,axis=0)

        return hierarchy


    def haversine(self,lat0,lon0,lat,lon):
        """
        Calculates distance (in km) between two points on Earth,
        assuming spherical Earth.

        Parameters
        ==========
        lat0 : float
            Latitude of site.
        lon0 : float
            Longitude of site.
        lat : float
            Latitude of grid.
        lon : float
            Longitude of grid.

        Returns
        =======
        km : float
            Haversine distance in kilometers.

        """
        #convert decimal degrees to radians
        lon0 = lon0*np.pi/180
        lat0 = lat0*np.pi/180
        lon = lon*np.pi/180
        lat = lat*np.pi/180

        #source: Haversine formula (https://en.wikipedia.org/wiki/Haversine_formula)

        dlon = lon - lon0
        dlat = lat - lat0
        a = np.sin(dlat/2)**2 + np.cos(lat0) * np.cos(lat) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))

        # Radius of earth in kilometers is 6371
        km = 6371* c
        return km


    def get_nearest_index(self,site,background_grid,time):
        """
        Gets nearest neighbor interpolation indices for the specifed site.

        Parameters
        ==========
        site : str
            Site for which you need indices.
        background_grid : array
            Base background grid.
        time : datetime object
            Time of image as requested by user.

        Returns
        =======
        nearest_idx : array
            Nearest index of each image cell closest to grid cell.

        """

        rewrite_file = False
        regrid_file = os.path.join(self.mangopy_path,'regrid_image_index.h5')
        if rewrite_file:
            os.remove(regrid_file)

        try:
            with h5py.File(regrid_file,'r') as f:
                nearest_idx = f[site['name']][:]
        except:

            flat_grid = np.array([background_grid[0].ravel(),background_grid[1].ravel()]).T
            lon_arr = background_grid[0,0,:]
            lat_arr = background_grid[1,:,0]

            # get site lat/lon arrays
            __, lat, lon, __ = self.get_data(site,time)

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
            nearest_idx = np.full(background_grid[0].shape,np.nan)
            nearest_idx[flags] = interpolate.griddata(flat_points,flat_idx,flat_grid[flags.ravel()],method='nearest')

            with h5py.File(regrid_file, 'a') as f:
                f.create_dataset(site['name'], data=nearest_idx, compression='gzip', compression_opts=1)

        return nearest_idx


    def grid_mosaic(self,time,grid,hierarchy):
        """
        Creates combined grid based on hierarchy.

        Parameters
        ==========
        time : datetime object
            Time of images on mosaic as requested by user.
        grid : array
            Base background grid.
        hierarchy : array
            Hierarchy of sites to be plotted.

        Returns
        =======
        combined_grid : array
            Combined grid.
        truetime : datetime object
            Time images were taken.

        """
        grid_img = []
        truetime = []
        for site in self.site_list:

            # get data
            try:
                img, __, __, tt = self.get_data(site,time)
                truetime.append(tt)
            except (OSError, IOError, ValueError) as e:
                print('Exception: {}'.format(str(e)))
                truetime.append('')
                grid_img.append(np.full(grid[0].shape,np.nan))
                continue

            flat_img = img.ravel()

            #get nearest neighbor interpolation indices for this site
            nearest_idx = self.get_nearest_index(site,grid,time)  # nearest index is site specific

            #interpolate image to grid
            img_interp = np.full(grid[0].shape,np.nan)
            img_interp[np.isfinite(nearest_idx)] = flat_img[nearest_idx[np.isfinite(nearest_idx)].astype('int32')]

            # add interpolated image to the list of interpolated images from all sites
            grid_img.append(img_interp)

        grid_img = np.array(grid_img)


        # create combined grid of all sites based on site hierarchy
        grid_shape = grid[0].shape
        combined_grid = np.full(grid_shape,np.nan)
        J, I = np.meshgrid(np.arange(grid_shape[1]),np.arange(grid_shape[0]))
        for lev in range(hierarchy.shape[0]):
            nans = np.isnan(combined_grid)
            combined_grid[nans] = grid_img[hierarchy[lev][nans].astype('int32'),I[nans],J[nans]]

        return combined_grid, truetime



    def create_mosaic(self,time,cell_edges=False):

        """
        Creates the background grid for images at specifed time.

        Parameters
        ==========
        time : datetime object
            User requested time.
        cell_edges : boolean, optional
            Draws cell edges if set to True.

        Returns
        =======
        combined_grid : array
            Background grid image.
        grid_lat_values : array
            Grid latitude values.
        grid_lon_values : array
            Grid longitude values.

        """

        # create background grid
        grid, edges = self.generate_grid()

        # find site hierarchy for background grid
        hierarchy = self.site_hierarchy(grid)

        # create mosaic of all sites on background grid
        combined_grid, truetime = self.grid_mosaic(time,grid,hierarchy)

        grid_lat_values = grid[1]
        grid_lon_values = grid[0]

        if cell_edges:
            # edge_lon, edge_lat = np.meshgrid(np.arange(lonmin-0.5*lonstp,lonmax,lonstp),np.arange(latmin-0.5*latstp,latmax,latstp))
            return combined_grid, grid_lat_values, grid_lon_values, edges[1], edges[0], truetime
        else:
            return combined_grid, grid_lat_values, grid_lon_values


    def plot_mosaic(self,time,dpi=300,saveFig = False):

        """
        Plots images of sites closest to requested time on map with grid.

        Parameters
        ==========
        time : datetime object
            Time of images on mosaic as requested by user.
        dpi : int, optional
            Defaults to 300.
        saveFig : boolean, optional
            Saves figure of mosaic if set to True.

        """
        # get background grid image and coordinates
        img, grid_lat, grid_lon, edge_lat, edge_lon, truetime = self.create_mosaic(time, cell_edges=True)

        # set up map
        fig = plt.figure(figsize=(13,10))
        map_proj = ccrs.LambertConformal(central_longitude=255.,central_latitude=40.0)
        ax = fig.add_subplot(111,projection=map_proj)
        ax.coastlines()
        ax.gridlines(color='lightgrey', linestyle='-', draw_labels=True, x_inline = False, y_inline = False)
        ax.add_feature(cfeature.STATES)
        ax.set_extent([235,285,20,52])

        # plot image on map
        ax.pcolormesh(edge_lon, edge_lat, img, cmap=plt.get_cmap('gist_heat'), transform=ccrs.PlateCarree())

        # add target time as title of plot
        ax.set_title('{:%Y-%m-%d %H:%M}'.format(time))

        # print actual image times below plot
        img_times = ['{} - {:%H:%M:%S}'.format(site['name'],ttime) for site, ttime in zip(self.site_list, truetime) if ttime]
        img_times = '\n'.join(img_times)
        ax.text(0.05,-0.03,img_times,verticalalignment='top',transform=ax.transAxes)
        if saveFig:
            plt.savefig('mosaic_{:%Y%m%d_%H%M}'.format(time), dpi=dpi)
        plt.show()


    def create_all_mosaic(self,date):
        '''
        Creates all mosaic images for a particular date.
        Images should be approximately 5 minutes apart.

        Parameters
        ==========
        date : datetime object
            Date for which mosaic is created.

        '''
        # create time list for night (images should be ~5 minutes apart)
        # currently this is hard-coded to range from 2-11 UT on the date given
        # Note - start and end times vary by season and should be determined by the data in some way
        starttime = dt.datetime.combine(date,dt.time(2,0,0))
        endtime = dt.datetime.combine(date,dt.time(11,0,0))
        dtime = 5      # time between frames in minutes
        num_frames = int((endtime-starttime).total_seconds()/60./dtime)+1
        time_list = [starttime+dt.timedelta(minutes=i*dtime) for i in range(num_frames)]

        # create save directory
        savedir = 'mosaic_images_{:%b%d%y}_gray'.format(date)
        if not os.path.exists(savedir):
            os.mkdir(savedir)

        # create background grid
        grid, edges = self.generate_grid()

        # find site hierarchy for background grid
        hierarchy = self.site_hierarchy(grid)

        for time in time_list:
            print(time)

            # create mosaic of all sites on background grid
            mosaic, truetime = self.grid_mosaic(time,grid,hierarchy)

            # set up map
            fig = plt.figure(figsize=(13,10))
            map_proj = ccrs.LambertConformal(central_longitude=255.,central_latitude=40.0)
            ax = fig.add_subplot(111,projection=map_proj)
            ax.coastlines()
            ax.gridlines(color='lightgrey', linestyle='-', draw_labels=True, x_inline = False, y_inline = False)
            ax.add_feature(cfeature.STATES)
            ax.set_extent([235,285,20,52])

            # plot image on map
            ax.pcolormesh(edges[0], edges[1], mosaic, cmap=plt.get_cmap('gray'),transform=ccrs.PlateCarree())

            # add target time as title of plot
            ax.set_title('{:%Y-%m-%d %H:%M}'.format(time))

            # print actual image times below plot
            img_times = ['{} - {:%H:%M:%S}'.format(site['name'],ttime) for site, ttime in zip(self.site_list, truetime) if ttime]
            img_times = '\n'.join(img_times)
            ax.text(0.05,-0.03,img_times,verticalalignment='top',transform=ax.transAxes)

            # save image
            plt.savefig('{}/mosaic_{:%Y%m%d_%H%M}'.format(savedir,time), dpi=300)


    def create_mosaic_movie(self,date):
        '''
        Creates a movie of all mosaic images for particular date.
        Requires ffmpeg to be installed.

        Parameters
        ==========
        date : datetime object
            Date for which mosaic movie is created.

        '''
        # create *.png image files for the given date
        self.create_all_mosaic(date)

        # combine image files into mp4 using ffmpeg
        ffmpeg_command = "ffmpeg -f image2 -r 5 -pattern_type glob -i 'mosaic_images_{:%b%d%y}/*.png' mosaic_movie_{:%b%d%y}.mp4".format(date,date)
        os.system(ffmpeg_command)


def main():
    # m = Mosaic(sites=['Rainwater Observatory','Hat Creek Observatory'])
    m = Mosaic()
    m.plot_mosaic(dt.datetime(2017,5,28,5,35))

if __name__ == '__main__':
    main()
