Who's larry?
============

The main class of the la package is a labeled array, larry. A larry consists
of data and labels. The data is stored as a NumPy array and the labels as a
list of lists (one list per dimension).

Here's larry in schematic form::

                         date1    date2    date3
                'AAPL'   209.19   207.87   210.11
            y = 'IBM'    129.03   130.39   130.55
                'DELL'    14.82    15.11    14.94
                
The larry above is stored internally as a `Numpy <http://www.numpy.org>`_
array and a list of lists::

        y.label = [['AAPL', 'IBM', 'DELL'], [date1, date2, date3]]
        y.x = np.array([[209.19, 207.87, 210.11],
                        [129.03, 130.39, 130.55],
                        [ 14.82,  15.11,  14.94]])               
    
A larry can have any number of dimensions except zero. Here, for example, is
one way to create a one-dimensional larry::

    >>> import la
    >>> y = la.larry([1, 2, 3])
    
In the statement above the list is converted to a Numpy array and the labels
default to ``range(n)``, where *n* in this case is 3.
    
larry has built-in methods such as **ranking, merge, shuffle, mov_sum,
zscore, demean, lag** as well as typical Numpy methods like **sum, max, std,
sign, clip**. NaNs are treated as missing data.
    
Alignment by label is automatic when you add (or subtract, multiply, divide)
two larrys.
    
You can archive larrys in HDF5 format using **save** and **load** or using a
dictionary-like interface::

    >>> io = la.IO('/tmp/dataset.hdf5')
    >>> io['y'] = y   # <--- save
    >>> z = io['y']   # <--- load
    >>> del io['y']   # <--- delete from archive
       
For the most part larry acts like a Numpy array. And, whenever you want,
you have direct access to the Numpy array that holds your data. For
example if you have a function, *myfunc*, that works on Numpy arrays and
doesn't change the shape or ordering of the array, then you can use it on a
larry, *y*, like this::

                           y.x = myfunc(y.x)
    
larry adds the convenience of labels, provides many built-in methods, and
let's you use your existing array functions.       

License
=======

The ``la`` package is distributed under a Simplified BSD license. Parts of
NumPy, Scipy, and numpydoc, which all have BSD licenses, are included in
``la``. Parts of matplotlib are also included. See the LICENSE file, which
is distributed with the ``la`` package, for details.

Installation
============

The ``la`` package requires Python and Numpy. Numpy 1.4.1 or newer is
recommended for its improved NaN handling. Also some of the unit tests in the
``la`` package require Numpy 1.4 or newer and many require
`nose <http://somethingaboutorange.com/mrl/projects/nose>`_.

To save and load larrys in HDF5 format, you need
`h5py <http://h5py.alfven.org>`_ with HDF5 1.8.
            
To install ``la``::

    $ python setup.py build
    $ sudo python setup.py install
    
Or, if you wish to specify where ``la`` is installed, for example inside
``/usr/local``::

    $ python setup.py build
    $ sudo python setup.py install --prefix=/usr/local
    
After you have installed ``la``, run the suite of unit tests::

    >>> import la
    >>> la.test()
    <snip>
    Ran 3002 tests in 1.387s
    OK
    <nose.result.TextTestResult run=2988 errors=0 failures=0> 
    
The ``la`` package contains C extensions that speed up common alignment
operations such as adding two unaligned larrys. If the C extensions don't
compile when you build ``la`` then there's an automatic fallback to python
versions of the functions. To see whether you are using the C functions or the
Python functions::

    >>> la.info()
    la version      0.4.0           
    la file         /usr/local/lib/python2.6/dist-packages/la/__init__.pyc 
    HDF5 archiving  Available       
    listmap         Faster C version
    listmap_fill    Faster C version    
    
Since ``la`` can run in a pure python mode, you can use ``la`` by just saving
it and making sure that python can find it.    
    
URLs
====

===============   ========================================================
 download          http://pypi.python.org/pypi/la
 docs              http://berkeleyanalytics.com/la
 code              http://github.com/kwgoodman/la
 issues, bugs      http://github.com/kwgoodman/la/issues 
 mailing list      http://groups.google.com/group/labeled-array
===============   ========================================================

``la`` at a glance
==================

**la package**

======================================    ====================================
package name                              ``la``
web site                                  http://berkeleyanalytics.com/la
license                                   Simplified BSD
programming languages                     Python, Cython
required dependencies                     Python, NumPy
optional dependencies                     h5py, Scipy, nose, C-compiler
year started (open source)                2008 (2010)
======================================    ====================================

**Data object**

=======================================   =====================================
data object (main class)                  larry
number of dimensions supported            nd > 0d
data container                            Numpy array
direct access to data container           yes
data types                                homogenous: float, int, str, object
label container                           list of lists
direct access to label container          yes
label types                               heterogenous, hashable    
label constraints                         unique along any one axis, hashable
missing values                            NaN (float),  partial: '' (str),
                                          None (object)
default for binary operations (+,*,...)   intersection of labels
IO                                        HDF5, partial support for CSV
=======================================   =====================================

**Similar to Numpy**

======================================    ====================================
Numpy array                               ``la`` larry
======================================    ====================================
``arr = np.array([[1, 2], [3, 4]])``      ``lar = la.larry([[1, 2], [3, 4]])``
``np.nansum(arr)``                        ``lar.sum()``
``arr.shape``, ``arr.dtype``,             ``lar.shape``, ``lar.dtype``
``arr.ndim``, ``arr.T``                   ``lar.ndim``, ``lar.T``
``arr.astype(float)``                     ``lar.astype(float)``
``arr1 + arr2``                           ``lar1 + lar2``
``arr[:,0]``                              ``lar[:,0]``
======================================    ====================================

