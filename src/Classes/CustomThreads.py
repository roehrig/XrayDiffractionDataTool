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
from CustomEvents import *
from diffractiondatatool import XYDataArray

# def SumData(self, roi_list, file_list, file_path, istart, iend):
#         logger = mp.get_logger()
#         mp.log_to_stderr(logging.INFO)
#
#         roi_sums = mproc.SHARED_ARRAY
#         data_array = XYDataArray()
#         num_rois = len(roi_list)
#         print "Reading files from %d to %d" % (istart, iend)
#         logger.info("Reading files from %d to %d" % (istart, iend))
#         for i in range (istart, iend):
#
#             data_array.CreateArrays(os.path.join(self._file_path, self._fileList[i]))
#
#             for j in range(num_rois):
#                 print "Summing roi %d from file %d" % (j, i)
#                 logger.info("Summing roi %d from file %d" % (j, i))
#                 roi_sums[j][i] = roi_sums[j][i] + data_array.SumROIData(roi_list[j].GetStart(), roi_list[j].GetEnd())
#
#         return

def SumData(istart, iend):
        print istart, iend

class DataSummationThread (threading.Thread):
    '''
    This class creates a thread that will open a list of files and sum the
    values of those files that fall within one or more ROIs that are set
    by the user.
    '''
    
    def __init__(self, parent, func, roi_list, file_list, path):
        '''
        Create the thread object.
        
        parent - The object that created this thread
        roiList - A list of ROI objects
        fileList - A list of files that contain the data to be summed.
        path - A path in the file system that gives the location of the files.
        '''
        
        threading.Thread.__init__(self)
        
        self._parent = parent
        self._roi_list = roi_list
        self._file_list = file_list
        self._file_path = path
        self._data = XYDataArray()
#        self._func = func
        self._func = SumData
        
        return
    
    def run(self):
        
        # Create an array the size of the roi list and initialized to zero.
        num_rois = len(self._roi_list)
        num_items = len(self._file_list)
        roi_sums = numpy.zeros((num_rois, num_items), dtype=numpy.float32)

#        arr = mproc.distribute_jobs(
#            roi_sums,
#            func=self._func,
#            num_files=num_items,
#            args=(self._roi_list, self._file_list, self._file_path),
#            ncore=2,
#            nchunk=None)

        # For each file, open the file, create an array of the values in the file,
        # then create a 2D array that holds the sums of the values that are in each
        # ROI.
#        for i in range(self._start, self._end):
        for i in range(num_items):
#            if self._fileList.IsChecked(i):
#                listItem = self._fileList.GetItem(i, 1)
#                fileName = listItem.GetText()
#                self._data.CreateArrays(os.path.join(self._path, fileName))
            self._data.CreateArrays(os.path.join(self._file_path, self._file_list[i]))
            
            for j in range(num_rois):
                roi_sums[j][i] = roi_sums[j][i] + self._data.SumROIData(self._roi_list[j].GetStart(), self._roi_list[j].GetEnd())
                
            # Cause the progress gauge on the main frame to update
            evt = UpdateProgressEvent(myEVT_UPDATE_PROGRESS, -1, i)
            wx.PostEvent(self._parent, evt)
        
        # Alert the main application that the data is ready to be plotted.
        print "Signal the GUI to plot the summation results"
        evt = DataSummationEvent(myEVT_SUM_DATA, -1, roi_sums)
        wx.PostEvent(self._parent, evt)

        return
