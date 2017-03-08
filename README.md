### Neuroimaging Widgets (niwidgets)

This repository is supposed to provide easy and general wrappers to display interactive widgets that visualise standard-format neuroimaging data, using new functions and standard functions from other libraries.

Install via:
```
pip install git+git://github.com/janfreyberg/niwidgets/
```

It requires nibabel and nilearn:
```
pip install nibabel nilearn
```

Check out the examples using the code in this notebook here:
https://github.com/janfreyberg/niwidgets/blob/master/visualisation_wrapper.ipynb
(you need to run the notebook on your local machine to use the interactive features).

### Usage:

So far, the widgets support plotting of nifti files, either in `nii` or `nii.gz` format. You initialise a widget class like this:

```
from niwidgets import NiWidget
my_widget = NiWidget('./path/to/file.nii')
```

You can then create a plot either with our default nifti plotter:

```
my_widget.nifti_plotter()
```

This will give you sliders to slice through the image, and an option to set the colormap.

You can also provide your own plotting function:
```
import nilearn.plotting as nip
my_widget.nifti_plotter(plotting_func=nip.plot_glass_brain)
```

By default, this will give you the following interactive features:
- selecting a colormap
- if supported, x-y-x sliders (e.g. for `nip.plot_img`)

Hopefully we will be able to add more interactive features in the future. If you have any suggestions for plot features to be added, please let us know!

By [Jan Freyberg](http://www.twitter.com/janfreyberg) and [Bjoern Soergel](http://www.ast.cam.ac.uk/~bs538/)
