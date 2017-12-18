"""Installer."""
from setuptools import setup
# To use a consistent encoding
from codecs import open
from os import path

blurb = 'A package that provides ipywidgets for standard neuroimaging plotting'
if path.isfile('README.md'):
    readme = open('README.md', 'r').read()
else:
    readme = blurb

version = '0.1.4'

setup(
    name='niwidgets',
    version=version,
    description=blurb,
    long_description=readme,
    url='https://github.com/nipy/niwidgets',
    download_url='https://github.com/nipy/niwidgets/archive/' +
        version + '.tar.gz',
    # Author details
    author='Bjoern Soergel & Jan Freyberg',
    author_email='jan.freyberg@gmail.com',
    packages=['niwidgets'],
    keywords=['widgets', 'neuroimaging'],
    install_requires=['ipywidgets', 'nilearn', 'nibabel', 'ipyvolume'],
    # Include the template file
    package_data={
        '': ['data/*nii*',
             'data/examples_surfaces/lh.*',
             'data/examples_surfaces/*.ctab']
    },
)
