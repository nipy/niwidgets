# Neuroimaging Widgets (`niwidgets`)

This repository is supposed to provide easy and general wrappers to display
interactive widgets that visualise standard-format neuroimaging data, using new
functions and standard functions from other libraries. It looks like this:

![](https://thumbs.gfycat.com/ExcitableReflectingLcont-size_restricted.gif)

Install via:

```
pip install niwidgets
```

Or, to get the most up-to-date development version from github:

```
pip install git+git://github.com/nipy/niwidgets/
```

It requires nibabel and nilearn:

```
pip install nibabel nilearn
```

Check out the examples using the code in this notebook here:
https://github.com/nipy/niwidgets/blob/master/index.ipynb (you need to run the
notebook on your local machine to use the interactive features).

or using binder here:
https://mybinder.org/v2/gh/nipy/niwidgets/master?filepath=index.ipynb

### Usage:

There are currently three supported widgets:

1. Volume widgets. This widget is primarily designed to mimic existing tools
such as <add tool here>, but it also allows you to wrap plots from the `nilearn`
plotting library to make them interactive.

2. Surface widgets. This widget takes freesurfer-generated volume files and
turns them into widgets using the `ipyvolume` library. It allows you to add
different overlays for the surface files.

3. Streamline widgets. This widget accepts `.trk` files and displays the tracts
using `ipyvolume`.

To see how to use these widgets, please check the
[documentation](nipy.org/niwidgets).

As an example of how you might generate a Volume widget:

```
from niwidgets import NiftiWidget

my_widget = NiftiWidget('./path/to/file.nii')
```

You can then create a plot either with the default nifti plotter:

```
my_widget.nifti_plotter()
```

This will give you sliders to slice through the image, and an option to set the
colormap.

You can also provide your own plotting function:

```
import nilearn.plotting as nip

my_widget.nifti_plotter(plotting_func=nip.plot_glass_brain)
```

By default, this will give you the following interactive features: -
selecting a colormap - if supported by the plotting function, x-y-x
sliders (e.g. for `nip.plot_img`)


You can, however, always provide features you would like to have interactive
yourself. This follows the normal ipywidgets format. For example, if you provide
a list of strings for a keyword argument, this becomes a drop-down menu. If you
provide a tuple of two numbers, this becomes a slider. Take a look at some
examples we have in [this
notebook](https://github.com/janfreyberg/niwidgets/blob/master/visualisation_wrapper.ipynb)
(you need to run the notebook on your local machine to use the interactive
features).

Hopefully we will be able to add more default interactive features in the
future, as well as plotting of other data (such as surface projections). If you
have any suggestions for plot features to be added, please let us know - or add
them yourself and create a pull request!

## Development

![](https://travis-ci.org/nipy/niwidgets.svg?branch=master)

### Contributing

Please contribute! When writing new widgets, please make sure you include
example data that allows users to try a widget without having to munge their
data into the right format first.

Please also make sure you write a test for your new widget. It's hard to test
jupyter widgets, but it would be great if you could at least write a test that
"instantiates" a widget. This allows us to maintain a stable release.

### Development installation

As always with pip packages, you can install a _"development"_ version of this
package by cloning the git repository and installing it via `pip install -e
/path/to/package`.

### Updating the documentation

To update the documentation, you can do the following things:

- Make your changes on a separate branch, such as DOC/update-api-documentation.
- Merge your branch into master Make sure you have the packages in
- `doc-requirements.txt` installed Run `make gh-pages` in the root directory of
- the repository

This should run sphinx to generate the documentation, push it to the gh-pages
branch, and then revert to master.

---

_Developed by [Jan Freyberg](http://www.twitter.com/janfreyberg), [Bjoern
Soergel](http://www.ast.cam.ac.uk/~bs538/), [Satrajit
Ghosh](https://github.com/satra), [Melanie
Ganz](https://github.com/melanieganz), [Murat
Bilgel](https://github.com/bilgelm), [Ariel Rokem](https://github.com/arokem),
and [elyb01](https://github.com/elyb01)._
