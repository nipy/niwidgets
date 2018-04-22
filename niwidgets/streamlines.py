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
    Turns nibabel track files into interactive plots using ipyvolume.

    Color for each line is rendered as a function of the endpoints of the
    streamline. Currently, this resolves to red for left-right, green for
    anterior-posterior, and blue for inferior-superior.

    Args
    ----
        filename : str, pathlib.Path
                The path to your ``.trk`` file. Can be a string, or a
                ``PosixPath`` from python3's pathlib.
        streamlines : a nibabel streamline object
                An streamlines attribute of an object loaded by
                nibabel.streamlines.load
    """

    def __init__(self, filename=None, streamlines=None):

        if filename:
            if not os.path.isfile(str(filename)):
                # for Python3 should have FileNotFoundError here
                raise IOError('file {} not found'.format(filename))

            if not nib.streamlines.is_supported(str(filename)):
                raise ValueError(('File {0} is not a streamline file supported'
                                  ' by nibabel').format(filename))

            # load data in advance
            self.streamlines = nib.streamlines.load(str(filename)).streamlines
        elif streamlines:
            self.streamlines = streamlines
        else:
            raise ValueError('One of filename or streamlines must be specified'
                             )
        self.lines2use_ = None

    def plot(self, display_fraction=0.1, **kwargs):
        """
        This is the main method for this widget.

        Args
        ----
            display_fraction : float
                    The fraction of streamlines to show
            percentile : int
                    The initial number of streamlines to show using a
                    percentile of length distribution
            width : int
                    The width of the figure
            height : int
                    The height of the figure
        """

        if display_fraction is not None and (display_fraction > 1 or
                                             display_fraction <= 0):
            raise ValueError('proportion_to_display is a float between 0 and 1'
                             ' (0 excluded) or None')

        N = len(self.streamlines)
        num_streamlines = int(display_fraction * N)
        indices = np.random.permutation(N)[:num_streamlines]
        self.lines2use_ = self.streamlines[indices]
        self._default_plotter(**kwargs)

    def _create_mesh(self, indices2use=None):
        if indices2use is None:
            lines2use = self.lines2use_
            local_colors = self.colors
        else:
            lines2use = self.lines2use_[indices2use]
            local_colors = self.colors[indices2use]
        x, y, z = np.concatenate(lines2use).T

        # will contain indices to the verties, [0, 1, 1, 2, 2, 3, 3, 4, 4, 5..]
        indices = np.zeros(np.sum((len(line) - 1) * 2 for
                                  line in lines2use), dtype=np.uint32)
        colors = np.zeros((len(x), 3), dtype=np.float32)

        vertex_offset = 0
        line_offset = 0
        line_pointers = []
        # if we have a line of 4 vertices, we need to add the indices:
        #  offset + [0, 1, 1, 2, 2, 3]
        # so we have approx 2x the number of indices compared to vertices
        for idx, line in enumerate(lines2use):
            line_length = len(line)
            # repeat all but the start and end vertex
            line_indices = np.repeat(np.arange(vertex_offset,
                                               vertex_offset + line_length,
                                               dtype=indices.dtype), 2)[1:-1]
            indices[line_offset:
                    line_offset + line_length * 2 - 2] = line_indices
            line_pointers.append([line_offset, line_length, line_indices])
            colors[vertex_offset:
                   vertex_offset + line_length] = local_colors[idx]
            line_offset += line_length * 2 - 2
            vertex_offset += line_length
        return x, y, z, indices, colors, line_pointers

    def _default_plotter(self, **kwargs):
        """
        Basic plot function to be used if no custom function is specified.

        This is called by plot, you shouldn't call it directly.
        """

        self.lengths = np.array([length(x) for x in self.lines2use_])
        if not('grayscale' in kwargs and kwargs['grayscale']):
            self.colors = np.array([color(x) for x in self.lines2use_])
        else:
            self.colors = np.zeros((len(self.lines2use_), 3), dtype=np.float16)
            self.colors[:] = [0.5, 0.5, 0.5]
        self.state = {'threshold': 0, 'indices': []}

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

        with fig.hold_sync():
            x, y, z, indices, colors, self.line_pointers = self._create_mesh()
            limits = np.array([min([x.min(), y.min(), z.min()]),
                               max([x.max(), y.max(), z.max()])])
            mesh = ipv.Mesh(x=x, y=y, z=z, lines=indices, color=colors)
            fig.meshes = [mesh]
            if 'style' not in kwargs:
                fig.style = {'axes': {'color': 'black',
                                      'label': {'color': 'black'},
                                      'ticklabel': {'color': 'black'},
                                      'visible': False},
                             'background-color': 'white',
                             'box': {'visible': False}}
            else:
                fig.style = kwargs['style']
            ipv.pylab._grow_limits(limits, limits, limits)
            fig.camera_fov = 1
        ipv.show()

        interact(self._plot_lines, state=fixed(self.state),
                 threshold=widgets.FloatSlider(
                     value=np.percentile(self.lengths, perc),
                     min=self.lengths.min() - 1,
                     max=self.lengths.max() - 1,
                     continuous_update=False))

    def _plot_lines(self, state, threshold):
        """
        Plots streamlines

        This function is called by _default_plotter
        """
        if threshold < state['threshold']:
            # when threshold is reduced, increase the number of lines
            state['indices'] = np.where(self.lengths > threshold)[0]
            with state['fig'].hold_sync():
                mesh = state['fig'].meshes[0]
                copy = mesh.lines.copy()
                for idx in state['indices']:
                    (line_offset, line_length,
                     line_indices) = self.line_pointers[idx]
                    copy[line_offset:line_offset + line_length * 2 - 2] = \
                        line_indices
                mesh.lines = copy
                mesh.send_state('lines')
        else:
            # when threshold is increased, decrease the number of lines
            indices = np.where(self.lengths <= threshold)[0]
            with state['fig'].hold_sync():
                mesh = state['fig'].meshes[0]
                copy = mesh.lines.copy()
                for idx in indices:
                    (line_offset, line_length,
                     line_indices) = self.line_pointers[idx]
                    copy[line_offset:line_offset + line_length * 2 - 2] = 0
                mesh.lines = copy
                mesh.send_state('lines')
            state['indices'] = np.where(self.lengths > threshold)[0]
        state['threshold'] = threshold
