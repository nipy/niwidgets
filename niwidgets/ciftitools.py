from __future__ import print_function
import os, sys, time
import numpy as np
import nibabel as nb

#class CiftiTools:
#    '''
#    Tools to manipulate cifti files and prepare them for display.
#    '''
#
#    def __init__(self, filename):
#        if not os.path.exists(filename):
#            raise ValueError('File {}does not exist, please provide a valid path.'.format(filename))
#        self.filename=filename

def cread(infile):
    '''
    Loads a cifti file and stores as five objects: data array, cifti header, nifti header, extra metadata, filemap
    Example call:
        cd,ch,cn,cx,cf=cread(path_to_cifti)
    
    Parameters
    ----------
    infile: str, Cifti2Image
        string containing path to cifti file or an already loaded cifti object
    '''
    if isinstance(infile,nb.cifti2.cifti2.Cifti2Image):
        try:
            cin=infile
        except:
            raise ValueError('Please provide a valid cifti file.')
    elif isinstance(infile,str):
        if not os.path.exists(infile):
            raise ValueError('File does not exist, please provide a valid path to a cifti file.')
        try:
            cin=nb.load(infile) # NB causes apparently benign warning as of NiBabel version 2.2.0dev
        except:
            raise ValueError('Please provide a valid cifti file.')
    cdata=np.asarray(cin.get_data()).copy()
    chead=cin.header.copy()
    cnhdr=cin.nifti_header.copy()
    cxtra=cin.extra.copy()
    cfmap=cin.file_map.copy()
    return cdata,chead,cnhdr,cxtra,cfmap

def csave(filename,cdata,chead,cnhdr=None,cxtra=None,cfmap=None,returnImg=False):
    '''
    Saves a cifti image from a collection of cifti substructures to file.
    
    Parameters
    ----------
    filename: str
        string containing output file path
    cdata: numpy ndarray
        array containing data to be saved, can be 1D (single timepoint) or 2D (timeseries)
    chead: Cifti2Header
        cifti header data, generally extracted from a previously read cifti file
    cnhdr: Nifti2Header (optional)
        nifti header data, also generally extracted from a previously read cifti file
    cxtra: dict (optional)
        extra cifti metadata, generally empty
    cfmap: dict (optional)
        file map, generally contains the string 'image'
    returnImg: bool
        optionally return the compiled cifti object
    '''
    cout=nb.Cifti2Image(dataobj=cdata,header=chead,nifti_header=cnhdr, extra=cxtra, file_map=cfmap)
    cout.to_filename(filename)
    if returnImg is True:
        return cout

def clthresh(data,thresh,setTo=0):
    '''
    Set all values below threshold for a cifti file to a given value (default 0).
    
    Parameters
    ----------
    data: numpy ndarray
        array containing data to be thresholded
    thresh: float
        Threshold value (exclusive)
    setTo: float
        Value to which voxels/vertices are set if below the threshold, default 0
    '''
    # 
    lthr_data=data.copy()
    lthr_data[lthr_data<thresh]=setTo
    return lthr_data

def cuthresh(data,thresh,setto=0):
    '''
    Set all values above threshold for a cifti file to a given value (default 0).
    
    Parameters
    ----------
    data: numpy ndarray
        array containing data to be thresholded
    thresh: float
        Threshold value (exclusive)
    setTo: float
        Value to which voxels/vertices are set if above the threshold, default 0
    '''
    # set all values above threshold to a given value (default 0)
    uthr_data=data.copy()
    uthr_data[uthr_data>thresh]=setto
    return uthr_data

def cmask(target,mask):
    '''
    Masks target cifti file with non-zero values of mask cifti file
    
    Parameters
    ----------
    target: numpy ndarray
        numpy array containing cifti data to be masked
    mask: numpy ndarray
        numpy array containing cifti data to use as mask. Can be 1D or 2D, must match target spatial dimensions.
    '''
    masked_data=target.copy()
    if target.shape != mask.shape:
        mask=np.tile(mask,(target.shape[0],1))
    masked_data[mask==0]=0 # NB could be sped up by using a data dictionary, not currently high-priority
    return masked_data

def cinfo(infile):
    '''
    Returns information about input cifti header
    
    Parameters
    ----------
    infile: str, Cifti2Image
        string containing path to cifti file or an already loaded cifti object
    verbose: bool
        report relatively esoteric cifti header info
    '''
    if isinstance(infile,nb.cifti2.cifti2.Cifti2Header):
        ch=infile
    elif isinstance(infile,nb.cifti2.cifti2.Cifti2Image):
        cin=infile
        cd,ch,cn,cx,cf=cread(infile)
    elif isinstance(infile,str):
        if not os.path.exists(infile):
            raise ValueError('File does not exist, please provide a valid path to a cifti file.')
        try:
            cd,ch,cn,cx,cf=cread(infile)
        except:
            raise ValueError('Please provide a valid cifti file.')
    ch0=ch.get_index_map(0)
    ch1=ch.get_index_map(1)
    if ch.get_index_map(0).indices_map_to_data_type=='CIFTI_INDEX_TYPE_SERIES': # support for other cifti types pending
        print('cifti data dype = fMRI timeseries')
        me=ch1.volume.transformation_matrix_voxel_indices_ijk_to_xyz.meter_exponent
        if me==-3:
            units='MM'
        else:
            units='x10^{e} M'.format(e=me)
        print('Xdim = {x} {u} x {xx}'.format(
            x=np.abs(ch1.volume.transformation_matrix_voxel_indices_ijk_to_xyz.matrix[0,0]),
            u=units,
            xx=ch1.volume.volume_dimensions[0]))
        print('Ydim = {y} {u} x {yy}'.format(
            y=np.abs(ch1.volume.transformation_matrix_voxel_indices_ijk_to_xyz.matrix[1,1]),
            u=units,
            yy=ch1.volume.volume_dimensions[1]))
        print('Zdim = {z} {u} x {zz}'.format(
            z=np.abs(ch1.volume.transformation_matrix_voxel_indices_ijk_to_xyz.matrix[2,2]),
            u=units,
            zz=ch1.volume.volume_dimensions[2]))
        print('Tdim = {y} {z} x {t}'.format(
            y=ch.get_index_map(0).series_step,
            z=ch.get_index_map(0).series_unit,
            t=ch.get_index_map(0).number_of_series_points))
    disp=[]
    voxels=0
    print('INDEX      OFFSET     SIZE       STRUCTURE')
    for idx, bm in enumerate(ch1.brain_models):
        disp.append([idx,bm.index_offset,bm.index_count,bm.brain_structure])
        if bm.model_type=='CIFTI_MODEL_TYPE_VOXELS':
            voxels=voxels+bm.index_count
    col_width = max(len(str(word)) for row in disp for word in row) + 2  # padding
    for row in disp:
        print("{: <10} {: <10} {: <10} {: <20}".format(*row))
    print('total left cortex vertices = {lv} of {lt}'.format(
        lv=list(ch1.brain_models)[0].index_count,
        lt=list(ch1.brain_models)[0].surface_number_of_vertices))
    print('total right cortex vertices = {rv} of {rt}'.format(
        rv=list(ch1.brain_models)[1].index_count,
        rt=list(ch1.brain_models)[1].surface_number_of_vertices))
    print('total subcortical voxels = {v}'.format(v=voxels))
    print('total data points = {total}'.format(
        total=list(ch1.brain_models)[0].index_count+list(ch1.brain_models)[1].index_count+voxels))

def cvoxels(header,MNI=True,trim=False):
    '''
    Returns array where each element is an array of coordinates for a particular cifti brain structure.
    Coordinates can be voxel indices (i,j,k) or MNI coordinates (x,y,z; default).
    
    Parameters
    ----------
    header: Cifti2Header
        cifti header object containing the voxel index mapping and list of brain structures
    MNI: bool
        True returns MNI coordinates, False returns voxel indices, default=True
    trim: bool
        removes array elements corresponding to cortical surfaces, default=False
    '''
    if not isinstance(header,nb.cifti2.cifti2.Cifti2Header):
        raise ValueError('Please provide a valid cifti header.')

    ch1=header.get_index_map(1)
    voxarray=[]
    if MNI is True:
        from nibabel.affines import apply_affine
        warp=ch1.volume.transformation_matrix_voxel_indices_ijk_to_xyz.matrix
    for idx, bm in enumerate(ch1.brain_models):
        if bm.model_type=='CIFTI_MODEL_TYPE_VOXELS':
            if MNI is False:
                voxarray.append(np.asarray(bm.voxel_indices_ijk))
            else:
                voxarray.append(apply_affine(warp,bm.voxel_indices_ijk))
        else:
            if trim is False:
                voxarray.append([[],[],[]])
    return np.asarray(voxarray)

def csplit(incifti,gii=False):
    '''
    Split cifti overlay into separate left surface, right surface, and subcortical voxel arrays.
    
    Parameters
    ----------
    incifti: str, Cifti2Image
        string containing path to cifti file or an already loaded cifti object
    gii: bool
        returns surfaces as GiftiImage objects, default=False
    '''
    if isinstance(incifti,nb.cifti2.cifti2.Cifti2Image):
        cd=np.asarray(incifti.get_data()).copy()
        ch=incifti.header.copy()
    elif isinstance(incifti,str):
        if not os.path.exists(incifti):
            raise ValueError('File does not exist, please provide a valid path to a cifti file.')
        try:
            cd,ch,cn,cx,cf=cread(incifti)
        except:
            raise ValueError('Please provide a valid cifti file.')   
    mim = ch.matrix[1]
    bm1 = list(mim.brain_models)[0]
    bm2 = list(mim.brain_models)[1]
    lidx = list(bm1.vertex_indices)
    ridx = [bm1.surface_number_of_vertices + val for val in bm2.vertex_indices]
    bidx = np.concatenate((lidx, ridx))
    # split cifti overlay into left surface, right surface, and subcortical volume
    clh=cd[:,0:len(lidx)]
    crh=cd[:,len(lidx):len(lidx)+len(ridx)+1]
    csc=cd[:,len(lidx)+len(ridx)+1:cd.shape[1]]
    if gii is True:
        glh=nb.gifti.gifti.GiftiImage()
        grh=nb.gifti.gifti.GiftiImage()
        glh.add_gifti_data_array(nb.gifti.gifti.GiftiDataArray(clh))
        grh.add_gifti_data_array(nb.gifti.gifti.GiftiDataArray(crh))
        left=glh
        right=grh
    else:
        left=clh
        right=crh
    sub=csc # option for .nii format subcortex data pending
    return left, right, sub
