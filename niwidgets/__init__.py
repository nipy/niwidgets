from __future__ import print_function
import nilearn.plotting as nip
import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import interact,fixed
import inspect
import os

# define the example data
root_dir, _ = os.path.split(__file__)
exampleatlas = os.path.join(root_dir, 'data', 'cc400_roi_atlas.nii')
examplezmap = os.path.join(root_dir, 'data', 'cognitive control_pFgA_z_FDR_0.01.nii.gz')
examplet1 = os.path.join(root_dir, 'data', 'T1.nii.gz')

class NiWidget:
    def __init__(self,filename,plotthis='dataobj'):
        self.filename = filename
        
    
    def plot_slices(self,data,x, y, z, colormap='viridis',figsize=(15,5)):
        """
        plots x,y,z slices
        """
        fig,axes=plt.subplots(1,3, figsize = figsize)
        axes[0].imshow(np.rot90(data[:,y,:]), cmap = colormap)
        axes[1].imshow(np.rot90(data[x,:,:]), cmap = colormap)
        axes[2].imshow(np.rot90(data[:,:,z]), cmap = colormap)
        plt.show()
        
    def default_plotter(self,**kwargs):
        """
        basic plot function to be used if no custom function is specified
        """
        
        # load data in advance
        self.data = nib.load(self.filename).dataobj
        
        # set default x y z values
        for dim, label in enumerate(['x', 'y', 'z']):
            if label not in kwargs.keys():
                kwargs[label] = (0,self.data.shape[dim]-1)
        
        # set default colormap
        if 'colormap' not in kwargs.keys():
            kwargs['colormap'] = ['viridis'] + sorted(m for m in plt.cm.datad if not m.endswith("_r"))
        elif len([kwargs['colormap']]) == 1:
            # fix cmap if only one given
            kwargs['colormap'] = fixed(kwargs['colormap'])
        
        # set default figure size
        if 'figsize' not in kwargs.keys():
            kwargs['figsize'] = fixed((15,5))
            
        interact(self.plot_slices, data = fixed(self.data), **kwargs)

        
    def _custom_plot_wrapper(self, data, **kwargs):
        """
        plot wrapper for custom function
        """
        if 'colormap' in kwargs.keys():
            self.colormap = kwargs['colormap']
            kwargs.pop('colormap', None)
        self.plotting_func(data,**kwargs)
        plt.set_cmap(self.colormap)
        plt.show()

    def custom_plotter(self,plotting_func,**kwargs):
        """
        collects data and starts interactive widget for custom plot
        """
        if 'colormap' not in kwargs.keys():
            kwargs['colormap'] = ['viridis'] + sorted(m for m in plt.cm.datad if not m.endswith("_r"))
        elif len([kwargs['colormap']]) == 1:
            # fix cmap if only one given
            kwargs['colormap'] = fixed(kwargs['colormap'])

        #gets name first argument, assuming this takes the filename 
        #argname = inspect.getargspec(plotting_func).args[0]
        #kwargs[argname] = fixed(self.filename
        #interact(self._custom_plot_wrapper,plotting_func=fixed(plotting_func),**kwargs)
        self.plotting_func = plotting_func
        self.data = nib.load(self.filename)
        
        interact(self._custom_plot_wrapper, data=fixed(self.data), **kwargs)
        
        
    def nifti_plotter(self,plotting_func=None,**kwargs):
        """
        main function to be called from outside
        """
        if plotting_func is None:
            self.default_plotter(**kwargs)
        else:
            self.custom_plotter(plotting_func,**kwargs)




# class NiWidget:
#     def __init__(self,filename,plotthis='dataobj'):
#         self.filename = filename
        


#     def plot_slices(self, data, x, y, z, Colormap='viridis'):

#         fig,axes=plt.subplots(1,3, figsize = (15, 5))
#         axes[0].imshow(np.rot90(data[:,y,:]), cmap = Colormap)
#         axes[1].imshow(np.rot90(data[x,:,:]), cmap = Colormap)
#         axes[2].imshow(np.rot90(data[:,:,z]), cmap = Colormap)
#         plt.show()


#     def plot_wrapper(self, data, **kwargs):
#         self.plotting_func(data, **kwargs)
#         plt.show()


#     def nifti_plotter(self,plotting_func=None, **kwargs):
        
#         self.plotting_func = plotting_func
#         #if no plotting function is specified: use default
#         if self.plotting_func is None:
#             self.data = nib.load(self.filename).dataobj
#             kwargs = {'x': (0,self.data.shape[0]-1),
#                          'y': (0,self.data.shape[1]-1),
#                          'z': (0,self.data.shape[2]-1),
#                          'Colormap': ['jet','viridis','gray']
#                          }         
#             interact(self.plot_slices, data = fixed(self.data), **kwargs)

#         else:
#             self.data = nib.load(self.filename)
#             interact(self.plot_wrapper, data=fixed(self.data), **kwargs)