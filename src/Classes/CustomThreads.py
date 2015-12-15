'''
Created on Nov 7, 2014

@author: roehrig
'''

import threading
import numpy
import wx
import os
from CustomEvents import *
from diffractiondatatool import XYDataArray

class DataSummationThread (threading.Thread):
    '''
    This class creates a thread that will open a list of files and sum the
    values of those files that fall within one or more ROIs that are set
    by the user.
    '''
    
    def __init__(self, parent, roiList, fileList, path):
        '''
        Create the thread object.
        
        parent - The object that created this thread
        roiList - A list of ROI objects
        fileList - A list of files that contain the data to be summed.
        path - A path in the file system that gives the location of the files.
        '''
        
        threading.Thread.__init__(self)
        
        self._parent = parent
        self._roiList = roiList
        self._fileList = fileList
        self._path = path
        self._data = XYDataArray()
        
        return
    
    def run(self):
        
        # Create an array the size of the roi list and initialized to zero.
        numRois = len(self._roiList)
#        numItems = self._fileList.GetItemCount()
        numItems = len(self._fileList)
        roiSums = numpy.zeros((numRois, numItems), dtype=numpy.float32)

        # For each file, open the file, create an array of the values in the file,
        # then create a 2D array that holds the sums of the values that are in each
        # ROI.
        for i in range(numItems):
#            if self._fileList.IsChecked(i):
#                listItem = self._fileList.GetItem(i, 1)
#                fileName = listItem.GetText()
#                self._data.CreateArrays(os.path.join(self._path, fileName))
            
                for j in range(numRois):
                    roiSums[j][i] = roiSums[j][i] + self._data.SumROIData(self._roiList[j].GetStart(), self._roiList[j].GetEnd())
                
                # Cause the progress gauge on the main frame to update    
                evt = UpdateProgressEvent(myEVT_UPDATE_PROGRESS, -1, i)
                wx.PostEvent(self._parent, evt)
        
        # Alert the main application that the data is ready to be plotted.            
        evt = DataSummationEvent(myEVT_SUM_DATA, -1, roiSums)
        wx.PostEvent(self._parent, evt)

        return
