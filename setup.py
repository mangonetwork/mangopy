from setuptools import setup
import os

REQUIREMENTS = [
    'scipy >= 1.2',
    'h5py >= 2.9',
    'matplotlib >= 2.2.4'
]

setup(name='mangopy',
      version='0.0.1',
      description='Software for MANGO ASI network',
      author = 'P. Venkatraman, L. Lamarche, A. Bhatt',
      license='GPLv3',
      packages=['mangopy'],
      install_requires=REQUIREMENTS,
      package_data={'mangopy': ['SiteInformation.csv']},
      zip_safe=False)
