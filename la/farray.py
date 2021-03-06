"Functions that work with numpy arrays."

import numpy as np

from la.external.scipy import nanmedian, rankdata, nanstd, nanmean
from la.missing import nans, ismissing


# Group functions ----------------------------------------------------------

def group_ranking(x, groups, norm='-1,1', ties=True, axis=0):
    """
    Ranking within groups along axis.
    
    Parameters
    ----------
    x : ndarray
        Data to be ranked.
    groups : list
        List of group membership of each element along axis=0.
    norm : str
        A string that specifies the normalization:
        '0,N-1'     Zero to N-1 ranking
        '-1,1'      Scale zero to N-1 ranking to be between -1 and 1
        'gaussian'  Rank data then scale to a Gaussian distribution
    ties : bool
        If two elements of `x` have the same value then they will be ranked
        by their order in the array (False). If `ties` is set to True
        (default), then the ranks are averaged.
    axis : int, {default: 0}
        axis along which the ranking is calculated
        
    Returns
    -------
    idx : ndarray
        The ranked data. The dtype of the output is always np.float even if
        the dtype of the input is int.
    
    Notes
    ----
    If there is only one non-NaN value within a group along the axis=0, then
    that value is set to the midpoint of the specified normalization method.
    
    For '0,N-1' normalization, note that N is the number of element in the
    group even in there are NaNs.
    
    """
  
    # Find set of unique groups
    ugroups = unique_group(groups)
    
    # Convert groups to a numpy array
    groups = np.asarray(groups)
  
    # Loop through unique groups and normalize
    xnorm = np.nan * np.zeros(x.shape)
    for group in ugroups:
        idx = groups == group
        idxall = [slice(None)] * x.ndim
        idxall[axis] = idx
        xnorm[idxall] = ranking(x[idxall], axis=axis, norm=norm, ties=ties) 
           
    return xnorm

def group_mean(x, groups, axis=0):
    """
    Mean with groups along an axis.
    
    Parameters
    ----------
    x : ndarray
        Input data.
    groups : list
        List of group membership of each element along the axis.
    axis : int, {default: 0}
        axis along which the mean is calculated
        
    Returns
    -------
    idx : ndarray
        An array with the same shape as the input array where every element is
        replaced by the group mean along the given axis.

    """

    # Find set of unique groups
    ugroups = unique_group(groups)
    
    # Convert groups to a numpy array
    groups = np.asarray(groups)    
  
    # Loop through unique groups and normalize
    xmean = np.nan * np.zeros(x.shape)    
    for group in ugroups:
        idx = groups == group
        idxall = [slice(None)] * x.ndim
        idxall[axis] = idx
        if idx.sum() > 0:
            norm = 1.0 * (~np.isnan(x[idxall])).sum(axis)
            ns = np.nansum(x[idxall], axis=axis) / norm
            xmean[idxall] = np.expand_dims(ns, axis)
            
    return xmean

def group_median(x, groups, axis=0):
    """
    Median with groups along an axis.
    
    Parameters
    ----------
    x : ndarray
        Input data.
    groups : list
        List of group membership of each element along the given axis.
    axis : int, {default: 0}
        axis along which the ranking is calculated.
        
    Returns
    -------
    idx : ndarray
        The group median of the data along axis 0.

    """

    # Find set of unique groups
    ugroups = unique_group(groups)
    
    # Convert groups to a numpy array
    groups = np.asarray(groups)    
  
    # Loop through unique groups and normalize
    xmedian = np.nan * np.zeros(x.shape)
    for group in ugroups:
        idx = groups == group
        idxall = [slice(None)] * x.ndim
        idxall[axis] = idx
        if idx.sum() > 0:
            ns = nanmedian(x[idxall], axis=axis)
            xmedian[idxall] = np.expand_dims(ns, axis)
            
    return xmedian
    
def unique_group(groups):
    """Find unique groups in list not including None."""    
    ugroups = set(groups)
    ugroups -= set((None,))
    ugroups = list(ugroups)
    ugroups.sort()
    return ugroups    
    
# Normalize functions -------------------------------------------------------

def geometric_mean(x, axis=-1, check_for_greater_than_zero=True):
    """
    Return the geometric mean of matrix x along axis, ignore NaNs.
    
    Raise an exception if any element of x is zero or less.
     
    """
    if (x <= 0).any() and check_for_greater_than_zero:
        msg = 'All elements of x (except NaNs) must be greater than zero.'
        raise ValueError, msg
    x = x.copy()
    m = np.isnan(x)
    x[m] = 1.0
    m = np.asarray(~m, np.float64)
    m = m.sum(axis)
    x = np.log(x).sum(axis)
    g = 1.0 / m
    x = np.multiply(g, x)
    x = np.exp(x)
    idx = np.ones(x.shape)
    if idx.ndim == 0:
        if m == 0:
            idx = np.nan
    else:
        idx[m == 0] = np.nan
    x = np.multiply(x, idx)
    return x

@np.deprecate(new_name='mov_sum')
def movingsum(x, window, skip=0, axis=-1, norm=False):
    """Moving sum optionally normalized for missing (NaN) data."""
    return mov_sum(x, window, skip=skip, axis=axis, norm=norm)

def mov_sum(arr, window, skip=0, axis=-1, norm=False):
    """
    Moving sum ignoring NaNs, optionally normalized for missing (NaN) data.
    
    Parameters
    ----------
    arr : ndarray
        Input array.
    window : int
        The number of elements in the moving window.
    skip : int, optional
        By default (skip=0) the movingsum at element *i* is the sum over the
        slice of elements from *i + 1 - window* to *i + 1* (so the last element
        in the sum is *i*). With nonzero `skip` the sum is over the slice from
        *i + 1 window - skip* to *i + 1 - skip*.
    axis : int, optional
        The axis over which to perform the moving sum. By default the moving
        sum is taken over the last axis (-1).
    norm : bool, optional
        Whether or not to normalize the sum. The default is not to normalize.
        If there are 3 missing elements in a window, for example, then the
        normalization would be to multiply the sum in that window by
        *window / (window - 3)*.

    Returns
    -------
    y : ndarray
        The moving sum of the input array along the specified axis.

    Examples
    --------
    >>> arr = np.array([1, 2, 3, 4, 5])
    >>> mov_sum(arr, 2)
    array([ NaN,   3.,   5.,   7.,   9.])

    >>> arr = np.array([1, 2, np.nan, 4, 5])
    >>> mov_sum(arr, 2)
    array([ NaN,   3.,   2.,   4.,   9.])
    >>> mov_sum(arr, 2, norm=True)
    array([ NaN,   3.,   4.,   8.,   9.])    
    
    """
    if window < 1:  
        raise ValueError, 'window must be at least 1'
    if window > arr.shape[axis]:
        raise ValueError, 'Window is too big.'      
    if skip > arr.shape[axis]:
        raise IndexError, 'Your skip is too large.'
    m = ismissing(arr) 
    arr = 1.0 * arr
    arr[m] = 0
    csx = arr.cumsum(axis)
    index1 = [slice(None)] * arr.ndim 
    index1[axis] = slice(window - 1, None)
    index2 = [slice(None)] * arr.ndim 
    index2[axis] = slice(None, -window) 
    msx = csx[index1]
    index3 = [slice(None)] * arr.ndim
    index3[axis] = slice(1, None)
    msx[index3] = msx[index3] - csx[index2] 
    csm = (~m).cumsum(axis)     
    msm = csm[index1]
    msm[index3] = msm[index3] - csm[index2]  
    if norm:
        ms = 1.0 * window * msx / msm
    else:
        ms = msx
        ms[msm == 0] = np.nan
    initshape = list(arr.shape)  
    initshape[axis] = skip + window - 1
    #Note: skip could be included in starting window
    cutslice = [slice(None)] * arr.ndim   
    cutslice[axis] = slice(None, -skip or None, None)
    pad = np.nan * np.zeros(initshape)
    ms = np.concatenate((pad, ms[cutslice]), axis) 
    return ms

def movingsum_forward(x, window, skip=0, axis=-1, norm=False):
    """Movingsum in the forward direction skipping skip dates."""
    flip_index = [slice(None)] * x.ndim 
    flip_index[axis] = slice(None, None, -1)
    msf = movingsum(x[flip_index], window, skip=skip, axis=axis, norm=norm)
    return msf[flip_index]

def movingrank(x, window, axis=-1):
    """Moving rank (normalized to -1 and 1) of a given window along axis.

    Normalized for missing (NaN) data.
    A data point with NaN data is returned as NaN
    If a window is all NaNs except last, this is returned as NaN
    """
    if window > x.shape[axis]:
        raise ValueError, 'Window is too big.'
    if window < 2:
        raise ValueError, 'Window is too small.'
    nt = x.shape[axis]
    mr = np.nan * np.zeros(x.shape)        
    for i in xrange(window-1, nt): 
        index1 = [slice(None)] * x.ndim 
        index1[axis] = i
        index2 = [slice(None)] * x.ndim 
        index2[axis] = slice(i-window+1, i+1, None)
        mr[index1] = np.squeeze(lastrank(x[index2], axis=axis))
    return mr
   
def lastrank(x, axis=-1, decay=0.0):
    """
    The ranking of the last element along the axis, ignoring NaNs.
    
    The ranking is normalized to be between -1 and 1 instead of the more
    common 1 and N. The results are adjusted for ties. Suitably slicing
    the output of the `ranking` method will give the same result as
    `lastrank`. The only difference is that `lastrank` is faster.       

    Parameters
    ----------
    x : numpy array
        The array to rank.
    axis : int, optional
        The axis over which to rank. By default (axis=-1) the ranking
        (and reducing) is performed over the last axis.          
    decay : scalar, optional
        Exponential decay strength. Cannot be negative. The default
        (decay=0) is no decay. In normal ranking (decay=0) all elements
        used to calculate the rank are equally weighted and so the
        ordering of all but the last element does not matter. In
        exponentially decayed ranking the ordering of the elements
        influences the ranking: elements nearer the last element get more
        weight.
        
    Returns
    -------
    d : array
        In the case of, for example, a 2d array of shape (n, m) and
        axis=1, the output will contain the rank (normalized to be between
        -1 and 1 and adjusted for ties) of the the last element of each row.
        The output in this example will have shape (n,). 
            
    Examples
    -------- 
    Create an array:
                    
    >>> y1 = larry([1, 2, 3])
    
    What is the rank of the last element (the value 3 in this example)?
    It is the largest element so the rank is 1.0:
    
    >>> import numpy as np
    >>> from la.afunc import lastrank
    >>> x1 = np.array([1, 2, 3])
    >>> lastrank(x1)
    1.0
    
    Now let's try an example where the last element has the smallest
    value:
    
    >>> x2 = np.array([3, 2, 1])
    >>> lastrank(x2)
    -1.0
    
    Here's an example where the last element is not the minimum or maximum
    value:
    
    >>> x3 = np.array([1, 3, 4, 5, 2])
    >>> lastrank(x3)
    -0.5
    
    Finally, let's add a large decay. The decay means that the elements
    closest to the last element receive the most weight. Because the
    decay is large, the first element (the value 1) doesn't get any weight
    and therefore the last element (2) becomes the smallest element:
    
    >>> lastrank(x3, decay=10)
    -1.0
    
    """
    if x.size == 0:
        # At least one dimension has length 0
        shape = list(x.shape)
        shape.pop(axis)
        r = nans(shape, dtype=x.dtype) 
        if (r.ndim == 0) and (r.size == 1):
            r = np.nan     
        return r 
    indlast = [slice(None)] * x.ndim 
    indlast[axis] = slice(-1, None)
    indlast2 = [slice(None)] * x.ndim 
    indlast2[axis] = -1  
    if decay > 0:
        # Exponential decay 
        nt = x.shape[axis]
        w = nt - np.ones(nt).cumsum()
        w = np.exp(-decay * w)
        w = nt * w / w.sum()
        matchdim = [None] * x.ndim 
        matchdim[axis] = slice(None)
        w = w[matchdim]
        g = ((x[indlast] > x) * w).sum(axis)
        e = ((x[indlast] == x) * w).sum(axis)
        n = (np.isfinite(x) * w).sum(axis)
        r = (g + g + e - w.flat[-1]) / 2.0
        r = r / (n - w.flat[-1])
    elif decay < 0:
        raise ValueError, 'decay must be greater than or equal to zero.'        
    else:
        # Special case the most common case, decay = 0, for speed
        g = (x[indlast] > x).sum(axis)
        e = (x[indlast] == x).sum(axis)
        n = np.isfinite(x).sum(axis)
        r = (g + g + e - 1.0) / 2.0
        r = r / (n - 1.0)      
    r = 2.0 * (r - 0.5)    
    if x.ndim == 1:
        if not np.isfinite(x[indlast2]):
            r = np.nan
    else:
        r[~np.isfinite(x[indlast2])] = np.nan
    return r    

def ranking(x, axis=0, norm='-1,1', ties=True):
    """
    Normalized ranking treating NaN as missing and average ties by default.
    
    Parameters
    ----------
    x : ndarray
        Data to be ranked.
    axis : int, optional
        Axis to rank over. Default axis is 0.
    norm: str, optional
        A string that specifies the normalization:
            ==========  ================================================
            '0,N-1'     Zero to N-1 ranking
            '-1,1'      Scale zero to N-1 ranking to be between -1 and 1
            'gaussian'  Rank data then scale to a Gaussian distribution
            ==========  ================================================
        The default ranking is '-1,1'.
    ties: bool
        If two elements of `x` have the same value then they will be ranked
        by their order in the array (False). If `ties` is set to True
        (default), then the ranks are averaged.
        
    Returns
    -------
    idx : ndarray
        The ranked data.The dtype of the output is always np.float even if
        the dtype of the input is int.
    
    Notes
    ----
    If there is only one non-NaN value along the given axis, then that value
    is set to the midpoint of the specified normalization method. For example,
    if the input is array([1.0, nan]), then 1.0 is set to zero for the '-1,1'
    and 'gaussian' normalizations and is set to 0.5 (mean of 0 and 1) for the
    '0,N-1' normalization.
    
    For '0,N-1' normalization, note that N is x.shape[axis] even in there are
    NaNs. That ensures that when ranking along the columns of a 2d array, for
    example, the output will have the same min and max along all columns.
    
    """
    ax = axis
    if ax < 0:
        # This converts a negative axis to the equivalent positive axis
        ax = range(x.ndim)[ax]
    masknan = np.isnan(x)
    countnan = np.expand_dims(masknan.sum(ax), ax)
    countnotnan = x.shape[ax] - countnan
    if not ties:
        maskinf = np.isinf(x)
        adj = masknan.cumsum(ax)
        if masknan.any():
            x = x.copy()
            x[masknan] = np.inf
        idxraw = x.argsort(ax).argsort(ax)
        idx = idxraw.astype(float)
        idx[masknan] = np.nan
        idx[maskinf] -= adj[maskinf]
    else:
        rank1d = rankdata # Note: stats.rankdata starts ranks at 1
        idx = np.nan * np.ones(x.shape)
        itshape = list(x.shape)
        itshape.pop(ax)
        for ij in np.ndindex(*itshape):
            ijslice = list(ij[:ax]) + [slice(None)] + list(ij[ax:])
            x1d = x[ijslice].astype(float)
            mask1d = ~np.isnan(x1d)
            x1d[mask1d] = rank1d(x1d[mask1d]) - 1
            idx[ijslice] = x1d
    if norm == '-1,1':
        idx /= (countnotnan - 1)
        idx *= 2
        idx -= 1
        middle = 0.0
    elif norm == '0,N-1':
        idx *= (1.0 * (x.shape[ax] - 1) / (countnotnan - 1))
        middle = (idx.shape[ax] + 1.0) / 2.0 - 1.0
    elif norm == 'gaussian':
        try:
            from scipy.special import ndtri
        except ImportError:
            raise ImportError, 'SciPy required for gaussian normalization.'   
        idx *= (1.0 * (x.shape[ax] - 1) / (countnotnan - 1))
        idx = ndtri((idx + 1.0) / (x.shape[ax] + 1.0))
        middle = 0.0
    else:
        msg = "norm must be '-1,1', '0,N-1', or 'gaussian'."
        raise ValueError(msg)
    idx[(countnotnan==1)*(~masknan)] = middle
    return idx

def push(x, n, axis=-1):
    "Fill missing values (NaN) with most recent non-missing values if recent."
    if axis != -1 or axis != x.ndim-1:
        x = np.rollaxis(x, axis, x.ndim)
    y = np.array(x) 
    if y.ndim == 1:
        y = y[None, :]
    fidx = np.isfinite(y)
    recent = np.nan * np.ones(y.shape[:-1])  
    count = np.nan * np.ones(y.shape[:-1])          
    for i in xrange(y.shape[-1]):
        idx = (i - count) > n
        recent[idx] = np.nan
        idx = ~fidx[...,i]
        y[idx, i] = recent[idx]
        idx = fidx[...,i]
        count[idx] = i
        recent[idx] = y[idx, i]
    if axis != -1 or axis != x.ndim-1:
        y = np.rollaxis(y, x.ndim-1, axis)
    if x.ndim == 1:
        return y[0]
    return y

def _quantileraw1d(xi, q):
    y = np.nan * np.asarray(xi)
    idx = np.where(np.isfinite(xi))[0]
    xi = xi[idx,:]
    nx = idx.size
    if nx:
        jdx = xi.argsort(axis=0).argsort(axis=0)
        mdx = np.nan * jdx
        kdx = 1.0 * (nx - 1) / (q) * np.ones((q, 1))
        kdx = kdx.cumsum(axis=0)
        kdx = np.concatenate((-1 * np.ones((1, kdx.shape[1])), kdx), 0)
        kdx[-1, 0] = nx
        for j in xrange(1, q+1):
            mdx[(jdx > kdx[j-1]) & (jdx <= kdx[j]),:] = j
        y[idx] = mdx
    return y

def quantile(x, q, axis=0):
    """
    Convert elements in each column to integers between 1 and q then normalize.
    
    Result is normalized to -1, 1.
    
    Parameters
    ----------
    x : ndarray
        Input array.
    q : int
        The number of bins into which to quantize the data. Must be at
        least 1 but less than the number of elements along the specified
        axis.
    axis : {int, None}, optional
        The axis along which to quantize the elements. The default is
        axis 0.

    Returns
    -------
    y : ndarray
        A quantized copy of the array.

    Examples
    --------
    >>> arr = np.array([1, 2, 3, 4, 5, 6])
    >>> la.farray.quantile(arr, 3)
    array([-1., -1.,  0.,  0.,  1.,  1.])

    """
    if q < 1:
        raise ValueError, 'q must be one or greater.'
    elif q == 1:
        y = np.zeros(x.shape)
        y[np.isnan(x)] = np.nan
        return y
    if axis == None:
        if q > x.size:
            msg = 'q must be less than or equal to the number of elements '
            msg += 'in x.'
            raise ValueError, msg
        y = np.apply_along_axis(_quantileraw1d, 0, x.flat, q)
        y = y.reshape(x.shape)
    else:        
        if q > x.shape[axis]:
            msg = 'q must be less than or equal to the number of rows in x.'
            raise ValueError, msg
        y = np.apply_along_axis(_quantileraw1d, axis, x, q)
    y = y - 1.0
    y = 1.0 * y / (q - 1.0)
    y = 2.0 * (y - 0.5)
    return y 

def demean(arr, axis=None):
    """
    Subtract the mean along the specified axis.
    
    Parameters
    ----------
    arr : ndarray
        Input array.
    axis : {int, None}, optional
        The axis along which to remove the mean. The default (None) is
        to subtract the mean of the flattened array.

    Returns
    -------
    y : ndarray
        A copy with the mean along the specified axis removed.

    Examples
    --------
    >>> arr = np.array([1, np.nan, 2, 3])
    >>> demean(arr)
    array([ -1.,  NaN,   0.,   1.])
 
    """
    # Adapted from pylab.demean
    if axis != 0 and not axis is None:
        ind = [slice(None)] * arr.ndim
        ind[axis] = np.newaxis
        arr = arr - nanmean(arr, axis)[ind]
    else:
        arr = arr - nanmean(arr, axis)   
    return arr

def demedian(arr, axis=None):
    """
    Subtract the median along the specified axis.
    
    Parameters
    ----------
    arr : ndarray
        Input array.
    axis : {int, None}, optional
        The axis along which to remove the median. The default (None) is
        to subtract the median of the flattened array.
    
    Returns
    -------
    y : ndarray
        A copy with the median along the specified axis removed.
    
    Examples
    --------
    >>> arr = np.array([1, np.nan, 2, 10])
    >>> demedian(arr)
    array([ -1.,  NaN,   0.,   8.])        
    
    """
    # Adapted from pylab.demean
    if axis != 0 and not axis is None:
        ind = [slice(None)] * arr.ndim
        ind[axis] = np.newaxis
        arr = arr - nanmedian(arr, axis)[ind]
    else:
        arr = arr - nanmedian(arr, axis)   
    return arr
    
def zscore(arr, axis=None):
    """
    Z-score along the specified axis.
    
    Parameters
    ----------
    arr : ndarray
        Input array.
    axis : {int, None}, optional
        The axis along which to take the z-score. The default (None) is
        to find the z-score of the flattened array.
    
    Returns
    -------
    y : ndarray
        A copy normalized with the Z-score along the specified axis.
    
    Examples
    --------
    >>> arr = np.array([1, np.nan, 2, 3])
    >>> zscore(arr)
    array([-1.22474487,         NaN,  0.        ,  1.22474487])
        
    """
    arr = demean(arr, axis)
    if axis != 0 and not axis is None:
        ind = [slice(None)] * arr.ndim
        ind[axis] = np.newaxis
        arr /= nanstd(arr, axis)[ind]
    else:
        arr /= nanstd(arr, axis)   
    return arr             
   
# Calc functions -----------------------------------------------------------

def correlation(arr1, arr2, axis=None):
    """
    Correlation between two Numpy arrays along the specified axis.
    
    This is not a cross correlation function. If the two input arrays have
    shape (n, m), for example, then the output will have shape (m,) if axis
    is 0 and shape (n,) if axis is 1.
    
    Parameters
    ----------
    arr1 : Numpy ndarray
        Input array.
    arr2 : Numpy ndarray
        Input array.        
    axis : {int, None}, optional
        The axis along which to measure the correlation. The default, axis
        None, flattens the input arrays before finding the correlation and
        returning it as a scalar.
    
    Returns
    -------
    corr : Numpy ndarray, scalar
        The correlation between `arr1` and `arr2` along the specified axis.
        
    Examples
    -------- 
    Make two Numpy arrays:
       
    >>> a1 = np.array([[1, 2], [3, 4]])
    >>> a2 = np.array([[2, 1], [4, 3]])
    >>> a1
    array([[1, 2],
           [3, 4]])
    >>> a2
    array([[2, 1],
           [4, 3]])
           
    Find the correlation between the two arrays along various axes:       
    
    >>> correlation(a1, a2)
    0.59999999999999998
    >>> correlation(a1, a2, axis=0)
    array([ 1.,  1.])
    >>> correlation(a1, a2, axis=1)
    array([-1., -1.])

    """
    mask = np.logical_or(np.isnan(arr1), np.isnan(arr2))
    if mask.any():
        # arr1 and/or arr2 contain NaNs, so use slower NaN functions if needed
        if axis == None:
            x1 = arr1.flatten()
            x2 = arr2.flatten()
            idx = ~mask.flatten()
            x1 = x1[idx]
            x2 = x2[idx]
            x1 = x1 - x1.mean()
            x2 = x2 - x2.mean()        
            num = (x1 * x2).sum()
            den = np.sqrt((x1 * x1).sum() * (x2 * x2).sum()) 
        else:
            x1 = arr1.copy()
            x2 = arr2.copy()
            x1[mask] = np.nan
            x2[mask] = np.nan 
            if axis == 0:
                x1 = x1 - nanmean(x1, axis)
                x2 = x2 - nanmean(x2, axis)              
            else:
                idx = [slice(None)] * x1.ndim
                idx[axis] = None
                x1 = x1 - nanmean(x1, axis)[idx]
                x2 = x2 - nanmean(x2, axis)[idx]           
            num = np.nansum(x1 * x2, axis)
            den = np.sqrt(np.nansum(x1 * x1, axis) * np.nansum(x2 * x2, axis))
    else:
        # Neither arr1 or arr2 contains nans, so use faster non-nan functions
        if axis == None:
            x1 = arr1.flatten()
            x2 = arr2.flatten()
            x1 = x1 - x1.mean()
            x2 = x2 - x2.mean()        
            num = (x1 * x2).sum()
            den = np.sqrt((x1 * x1).sum() * (x2 * x2).sum()) 
        else:
            x1 = arr1
            x2 = arr2
            if axis == 0:
                x1 = x1 - x1.mean(axis)
                x2 = x2 - x2.mean(axis)              
            else:
                idx = [slice(None)] * x1.ndim
                idx[axis] = None   
                x1 = x1 - x1.mean(axis)[idx]
                x2 = x2 - x2.mean(axis)[idx]           
            num = np.sum(x1 * x2, axis)
            den = np.sqrt(np.sum(x1 * x1, axis) * np.sum(x2 * x2, axis))                
    return num / den 

def covMissing(R):
    """
    Covariance matrix adjusted for missing returns.

    covMissing returns the covariance matrix adjusted for missing returns.
    R (NxT) is log stock returns; missing returns are NaN.

    Note the mean of each row of R is assumed to be zero. So returns are not
    demeaned and the covariance is normalized by T not T-1.
    
    
    Notes
    -----
    
    equivalence to using numpy masked array function
    l7.demean(axis=1).cov().x -np.ma.cov(np.ma.fix_invalid(x7), bias=1).data
    
    """
    mask = np.isnan(R)
    R[mask] = 0
    mask = np.asarray(mask, np.float64)
    mask = 1 - mask # Change meaning of missing matrix to present matrix  

    normalization = np.dot(mask, mask.T)

    if np.any(normalization < 2):
        raise ValueError, 'covMissing: not enough observations'

    C = np.dot(R, R.T) / normalization

    return C   

# Random functions ----------------------------------------------------------

def shuffle(x, axis=0):
    """
    Shuffle the data inplace along the specified axis.
    
    Unlike numpy's shuffle, this shuffle takes an axis argument. The
    ordering of the labels is not changed, only the data is shuffled.
    
    Parameters
    ----------
    x : ndarray
        Array to be shuffled.
    axis : int
        The axis to shuffle the data along. Default is axis 0.
        
    Returns
    -------
    out : None
        The data is shuffled inplace.        
    
    """
    np.random.shuffle(np.rollaxis(x, axis))

