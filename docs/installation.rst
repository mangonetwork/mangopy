Intallation
===========

Installing cartopy
==================
`Cartopy <https://scitools.org.uk/cartopy/docs/latest/index.html>`_ is used for visualizing MANGO data and must be installed before mangopy.  Please refer to the `cartopy installation instructions <https://scitools.org.uk/cartopy/docs/latest/installing.html#installing>`_ and make sure cartopy is successfully installed on your system before attempting to install mangopy.

Installing mangopy
==================
Mangopy can be installed with pip directly from the GitHub repository::

  pip install git+https://github.com/mangonetwork/mangopy.git


Installing for development
==========================
If you would would like to clone the mangopy repo so you can modify the source code, follow the following instructions:

1. Clone the mangopy git repo::

  git clone https://github.com/mangonetwork/mangopy.git

2. Change directories into the mangopy directory::

  cd mangopy

3. To install in development mode, run the following command::

  pip install -e .
