from mangopy.mango import Mango
from mangopy.mosaic import Mosaic
import datetime as dt

time = dt.datetime(2017,5,27,4,55)

# # plot single FoV
# m = Mango()
# site = m.get_site_info('Hat Creek Observatory')
# m.map(site,time)

# plot mosaic
m = Mosaic()
m.plot_mosaic(time)
