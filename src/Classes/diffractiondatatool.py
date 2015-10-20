'''
Created on Aug 20, 2014

@author: roehrig
'''

import os
import numpy as np
import decimal
import matplotlib.pyplot as plt
from scipy import signal
from math import sqrt

class XYZDataArray(object):
    '''
    This class contains a 3 dimensional numpy array.  The array values are taken from
    multiple x-ray diffraction data files
    '''

    def __init__(self, num_files):
        '''
        Constructor
        '''

        self._num_files = num_files

        return


class XYDataArray(object):
    '''
    This class contains a 2 dimensional numpy array. The array values are taken from 
    a x-ray diffraction data file. 
    '''


    def __init__(self):
        '''
        Constructor
        '''

        self.x_label = None
        self.y_label = None
        self.data_source = None
        self.array_size = 0
        self.data_values = None
        
        return
    
    def CreateArrays(self, fileName):
        '''
        fileName - The name of the file to read the data from.
        
        Create two arrays from a file.  The file format is as follows
        
        file name
        x-axis label
        y-axis label
        number of data points
        x,y data point 1
        x,y data point 2
        x,y data point 3
              .
              .
              .
        end of file
        '''
        try:
            with open(fileName, 'r') as fileHandle:
                # Read in the first four lines of the file
                self.data_source = fileHandle.readline()[:-1]
                self.x_label = fileHandle.readline()[:-1]
                self.y_label = fileHandle.readline()[:-1]
                self.array_size = int(fileHandle.readline())
                
                # The rest of the file is the data.  It creates an array of size [array_size,2].
                # We want an array of size [2, array_size], so transpose the data.
                temp = np.loadtxt(fileName, skiprows=4)
                self.data_values = temp.transpose()
                
        except IOError as e:
            return
        
    def GetDataArray(self):
        return self.data_values
    
    def GetDataFileName(self):
        return self.data_source
    
    def GetArraySize(self):
        return self.data_values.shape
    
    def GetAxisLabels(self):
        return self.x_label, self.y_label
    
    def SumROIData(self, roiStart, roiEnd):
        sumVal = 0.0
        
        # If the value of the ith element in the first dimension is between the two
        # suplied values, then add the value of the ith element in the second
        # dimension to the running total.
#        for i in range(self.array_size):
#            if (self.data_values[0,i] >= roiStart) and (self.data_values[0,i] <= roiEnd):
#                sumVal = sumVal + self.data_values[1,i]

        indices=np.where(np.logical_and(self.data_values[0] >= roiStart, self.data_values[0] <= roiEnd))
        sumVal = np.sum(self.data_values[1,indices])

        return sumVal

    '''
    This function implements the SNIP algorithm as published in

    C.G.Ryan, E. Claytpon, W.L. Griffin, S.H. Sie, and D.R. Cousens
    SNIP, A Statistics-Sensitive Background treatment for the quantitative analysis
    of Pixie Spectra in Geoscience Applications.
    Nuclear Instruments and Methods in Physics Research, 1988

    '''
    def CalculateBackground(self):

        spectra = self.data_values[1].copy()

        indices = np.where(spectra > 0) # The variable indices is a tuple.
        background = spectra[indices]
        background_size = background.size

#!        x = np.arange(background.size)
#!        plt.plot(x, background,color='g')
#!        plt.show()

        filtered_background = np.zeros(background_size,np.float)
        smoothed_background = np.zeros(background_size,np.float)
        fwhm = 6
        fwhm_scale_factor = 1.5
        width = fwhm * fwhm_scale_factor
        scanning_width = 0.5 * fwhm
        target_sum = 10
        cut_off_constant = 75
        slope_constant = 1.3
        number_clipping_loops = 24

        background = np.log(background)

#        x = np.arange(background_size)
#        plt.plot(x, background,color='b')
#        plt.show()

###############################################################################
#       This section is the low statistics digital filter part of the algorithm.
#       It did not seem to be necessary, perhaps because the peaks are all
#       very sharp.

#        for i in range(background_size):
#
#            left_sum = 0
#            right_sum = 0
#            j = i - 1
#            k = i + 1

#            cut_off = cut_off_constant * sqrt(background[i])

#            left_edge = i - int(width)
#            right_edge = i + int(width)
#            if left_edge < 0:
#                left_edge = 0
#            if right_edge >= background_size:
#                right_edge = background_size - 1

#            if i == 0:
#                j = i

#            if i == background_size - 1:
#                k = i

#            left_sum = background[left_edge:j].sum()
#            right_sum = background[k:right_edge].sum()
#            total_sum = left_sum + right_sum
#            slope = (right_sum + 1) / (left_sum + 1)

#            while total_sum > target_sum and total_sum > cut_off and 1/slope_constant < slope < slope_constant:
#                tempWidth = width / sqrt(2)
#                newWidth = int(tempWidth)

#                left_edge = i - newWidth
#                right_edge = i + newWidth
#                if left_edge < 0:
#                    left_edge = 0
#                if right_edge >= background_size:
#                    right_edge = background_size - 1

#                left_sum = background[left_edge:j].sum()
#                right_sum = background[k:right_edge].sum()
#                total_sum = left_sum + right_sum
#                slope = (right_sum + 1) / (left_sum + 1)

#            filtered_background[i] = total_sum / (2 * width + 1)
###############################################################################
        filtered_background = background.copy()

#!        x = np.arange(filtered_background.size)
#!        plt.plot(x, filtered_background,color='g')
#!        plt.show()

###############################################################################
#       This secton is the peak clipping section of the algorithm.

        for j in range(number_clipping_loops):
            if j >= ((number_clipping_loops * 2) / 3):
                scanning_width = scanning_width / sqrt(2)
            for i in range(background_size):
                high_value = min(i + scanning_width, background_size - 1)
                low_value = max(i - scanning_width, 0)

                mean = (filtered_background[high_value] + filtered_background[low_value]) / 2

                smoothed_background[i] = min(filtered_background[i], mean)

            filtered_background = smoothed_background
###############################################################################

#!        x = np.arange(filtered_background.size)
#!        plt.plot(x, filtered_background,color='r')
#!        plt.show()
    
        filtered_background = np.exp(filtered_background)

#!        x = np.arange(filtered_background.size)
#!        plt.plot(x, filtered_background,color='r')
#!        plt.show()

        background = np.exp(background)

        background = background - filtered_background

#!        x = np.arange(background_size)
#!        plt.plot(x, background,color='y')
#!        plt.show()

        # Copy the new spectra back.  Rounding errors may make some values slightly
        # below zero, so make sure all values are positive.
        for i in range(background_size):
            if background[i] >= 0:
                spectra[indices[0][i]] = background[i]
            else:
                spectra[indices[0][i]] = 0

        return spectra