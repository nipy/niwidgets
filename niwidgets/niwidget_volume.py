"""Widgets that visualise volume images in .nii files."""
import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import interact, fixed, IntSlider
import ipywidgets as widgets
import inspect
import scipy.ndimage

from .colormaps import get_cmap_dropdown

# import pathlib & backwards compatibility
try:
    # on >3 this ships by default
    from pathlib import Path
except ModuleNotFoundError:
    # on 2.7 this should work
    try:
        from pathlib2 import Path
    except ModuleNotFoundError:
        raise ModuleNotFoundError('On python 2.7, niwidgets requires '
                                  'pathlib2 to be installed.')


class NiftiWidget:
    """Turn .nii files into interactive plots using ipywidgets.

    Args
    ----
        filename : str
                The path to your ``.nii`` file. Can be a string, or a
                ``PosixPath`` from python3's pathlib.
    """

    def __init__(self, filename):
        """
        Turn .nii files into interactive plots using ipywidgets.

        Args
        ----
            filename : str
                    The path to your ``.nii`` file. Can be a string, or a
                    ``PosixPath`` from python3's pathlib.
        """
        if hasattr(filename, 'get_data'):
            self.data = filename
        else:
            filename = Path(filename).resolve()
            if not filename.is_file():
                raise OSError('File ' + filename.name + ' not found.')

            # load data in advance
            # this ensures once the widget is created that the file is of a
            # format readable by nibabel
            self.data = nib.load(str(filename))

        # initialise where the image handles will go
        self.image_handles = None

    def nifti_plotter(self, plotting_func=None, colormap=None, figsize=(15, 5),
                      **kwargs):
        """
        Plot volumetric data.

        Args
        ----
            plotting_func : function
                    A plotting function for .nii files, most likely
            mask_background : bool
                    Whether the background should be masked (set to NA).
                    This parameter only works in conjunction with the default
                    plotting function (`plotting_func=None`). It finds clusters
                    of values that round to zero and somewhere touch the edges
                    of the image. These are set to NA. If you think you are
                    missing data in your image, set this False.
            colormap : str | list
                    The matplotlib colormap that should be applied to the data.
                    By default, the widget will allow you to pick from all that
                    are available, but you can pass a string to fix the
                    colormap or a list of strings to offer the user a few
                    options.
            figsize : tup
                    The figure height and width for matplotlib, in inches.

            If you are providing a custom plot function, any kwargs you provide
            to nifti_plotter will be passed to that function.

        """
        kwargs['colormap'] = get_cmap_dropdown(colormap)
        kwargs['figsize'] = fixed(figsize)

        if plotting_func is None:
            self._default_plotter(**kwargs)
        else:
            self._custom_plotter(plotting_func, **kwargs)

    def _default_plotter(self, mask_background=False, **kwargs):
        """Plot three orthogonal views.

        This is called by nifti_plotter, you shouldn't call it directly.
        """
        plt.gcf().clear()
        plt.ioff()  # disable interactive mode

        data_array = self.data.get_data()

        if not ((data_array.ndim == 3) or (data_array.ndim == 4)):
            raise ValueError('Input image should be 3D or 4D')

        # mask the background
        if mask_background:
            # TODO: add the ability to pass 'mne' to use a default brain mask
            # TODO: split this out into a different function
            if data_array.ndim == 3:
                labels, n_labels = scipy.ndimage.measurements.label(
                                            (np.round(data_array) == 0))
            else:  # 4D
                labels, n_labels = scipy.ndimage.measurements.label(
                    (np.round(data_array).max(axis=3) == 0)
                )

            mask_labels = [lab for lab in range(1, n_labels+1)
                           if (np.any(labels[[0, -1], :, :] == lab) |
                               np.any(labels[:, [0, -1], :] == lab) |
                               np.any(labels[:, :, [0, -1]] == lab))]

            if data_array.ndim == 3:
                data_array = np.ma.masked_where(
                    np.isin(labels, mask_labels), data_array)
            else:
                data_array = np.ma.masked_where(
                    np.broadcast_to(
                        np.isin(labels, mask_labels)[:, :, :, np.newaxis],
                        data_array.shape
                    ),
                    data_array
                )

        # init sliders for the various dimensions
        for dim, label in enumerate(['x', 'y', 'z']):
            if label not in kwargs.keys():
                kwargs[label] = IntSlider(
                    value=(data_array.shape[dim] - 1)/2,
                    min=0, max=data_array.shape[dim] - 1,
                    continuous_update=False
                )

        if (data_array.ndim == 3) or (data_array.shape[3] == 1):
            kwargs['t'] = fixed(None)  # time is fixed
        else:
            kwargs['t'] = IntSlider(
                value=0, min=0, max=data_array.shape[3] - 1,
                continuous_update=False
            )

        widgets.interact(self._plot_slices, data=fixed(data_array), **kwargs)

        plt.close()  # clear plot
        plt.ion()  # return to interactive state

    def _plot_slices(self, data, x, y, z, t,
                     colormap='viridis', figsize=(15, 5)):
        """
        Plot x,y,z slices.

        This function is called by _default_plotter
        """
        fresh = self.image_handles is None
        if fresh:
            self._init_figure(data, colormap, figsize)

        coords = [x, y, z]

        # add plot titles to the subplots
        views = ['Sagittal', 'Coronal', 'Axial']
        for i, ax in enumerate(self.fig.axes):
            ax.set_title(views[i])

        for ii, imh in enumerate(self.image_handles):

            slice_obj = 3 * [slice(None)]

            if data.ndim == 4:
                slice_obj.append(t)

            slice_obj[ii] = coords[ii]

            # update the image
            imh.set_data(
                np.flipud(np.rot90(data[slice_obj], k=1))
                if views[ii] != 'Sagittal' else
                np.fliplr(np.flipud(np.rot90(data[slice_obj], k=1)))
            )

            # draw guides to show selected coordinates
            guide_positions = [val for jj, val in enumerate(coords)
                               if jj != ii]
            imh.axes.lines[0].set_xdata(2*[guide_positions[0]])
            imh.axes.lines[1].set_ydata(2*[guide_positions[1]])

            imh.set_cmap(colormap)

        if not fresh:
            return self.fig

    def _init_figure(self, data, colormap, figsize):
        # init an empty list
        self.image_handles = []
        # open the figure
        self.fig, axes = plt.subplots(1, 3, figsize=figsize)

        for ii, ax in enumerate(axes):

            ax.set_facecolor('black')

            ax.tick_params(
                axis='both', which='both', bottom='off', top='off',
                labelbottom='off', right='off', left='off', labelleft='off'
                )
            # fix the axis limits
            axis_limits = [limit for jj, limit in enumerate(data.shape[:3])
                           if jj != ii]
            ax.set_xlim(0, axis_limits[0])
            ax.set_ylim(0, axis_limits[1])

            img = np.zeros(axis_limits[::-1])
            # img[1] = data_max
            im = ax.imshow(img, cmap=colormap,
                           vmin=data.min(), vmax=data.max())
            # add "cross hair"
            ax.axvline(x=0, color='gray', alpha=0.8)
            ax.axhline(y=0, color='gray', alpha=0.8)
            # append to image handles
            self.image_handles.append(im)
        # plt.show()

    def _custom_plotter(self, plotting_func, **kwargs):
        """Collect data and start interactive widget for custom plot."""
        self.plotting_func = plotting_func
        plt.gcf().clear()
        plt.ioff()

        # XYZ Sliders if plot supports it and user didn't provide any:
        if ('cut_coords' in inspect.getargspec(self.plotting_func)[0]
                and 'cut_coords' not in kwargs.keys()):
            for label in ['x', 'y', 'z']:
                if label not in kwargs.keys():
                    # cut_coords should be given in MNI coordinates
                    kwargs[label] = IntSlider(value=0, min=-90, max=90,
                                              continuous_update=False)

        # Create the widget:
        interact(self._custom_plot_wrapper, data=fixed(self.data), **kwargs)
        plt.ion()

    def _custom_plot_wrapper(self, data, **kwargs):
        """Wrap a custom function."""
        # start the figure
        fig = plt.figure(figsize=kwargs.pop('figsize', None))

        # The following should provide a colormap option to most plots:
        if 'colormap' in kwargs.keys():
            if 'cmap' in inspect.getargspec(self.plotting_func)[0]:
                # if cmap is valid argument to plot func, rename colormap
                kwargs['cmap'] = kwargs.pop('colormap')
            else:
                # if cmap is not valid for plot func, try and coerce it
                plt.set_cmap(kwargs.pop('colormap'))

        # reconstruct manually added x-y-z-sliders:
        if ('cut_coords' in inspect.getargspec(self.plotting_func)[0]
                and 'x' in kwargs.keys()):

            # add the x-y-z as cut_coords
            if ('display_mode' not in kwargs.keys()
                or not any([label in kwargs['display_mode']
                            for label in ['x', 'y', 'z']])):
                # If no xyz combination of display modes was requested:
                kwargs['cut_coords'] = [kwargs[label]
                                        for label in ['x', 'y', 'z']]
            else:
                kwargs['cut_coords'] = [kwargs[label]
                                        for label in ['x', 'y', 'z']
                                        if label in kwargs['display_mode']]
            # remove x-y-z from kwargs
            [kwargs.pop(label, None) for label in ['x', 'y', 'z']]

        # Actually plot the image
        self.plotting_func(data, figure=fig, **kwargs)
        plt.show()
