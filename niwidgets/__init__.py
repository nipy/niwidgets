"""
Widgets to visualise neuroimaging data.

For volume images, try NiftiWidget. For surface images, try SurfaceWidget.
"""
# import example data
from .exampledata import exampleatlas, examplezmap, examplet1  # noqa
# import widget classes.
from .niwidget import NiftiWidget  # noqa
from .niwidget_surface import SurfaceWidget  # noqa
