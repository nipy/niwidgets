from __future__ import print_function
import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import interact, fixed, IntSlider
import os
import inspect
import scipy.ndimage

class NiftiWidget:
    """
    Turns .nii files into interactive plots using ipywidgets.

    Args
    ----
        filename : str
                The path to your ``.nii`` file. Can be a string, or a
                ``PosixPath`` from python3's pathlib.
    """

    def __init__(self, filename):

        if not os.path.isfile(filename):
            # for Python3 should have FileNotFoundError here
            raise IOError('file {} not found'.format(filename))

        # load data in advance
        # this ensures once the widget is created that the file is of a format
        # readable by nibabel
        self.data = nib.load(filename).dataobj.get_unscaled()
        self.image_handles = None

    def nifti_plotter(self, plotting_func=None, colormap=None, figsize=(15, 5),
                      **kwargs):
        """
        This is the main method for this widget.

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

        # set default colormap options & add them to the kwargs
        if colormap is None:
            kwargs['colormap'] = ['viridis'] + \
                sorted(m for m in plt.cm.datad if not m.endswith("_r"))
        elif type(colormap) is str:
            # fix cmap if only one given
            kwargs['colormap'] = fixed(colormap)

        kwargs['figsize'] = fixed(figsize)

        if plotting_func is None:
            self._default_plotter(**kwargs)
        else:
            self._custom_plotter(plotting_func, **kwargs)


    def _default_plotter(self, mask_background=True, **kwargs):
        """
        Basic plot function to be used if no custom function is specified.

        This is called by nifti_plotter, you shouldn't call it directly.
        """

        if not ((self.data.ndim==3) or (self.data.ndim==4)):
            raise ValueError('Input image should be 3D or 4D')

        # mask the background
        if mask_background:
            if self.data.ndim==3:
                labels, n_labels = scipy.ndimage.measurements.label(
                                            (np.round(self.data) == 0))
            else: #4D
                labels, n_labels = scipy.ndimage.measurements.label(
                                        (np.round(self.data).max(axis=3) == 0))

            mask_labels = [lab for lab in range(1, n_labels+1)
                           if (np.any(labels[[0, -1], :, :] == lab) |
                           np.any(labels[:, [0, -1], :] == lab) |
                           np.any(labels[:, :, [0, -1]] == lab))]

            if self.data.ndim==3:
                self.data = np.ma.masked_where(
                    np.isin(labels, mask_labels), self.data)
            else:
                self.data = np.ma.masked_where(
                    np.broadcast_to(np.isin(labels, mask_labels)[:,:,:,np.newaxis],self.data.shape), self.data)

        # set default x y z values
        for dim, label in enumerate(['x', 'y', 'z']):
            if label not in kwargs.keys():
                kwargs[label] = IntSlider((self.data.shape[dim] - 1)/2,
                                          min=0, max=self.data.shape[dim] - 1, continuous_update=False)

        if (self.data.ndim==3) or (self.data.shape[3]==1):
            kwargs['t'] = fixed(0)
        else: # 4D
            kwargs['t'] = IntSlider(0, min=0, max=self.data.shape[3] - 1, continuous_update=False)

        interact(self._plot_slices, data=fixed(self.data), **kwargs)


    def _init_figure(self, data, colormap, figsize):
        self.fig, axes = plt.subplots(1, 3, figsize=figsize)

        data_max = data.max()

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
            img[1] = data_max
            im = ax.imshow(img, cmap=colormap)

            ax.axvline(x=0, color='gray', alpha=0.8)
            ax.axhline(y=0, color='gray', alpha=0.8)

            self.image_handles.append(im)


    def _plot_slices(self, data, x, y, z, t, colormap='viridis', figsize=(15, 5)):
        """
        Plots x,y,z slices.

        This function is called by
        """
        if self.image_handles is None:
            self.image_handles = []
            self._init_figure(data, colormap, figsize)

        coords = [x, y, z]
        views = ['Sagittal', 'Coronal', 'Axial']


        for ii, imh in enumerate(self.image_handles):
            slice_obj = 3 * [slice(None)]
            if data.ndim==4:
                slice_obj += [t]
            slice_obj[ii] = coords[ii]

            # plot the actual slice
            if ii == 0:
                imh.set_data(np.flipud(np.rot90(data[slice_obj], k=1)))
            else:
                imh.set_data(np.flipud(np.rot90(data[slice_obj], k=3)))
            # draw guides to show where the other two slices are
            guide_positions = [val for jj, val in enumerate(coords)
                               if jj != ii]
            imh.axes.lines[0].set_xdata(2*[guide_positions[0]])
            imh.axes.lines[1].set_ydata(2*[guide_positions[1]])

            imh.set_cmap(colormap)

        # print the value at that point in case people need to know
        #print('Value at point {x}, {y}, {z}: {intensity}'.format(
        #    x=x, y=y, z=z, intensity=data[x, y , z]
        #)) # -- this print statement leads staggered figures updates
        return self.fig


    def _custom_plotter(self, plotting_func, **kwargs):
        """
        Collects data and starts interactive widget for custom plot
        """

        self.plotting_func = plotting_func

        # XYZ Sliders if plot supports it and user didn't provide any:
        if ('cut_coords' in inspect.getargspec(self.plotting_func)[0]
            and 'cut_coords' not in kwargs.keys()):
            for label in ['x', 'y', 'z']:
                if label not in kwargs.keys():
                    # cut_coords should be given in MNI coordinates
                    kwargs[label] = (-90, 90)

        # Create the widget:
        interact(self._custom_plot_wrapper, data=fixed(self.data), **kwargs)


    def _custom_plot_wrapper(self, data, **kwargs):
        """
        Plot wrapper for custom function
        """

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


    def surface_projection(self, pycortexid, pycortexxfm):
        """
        Creates interactive pycortex plots using ipywidgets.

        Input: the subject ID for a subject already in your pycortex database.
        """
        # import pycortex in case it's not imported yet
        import cortex

        # check if the subject is in the pycortex database
        if not pycortexid in dir(cortex.db):
            raise IOError('Subject {} not in pycortex db.'.format(pycortexid))

        self.pycortexid = pycortexid

        # Surface projections in pycortex are done via "transforms", which are
        # stored in its database.
