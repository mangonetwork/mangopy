import mangopy as mango
import datetime as dt

time = dt.datetime(2021,5,5,6,25)
# time = dt.datetime(2016,8,8,6,30)
# date = dt.datetime(2017,6,10)

# plot single FoV
m = mango.Mango(download_data=False)
site = m.get_site_info('Hat Creek Observatory')
# m.fetch_datafile(site,time.date())
m.plot(site,time)
m.map(site,time)

img_array, lat, lon, truetime = m.get_data(site,time)
print(img_array)

# plot mosaic
m = mango.Mosaic(download_data=False)
m.plot_mosaic(time)
mos, lat, lon = m.create_mosaic(time)
print(mos)
# m.create_all_mosaic(date)
# m.create_mosaic_movie(date)
