'''
Created on Nov 7, 2014

@author: roehrig
'''

import threading
import numpy
import wx
import os
import logging
import mproc as mproc
import multiprocessing as mp
from math import *
from CustomEvents import *
from diffractiondatatool import XYDataArray
from diffractiondatatool import TiffDatatArray
from time import time


def SumData(roi_start_list, roi_end_list, file_list, file_path, istart, iend, queue):
    logger = mp.get_logger()
    mp.log_to_stderr(logging.INFO)

    roi_sums = mproc.SHARED_ARRAY
    data_array = XYDataArray()
    num_rois = len(roi_start_list)
    logger.info("Reading files from %d to %d" % (istart, iend))
    if istart > 0:
        istart = istart - 1

    # Process each file in the list that falls in the range istart to iend
    for i in range(istart, iend):

        # Read in the information from the file and create numpy arrays from that information.
        data_array.CreateArrays(os.path.join(file_path, file_list[i]))

        # Sum the data in the arrays that lies between the roi values.  Do this
        # for each roi that was created.
        for j in range(num_rois):
#           logger.info("Summing roi %d from file %d" % (j, i))
            roi_sums[j][i] = roi_sums[j][i] + data_array.SumROIData(roi_start_list[j], roi_end_list[j])

        # Add a value of 1 to the queue so that the user interface can be updated
        # with the latest progress.
        queue.put(1)
    return roi_sums


def SumImageROI(roi_start_list, roi_end_list, file_list, file_path, istart, iend, queue):
    logger = mp.get_logger()
    mp.log_to_stderr(logging.INFO)

    roi_sums = mproc.SHARED_ARRAY
    data_array = TiffDatatArray()
    num_rois = len(roi_start_list)
    logger.info("Reading files from %d to %d" % (istart, iend))
    if istart > 0:
        istart = istart - 1

    # Process each file in the list that falls in the range istart to iend
    for i in range(istart, iend):

        # Read in the information from the file and create numpy arrays from that information.
        data_array.CreateArrays(os.path.join(file_path, file_list[i]))

        # Sum the data in the arrays that lies between the roi values.  Do this
        # for each roi that was created.
        for j in range(num_rois):
            new_sum = data_array.SumROIData(roi_start_list[j], roi_end_list[j])
            roi_sums[j][i] = roi_sums[j][i] + new_sum

        # Add a value of 1 to the queue so that the user interface can be updated
        # with the latest progress.
        queue.put(1)

    return roi_sums

def SumPixels(file_list, file_path, istart, iend, queue):
    logger = mp.get_logger()
    mp.log_to_stderr(logging.INFO)

    roi_sums = mproc.SHARED_ARRAY
    data_array = TiffDatatArray()
    logger.info("Reading files from %d to %d" % (istart, iend))
    if istart > 0:
        istart = istart - 1

    # Process each file in the list that falls in the range istart to iend
    for i in range(istart, iend):

        # Read in the information from the file and create numpy arrays from that information.
        data_array.CreateArrays(os.path.join(file_path, file_list[i]))

        # Sum the data in the arrays that lies between the roi values.  Do this
        # for each roi that was created.
        new_sum = data_array.GetDataArray()
        roi_sums = numpy.add(roi_sums, new_sum)

        # Add a value of 1 to the queue so that the user interface can be updated
        # with the latest progress.
        queue.put(1)
    return roi_sums

class DataSummationThread (threading.Thread):
    '''
    This class creates a thread that will open a list of files and sum the
    values of those files that fall within one or more ROIs that are set
    by the user.
    '''
    
    def __init__(self, parent, roi_list, file_list, path, update_func):
        '''
        Create the thread object.
        
        parent - The object that created this thread
        roiList - A list of ROI objects
        fileList - A list of files that contain the data to be summed.
        path - A path in the file system that gives the location of the files.
        update_func - A function to be called for updating the user interface.
        '''
        
        threading.Thread.__init__(self)
        
        self._parent = parent
        self._roi_list = roi_list
        self._file_list = file_list
        self._file_path = path
        self._data = XYDataArray()
        self._func = SumData
        self._update_func = update_func

        return
    
    def run(self):
        
        # Create an array the size of the roi list and initialized to zero.
        num_rois = len(self._roi_list)
        num_items = len(self._file_list)
        roi_sums = numpy.zeros((num_rois, num_items), dtype=numpy.float32)

#!        start_time = time()

        # Create two lists.  The first holds the starting values of each roi,
        # the second holds the ending values of each roi.  Do this because the
        # roi_list object can't be pickled, which causes difficulties for multiprocessing.
        roi_start_list = []
        roi_end_list = []
        for i in range(num_rois):
            roi_start_list.append(self._roi_list[i].GetStart())
            roi_end_list.append(self._roi_list[i].GetEnd())

        roi_sums = mproc.distribute_jobs(
            roi_sums,
            func=self._func,
            update_func=self._update_func,
            num_files=num_items,
            args=(roi_start_list, roi_end_list, self._file_list, self._file_path),
            ncore=None,
            nchunk=None)

###############################################################################################################
## This section of code works, but it runs in a single thread, so it is very slow for large numbers of files.

        # For each file, open the file, create an array of the values in the file,
        # then create a 2D array that holds the sums of the values that are in each
        # ROI.
#!        for i in range(num_items):
#!            self._data.CreateArrays(os.path.join(self._file_path, self._file_list[i]))
            
#!            for j in range(num_rois):
#!                roi_sums[j][i] = roi_sums[j][i] + self._data.SumROIData(self._roi_list[j].GetStart(), self._roi_list[j].GetEnd())
                
            # Cause the progress gauge on the main frame to update
#!            evt = UpdateProgressEvent(myEVT_UPDATE_PROGRESS, -1, i)
#!            wx.PostEvent(self._parent, evt)
###############################################################################################################

#!        end_time = time()

#!        elapsed_time = end_time - start_time
#!        print "Time to caluclate roi sums=%f" % elapsed_time

        # Alert the main application that the data is ready to be plotted.
        evt = DataSummationEvent(myEVT_SUM_DATA, -1, roi_sums)
        wx.PostEvent(self._parent, evt)

        return

class ImageROISummationThread (threading.Thread):
    '''
    This class creates a thread that will open a list of files and sums the
    values of the pixels in each file that falls within the ROIs that are set
    by the user.
    '''

    def __init__(self, parent, roi_list, file_list, path, update_func):
        '''
        Create the thread object.

        parent - The object that created this thread
        roiList - A list of ROI objects
        fileList - A list of files that contain the data to be summed.
        path - A path in the file system that gives the location of the files.
        update_func - A function to be called for updating the user interface.
        '''
        threading.Thread.__init__(self)

        self._parent = parent
        self._roi_list = roi_list
        self._file_list = file_list
        self._file_path = path
        self._data = TiffDatatArray()
        self._func = SumImageROI
        self._update_func = update_func

        return

    def run(self):

        # Create an array the size of the roi list and initialized to zero.
        num_rois = len(self._roi_list)
        num_items = len(self._file_list)
        roi_sums = numpy.zeros((num_rois, num_items), dtype=numpy.float32)

        # Create two lists.  The first holds the starting values of each roi,
        # the second holds the ending values of each roi.  Do this because the
        # roi_list object can't be pickled, which causes difficulties for multiprocessing.
        roi_start_list = []
        roi_end_list = []
        for roi in self._roi_list:
            points = roi.GetDimensions()
            x0 = points[0]
            y0 = points[1]
            x1 = points[2]
            y1 = points[3]

            if x1 > x0:
                x0 = int(floor(x0))
                x1 = int(ceil(x1))
            else:
                x1 = int(floor(x1))
                x0 = int(ceil(x0))
                temp = x1
                x1 = x0
                x0 = temp

            if y0 > y1:
                y1 = int(floor(y1))
                y0 = int(ceil(y0))
                temp = y1
                y1 = y0
                y0 = temp
            else:
                y0 = int(floor(y0))
                y1 = int(ceil(y1))

            print (x0,y0,x1,y1)
            roi_start_list.append((x0, y0))
            roi_end_list.append((x1, y1))

#        for i in range(num_items):
#            self._data.CreateArrays(os.path.join(self._file_path, self._file_list[i]))

#            for j in range(num_rois):
#                roi_sums[j][i] = roi_sums[j][i] + self._data.SumROIData(roi_start_list[j], roi_end_list[j])

#            print i

        roi_sums = mproc.distribute_jobs(
            roi_sums,
            func=self._func,
            update_func=self._update_func,
            num_files=num_items,
            args=(roi_start_list, roi_end_list, self._file_list, self._file_path),
            ncore=None,
            nchunk=None)

        # Alert the main application that the data is ready to be plotted.
        evt = DataSummationEvent(myEVT_SUM_DATA, -1, roi_sums)
        wx.PostEvent(self._parent, evt)

        return

class ImagePixelSummationThread (threading.Thread):
    '''
    This class creates a thread that will open a list of files and sums the
    values of the pixels in each file.
    '''

    def __init__(self, parent, size, file_list, path, update_func):
        '''
        Create the thread object.

        parent - The object that created this thread
        roiList - A list of ROI objects
        fileList - A list of files that contain the data to be summed.
        path - A path in the file system that gives the location of the files.
        update_func - A function to be called for updating the user interface.
        '''
        threading.Thread.__init__(self)

        self._parent = parent
        self._file_list = file_list
        self._file_path = path
        self._data = TiffDatatArray()
        self._func = SumPixels
        self._update_func = update_func
        self._height = size[0]
        self._width = size[1]

        return

    def run(self):

        # Create an array the size of the roi list and initialized to zero.
        num_items = len(self._file_list)
        pixel_sums = numpy.zeros((self._height, self._width), dtype=numpy.float32)

        pixel_sums = mproc.distribute_jobs(
            pixel_sums,
            func=self._func,
            update_func=self._update_func,
            num_files=num_items,
            args=(self._file_list, self._file_path),
            ncore=None,
            nchunk=None)

        # Alert the main application that the data is ready to be plotted.
        evt = ImageSummationEvent(myEVT_PLOT_IMAGE_SUM, -1, pixel_sums)
        wx.PostEvent(self._parent, evt)

        return
