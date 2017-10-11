.. niwidgets documentation master file, created by


Make your neuroimaging plots interactive.
==================

``niwidgets`` is a package that provides easy and general wrappers to display interactive widgets that visualise standard-format neuroimaging data, using new functions and standard functions from other libraries.

|

.. ipywidgets-display::

    from niwidgets import NiftiWidget, exampledata

    my_widget = NiftiWidget(exampledata.examplet1)
    my_widget.nifti_plotter()

.. image:: img/example.gif

|

``niwidgets`` was initially developed by `Bjoern Soergel <http://www.ast.cam.ac.uk/~bs538/index.html>`_ and `Jan Freyberg <http://www.janfreyberg.com/>`_. It's actively being developed by members of the `brainhack <http://www.brainhack.org/>`_ community, in particular `Satrajit Ghosh <https://github.com/satra>`_, `Melanie Ganz <https://github.com/melanieganz>`_, `Murat Bilgel <https://github.com/bilgelm>`_, `Ariel Rokem <https://github.com/arokem>`_, and `@elyb01 <https://github.com/elyb01>`_.

We welcome contributions of any kind - feature suggestions, feature additions or bug reports should all be done at http://www.github.com/nipy/niwidgets.

|

.. toctree::
   :maxdepth: 3
   :caption: Documentation content:

   installation.rst
   examples.ipynb
   api
