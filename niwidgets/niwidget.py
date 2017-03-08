from __future__ import print_function
import nilearn.plotting as nip
import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import interact, fixed
import os
import inspect


class NiWidget:
    """
    creates interactive NI plots using ipywidgets
    """

    def __init__(self, filename):

        if not os.path.isfile(filename):
            # for Python3 should have FileNotFoundError here
            raise IOError('file {} not found'.format(filename))

        # could also add a check here that input file is in one of the formats
        # that nibabel can read

        self.filename = filename

    def plot_slices(self, data, x, y, z, colormap='viridis', figsize=(15, 5)):
        """
        plots x,y,z slices
        """
        fig, axes = plt.subplots(1, 3, figsize=figsize)
        axes[0].imshow(np.rot90(data[:, y, :]), cmap=colormap)
        axes[1].imshow(np.rot90(data[x, :, :]), cmap=colormap)
        axes[2].imshow(np.rot90(data[:, :, z]), cmap=colormap)
        plt.show()

    def default_plotter(self, **kwargs):
        """
        basic plot function to be used if no custom function is specified
        """

        # load data in advance
        self.data = nib.load(self.filename).dataobj

        # set default x y z values
        for dim, label in enumerate(['x', 'y', 'z']):
            if label not in kwargs.keys():
                kwargs[label] = (0, self.data.shape[dim] - 1)

        # set default colormap
        if 'colormap' not in kwargs.keys():
            kwargs['colormap'] = ['viridis'] + \
                sorted(m for m in plt.cm.datad if not m.endswith("_r"))
        elif len([kwargs['colormap']]) == 1:
            # fix cmap if only one given
            kwargs['colormap'] = fixed(kwargs['colormap'])

        # set default figure size
        if 'figsize' not in kwargs.keys():
            kwargs['figsize'] = fixed((15, 5))

        interact(self.plot_slices, data=fixed(self.data), **kwargs)

    def _custom_plot_wrapper(self, data, **kwargs):
        """
        plot wrapper for custom function
        """
        # The following should provide a colormap option to most plots:
        if 'colormap' in kwargs.keys():
            if 'cmap' in inspect.getargspec(self.plotting_func)[0]:
                # if cmap is valid argument to plot func, rename but keep
                kwargs['cmap'] = kwargs['colormap']
                kwargs.pop('colormap', None)
            else:
                # if cmap is not valid for plot func, try and use it anyways
                self.colormap = kwargs['colormap']  # set this for later
                kwargs.pop('colormap', None)
                plt.set_cmap(self.colormap)
        # reconstruct manually added x-y-z-sliders:
        if 'cut_coords' in inspect.getargspec(self.plotting_func)[0] \
                and 'x' in kwargs.keys():
            # add the x-y-z as cut_coords
            kwargs['cut_coords'] = [kwargs[label] for label in ['x', 'y', 'z']]
            # remove x-y-z from kwargs
            [kwargs.pop(label, None) for label in ['x', 'y', 'z']]
        # Actually plot the image
        self.plotting_func(data, **kwargs)
        plt.show()
        pass

    def custom_plotter(self, plotting_func, **kwargs):
        """
        collects data and starts interactive widget for custom plot
        """

        self.plotting_func = plotting_func
        self.data = nib.load(self.filename)

        # Colormap options for most plots:
        if 'colormap' not in kwargs.keys():
            kwargs['colormap'] = ['viridis'] + \
                sorted(m for m in plt.cm.datad if not m.endswith("_r"))
        elif len([kwargs['colormap']]) == 1:
            # fix cmap if only one given
            kwargs['colormap'] = fixed(kwargs['colormap'])

        # XYZ Sliders for most plots that support it:
        if 'cut_coords' in inspect.getargspec(self.plotting_func)[0] \
                and 'cut_coords' not in kwargs.keys():
            # If no cut_coords provided but function supports it, add sliders:
            # These will be removed inside the wrapper
            for dim, label in enumerate(['x', 'y', 'z']):
                if label not in kwargs.keys():
                    kwargs[label] = (0, self.data.shape[dim] - 1)

        # Create the widget:
        interact(self._custom_plot_wrapper, data=fixed(self.data), **kwargs)

    def nifti_plotter(self, plotting_func=None, **kwargs):
        """
        main function to be called from outside
        """
        if plotting_func is None:
            self.default_plotter(**kwargs)
        else:
            self.custom_plotter(plotting_func, **kwargs)
