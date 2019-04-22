"""Example files for use with niwidgets."""
__all__ = ['exampleatlas', 'examplezmap', 'examplet1',
           'examplesurface', 'exampleoverlays', 'streamlines']

import os.path

root_dir = os.path.join(os.path.dirname(__file__), 'data')

exampleatlas = os.path.join(root_dir, 'cc400_roi_atlas.nii')
examplezmap = os.path.join(root_dir, 'cognitive control_pFgA_z.nii.gz')
examplet1 = os.path.join(root_dir, 'T1.nii.gz')

surface_dir = os.path.join(root_dir, 'example_surfaces')

examplesurface = os.path.join(surface_dir, 'lh.inflated')

exampleoverlays = {
    key: os.path.join(surface_dir, f)
    for key, f in zip(['Area', 'Curvature', 'Thickness', 'Annotation'],
                      ('lh.area', 'lh.curv', 'lh.thickness', 'lh.aparc.annot'))
}

streamlines = os.path.join(root_dir, 'streamlines.trk')
