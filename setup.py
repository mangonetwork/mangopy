from setuptools import setup
import os

REQUIREMENTS = [
    'scipy >= 1.2',
    'h5py >= 2.9',
    'matplotlib >= 2.2.4'
]

with open("README.rst", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(name='mangopy',
      version='1.0.1',
      description='Software for MANGO ASI network',
      author = 'P. Venkatraman, L. Lamarche, A. Bhatt',
      long_description=long_description,
      long_description_content_type="text/x-rst",
      license='GPLv3',
      packages=['mangopy'],
      install_requires=REQUIREMENTS,
      package_data={'mangopy': ['SiteInformation.csv']},
      zip_safe=False)
