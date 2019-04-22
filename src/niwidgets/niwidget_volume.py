"""Widgets that visualise volume images in .nii files."""
import inspect
import os.path

import ipywidgets as widgets
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import scipy.ndimage
import traitlets
from IPython import display
from ipywidgets import IntSlider, fixed, interact

from .colormaps import get_cmap_dropdown
from .controls import PlaySlider


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
        if hasattr(filename, "get_data"):
            self.data = filename
        else:
            filename = str(filename)
            if not os.path.isfile(filename):
                raise OSError("File " + filename + " not found.")

            # load data in advance
            # this ensures once the widget is created that the file is of a
            # format readable by nibabel
            self.data = nib.load(str(filename))

        # initialise where the image handles will go
        self.image_handles = None

    def nifti_plotter(
        self, plotting_func=None, colormap=None, figsize=(15, 5), **kwargs
    ):
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
        kwargs["colormap"] = get_cmap_dropdown(colormap)
        kwargs["figsize"] = fixed(figsize)

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
            raise ValueError("Input image should be 3D or 4D")

        # mask the background
        if mask_background:
            # TODO: add the ability to pass 'mne' to use a default brain mask
            # TODO: split this out into a different function
            if data_array.ndim == 3:
                labels, n_labels = scipy.ndimage.measurements.label(
                    (np.round(data_array) == 0)
                )
            else:  # 4D
                labels, n_labels = scipy.ndimage.measurements.label(
                    (np.round(data_array).max(axis=3) == 0)
                )

            mask_labels = [
                lab
                for lab in range(1, n_labels + 1)
                if (
                    np.any(labels[[0, -1], :, :] == lab)
                    | np.any(labels[:, [0, -1], :] == lab)
                    | np.any(labels[:, :, [0, -1]] == lab)
                )
            ]

            if data_array.ndim == 3:
                data_array = np.ma.masked_where(
                    np.isin(labels, mask_labels), data_array
                )
            else:
                data_array = np.ma.masked_where(
                    np.broadcast_to(
                        np.isin(labels, mask_labels)[:, :, :, np.newaxis],
                        data_array.shape,
                    ),
                    data_array,
                )

        # init sliders for the various dimensions
        for dim, label in enumerate(["x", "y", "z"]):
            if label not in kwargs.keys():
                kwargs[label] = IntSlider(
                    value=(data_array.shape[dim] - 1) / 2,
                    min=0,
                    max=data_array.shape[dim] - 1,
                    continuous_update=False,
                )

        if (data_array.ndim == 3) or (data_array.shape[3] == 1):
            kwargs["t"] = fixed(None)  # time is fixed
        else:
            kwargs["t"] = IntSlider(
                value=0,
                min=0,
                max=data_array.shape[3] - 1,
                continuous_update=False,
            )

        widgets.interact(self._plot_slices, data=fixed(data_array), **kwargs)

        plt.close()  # clear plot
        plt.ion()  # return to interactive state

    def _plot_slices(
        self, data, x, y, z, t, colormap="viridis", figsize=(15, 5)
    ):
        """
        Plot x,y,z slices.

        This function is called by _default_plotter
        """
        fresh = self.image_handles is None
        if fresh:
            self._init_figure(data, colormap, figsize)

        coords = [x, y, z]

        # add plot titles to the subplots
        views = ["Sagittal", "Coronal", "Axial"]
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
                if views[ii] != "Sagittal"
                else np.fliplr(np.flipud(np.rot90(data[slice_obj], k=1)))
            )

            # draw guides to show selected coordinates
            guide_positions = [
                val for jj, val in enumerate(coords) if jj != ii
            ]
            imh.axes.lines[0].set_xdata(2 * [guide_positions[0]])
            imh.axes.lines[1].set_ydata(2 * [guide_positions[1]])

            imh.set_cmap(colormap)

        if not fresh:
            return self.fig

    def _init_figure(self, data, colormap, figsize):
        # init an empty list
        self.image_handles = []
        # open the figure
        self.fig, axes = plt.subplots(1, 3, figsize=figsize)

        for ii, ax in enumerate(axes):

            ax.set_facecolor("black")

            ax.tick_params(
                axis="both",
                which="both",
                bottom="off",
                top="off",
                labelbottom="off",
                right="off",
                left="off",
                labelleft="off",
            )
            # fix the axis limits
            axis_limits = [
                limit for jj, limit in enumerate(data.shape[:3]) if jj != ii
            ]
            ax.set_xlim(0, axis_limits[0])
            ax.set_ylim(0, axis_limits[1])

            img = np.zeros(axis_limits[::-1])
            # img[1] = data_max
            im = ax.imshow(
                img, cmap=colormap, vmin=data.min(), vmax=data.max()
            )
            # add "cross hair"
            ax.axvline(x=0, color="gray", alpha=0.8)
            ax.axhline(y=0, color="gray", alpha=0.8)
            # append to image handles
            self.image_handles.append(im)
        # plt.show()

    def _custom_plotter(self, plotting_func, **kwargs):
        """Collect data and start interactive widget for custom plot."""
        self.plotting_func = plotting_func
        plt.gcf().clear()
        plt.ioff()

        # XYZ Sliders if plot supports it and user didn't provide any:
        if (
            "cut_coords" in inspect.getargspec(self.plotting_func)[0]
            and "cut_coords" not in kwargs.keys()
        ):
            for label in ["x", "y", "z"]:
                if label not in kwargs.keys():
                    # cut_coords should be given in MNI coordinates
                    kwargs[label] = IntSlider(
                        value=0, min=-90, max=90, continuous_update=False
                    )

        # Create the widget:
        interact(self._custom_plot_wrapper, data=fixed(self.data), **kwargs)
        plt.ion()

    def _custom_plot_wrapper(self, data, **kwargs):
        """Wrap a custom function."""
        # start the figure
        fig = plt.figure(figsize=kwargs.pop("figsize", None))

        # The following should provide a colormap option to most plots:
        if "colormap" in kwargs.keys():
            if "cmap" in inspect.getargspec(self.plotting_func)[0]:
                # if cmap is valid argument to plot func, rename colormap
                kwargs["cmap"] = kwargs.pop("colormap")
            else:
                # if cmap is not valid for plot func, try and coerce it
                plt.set_cmap(kwargs.pop("colormap"))

        # reconstruct manually added x-y-z-sliders:
        if (
            "cut_coords" in inspect.getargspec(self.plotting_func)[0]
            and "x" in kwargs.keys()
        ):

            # add the x-y-z as cut_coords
            if "display_mode" not in kwargs.keys() or not any(
                [label in kwargs["display_mode"] for label in ["x", "y", "z"]]
            ):
                # If no xyz combination of display modes was requested:
                kwargs["cut_coords"] = [
                    kwargs[label] for label in ["x", "y", "z"]
                ]
            else:
                kwargs["cut_coords"] = [
                    kwargs[label]
                    for label in ["x", "y", "z"]
                    if label in kwargs["display_mode"]
                ]
            # remove x-y-z from kwargs
            [kwargs.pop(label, None) for label in ["x", "y", "z"]]

        # Actually plot the image
        self.plotting_func(data, figure=fig, **kwargs)
        plt.show()


class VolumeWidget(traitlets.HasTraits):
    """Turn .nii files into interactive plots using ipywidgets.

    Args
    ----
        filename : str
                The path to your ``.nii`` file. Can be a string, or a
                ``PosixPath`` from python3's pathlib.
    """

    # the indices are traitlets that can be linked:
    x = traitlets.Integer(0)
    y = traitlets.Integer(0)
    z = traitlets.Integer(0)
    t = traitlets.Integer(0)
    colormap = traitlets.Unicode("summer")
    reverse_colors = traitlets.Bool(False)

    guidelines = traitlets.Bool(True)
    orient_radiology = traitlets.Bool(True)

    def __init__(
        self,
        filename,
        figsize=(5, 5),
        colormap=None,
        orient_radiology=None,
        guidelines=None,
        animation_speed=300,
    ):
        """
        Turn .nii files into interactive plots using ipywidgets.

        Args
        ----
            filename : str
                    The path to your ``.nii`` file. Can be a string, or a
                    ``PosixPath`` from python3's pathlib.
            figsize : tuple
                    The figure size for each individual view.
            colormaps : tuple, list
                    A list of colormaps, or single colormap.
                    If None, a selection of maps is used to populate the
                    dropdown widget.
            orient_radiology : bool
                    Whether to display the images in the "radiological" style,
                    i.e. with lef and right reversed. If None, a checkbox is
                    offered.
            guidelines : bool
                    Whether to display guide lines. If None, a checkbox is
                    offered.
            animation_speed : int
                    The speed used for the animation, in milliseconds between
                    frames (the lower, the faster, up to a limit).
        """

        if hasattr(filename, "get_data"):
            self.data = filename
        else:
            filename = str(filename)
            if not os.path.isfile(filename):
                raise OSError("File " + filename + " not found.")
            # load data to ensures that the file readable by nibabel
            self.data = nib.load(str(filename))

        self.displays = [widgets.Output() for _ in range(3)]
        self._generate_axes(figsize=figsize)

        # set how many dimensions this file has
        self.ndim = len(self.data.shape)

        # initialise the control components of this widget
        self.dims = ["x", "y", "z", "t"][: self.ndim]
        self.controls = {}
        for i, dim in enumerate(self.dims):
            maxval = self.data.shape[i] - 1
            self.controls[dim] = PlaySlider(
                min=0,
                max=maxval,
                value=maxval // 2,
                interval=animation_speed,
                label=dim.upper(),
                continuous_update=False,
            )
            widgets.link((self.controls[dim], "value"), (self, dim))

        if not isinstance(colormap, str):
            self.color_picker = get_cmap_dropdown(colormap)
            widgets.link((self.color_picker, "value"), (self, "colormap"))
            self.color_reverser = widgets.Checkbox(
                description="Reverse colormap", indent=True
            )
            widgets.link(
                (self.color_reverser, "value"), (self, "reverse_colors")
            )
        else:
            self.color_picker = widgets.HBox([])
            self.color_reverser = widgets.HBox([])
            self.colormap = colormap

        if guidelines is None:
            self.guideline_picker = widgets.Checkbox(
                value=True, description="Show guides", indent=False
            )
            widgets.link(
                (self.guideline_picker, "value"), (self, "guidelines")
            )
        else:
            self.guideline_picker = widgets.Box([])
            self.guidelines = guidelines

        if orient_radiology is None:
            self.orientation_switcher = widgets.Checkbox(
                value=self.orient_radiology,
                indent=False,
                description="Radiological Orientation",
            )
            widgets.link(
                (self.orientation_switcher, "value"),
                (self, "orient_radiology"),
            )
        else:
            self.orientation_switcher = widgets.Box([])
            self.orient_radiology = orient_radiology

        self._update_orientation(True)

    @property
    def indices(self):
        return [self.x, self.y, self.z, self.t][: self.ndim]

    @traitlets.observe("x", "y", "z", "t", "guidelines", "orient_radiology")
    def _update_slices(self, change):
        array = self.data.get_data()

        if self.ndim == 3:
            array = array[:, :, :, np.newaxis]

        for iimage, (disp, fig, ax, image) in enumerate(
            zip(self.displays, self.figures, self.axes, self.images)
        ):
            image_data = np.rot90(
                array[
                    tuple(
                        slice(None) if iimage != idim else self.indices[idim]
                        for idim in range(3)
                    )
                    + (self.t,)
                ]
            )
            if image is not None:
                image.set_data(image_data)
            else:
                self.images[iimage] = ax.imshow(
                    image_data,
                    cmap=self.colormap,
                    vmin=self.data.get_data().min(),
                    vmax=self.data.get_data().max(),
                )

            if self.guidelines:
                # add "cross hair"
                x_idx, y_idx = (i for i in range(3) if i != iimage)
                x = self.indices[x_idx]
                y = self.data.shape[y_idx] - self.indices[y_idx]
                ax.lines = [
                    ax.axvline(x=x, color="gray"),
                    ax.axhline(y=y, color="gray"),
                ]
            else:
                ax.lines = []

        self._redraw()

    @traitlets.observe("orient_radiology")
    def _update_orientation(self, change):
        for i, ax in enumerate(self.axes):
            if change is not None:
                ax.invert_xaxis()
            ax.texts = []
            if self.orient_radiology:
                if i == 0:
                    ax.text(
                        -0.01,
                        0.5,
                        "F",
                        transform=ax.transAxes,
                        horizontalalignment="right",
                        verticalalignment="center",
                        fontsize=16,
                    )
                    ax.text(
                        1.01,
                        0.5,
                        "P",
                        transform=ax.transAxes,
                        horizontalalignment="left",
                        verticalalignment="center",
                        fontsize=16,
                    )
                elif i == 1 or i == 2:
                    ax.text(
                        -0.01,
                        0.5,
                        "R",
                        transform=ax.transAxes,
                        horizontalalignment="right",
                        verticalalignment="center",
                        fontsize=16,
                    )
                    ax.text(
                        1.01,
                        0.5,
                        "L",
                        transform=ax.transAxes,
                        horizontalalignment="left",
                        verticalalignment="center",
                        fontsize=16,
                    )
            else:
                if i == 0:
                    ax.text(
                        -0.01,
                        0.5,
                        "P",
                        transform=ax.transAxes,
                        horizontalalignment="right",
                        verticalalignment="center",
                        fontsize=16,
                    )
                    ax.text(
                        1.01,
                        0.5,
                        "F",
                        transform=ax.transAxes,
                        horizontalalignment="left",
                        verticalalignment="center",
                        fontsize=16,
                    )
                elif i == 1 or i == 2:
                    ax.text(
                        -0.01,
                        0.5,
                        "L",
                        transform=ax.transAxes,
                        horizontalalignment="right",
                        verticalalignment="center",
                        fontsize=16,
                    )
                    ax.text(
                        1.01,
                        0.5,
                        "R",
                        transform=ax.transAxes,
                        horizontalalignment="left",
                        verticalalignment="center",
                        fontsize=16,
                    )

        self._redraw()

    @traitlets.observe("colormap", "reverse_colors")
    def _update_colormap(self, change):
        for image in self.images:
            if self.reverse_colors:
                image.set_cmap(self.colormap + "_r")
            else:
                image.set_cmap(self.colormap)
        self._redraw()

    def _generate_axes(self, figsize=(5, 5)):
        plt.ioff()  # to avoid figure duplication
        self.figures, self.axes = zip(
            *[plt.subplots(1, 1, figsize=figsize) for _ in range(3)]
        )

        self.images = [None] * 3
        for ax, title in zip(self.axes, ["Sagittal", "Coronal", "Axial"]):
            ax.set_title(title)
            ax.set_axis_off()

    def _redraw(self):
        for fig, disp in zip(self.figures, self.displays):
            with disp:
                display.clear_output(wait=True)
                display.display(fig)

    def render(self):
        """Build the widget view and return it."""
        self.layout = widgets.VBox(
            [
                widgets.Box(
                    [self.controls[dim] for dim in self.dims],
                    layout={"flex_flow": "row wrap"},
                ),
                widgets.HBox([self.color_picker]),
                widgets.HBox(
                    [
                        self.color_reverser,
                        self.guideline_picker,
                        self.orientation_switcher,
                    ],
                    layout={"flex_flow": "row wrap"},
                ),
                widgets.Box(self.displays, layout={"flex_flow": "row wrap"}),
            ]
        )
        return self.layout

    def _ipython_display_(self):
        """This gets called instead of __repr__ in ipython."""
        display.display(self.render())

    def close(self):
        """Close all figures created for this widget."""
        for fig in self.figures:
            plt.close(fig)  # to avoid matplotlib warnings

    def __del__(self):
        """Method to tidy up afterwards."""
        self.close()
