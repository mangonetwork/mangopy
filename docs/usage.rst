Usage
=====

Mango
-----

First, import the Mango class::

	from mangopy import Mango
	%pylab inline

To instantiate a Mango object::

	mango_object = Mango()

You can also specify the directory where the data can be found using the 'datadir' keyword.

Specify what site you would like to look at. For example, for Capitol Reef Field Station::

	site = mango_object.get_site_info('Capitol Reef Field Station')

To specify a particular time and view an image, import datetime, and set a datetime object. You can view the image for the specified site at this time::

	import datetime as dt

	time_obj = dt.datetime(2016, 4, 10, 5, 30)
	mango_object.plot(site, time_obj)

To show the site on a map::

	mango_object.map(site, time_obj)


Mosaic
------

Now, import the Mosaic class::

	from mangopy import Mosaic


Here's how you can instantiate the Mosaic class. By default, all sites will appear on the Mosaic, but you can specify a list of sites using the sites keyword. For all sites::

	mosaic_all_sites = Mosaic()

To visualize a mosaic of Capitol Reef Field Station and Bridger alone::

	mosaic_specific = Mosaic(sites = ['Capitol Reef Field Station', 'Bridger'])

To plot the mosaic for all sites at the time specifed::

	mosaic_all_sites.plot_mosaic(time_obj)

If you prefer working with Jupyter Notebooks, here is the same `tutorial <https://github.com/mangonetwork/mangopy/blob/master/mangopy_tutorial.ipynb>`_, with an additional 'Accessing Data' example available on Jupyter Notebooks.