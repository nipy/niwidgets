from __future__ import print_function
import nilearn.plotting as nip
import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import interact,fixed
import inspect

class NiWidget:
    def __init__(self,filename,plotthis='dataobj'):
        self.filename = filename
        


    def plot_slices(self, data, x, y, z, Colormap='viridis'):

        fig,axes=plt.subplots(1,3, figsize = (15, 5))
        axes[0].imshow(np.rot90(data[:,y,:]), cmap = Colormap)
        axes[1].imshow(np.rot90(data[x,:,:]), cmap = Colormap)
        axes[2].imshow(np.rot90(data[:,:,z]), cmap = Colormap)
        plt.show()


    def plot_wrapper(self, data, **kwargs):
        self.plotting_func(data, **kwargs)
        plt.show()


    def nifti_plotter(self,plotting_func=None, **kwargs):
        
        self.plotting_func = plotting_func
        #if no plotting function is specified: use default
        if self.plotting_func is None:
            self.data = nib.load(self.filename).dataobj
            kwargs = {'x': (0,self.data.shape[0]-1),
                         'y': (0,self.data.shape[1]-1),
                         'z': (0,self.data.shape[2]-1),
                         'Colormap': ['jet','viridis','gray']
                         }         
            interact(self.plot_slices, data = fixed(self.data), **kwargs)

        else:
            self.data = nib.load(self.filename)
            interact(self.plot_wrapper, data=fixed(self.data), **kwargs)