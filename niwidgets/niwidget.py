from __future__ import print_function
import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import interact, fixed
import os
import inspect
import scipy.ndimage


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
        coords = [x, y, z]
        views = ['Sagittal', 'Coronal', 'Axial']
        fig, axes = plt.subplots(1, 3, figsize=figsize)
        for subplot in range(3):
            slice_obj = 3 * [slice(None)]
            slice_obj[subplot] = coords[subplot]
            plt.sca(axes[subplot])
            axes[subplot].set_facecolor('black')
            axes[subplot].set_title(views[subplot])
            axes[subplot].tick_params(
                axis='both', which='both', bottom='off', top='off',
                labelbottom='off', right='off', left='off', labelleft='off'
                )
            # fix the axis limits
            axis_limits = [limit for i, limit in enumerate(data.shape)
                           if i != subplot]
            axes[subplot].set_xlim(0, axis_limits[0])
            axes[subplot].set_ylim(0, axis_limits[1])
            # plot the actual slice
            plt.imshow(np.rot90(data[slice_obj], k=3), cmap=colormap)
            # draw guides to show where the other two slices are
            guide_positions = [data.shape[i] - val if i == 1 else val
                               for i, val in enumerate(coords)
                               if i != subplot]
            plt.axvline(x=guide_positions[0], color='gray', alpha=0.8)
            plt.axhline(y=guide_positions[1], color='gray', alpha=0.8)

        plt.show()
        print(f'Value at point {x}, {y}, {z}: {data[x, y, z]}')

    def default_plotter(self, mask_background=True, **kwargs):
        """
        basic plot function to be used if no custom function is specified
        """

        # load data in advance
        self.data = nib.load(self.filename).dataobj.get_unscaled()

        # mask the background
        if mask_background:
            labels, n_labels = scipy.ndimage.measurements.label(
                (np.round(self.data) == 0)
                )
            mask_labels = [lab for lab in range(1, n_labels+1)
                           if (np.any(labels[[0, -1], :, :] == lab) |
                           np.any(labels[:, [0, -1], :] == lab) |
                           np.any(labels[:, :, [0, -1]] == lab))
                           ]
            self.data = np.ma.masked_where(
                np.isin(labels, mask_labels), self.data
                )

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
                self.colormap = kwargs['colormap']
                kwargs.pop('colormap', None)
                plt.set_cmap(self.colormap)

        # reconstruct manually added x-y-z-sliders:
        if 'cut_coords' in inspect.getargspec(self.plotting_func)[0] \
                and 'x' in kwargs.keys():

            # add the x-y-z as cut_coords
            if 'display_mode' not in kwargs.keys() \
                    or not any([label in kwargs['display_mode']
                                for label in ['x', 'y', 'z']]):
                # If no xyz combination of displaymodes was requested:
                kwargs['cut_coords'] = [kwargs[label]
                                        for label in ['x', 'y', 'z']]
            else:
                kwargs['cut_coords'] = [kwargs[label]
                                        for label in ['x', 'y', 'z']
                                        if label in kwargs['display_mode']]
            # remove x-y-z from kwargs
            [kwargs.pop(label, None) for label in ['x', 'y', 'z']]
        # Actually plot the image
        self.plotting_func(data, **kwargs)
        plt.show()

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
                    # cut_coords should be given in MNI coordinates
                    kwargs[label] = (-90, 90)

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
