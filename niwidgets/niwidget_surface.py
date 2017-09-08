from __future__ import print_function
import nibabel as nb
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import interact, fixed, IntSlider
import ipyvolume.pylab as p3
import ipyvolume.widgets as ipv
import os
import inspect
import scipy.ndimage


class SurfaceWidget:
    def __init__(self, meshfile, overlayfiles):
        self.meshfile = meshfile
        self.overlayfiles = overlayfiles
        self.meshes = None

    def _init_figure(self, x, y, z, triangles, figsize, figlims):
        #fig = gcf()

        fig = p3.figure(width=figsize[0], height=figsize[1])
        fig.camera_fov = 1
        fig.style = {'axes': {'color': 'black',
                     'label': {'color': 'black'},
                     'ticklabel': {'color': 'black'},
                     'visible': False},
                     'background-color': 'white',
                     'box': {'visible': False}}
        fig.xlim = (figlims[0][0], figlims[0][1])
        fig.ylim = (figlims[1][0], figlims[1][1])
        fig.zlim = (figlims[2][0], figlims[2][1])

        p3.figure()
        # we draw the tetrahedron
        mesh = p3.plot_trisurf(x, y, z, triangles=triangles,
                               color=np.ones((len(x),3)))

        '''
        if triangles is not None:
            triangles = np.array(triangles).astype(dtype=np.uint32)

        mesh = p3.Mesh(x=x, y=y, z=z, triangles=triangles,
                        lines=None, color=np.ones([len(x),3]),
                        u=u, v=v, texture=texture)

        # can comment out if there are problems
        mesh._grow_limits(np.array(x).reshape(-1), np.array(y).reshape(-1), np.array(z).reshape(-1))
        '''

        self.meshes.append(mesh)

    def _plot_surface(self, x, y, z, triangles,
                      overlays=None, frame=0,
                      colormap='summer',
                      figsize=np.array([600,600]),
                      figlims=np.array([[-100,100],[-100,100],[-100,100]])):
        if self.meshes is None:
            self.meshes = []
            self._init_figure(x, y, z, triangles, figsize, figlims)

        # overlays is a 2D matrix
        # with 2nd dimension corresponding to (time) frame
        my_color = plt.cm.get_cmap(colormap)
        activation = overlays[:,frame]
        colors=my_color((activation-min(activation))/(max(activation)-min(activation)))
        print(colors)
        self.meshes[0].color = colors[:,:3]
        p3.show()

    def surface_plotter(self, colormap=None,
                        figsize=np.array([600,600]),
                        figlims=np.array([[-100,100],[-100,100],[-100,100]]),
                        **kwargs):
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
                error('File does not exist, please provide a valid file path to a gifti or FreeSurfer file.')
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
                fsgeometry = nb.freesurfer.read_geometry(mesh)
                x,y,z = fsgeometry[0].T
                vertex_edges=fsgeometry[1]

        if isinstance(self.meshfile,nb.gifti.gifti.GiftiImage):
            try:
                vertex_spatial=self.meshfile.darrays[0].data
                vertex_edges=self.meshfile.darrays[1].data
                x, y, z = vertex_spatial.T
            except:
                raise ValueError('Please provide a valid gifti file.')

        print(x.shape)
        print(y.shape)
        print(z.shape)

        if isinstance(self.overlayfiles,list):
            max_frame = len(self.overlayfiles)-1
        else:
            max_frame = 0
            self.overlayfiles = [self.overlayfiles] # hack

        overlays = np.zeros((len(x),len(self.overlayfiles)))
        for ii, overlayfile in enumerate(self.overlayfiles):
            if isinstance(overlayfile,str):
                if not os.path.exists(overlayfile):
                    error('File does not exist, please provide a valid file path to a gifti or FreeSurfer file.')
                filename, file_extension = os.path.splitext(overlayfile)

                if file_extension is '.gii':
                    overlay = nb.load(overlayfile)
                    try:
                        overlays[:,ii]=overlay.darrays[0].data
                    except:
                        raise ValueError('Please provide a valid gifti file')
                elif (file_extension in ('.annot','')):
                    annot = nb.freesurfer.read_annot(overlayfile)
                    overlays[:,ii] = annot[0]
                elif (file_extension in ('.curv','.thickness','.sulc')):
                    overlays[:,ii] = nb.freesurfer.read_morph_data(overlayfile)

            if isinstance(overlayfile,nb.gifti.gifti.GiftiImage):
                try:
                    overlays[:,ii]=overlayfile.darrays[0].data
                except:
                    raise ValueError('Please provide a valid gifti file')

        kwargs['triangles'] = fixed(vertex_edges)
        kwargs['x'] = fixed(x)
        kwargs['y'] = fixed(y)
        kwargs['z'] = fixed(z)
        kwargs['overlays'] = fixed(overlays)

        interact(self._plot_surface,
                 frame=IntSlider(default=0,
                                 min=0,
                                 max=max_frame),
                 **kwargs)
