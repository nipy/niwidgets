from __future__ import print_function
import nibabel as nib
import numpy as np
from ipywidgets import interact, fixed, widgets
import os
import ipyvolume.pylab as p3


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
            colors = [color(x) for x in self.lines2use]
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

        p3.clear()
        fig = p3.figure(width=width, height=height)
        self.state['fig'] = fig

        with fig.hold_sync():
            if 'style' not in kwargs:
                fig.style = {'axes': {'color': 'black',
                                      'label': {'color': 'black'},
                                      'ticklabel': {'color': 'black'},
                                      'visible': False},
                             'background-color': 'white',
                             'box': {'visible': False}}
            else:
                fig.style = kwargs['style']
            fig.camera_fov = 1

            fig.xlim = tuple(sl.header['dimensions'].max() * np.array([0, 1]))
            fig.ylim = tuple(sl.header['dimensions'].max() * np.array([0, 1]))
            fig.zlim = tuple(sl.header['dimensions'].max() * np.array([0, 1]))
            for idx, line in enumerate(self.lines2use):
                if 'grayscale' in kwargs and kwargs['grayscale']:
                    p3.plot(*line.T, color=[0.5, 0.5, 0.5], visible_lines=False)
                else:
                    p3.plot(*line.T, color=colors[idx], visible_lines=False)
        p3.show()

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
            for idx in indices:
                state['fig'].scatters[idx].visible_lines = True
        else:
            indices = np.setdiff1d(state['indices'],
                                   np.where(self.lengths > threshold)[0].astype(int))
            for idx in indices:
                state['fig'].scatters[idx].visible_lines = False
            state['indices'] = np.setdiff1d(state['indices'], indices)
        state['threshold'] = threshold

