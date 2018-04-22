"""A widget for surface-warped neuroimaging data."""
from __future__ import print_function
from collections import defaultdict
import os

import nibabel as nb
from xml.parsers.expat import ExpatError

import matplotlib.pyplot as plt
import numpy as np

from IPython.display import display
from ipywidgets import interact, fixed, Dropdown
import ipyvolume.pylab as p3

from .colormaps import get_cmap_dropdown


def _check_file(file):
    """Check if file exists and if it's valid"""
    if isinstance(file, nb.gifti.gifti.GiftiImage):
        return file
    elif os.path.isfile(str(file)):
        return str(file)
    else:
        raise ValueError('The argument meshfile needs to either be '
                         'a nibabel Gifti image or an existing file, '
                         'but ' + str(file) + ' was provided.')


def _get_name(file):
    """Get a name for the supplied file / giftiimage"""
    if isinstance(file, nb.gifti.gifti.GiftiImage):
        if file.get_filename():
            return os.path.basename(file.get_filename())
        else:
            return str(file)
    elif os.path.isfile(str(file)):
        return os.path.basename(str(file))


class SurfaceWidget:
    """Interact with brain surfaces right in the notebook."""

    def __init__(self, meshfile, overlayfiles=()):
        """Create a surface widget.

        This widget takes in surface data, in the form of gifti files or
        freesurfer files, and displays them interactively.

        meshfile : str, Path, nb.gifti.gifti.GiftiImage
            A file containing the the surface information. It can either be
            a Freesurfer file (i.e. lh.pial) or a .gii mesh file. A loaded
            GiftiImage (using nibabel) will also work.

        overlayfiles : tuple, dict, str, nb.gifti.gifti.GiftiImage
            Data you'd like to overlay on the 3D mesh. This can be a tuple of
            files, a dictionary (in which case the keys of the dict are used
            as options in a dropdown menu), or a single file name / loaded
            GiftiImage. Possible file formats: .annot, .thickness, .curv, .sulc
            or .gii.

        """
        # check meshfile is a valid argument
        self.meshfile = _check_file(meshfile)

        # make sure overlayfiles is a dictionary
        if isinstance(overlayfiles, dict):
            self.overlayfiles = overlayfiles
        elif isinstance(overlayfiles, (list, tuple)):
            self.overlayfiles = {
                _get_name(file): _check_file(file)
                for file in overlayfiles
            }
        else:
            self.overlayfiles = {_get_name(overlayfiles):
                                 _check_file(overlayfiles)}

        self.fig = None

    def _init_figure(self, x, y, z, triangles, figsize, figlims):
        """
        Initialize the figure by plotting the surface without any overlay.

        x: x coordinates of vertices (V x 1 numpy array)
        y: y coordinates of vertices (V x 1 numpy array)
        z: z coordinates of vertices (V x 1 numpy array)
        triangles: triangle specifications (T x 3 numpy array, where
        T=#triangles)
        figsize: 2x1 list of integers
        figlims: 3x2 list of integers
        """
        self.fig = p3.figure(width=figsize[0], height=figsize[1])
        self.fig.camera_fov = 1
        self.fig.style = {'axes': {'color': 'black',
                                   'label': {'color': 'black'},
                                   'ticklabel': {'color': 'black'},
                                   'visible': False},
                          'background-color': 'white',
                          'box': {'visible': False}}
        self.fig.xlim = (figlims[0][0], figlims[0][1])
        self.fig.ylim = (figlims[1][0], figlims[1][1])
        self.fig.zlim = (figlims[2][0], figlims[2][1])

        # draw the tetrahedron
        p3.plot_trisurf(x, y, z, triangles=triangles,
                        color=np.ones((len(x), 3)))

    def _plot_surface(self, x, y, z, triangles,
                      overlays=None, frame=0,
                      colormap='summer', figsize=np.array([600, 600]),
                      figlims=np.array(3 * [[-100, 100]])):
        """
        Visualize/update the overlay.

        This function changes the color associated with mesh vertices.

        overlays: V x F numpy array, where each column corresponds to a
                  different overlay. F=#frames or #timepoints.

        """
        if self.fig is None:
            self._init_figure(x, y, z, triangles, figsize, figlims)
        # overlays is a 2D matrix
        # with 2nd dimension corresponding to (time) frame
        my_color = plt.cm.get_cmap(colormap)
        if overlays[frame] is not None:
            # activation = overlays[:, frame]
            activation = overlays[frame]
            if max(activation) - min(activation) > 0:
                colors = my_color((activation - min(activation))
                                  / (max(activation) - min(activation)))
            else:
                colors = my_color((activation - min(activation)))
            self.fig.meshes[0].color = colors[:, :3]

    def zmask(surf, mask):
        """
        Masks out vertices with intensity=0 from overlay.

        Also returns masked-out vertices.

        Parameters
        ----------
        surf: gifti object
            already loaded gifti object of target surface
        mask: gifti object
            already loaded gifti object of overlay with zeroes
            at vertices of no interest (e.g. medial wall)

        Returns
        -------
        mask_keep : np.ndarray
            Boolean array of what to show.
        mask_kill : np.ndarray
            Boolean array of what to hide.

        """
        ikill = np.flatnonzero(mask.darrays[0].data == 0)

        # create empty arrays matching surface mesh dimentions
        mask_kill = np.zeros([surf.darrays[1].data.shape[0]], dtype=bool)

        for ii, row in enumerate(surf.darrays[1].data):
            for item in row:
                if item in ikill:
                    mask_kill[ii] = True

        return ~mask_kill, mask_kill

    def surface_plotter(self, colormap=None, figsize=np.array([600, 600]),
                        figlims=np.array(3 * [[-100, 100]]),
                        show_zeroes=True, **kwargs):
        """Visualise a surface mesh (with overlay) inside notebooks.

        This method displays the surface widget.

        Parameters
        ----------
        surface : str, gifti object
            Path to surface file in gifti or FS surface format or an
            already loaded gifti object of surface
        overlay : str, gifti object
            Path to overlay file in gifti or FS annot or anatomical
            (.curv,.sulc,.thickness) format or an already loaded
            gifti object of overlay, default None
        colormap : string
            A matplotlib colormap, default summer
        figsize : ndarray
            Size of the figure to display, default [600,600]
        figlims : ndarray
            x,y and z limits of the axes, default
            [[-100,100],[-100,100],[-100,100]]
        show_zeroes : bool
            Display vertices with intensity = 0, default True

        """
        kwargs['colormap'] = get_cmap_dropdown(colormap)
        kwargs['figsize'] = fixed(figsize)
        kwargs['figlims'] = fixed(figlims)

        if isinstance(self.meshfile, str):
            # if mesh has not been loaded before, load it
            if os.path.splitext(self.meshfile)[1].lower() == '.gii':
                # load gifti file
                try:
                    self.meshfile = nb.load(self.meshfile)
                    x, y, z = self.meshfile.darrays[0].data.T
                    vertex_edges = self.meshfile.darrays[1].data
                except ExpatError:
                    raise ValueError(
                        'The file {} could not be read. '.format(self.meshfile)
                        + 'Please provide a valid gifti file.')
            else:
                # load freesurfer file
                fsgeometry = nb.freesurfer.read_geometry(self.meshfile)
                x, y, z = fsgeometry[0].T
                vertex_edges = fsgeometry[1]

        elif isinstance(self.meshfile, nb.gifti.gifti.GiftiImage):
            # if mesh has been loaded as a GiftiImage, format the data
            x, y, z = self.meshfile.darrays[0].data.T
            vertex_edges = self.meshfile.darrays[1].data

        overlays = defaultdict(lambda: None)
        if len(self.overlayfiles) > 0:

            for key, overlayfile in self.overlayfiles.items():

                file_ext = os.path.splitext(overlayfile)[1].lower()

                if isinstance(overlayfile, nb.gifti.gifti.GiftiImage):
                    overlays[key] = overlayfile.darrays[0].data
                else:
                    file_ext = os.path.splitext(overlayfile)[1].lower()

                    if file_ext == '.gii':
                        try:
                            overlay = nb.load(overlayfile)
                            overlays[key] = overlay.darrays[0].data
                        except ExpatError:
                            raise ValueError(
                                'The file {} could not be read. '
                                .format(overlayfile)
                                + 'Please provide a valid gifti file.')

                    elif (file_ext in ('.annot', '')):
                        annot = nb.freesurfer.read_annot(overlayfile)
                        overlays[key] = annot[0]

                    elif (file_ext in ('.curv', '.thickness', '.sulc')):
                        overlays[key] = nb.freesurfer.read_morph_data(
                            overlayfile)

                    if not show_zeroes:
                        pass

        kwargs['triangles'] = fixed(vertex_edges)
        kwargs['x'] = fixed(x)
        kwargs['y'] = fixed(y)
        kwargs['z'] = fixed(z)
        kwargs['overlays'] = fixed(overlays)

        if len(self.overlayfiles) < 2:
            frame = fixed(None)
        else:
            frame = Dropdown(
                options=list(self.overlayfiles.keys()),
                value=list(self.overlayfiles.keys())[0],
                description='Overlay:'
            )

        interact(self._plot_surface, frame=frame, **kwargs)
        display(self.fig)
