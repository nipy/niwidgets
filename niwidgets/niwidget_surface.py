"""A widget for surface-warped neuroimaging data."""
from __future__ import print_function
import nibabel as nb
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import display
from ipywidgets import interact, fixed, IntSlider
# from ipyvolume import gcf
import ipyvolume.pylab as p3
import os
from pathlib import Path


class SurfaceWidget:
    """Interact with brain surfaces right in the notebook."""

    def __init__(self, meshfile, overlayfiles=[]):
        """
        Create a surface widget.

        meshfile: file containing the
                  (1) 3D coordinates of each vertex (V x 3 array, where
                  V=#vertices)
                  (2) triangle specifications (T x 3 array, where T=#triangles)
                  Can be a FreeSurfer (i.e., lh.pial) or .gii mesh file

        overlayfiles: overlay file containing the scalar value at each vertex
                      (V x 1)
                      Can be a FreeSurfer .annot, .thickness, .curv, .sulc;
                      or .gii

        """
        self.meshfile = meshfile
        self.overlayfiles = overlayfiles
        #self.meshes = None
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

        # we draw the tetrahedron
        p3.plot_trisurf(x, y, z, triangles=triangles, color=np.ones((len(x),3)))
        #p3.show()

    def _plot_surface(self, x, y, z, triangles,
                      overlays=None, frame=0,
                      colormap='summer',
                      figsize=np.array([600,600]),
                      figlims=np.array([[-100,100],[-100,100],[-100,100]])):
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
        if overlays is not None:
            activation = overlays[:, frame]
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
        mask_keep: np.ndarray
            Boolean array of what to show.
        mask_kill: np.ndarray
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
        """
        Visualise a surface mesh (with overlay) inside notebooks.

        Basic functionality:
        Read mesh and overlay data
        Setup the interactive widget
        Set defaults for plotting

        Parameters
        ----------
        surface: str, gifti object
            Path to surface file in gifti or FS surface format or an
            already loaded gifti object of surface
        overlay: str, gifti object
            Path to overlay file in gifti or FS annot or anatomical
            (.curv,.sulc,.thickness) format or an already loaded
            gifti object of overlay, default None
        colormap: string
            A matplotlib colormap, default summer
        figsize: ndarray
            Size of the figure to display, default [600,600]
        figlims: ndarray
            x,y and z limits of the axes, default
            [[-100,100],[-100,100],[-100,100]]
        show_zeroes: bool
            Display vertices with intensity = 0, default True

        """
        # set default colormap options & add them to the kwargs
        if colormap is None:
            kwargs['colormap'] = ['viridis'] + \
                sorted(m for m in plt.cm.datad if not m.endswith("_r"))
        elif type(colormap) is str:
            # fix cmap if only one given
            kwargs['colormap'] = fixed(colormap)

        kwargs['figsize'] = fixed(figsize)
        kwargs['figlims'] = fixed(figlims)


        if isinstance(self.meshfile,str):
            if not os.path.exists(self.meshfile):
                raise IOError('File does not exist, please provide a valid file path to a gifti or FreeSurfer file.')
            filename, file_extension = os.path.splitext(self.meshfile)
            if file_extension is '.gii':
                mesh = nb.load(self.meshfile)
                try:
                    vertex_spatial=mesh.darrays[0].data
                    vertex_edges=mesh.darrays[1].data
                    x, y, z = vertex_spatial.T
                except:
                    raise ValueError('Please provide a valid gifti file.')
            else:
                fsgeometry = nb.freesurfer.read_geometry(self.meshfile)
                x,y,z = fsgeometry[0].T
                vertex_edges=fsgeometry[1]

        if isinstance(self.meshfile,nb.gifti.gifti.GiftiImage):
            try:
                vertex_spatial=self.meshfile.darrays[0].data
                vertex_edges=self.meshfile.darrays[1].data
                x, y, z = vertex_spatial.T
            except:
                raise ValueError('Please provide a valid gifti file.')

        if isinstance(self.overlayfiles,list):
            max_frame = len(self.overlayfiles)-1
        else:
            max_frame = 0
            self.overlayfiles = [self.overlayfiles] # hack

        overlays = np.zeros((len(x),len(self.overlayfiles)))
        for ii, overlayfile in enumerate(self.overlayfiles):
            if isinstance(overlayfile,str):
                if not os.path.exists(overlayfile):
                    raise IOError('File does not exist, please provide a valid file path to a gifti or FreeSurfer file.')
        if len(self.overlayfiles) > 0:
            overlays = np.zeros((len(x), len(self.overlayfiles)))
            for i, overlayfile in enumerate(self.overlayfiles):

                filename, file_extension = os.path.splitext(overlayfile)

                if file_extension is '.gii':
                    overlay = nb.load(overlayfile)
                    try:
                        overlays[:, i] = overlay.darrays[0].data
                    except:
                        raise ValueError('Please provide a valid gifti file')

                elif (file_extension in ('.annot', '')):
                    annot = nb.freesurfer.read_annot(overlayfile)
                    overlays[:, i] = annot[0]

                elif (file_extension in ('.curv', '.thickness', '.sulc')):
                    overlays[:, i] = nb.freesurfer.read_morph_data(overlayfile)

                if isinstance(overlayfile, nb.gifti.gifti.GiftiImage):
                    try:
                        overlays[:, i] = overlayfile.darrays[0].data
                    except:
                        raise ValueError('Please provide a valid gifti file')

                if not show_zeroes:
                    pass
                    # try:
                    #     mkeep, mkill = self.zmask(surface, overlay)
                    # except:
                    #     raise ValueError(
                    #         'Overlay required for medial wall masking.'
                    #         )
        else:
            overlays = None

        kwargs['triangles'] = fixed(vertex_edges)
        kwargs['x'] = fixed(x)
        kwargs['y'] = fixed(y)
        kwargs['z'] = fixed(z)
        kwargs['overlays'] = fixed(overlays)

        if len(self.overlayfiles) < 2:
            frame = fixed(0)
        else:
            frame = IntSlider(value=0, min=0, max=len(self.overlayfiles) - 1)

        interact(self._plot_surface, frame=frame, **kwargs)
        display(self.fig)
