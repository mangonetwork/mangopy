from mangopy.mango import Mango
from mangopy.mosaic import Mosaic
import datetime as dt

time = dt.datetime(2017,5,28,6,25)
# date = dt.datetime(2017,6,10)

# # plot single FoV
# m = Mango()
# site = m.get_site_info('Hat Creek Observatory')
# m.map(site,time)

# plot mosaic
m = Mosaic()
m.plot_mosaic(time)
# m.create_all_mosaic(date)
# m.create_mosaic_movie(date)
