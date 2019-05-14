import mangopy as mango
import datetime as dt

# time = dt.datetime(2017,5,5,6,25)
time = dt.datetime(2016,8,2,5,3)
# date = dt.datetime(2017,6,10)

# plot single FoV
m = mango.Mango()
site = m.get_site_info('Madison')
m.plot(site,time)
m.map(site,time)

img_array, lat, lon, truetime = m.get_data(site,time)
print(img_array)

# plot mosaic
m = mango.Mosaic()
m.plot_mosaic(time)
mos, lat, lon = m.create_mosaic(time)
print(mos)
# m.create_all_mosaic(date)
# m.create_mosaic_movie(date)
