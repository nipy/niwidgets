"""
Widgets to visualise neuroimaging data.

For volume images, try import NiftiWidget.
For surface images, try SurfaceWidget.
"""
from .version import __version__  # noqa: F401
from .exampledata import exampleatlas, examplezmap, examplet1  # noqa: F401
from .niwidget_volume import NiftiWidget  # noqa: F401
from .niwidget_surface import SurfaceWidget  # noqa: F401
from .streamlines import StreamlineWidget  # noqa: F401
