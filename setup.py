from setuptools import setup
import os

# # Get the package requirements
# REQSFILE = os.path.join(os.path.dirname(__file__), 'requirements.txt')
# with open(REQSFILE, 'r') as f:
#     REQUIREMENTS = f.readlines()
# REQUIREMENTS = '\n'.join(REQUIREMENTS)
REQUIREMENTS = [
    'scipy >= 1.2',
    'h5py >= 2.9',
    'matplotlib >= 2.2.4'
]

setup(name='mangopy_test',
      version='0.1',
      description='Software for MANGO ASI network',
      author = 'P. Venkatraman, L. Lamarche, A. Bhatt',
      license='GPLv3',
      packages=['mangopy'],
      install_requires=REQUIREMENTS,
      package_data={'mangopy': ['SiteInformation.csv']},
      zip_safe=False)
