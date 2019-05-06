import mangopy as mango
import datetime as dt

# time = dt.datetime(2017,5,5,6,25)
time = dt.datetime(2015,8,24,6,25)
# date = dt.datetime(2017,6,10)

# plot single FoV
m = mango.Mango()
site = m.get_site_info('Capitol Reef Field Station')
m.plot(site,time)
m.map(site,time)

# plot mosaic
m = mango.Mosaic()
m.plot_mosaic(time)
# m.create_all_mosaic(date)
# m.create_mosaic_movie(date)
