"""Example files for use with niwidgets."""
from pathlib import Path


root_dir = Path(__file__).parent / 'data'

exampleatlas = root_dir / 'cc400_roi_atlas.nii'
examplezmap = root_dir / 'cognitive control_pFgA_z.nii.gz'
examplet1 = root_dir / 'T1.nii.gz'

surface_dir = root_dir / 'example_surfaces'

examplesurface = surface_dir / 'lh.inflated'
exampleoverlays = [
    surface_dir / f
    for f in ('lh.area', 'lh.curv', 'lh.thickness', 'lh.aparc.annot')
]
