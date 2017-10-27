from __future__ import print_function
import nibabel as nib
import numpy as np
from ipywidgets import interact, fixed, widgets
import os
import ipyvolume as ipv

def length(x):
    """Returns the sum of euclidean distances between neighboring points"""
    return np.sum(np.sqrt(np.sum((x[:-1, :] - x[1:, :]) *
                                 (x[:-1, :] - x[1:, :]),
                                 axis=1)))


def color(x):
    """Returns an approximation for color of line based on its endpoints"""
    dirvec = (x[0, :] - x[-1, :])
    return (dirvec/(np.sqrt(np.sum(dirvec*dirvec, axis=-1)))).dot(np.eye(3))


class StreamlineWidget:
    """
    Turns mrtrix track or trackvis files into interactive plots using ipyvolume

    Args
    ----
        filename : str
                The path to your ``.trk`` file. Can be a string, or a
                ``PosixPath`` from python3's pathlib.
    """

    def __init__(self, filename):

        if not os.path.isfile(filename):
            # for Python3 should have FileNotFoundError here
            raise IOError('file {} not found'.format(filename))

        if not nib.streamlines.is_supported(filename):
            raise ValueError(('File {0} is not a streamline file supported '
                              'by nibabel').format(filename))

        self.filename = filename

    def plot(self, skip=100, **kwargs):
        """
        This is the main method for this widget.

        Args
        ----
            skip : int
                    The number of streamlines to skip
            percentile : int
                    The initial number of streamlines to show using a percentile
                    of length distribution
            width : int
                    The width of the figure
            height : int
                    The height of the figure
        """

        self._default_plotter(skip=skip, **kwargs)

    def _create_mesh(self, indices2use=None):
        if indices2use is None:
            lines2use = self.lines2use
            local_colors = self.colors
        else:
            lines2use = self.lines2use[indices2use]
            local_colors = self.colors[indices2use]
        x, y, z = np.concatenate(lines2use).T

        # will contain indices to the verties, [0, 1, 1, 2, 2, 3, 3, 4, 4, 5...]
        indices = np.zeros(np.sum((len(line) - 1) * 2 for
                                  line in lines2use), dtype=np.uint32)
        colors = np.zeros((len(x), 3), dtype=np.float32)

        vertex_offset = 0
        line_offset = 0
        # so basically of we have a line of 4 vertices, we need to add the indices:
        #  offset + [0, 1, 1, 2, 2, 3]
        # so we have approx 2x the number of indices compared to vertices
        for idx, line in enumerate(lines2use):
            line_length = len(line)
            # repeat all but the start and end vertex
            line_indices = np.repeat(np.arange(vertex_offset,
                                               vertex_offset + line_length,
                                               dtype=indices.dtype), 2)[1:-1]
            indices[line_offset:line_offset + line_length * 2 - 2] = line_indices
            colors[vertex_offset:vertex_offset + line_length] = local_colors[idx]
            line_offset += line_length * 2 - 2
            vertex_offset += line_length
        return x, y, z, indices, colors

    def _default_plotter(self, skip=100, **kwargs):
        """
        Basic plot function to be used if no custom function is specified.

        This is called by plot, you shouldn't call it directly.
        """

        # load data in advance
        sl = nib.streamlines.load(self.filename)

        self.lines2use = sl.streamlines[::skip]
        self.lengths = np.array([length(x) for x in self.lines2use])
        if not('grayscale' in kwargs and kwargs['grayscale']):
            self.colors = np.array([color(x) for x in self.lines2use])
        else:
            self.colors = np.zeros((len(self.lines2use), 3), dtype=np.float16)
            self.colors[:] = [0.5, 0.5, 0.5]
        self.state = {'threshold': np.inf, 'indices': []}

        width = 600
        height = 600
        perc = 80
        if 'width' in kwargs:
            width = kwargs['width']
        if 'height' in kwargs:
            height = kwargs['height']
        if 'percentile' in kwargs:
            perc = kwargs['percentile']

        ipv.clear()
        fig = ipv.figure(width=width, height=height)
        self.state['fig'] = fig

        if 'style' not in kwargs:
            fig.style = {'axes': {'color': 'black',
                                  'label': {'color': 'black'},
                                  'ticklabel': {'color': 'black'},
                                  'visible': False},
                         'background-color': 'white',
                         'box': {'visible': False}}
        else:
            fig.style = kwargs['style']
        '''
        with fig.hold_sync():
            x, y, z, indices, colors = self._create_mesh()
            if 'grayscale' in kwargs and kwargs['grayscale']:
                mesh = ipv.Mesh(x=x, y=y, z=z, lines=indices, color=[0.5, 0.5, 0.5])
            else:
                mesh = ipv.Mesh(x=x, y=y, z=z, lines=indices, color=colors)

            fig.meshes = list(fig.meshes) + [mesh]
        '''
        ipv.show()

        interact(self._plot_lines, state=fixed(self.state),
                 threshold=widgets.FloatSlider(value=np.percentile(self.lengths,
                                                                   perc),
                                               min=self.lengths.min() - 1,
                                               max=self.lengths.max() + 1,
                                               continuous_update=False));

    def _plot_lines(self, state, threshold):
        """
        Plots streamlines

        This function is called by _default_plotter
        """
        if threshold < state['threshold']:
            indices = np.setdiff1d(np.where(self.lengths > threshold)[0],
                                   state['indices'])
            state['indices'] = np.concatenate((state['indices'], indices)).astype(int)
        else:
            indices = np.setdiff1d(state['indices'],
                                   np.where(self.lengths > threshold)[0].astype(int))
            state['indices'] = np.setdiff1d(state['indices'], indices)
        state['threshold'] = threshold
        with state['fig'].hold_sync():
            fig = state['fig']
            print(len(state['indices']))
            x, y, z, indices, colors = self._create_mesh(indices2use=state['indices'])
            print(len(x))
            mesh = ipv.Mesh(x=x, y=y, z=z, lines=indices, color=colors)
            '''
            meshes = list(fig.meshes)
            if meshes:
                meshes.pop()
                fig.meshes = meshes
            '''
            fig.meshes = [mesh]
            ipv.pylab._grow_limits(y, y, y)  # may chance in the future.. ?
            fig.camera_fov = 1
            fig.meshes[0].send_state()

