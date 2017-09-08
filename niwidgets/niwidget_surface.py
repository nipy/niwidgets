from __future__ import print_function
import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import interact, fixed
import os
import inspect
import scipy.ndimage

class SurfaceWidget:
    def __init__(self, meshfile, overlayfiles):
        if not os.path.isfile(meshfile):
            # for Python3 should have FileNotFoundError here
            raise IOError('file {} not found'.format(meshfile))
        for overlayfile in overlayfiles:
            if not os.path.isfile(overlayfile):
                # for Python3 should have FileNotFoundError here
                raise IOError('file {} not found'.format(overlayfile))
        self.meshfile = meshfile
        self.overlayfiles = overlayfiles
        self.image_handles = None

    def 
