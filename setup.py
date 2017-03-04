from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

readme = 'A package that provides ipywidgets for standard neuroimaging plotting'
if path.isfile('README.md'):
    readme = open('README.md', 'r').read()

version = '0.1.0'

setup(
    name='niwidgets',
    version=version,
    description='Ipywidget wrappers for neuroimaging plot functions',
    long_description=readme,
    url='https://github.com/janfreyberg/niwidgets',
    download_url='https://github.com/janfreyberg/niwidgets' +
        version,
    # Author details
    author='Jan Freyberg',
    author_email='jan.freyberg@gmail.com',
    packages=['niwidgets'],
    install_requires=['ipywidgets', 'nilearn', 'nibabel'],
    # Include the template file
    package_data={
        '': ['data/*nii*']
    },
)
