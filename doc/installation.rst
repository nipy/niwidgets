Installation
============

Install via ``pip``
-------------------

Install latest stable from pypi via:::

    pip install niwidgets

Install the latest development version:::

    pip install git+git://github.com/janfreyberg/niwidgets/

Dependencies
------------

When you install niwidgets via `pip`, it will automatically install the packages it depends on. However, you will have to make sure that they are enabled as jupyter extensions.

In particular, you will need to run the following two commands:::

    jupyter nbextension enable --py widgetsnbextension
    jupyter nbextension enable --py --sys-prefix ipyvolume

This enables widgets in your jupyter notebook application, and also enables ipyvolume (which is used to display surface widgets). It's recommended to run these two commands if you're having the issue that rather than displaying a widget, your code produces text saying ``A Jupyter widget.``

It should be noted that at the moment, this doesn't work in jupyterlab, as widget support in jupyterlab is at very early stages.

Development installation
------------------------

As always with pip packages, you can install a "development" version of this package by cloning the git repository and installing it via:::

    pip install -e /path/to/package

This means you can make changes in your code locally and they will affect your code straight away. To make this even easier, you can add the following two lines to the top of your notebook, which ensure packages are re-loaded every time you run code (so you don't have to restart your jupyter kernel each time):::

    %load_ext autoreload
    %autoreload 2
