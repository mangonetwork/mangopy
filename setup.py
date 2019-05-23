from setuptools import setup
import os

# Get the package requirements
REQSFILE = os.path.join(os.path.dirname(__file__), 'requirements.txt')
with open(REQSFILE, 'r') as f:
    REQUIREMENTS = f.readlines()
REQUIREMENTS = '\n'.join(REQUIREMENTS)

setup(name='mangopy',
      version='0.1',
      description='Software for MANGO ASI network',
      license='GPLv3',
      packages=['mangopy'],
      install_requires=REQUIREMENTS,
      package_data={'mangopy': ['SiteInformation.csv']},
      zip_safe=False)
