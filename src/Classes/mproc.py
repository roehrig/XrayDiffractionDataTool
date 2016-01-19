#!/usr/bin/env python
# -*- coding: utf-8 -*-

# #########################################################################
# Copyright (c) 2015, UChicago Argonne, LLC. All rights reserved.         #
#                                                                         #
# Copyright 2015. UChicago Argonne, LLC. This software was produced       #
# under U.S. Government contract DE-AC02-06CH11357 for Argonne National   #
# Laboratory (ANL), which is operated by UChicago Argonne, LLC for the    #
# U.S. Department of Energy. The U.S. Government has rights to use,       #
# reproduce, and distribute this software.  NEITHER THE GOVERNMENT NOR    #
# UChicago Argonne, LLC MAKES ANY WARRANTY, EXPRESS OR IMPLIED, OR        #
# ASSUMES ANY LIABILITY FOR THE USE OF THIS SOFTWARE.  If software is     #
# modified to produce derivative works, such modified software should     #
# be clearly marked, so as not to confuse it with the version available   #
# from ANL.                                                               #
#                                                                         #
# Additionally, redistribution and use in source and binary forms, with   #
# or without modification, are permitted provided that the following      #
# conditions are met:                                                     #
#                                                                         #
#     * Redistributions of source code must retain the above copyright    #
#       notice, this list of conditions and the following disclaimer.     #
#                                                                         #
#     * Redistributions in binary form must reproduce the above copyright #
#       notice, this list of conditions and the following disclaimer in   #
#       the documentation and/or other materials provided with the        #
#       distribution.                                                     #
#                                                                         #
#     * Neither the name of UChicago Argonne, LLC, Argonne National       #
#       Laboratory, ANL, the U.S. Government, nor the names of its        #
#       contributors may be used to endorse or promote products derived   #
#       from this software without specific prior written permission.     #
#                                                                         #
# THIS SOFTWARE IS PROVIDED BY UChicago Argonne, LLC AND CONTRIBUTORS     #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT       #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS       #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL UChicago     #
# Argonne, LLC OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,        #
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,    #
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;        #
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER        #
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT      #
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN       #
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         #
# POSSIBILITY OF SUCH DAMAGE.                                             #
# #########################################################################

"""
Module for multiprocessing tasks.
"""

from __future__ import absolute_import, division, print_function

import numpy as np
import multiprocessing as mp
import ctypes
from contextlib import closing
from Queue import Empty as QueueEmpty
import logging

#logging.basicConfig(filename='DiffLogFile.log',level=logging.DEBUG)
#logger = logging.getLogger(__name__)
logger = mp.get_logger()
mp.log_to_stderr(logging.INFO)


__author__ = "Doga Gursoy"
__copyright__ = "Copyright (c) 2015, UChicago Argonne, LLC."
__docformat__ = 'restructuredtext en'
__all__ = ['distribute_jobs',
           'init_tomo',
           'init_obj']


#def distribute_jobs(arr, func, axis, args=None, kwargs=None, ncore=None, nchunk=None):
def distribute_jobs(arr, func, update_func, num_files, args=None, kwargs=None, ncore=None, nchunk=None):
    """
    Distribute N-dimensional shared-memory array in chunks into cores.

    One can either specify the number of cores (ncore) or the size of data
    chunking (nchunk). If both arguments are provided simultaneously as
    input, ncore will be overwritten according to the given nchunk.

    Parameters
    ----------
    func : func
        Function to be parallelized.
    args : list
        Arguments of the function in a list.
    kwargs : list
        Keyword arguments of the function in a dictionary.
    axis : int
        Axis along which parallelization is performed.
    ncore : int, optional
        Number of cores that will be assigned to jobs.
    nchunk : int, optional
        Chunk size for each core.

    Returns
    -------
    ndarray
        Output array.
    """
    if ncore is not None and nchunk is not None:
        logger.warning('ncore will be overwritten according to nchunk')

    # Arrange number of processors.
    if ncore is None or ncore > mp.cpu_count():
        ncore = mp.cpu_count() - 1

    if ncore <= 0:
        ncore = 1

    logger.info('Number of cores to be used is %d' % ncore)
    ndim = num_files
    logger.info('Number of files is %d' % ndim)

    # Maximum number of processors for the task.
    if ndim < ncore:
        ncore = ndim

    # Arrange chunk size.
    if nchunk is None:
        nchunk = (ndim - 1) // ncore + 1

    logger.info('Chunk size is %d' % nchunk)

    # Determine pool size.
    npool = ndim // nchunk + 1

    logger.info('Pool size is %d' % npool)

    # Zip arguments.
    _args = []
    for m in range(npool):
        if m == 0:
            istart = 0
        else:
            istart = (m * nchunk) + 1
        iend = (m + 1) * nchunk

        # Adjustments for last chunk.
        if istart >= ndim:
            npool -= 1
            break
        if iend > ndim:
            iend = ndim

        logger.info('Chunk start=%d, end=%d' % (istart, iend))
        logger.info('Function to be called=%s' % func)

        # Generate sorted args.
        _args.append(_prepare_args(func, args, kwargs, istart, iend))

    # Start processes.
    return _start_proc(arr, _args, update_func)


def _prepare_args(func, args, kwargs, istart, iend):
    _arg = []
    _arg.append(func)
    if args is not None:
        for a in args:
            _arg.append(a)
    if kwargs is not None:
        _arg.append(kwargs)
    _arg.append(istart)
    _arg.append(iend)
    return _arg

def _start_proc(arr, args, update_func):
    shared_arr = get_shared(arr)
    init_shared(shared_arr)
    man = mp.Manager()
    queue = man.Queue()
    for i in range(len(args)):
        args[i].append(queue)
#    print("Starting Processes")

#!    with closing(
#!        mp.Pool(processes=len(args),
#!                initializer=init_shared,
#!                initargs=(shared_arr, queue))) as p:
#!            result=p.map(_arg_parser, args)

    p = mp.Pool(processes=len(args), initializer=init_shared, initargs=(shared_arr, queue))
    result=p.map_async(_arg_parser, args)

    while True:
        try:
            roi_sums_list = result.get(0.1)
            break;
        except mp.TimeoutError:
            while not queue.empty():
                try:
                    update_progress(update_func, queue.get())
                except QueueEmpty:
                    break

    p.close()
    p.join()
#!    clear_queue(queue)

#!    roi_sums = result[0]
#!    for i in range(1, len(result)):
#!        roi_sums = roi_sums + result[i]

    roi_sums = roi_sums_list[0]
    for i in range(1, len(roi_sums_list)):
        roi_sums = np.add(roi_sums, roi_sums_list[i])

    return roi_sums

def update_progress(update_func, value):
    update_func(value)

    return

def _arg_parser(args):
#    print("Calling function")
    func = args[0]
    arr = func(*args[1::])
    return arr


def get_shared(arr):
    shared_arr = mp.Array(ctypes.c_float, arr.size)
    shared_arr = _to_numpy_array(shared_arr, arr.shape)
    shared_arr[:] = arr
    return shared_arr


def _to_numpy_array(mp_arr, dshape):
    a = np.frombuffer(mp_arr.get_obj(), dtype=np.float32)
    return np.reshape(a, dshape)


def init_shared(shared_arr, queue=None):
    global SHARED_ARRAY
    SHARED_ARRAY = shared_arr
    global SHARED_QUEUE
    SHARED_QUEUE = queue


def init_tomo(arr):
    global SHARED_TOMO
    SHARED_TOMO = get_shared(arr)


def init_obj(arr):
    global SHARED_OBJ
    SHARED_OBJ = get_shared(arr)


def clear_queue(queue):
    while not queue.empty():
        args = queue.get(False)
        func = args[0]
        func(*args[1::])
