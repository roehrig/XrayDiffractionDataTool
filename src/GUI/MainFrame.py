'''
Created on Aug 18, 2014

@author: roehrig
'''

import wx
import os
import sys
import PlotFrame3D
import matplotlib
import numpy
import logging
import Classes.constants as constants
import Classes.mproc as mproc
import multiprocessing as mp
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx as Toolbar
from matplotlib.figure import Figure
from matplotlib import cm
#from numpy import *
from checklistcontrol import CheckListControl as CLC
from GrowableSectionPanel import DynamicTextControlPanel
from Classes.filelistbuilder import FileListBuilder
from Classes.diffractiondatatool import DataArray
from Classes.diffractiondatatool import XYDataArray
from Classes.diffractiondatatool import TiffDatatArray
from Classes.CustomEvents import EVT_SUM_DATA
from Classes.CustomEvents import EVT_UPDATE_PROGRESS
from Classes.CustomEvents import EVT_PLOT_IMAGE_SUM
from Classes.CustomThreads import DataSummationThread
from Classes.CustomThreads import ImageROISummationThread
from Classes.CustomThreads import ImagePixelSummationThread
from Classes.graphingtools import ROI
from wx.lib.scrolledpanel import ScrolledPanel

# The API for pubsub changed with wx version 2.9
try:
    from wx.lib.pubsub import Publisher
    USE_OLD_PUBLISHER = True
except:
    USE_OLD_PUBLISHER = False
    from wx.lib.pubsub import pub

class MainFrame(wx.Frame):
    '''
    Create a frame to hold all other objects.
    '''

    def __init__(self, parent, title):
        '''
        Constructor
        '''
        
        wx.Frame.__init__(self, parent, title=title, pos=(200,200), size=(600,600))
                
        self.data = None
        self.plot_type = constants.TWOD_PLOT
        self.plotFile = None
        self.numThreadsDone = 0
        self.maxNumThreads = 10
        self.index = 0
        self.scale_factor = 1
        
        # Create a Publisher object and subscribe to two topics
        if USE_OLD_PUBLISHER:
            self.dataPublisher = Publisher()
            self.dataPublisher.subscribe(self.NewScanLoaded, "new_scan_dimensions")
            self.dataPublisher.subscribe(self.ShowPixelData, "new_pixel_selected")
            self.dataPublisher.subscribe(self.UpdateProgressBar, "update_progress_bar")
        else:
            self.dataPublisher = pub.getDefaultPublisher()
            self.dataPublisher.subscribe(self.NewScanLoaded, "new_scan_dimensions")
            self.dataPublisher.subscribe(self.ShowPixelData, "new_pixel_selected")
            self.dataPublisher.subscribe(self.UpdateProgressBar, "update_progress_bar")

        # Create the fileTree variable so that it exists when the plottingPanel is created.
        self.fileTree = None
        
        self.plottingPanel = PlottingPanel(self)
        # Get the figure, canvas, and axes objects and pass them to the fileTree panel.
        # These eventually get passed to the panel that holds the ROI widgets.
        plotObjects = self.plottingPanel.GetPlotInfo()
        self.fileTree = FileTreePanel(self, plotObjects)
        
        self.frameSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.frameSizer.Add(self.plottingPanel, 1, wx.EXPAND)
#        self.frameSizer.Add(self.fileTree, 1, wx.EXPAND)
        self.frameSizer.Add(self.fileTree, 0)
        
        self.Bind(wx.EVT_BUTTON, self.OnCloseButtonClick, self.fileTree.buttonPanel.fileButtonPanel.exitButton)
        self.Bind(wx.EVT_BUTTON, self.OnPlotButtonClick, self.fileTree.buttonPanel.fileButtonPanel.plotDataButton)
        self.Bind(wx.EVT_BUTTON, self.OnSaveFileButtonClick, self.fileTree.buttonPanel.fileButtonPanel.saveAsFileButton)
        self.Bind(wx.EVT_BUTTON, self.OnSumDataButtonClick, self.fileTree.buttonPanel.fileButtonPanel.sumDataButton)
        self.Bind(wx.EVT_BUTTON, self.OnPlotImageSumButtonClick, self.fileTree.buttonPanel.fileButtonPanel.plotSumButton)
        self.Bind(EVT_SUM_DATA, self.PlotSumData)
        self.Bind(EVT_PLOT_IMAGE_SUM, self.PlotImageSum)
        self.Bind(EVT_UPDATE_PROGRESS, self.UpdateProgressBar)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        
        self.SetSizer(self.frameSizer)
        self.SetAutoLayout(True)
        self.frameSizer.Fit(self)

        self.Layout()
        
        return
    
    def NewScanLoaded(self, message):
        '''
        Set the values of the widgets that display the number of rows and columns in the scan.
        
        message - if a 2D scan, then a tuple of (columns, rows), otherwise a single value equal to columns
        '''
        
        # Assume that this is a 2D scan.  If not, then it is a 1D scan and the input argument has only
        # one value.  In that case, set the number of rows to zero.
        if USE_OLD_PUBLISHER:
            try:
                self.fileTree.buttonPanel.fileButtonPanel.numColumnsTextCtrl.SetValue("%d" % message.data[0])
                self.fileTree.buttonPanel.fileButtonPanel.numRowsTextCtrl.SetValue("%d" % message.data[1])
            except TypeError:
                self.fileTree.buttonPanel.fileButtonPanel.numColumnsTextCtrl.SetValue("%d" % message.data)
                self.fileTree.buttonPanel.fileButtonPanel.numRowsTextCtrl.SetValue("%d" % 0)
        else:
            try:
                self.fileTree.buttonPanel.fileButtonPanel.numColumnsTextCtrl.SetValue("%d" % message[0])
                self.fileTree.buttonPanel.fileButtonPanel.numRowsTextCtrl.SetValue("%d" % message[1])
            except TypeError:
                self.fileTree.buttonPanel.fileButtonPanel.numColumnsTextCtrl.SetValue("%d" % message)
                self.fileTree.buttonPanel.fileButtonPanel.numRowsTextCtrl.SetValue("%d" % 0)
        
        return
    
    def ShowPixelData(self, message):
        '''
        Plot the diffraction data for the pixel selected from the mda file.
        
        message - data passed into this function, has the form of a tuple
                  (inner scan number of pixels, pixel x value, pixel y value)
        '''
        if USE_OLD_PUBLISHER:
            sizeX = message.data[0]
            valueX = message.data[1]
            valueY = message.data[2]
        else:
            sizeX = message[0]
            valueX = message[1]
            valueY = message[2]
        
        # Calculate the index of the file for the desired pixel.
        self.index = ((sizeX * valueY) + valueX)
        self.PlotDiffractionFile(self.index)
        
        return
    
    def GetROIBounds(self):
        '''
        Set the values of the ROI display widgets.
        '''
        
        if self.fileTree:
            i = 0
            roiList = self.fileTree.buttonPanel.roiPanel.GetRoiList()
            controlList = self.fileTree.buttonPanel.roiPanel.GetTextControlList()

            if self.plot_type == constants.TWOD_PLOT:
                # For each set of ROI widgets, check to make sure that the lower value
                # is less than the upper value.  If not, then switch them.
                for ctrl in controlList:
                    roiList[i].SetNewLineData()
                    bounds = roiList[i].GetLinePositions()
                    lowerBound = bounds[0]
                    upperBound = bounds[1]
                    print bounds
                    if lowerBound < upperBound:
                        ctrl[0].SetValue("%f" % lowerBound)
                        ctrl[1].SetValue("%f" % upperBound)
                    else:
                        ctrl[0].SetValue("%f" % upperBound)
                        ctrl[1].SetValue("%f" % lowerBound)
                
                    i = i + 1

            if self.plot_type == constants.IMAGE:
                for ctrl in controlList:
                    dimensions = roiList[i].GetDimensions()
                    ctrl[0].SetValue("%d,%d" % (dimensions[0], dimensions[1]))
                    ctrl[1].SetValue("%d,%d" % (dimensions[2], dimensions[3]))
        
        return

    def OnSaveFileButtonClick(self, event):

        # Get the path to the file and the file name
        path = self.fileTree.dirPanel.dirControl.GetPath()
        listItem = self.fileTree.filePanel.fileListCtrl.GetItem(self.index, 1)
        filename = listItem.GetText()

        filename = filename + '_nobackground'
        self.data.WriteFileWithoutBackground(os.path.join(path, filename))

        return
    
    def OnPlotButtonClick(self, event):
        '''
        Creates a 2D plot when the user clicks the button.
        '''
        
        self.index = self.fileTree.filePanel.fileListCtrl.GetFocusedItem()

        subtract_background = self.fileTree.buttonPanel.fileButtonPanel.backgroundCheckBox.IsChecked()

        self.PlotDiffractionFile(self.index, subtract_background)
               
        return
    
    def PlotDiffractionFile(self, index, subtract_background=False):
        '''
        Plot a file that contains diffraction data.
        
        
        This function expects that the file is of a particular file format.
        '''
        
        # Get the path to the file and the file name
        path = self.fileTree.dirPanel.dirControl.GetPath()
        listItem = self.fileTree.filePanel.fileListCtrl.GetItem(index, 1)
        fileName = listItem.GetText()

        if fileName.endswith('.tif'):
            self.data = TiffDatatArray()
            if not self.plot_type == constants.IMAGE:
                self.fileTree.buttonPanel.roiPanel.ClearAndReset(2, constants.RECTANGLE)
            self.plot_type = constants.IMAGE
            self.fileTree.buttonPanel.fileButtonPanel.backgroundCheckBox.SetValue(False)
        elif fileName.endswith('.int'):
            self.data = XYDataArray()
            if not self.plot_type == constants.TWOD_PLOT:
                self.fileTree.buttonPanel.roiPanel.ClearAndReset(2, constants.LINE)
            self.plot_type = constants.TWOD_PLOT
        else:
            dlg = wx.MessageDialog(parent=None, message="Error: Unknown file type",
                                   caption="File Type Error", style=wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            dlg.Destroy()
            return
        
        # Read the file data
        self.data.CreateArrays(os.path.join(path, fileName))

#        if subtract_background:
#            self.data.CalculateBackground()
#            self.plottingPanel.draw(self.data, False)
#        else:
            # Clear the old plot and draw the new one.
        self.plottingPanel.draw(self.data, True, self.plot_type)
        
        # If there were ROI lines on a previous plot, redraw them.
        roiList = self.fileTree.buttonPanel.roiPanel.GetRoiList()
        for roi in roiList:
            roi.SetNewAxes(self.plottingPanel.subplot)
            roi.AddLines()
    
        self.plottingPanel.canvas.draw()
        
        return
    
    def OnSumDataButtonClick(self, event):
        '''
        Start a thread to sum the data in all ROIs across all data files.
        '''

        # Get the number of rows and columns in the scan.  Make sure that there are values
        # before going to the trouble of processing all the data files.
        try:
            numRows = int(self.fileTree.buttonPanel.fileButtonPanel.numRowsTextCtrl.GetValue())
            numColumns = int(self.fileTree.buttonPanel.fileButtonPanel.numColumnsTextCtrl.GetValue())
        except ValueError:
            print 'Error'
            dialog = wx.MessageDialog(self, "Please enter values for the number of rows and columns in the scan.", "Error", style=wx.ICON_ERROR)
            dialog.ShowModal()
            return

        # Get the list of region of interest objects.
        roiList = self.fileTree.buttonPanel.roiPanel.GetRoiList()
        numRois = len(roiList)
        path = self.fileTree.dirPanel.dirControl.GetPath()
        fileList = self.fileTree.filePanel.fileListCtrl

        # Create a list of all of the files that were checked by the user to be
        # included in the summation.
        checkedFileList = self.CreateCheckedFileList(fileList)

        # Set the range of the progress bar to be the number of files that will be summed.
        self.fileTree.buttonPanel.fileButtonPanel.progressGauge.SetRange(len(checkedFileList))

        if self.plot_type == constants.TWOD_PLOT:
            worker = DataSummationThread(self, roiList, checkedFileList, path, self.UpdateProgressBar)

        if self.plot_type == constants.IMAGE:
            worker = ImageROISummationThread(self, roiList, checkedFileList, path, self.UpdateProgressBar)

        worker.start()
        return

    def PlotSumData(self, evt):
        '''
        Create plots of the summed ROI data for each ROI.
        '''

        # Get the number of rows and columns in the scan.
        try:
            numRows = int(self.fileTree.buttonPanel.fileButtonPanel.numRowsTextCtrl.GetValue())
            numColumns = int(self.fileTree.buttonPanel.fileButtonPanel.numColumnsTextCtrl.GetValue())
        except ValueError:
            self.fileTree.buttonPanel.fileButtonPanel.progressGauge.SetValue(0)
            return
        
        # Get the arrays that need to be plotted.
        roiSums = evt.GetValue()

        # Get the number of ROIs that the user set up.
        numRois = len(self.fileTree.buttonPanel.roiPanel.GetRoiList())
        
        # For each ROI, plot the sum of the data.
        for j in range(numRois):
            # Reshape the ROI from a 1D array to a 2D array
            z_values = numpy.reshape(roiSums[j], (numRows, numColumns), order='C')
            maxVal = numpy.amax(roiSums[j])
            minVal = numpy.amin(roiSums[j])
            # Create a wx.Frame object to display the plot.
            plotFrame = PlotFrame3D.PlotFrame3D(self, "ROI %d" % (j + 1), numRows, numColumns, z_values, maxVal, minVal)
            plotFrame.Show(True)
        
        # Reset the progress bar back to zero.
        self.fileTree.buttonPanel.fileButtonPanel.progressGauge.SetValue(0)
            
        return

    def OnPlotImageSumButtonClick(self, event):
        self.ImageSum()
        return

    def ImageSum(self):

        path = self.fileTree.dirPanel.dirControl.GetPath()
        fileList = self.fileTree.filePanel.fileListCtrl

        checkedFileList = self.CreateCheckedFileList(fileList)
        self.scale_factor = len(checkedFileList)

        # Set the range of the progress bar to be the number of files that will be summed.
        self.fileTree.buttonPanel.fileButtonPanel.progressGauge.SetRange(len(checkedFileList))

        if self.plot_type == constants.IMAGE:
            worker = ImagePixelSummationThread(self, self.data.GetArraySize(),checkedFileList, path,
                                               self.UpdateProgressBar)
            worker.start()

        return

    def PlotImageSum(self, evt):

        image = evt.GetValue()
        self.data = DataArray(data=image)

        self.data.ScaleData(self.scale_factor)

        self.plottingPanel.draw(self.data, True, self.plot_type)

        # Reset the progress bar back to zero.
        self.fileTree.buttonPanel.fileButtonPanel.progressGauge.SetValue(0)

        # If there were ROI lines on a previous plot, redraw them.
        roiList = self.fileTree.buttonPanel.roiPanel.GetRoiList()
        for roi in roiList:
            roi.SetNewAxes(self.plottingPanel.subplot)
            roi.AddLines()

        self.plottingPanel.canvas.draw()

        return

    def UpdateProgressBar(self, message):

        old_value = self.fileTree.buttonPanel.fileButtonPanel.progressGauge.GetValue()
        self.fileTree.buttonPanel.fileButtonPanel.progressGauge.SetValue(old_value + message)

        return

    def CreateCheckedFileList(self, fileList):

        # Create a list of all of the files that were checked by the user to be
        # included in the summation.
        numFiles = fileList.GetItemCount()
        checkedFileList = []
        for i in range(numFiles):
            if fileList.IsChecked(i):
                listItem = fileList.GetItem(i, 1)
                fileName = listItem.GetText()
                checkedFileList.append(fileName)

        return checkedFileList
    
    def OnCloseButtonClick(self, event):
        self.Close(True)
        return
    
    def OnCloseWindow(self, event):
        if (USE_OLD_PUBLISHER):
            self.dataPublisher.sendMessage(("close_application"), None, onTopicNeverCreated=None)
        else:
            self.dataPublisher.sendMessage(("close_application"), message=None)

        self.Destroy()
        return

#################################################################################################################################    
class PlottingPanel(wx.Panel):
    '''
    Creates a panel to hold objects from matplotlib that are used for plotting 
    diffraction data from a file.
    '''
    
    def __init__(self, parent):
        '''
        Constructor
        '''

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        self.parent = parent
        self.arrayValues = None
        self.min = None
        self.max = None
        self.figure_height = 5.0
        self.figure_width = 5.0
        self.data = None
        self.plot_type = None
        self.plot = None
        
        # Create the figure, canvas, and axes used to plot the data
        self.figure = Figure((5,5), 150)
        self.subplot = self.figure.add_subplot(111)
        self.figure.tight_layout(pad=1.2)
        self.canvas = FigureCanvas(self, -1, self.figure)

        self.adjustmentsPanel = ImageAdjustmentPanel(self)

        self.toolbar = Toolbar(self.canvas)
        self.toolbar.Realize()
        
        # Bind a draw event to a function
        self.canvas.mpl_connect('draw_event', self.GetROIBounds)

        self.Bind(wx.EVT_SLIDER, self.AdjustImage, id=self.adjustmentsPanel.contrastSlider.GetId())
        
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(self.canvas, 1, wx.EXPAND)
        panelSizer.Add(self.adjustmentsPanel, 0, wx.EXPAND)
        panelSizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        
        self.SetSizer(panelSizer)
        self.Fit()
        
        return

    def AdjustImage(self, event):

        if self.plot_type == constants.IMAGE:

            value = float(self.adjustmentsPanel.contrastSlider.GetValue())
            tempMax = float(self.max) * (1.0/value)
            self.plot.set_clim(vmax=tempMax)
            self.canvas.draw()

        return
    
    def GetROIBounds(self, event):
        parent = self.GetParent()
        parent.GetROIBounds()
        
        return
    
    def draw(self, data, clear=False, plot_type=constants.TWOD_PLOT):
        '''
        Draw the data on the plot
        
        data - This is an object of type XYDataArray
        clear - This indicates whether or not the current plot should be erased before new data is plotted.
        '''

        # Get the data to be plotted.  It is a 2D array.
        self.arrayValues = data.GetDataArray()
        self.data = data
        self.plot_type = plot_type

        if clear:
            self.figure.clear()
            self.subplot = self.figure.add_subplot(111)
        
        # Set the plot and axies labels, then draw the plot.    
        self.subplot.set_xlabel(data.GetAxisLabels()[0])
        self.subplot.set_ylabel(data.GetAxisLabels()[1])
        self.figure.suptitle(data.GetDataFileName(), fontsize=8)

        if plot_type == constants.TWOD_PLOT:
            x_values = self.arrayValues[0]
            y_values = self.arrayValues[1]

            if self.parent.fileTree.buttonPanel.fileButtonPanel.backgroundCheckBox.IsChecked():
                background = data.CalculateBackground()
                self.subplot.plot(x_values, background)
            else:
                self.subplot.plot(x_values, y_values)

        if plot_type == constants.IMAGE:
            self.min = numpy.amin(self.arrayValues)
            self.max = numpy.amax(self.arrayValues)
            sliderMax = self.adjustmentsPanel.contrastSlider.GetMax()
            sliderVal = self.adjustmentsPanel.contrastSlider.GetValue()

            # Set the maximum of the contrast slider to half of the maximum value of the image.
            # That way, the least value of vmax that can be set by the slider is 2.
            self.adjustmentsPanel.contrastSlider.SetMax(self.max/2)

            # Scale the value of the slider control so that the image appearance does not
            # change from one to the next.
            newSliderVal = float(sliderVal) * ((float(self.max)/2.0) / float(sliderMax))
            self.adjustmentsPanel.contrastSlider.SetValue(newSliderVal)

            # Set the maximum value displayed.
            tempMax = float(self.max) * (1.0/newSliderVal)
            print tempMax

            # Plot the image
            self.plot = self.subplot.imshow(self.arrayValues, cmap=cm.get_cmap('gnuplot2'), norm=None, aspect='equal',
                                            interpolation=None, alpha=None, vmin=self.min, vmax=tempMax,
                                            origin='upper')

        self.canvas.draw()

        return
        
    def GetPlotInfo(self):
        return (self.subplot, self.figure, self.canvas)

class ImageAdjustmentPanel(wx.Panel):
    '''
    classdocs
    '''

    def __init__(self, parent):
        '''
        Constructor
        '''

        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.parent = parent

        self.contrastLabel = wx.StaticText(self, -1, "Contrast", style=wx.ALIGN_CENTER | wx.SIMPLE_BORDER)

        self.contrastSlider = wx.Slider(self, id=1001, minValue=1, maxValue=500)

        panelSizer = wx.BoxSizer(wx.HORIZONTAL)
        panelSizer.Add(self.contrastLabel, 0)
        panelSizer.Add(self.contrastSlider, 1, wx.EXPAND)

        self.SetSizer(panelSizer)
        self.Fit()

        return
#################################################################################################################################
class FileTreePanel(wx.Panel):
    '''
    classdocs
    '''
    
    def __init__(self, parent, plotObjects):
        '''
        Constructor
        '''
        
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.parent = parent
                
        splitter = wx.SplitterWindow(self, -1, style=wx.CLIP_CHILDREN | wx.SP_LIVE_UPDATE | wx.SP_3D)
        
        self.dirPanel = DirectoryPanel(splitter)
        self.filePanel = FilePanel(splitter)
        self.buttonPanel = ButtonPanel(self, plotObjects)

        splitter.SetMinimumPaneSize(100)
        splitter.SplitVertically(self.dirPanel, self.filePanel, 0)

        self.fileFilterBox = wx.ComboBox(self, -1, value=".*", size=wx.Size(100,30),
                                         choices=[".*", ".int", ".int_nobackground", ".tif"], style=wx.CB_READONLY)
        
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnDirSelectionChanged, self.dirPanel.dirControl.GetTreeCtrl())
        self.Bind(wx.EVT_BUTTON, self.OnSelectAllButtonClick, self.buttonPanel.fileButtonPanel.selectAllButton)
        self.Bind(wx.EVT_BUTTON, self.OnSelectRangeButtonClick, self.buttonPanel.fileButtonPanel.selectRangeButton)
        self.Bind(wx.EVT_BUTTON, self.OnClearAllButtonClick, self.buttonPanel.fileButtonPanel.clearAllButton)
        self.Bind(wx.EVT_COMBOBOX, self.OnSelectFileFilter, self.fileFilterBox)
        
        
        splitterSizer = wx.BoxSizer(wx.VERTICAL)
        splitterSizer.Add(splitter, 1, wx.EXPAND)
        splitterSizer.Add(self.fileFilterBox, 0, wx.ALIGN_RIGHT)
        
        buttonPanelSizer = wx.BoxSizer(wx.VERTICAL)
        buttonPanelSizer.Add(self.buttonPanel, 0, wx.EXPAND)
        
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(splitterSizer, 1, wx.EXPAND)
        panelSizer.Add(buttonPanelSizer, 0, wx.EXPAND) 
        
        self.SetAutoLayout(True)
        self.SetSizer(panelSizer)
        self.Layout()

        return
    
    def OnDirSelectionChanged(self, event):
        '''
        This function populates the list control with a list
        of files every time the user selects a new directory.
        '''
        
        # Get the directory path selected by the user.
        currentPath = self.dirPanel.dirControl.GetPath()

        # Get rid of the current list of files
        listSize = self.filePanel.fileListCtrl.GetItemCount()
        if listSize > 0:
            self.filePanel.fileListCtrl.DeleteAllItems()
        
        # Generate a new list of files using the selected path.
        builder = FileListBuilder()
        files = builder.CreateNewSortedFileList(currentPath, None)
        num_files = range(len(files))
        # Populate the list control with the new file list.
        for num, file_name in zip(num_files, files):
            index = self.filePanel.fileListCtrl.InsertStringItem(sys.maxint, "%d" % (num + 1))
            self.filePanel.fileListCtrl.SetStringItem(index, 1, "%s" % file_name)

        event.Skip()
        return

    def OnSelectFileFilter(self, event):
        # Get the directory path and the file filter selected by the user.
        currentPath = self.dirPanel.dirControl.GetPath()
        fileFilterIndex = self.fileFilterBox.GetSelection()
        if fileFilterIndex == 0:
            fileFilterString = None
        else:
            fileFilterString = self.fileFilterBox.GetStringSelection()

        # Generate a new list of files using the selected path and filter.
        builder = FileListBuilder()
        files = builder.CreateNewSortedFileList(currentPath, fileFilterString)

        # Clear the current list control of items
        self.filePanel.fileListCtrl.DeleteAllItems()
        i = 1
        for fileitem in files:
            index = self.filePanel.fileListCtrl.InsertStringItem(sys.maxint, "%d" % i)
            self.filePanel.fileListCtrl.SetStringItem(index, 1, "%s" % fileitem[0])
            i = i + 1

        # Redraw the list of files
        self.filePanel.fileListCtrl.RefreshItems(itemFrom=0, itemTo=len(files))

        return
    
    def OnSelectAllButtonClick(self, event):
        '''
        This function causes all items in the list control to be selected
        '''
        
        numItems = self.filePanel.fileListCtrl.GetItemCount()
        
        for i in range(numItems):
            self.filePanel.fileListCtrl.CheckItem(i, True)
            
        return
    
    def OnClearAllButtonClick(self, event):
        '''
        This function causes all items in the list control to be deselected.
        '''
        
        numItems = self.filePanel.fileListCtrl.GetItemCount()
        
        for i in range(numItems):
            self.filePanel.fileListCtrl.CheckItem(i, False)
            
        return
    
    def OnSelectRangeButtonClick(self, event):
        '''
        This function selects a range of items in the list control
        based on user input.
        '''
        
        beginning = int(self.buttonPanel.fileButtonPanel.beginRangeTextCtrl.GetValue()) - 1
        end = int(self.buttonPanel.fileButtonPanel.endRangeTextCtrl.GetValue())
        selectRange = (end - beginning) 
        
        for i in range(selectRange):
            self.filePanel.fileListCtrl.CheckItem(beginning + i, True)
        
            
        return

#################################################################################################################################
class DirectoryPanel(wx.Panel):
    '''
    classdocs
    '''
    
    def __init__(self, parent):
        '''
        Constructor
        '''
        
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.dirControl = wx.GenericDirCtrl(self, -1, size=wx.Size(200,425), style=wx.DIRCTRL_DIR_ONLY)
        
        panelSizer.Add(self.dirControl, 1, wx.EXPAND)
        
        self.SetAutoLayout(True)
        self.SetSizer(panelSizer)
        self.Layout()
        
        return

#################################################################################################################################    
class FilePanel(wx.Panel):
    '''
    classdocs
    '''
    
    def __init__(self, parent):
        '''
        Constructor
        '''
        
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        
        self.fileListCtrl = CLC(self, size=wx.Size(300, 300))
        
        self.fileListCtrl.InsertColumn(0, "Item #")
        self.fileListCtrl.InsertColumn(1, "File Name")
        
        self.fileListCtrl.SetColumnWidth(0,75)
        self.fileListCtrl.SetColumnWidth(1,225)
        
        panelSizer.Add(self.fileListCtrl, 1, wx.EXPAND)
        
        self.SetAutoLayout(True)
        self.SetSizer(panelSizer)
        self.Layout()
        
        return

#################################################################################################################################    
class ButtonPanel(wx.Panel):
    '''
    classdocs
    '''

    def __init__(self, parent, plot):
        '''
        Constructor
        '''
        
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)

        self.parent = parent
        
        self.panelSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.fileButtonPanel = FileButtonPanel(self)
        self.roiPanel = DynamicTextControlPanel(self, "ROI", plot, 60, 20, 1, 2)
        self.roiPanel.SetupScrolling(scroll_x=False)
        
        self.panelSizer.Add(self.roiPanel, 1, wx.ALIGN_CENTER | wx.ALL, 20)
        self.panelSizer.Add(self.fileButtonPanel, 1, wx.ALIGN_CENTER | wx.ALL, 20)
        
        self.SetAutoLayout(True)
        self.SetSizer(self.panelSizer)
        self.Layout()
        
        return
    
    def Redraw(self):
        self.panelSizer.Layout()
        return

    def Reset(self):
        return
    
#################################################################################################################################    
class FileButtonPanel(wx.Panel):
    '''
    classdocs
    '''
    
    def __init__(self, parent):
        '''
        Constructor
        '''
        
        wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
        
        self.selectAllButton = wx.Button(self, -1, "Select All",size=wx.Size(100,30))
        self.clearAllButton = wx.Button(self, -1, "Clear All",size=wx.Size(100,30))
        self.plotDataButton = wx.Button(self, -1, "Plot File",size=wx.Size(100,30))
        self.sumDataButton = wx.Button(self, -1, "Sum ROIs",size=wx.Size(100,30))
        self.plotSumButton = wx.Button(self, -1, "Plot Image Sum",size=wx.Size(100,30))
        self.exitButton = wx.Button(self, -1, "Exit",size=wx.Size(100,30))
        
        self.selectRangeButton = wx.Button(self, -1, "Select Range",size=wx.Size(100,30))
        self.beginRangeTextCtrl = wx.TextCtrl(self, -1, " ",size = wx.Size(60,30), style=wx.SIMPLE_BORDER)
        self.endRangeTextCtrl = wx.TextCtrl(self, -1, " ",size = wx.Size(60,30), style=wx.SIMPLE_BORDER)
        self.rangeLabel = wx.StaticText(self, -1, "To", style=wx.ALIGN_CENTER | wx.SIMPLE_BORDER)
        
        self.rowsLabel = wx.StaticText(self, -1, "# points in Y", style=wx.ALIGN_CENTER | wx.SIMPLE_BORDER)
        self.columnsLabel = wx.StaticText(self, -1, "# points in X", style=wx.ALIGN_CENTER | wx.SIMPLE_BORDER)
        self.numRowsTextCtrl = wx.TextCtrl(self, -1, " ",size = wx.Size(60,30), style=wx.SIMPLE_BORDER)
        self.numColumnsTextCtrl = wx.TextCtrl(self, -1, " ",size = wx.Size(60,30), style=wx.SIMPLE_BORDER)
        
        self.backgroundCheckBox = wx.CheckBox(self, -1, "Remove background", size=wx.Size(150,20))
        self.saveAsFileButton = wx.Button(self, -1, "Save Without Background",size=wx.Size(200,30))
        
        self.progressGauge = wx.Gauge(self, -1, range=2500, size=wx.Size(200,30))
        
        self.line1 = wx.StaticLine(self, -1, size=wx.Size(250,8), style=wx.LI_HORIZONTAL)
        self.line2 = wx.StaticLine(self, -1, size=wx.Size(250,8), style=wx.LI_HORIZONTAL)
        self.line3 = wx.StaticLine(self, -1, size=wx.Size(250,8), style=wx.LI_HORIZONTAL)
        
        self.selectAllButton.SetToolTipString("Select all listed files for summing ROIs.")
        self.selectRangeButton.SetToolTipString("Select a range of files listed for summing ROIs.")
        self.clearAllButton.SetToolTipString("Deselect all files.")
        self.plotDataButton.SetToolTipString("Show file data in a 2D plot.")
        self.saveAsFileButton.SetToolTipString("Save plotted file with background subtracted")
        self.sumDataButton.SetToolTipString("Sum all ROI data in selected files and create plots.")
        self.plotSumButton.SetToolTipString("Plot a sum of all selected images.")
        self.exitButton.SetToolTipString("Exit the application.")
        
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer1.Add(self.selectAllButton, 0, wx.ALIGN_CENTER)
        sizer1.Add(self.clearAllButton, 0, wx.ALIGN_CENTER)
        
        rangeSizer = wx.BoxSizer(wx.HORIZONTAL)
        rangeSizer.Add(self.selectRangeButton, 0, wx.ALIGN_CENTER)
        rangeSizer.Add(self.beginRangeTextCtrl, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, border=5)
        rangeSizer.Add(self.rangeLabel, 0, wx.ALIGN_CENTER)
        rangeSizer.Add(self.endRangeTextCtrl, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, border=5)
        
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2.Add(self.columnsLabel, 0, wx.ALIGN_CENTER)
        sizer2.Add(self.numColumnsTextCtrl, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, border=5)
        sizer2.Add(self.rowsLabel, 0, wx.ALIGN_CENTER)
        sizer2.Add(self.numRowsTextCtrl, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, border=5)
        
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(self.plotDataButton, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, border=5)
        sizer3.Add(self.backgroundCheckBox, 0, wx.ALIGN_CENTER)

        sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        sizer4.Add(self.saveAsFileButton, 0, wx.ALIGN_CENTER)
        
        panelSizer = wx.BoxSizer(wx.VERTICAL)
        
        panelSizer.Add(sizer1, 0, wx.ALIGN_CENTER)
        panelSizer.Add(rangeSizer, 0, wx.ALIGN_CENTER)
        panelSizer.Add(self.line1, 0, wx.ALIGN_CENTER)
        panelSizer.Add(sizer2, 0, wx.ALIGN_CENTER)
        panelSizer.Add(sizer3, 0, wx.ALIGN_CENTER)
        panelSizer.Add(sizer4, 0, wx.ALIGN_CENTER)
        panelSizer.Add(self.line2, 0, wx.ALIGN_CENTER)
        panelSizer.Add(self.sumDataButton, 0, wx.ALIGN_CENTER)
        panelSizer.Add(self.plotSumButton, 0, wx.ALIGN_CENTER)
        panelSizer.Add(self.progressGauge, 0, wx.ALIGN_CENTER)
        panelSizer.Add(self.line3, 0, wx.ALIGN_CENTER)
        panelSizer.Add(self.exitButton, 0, wx.ALIGN_CENTER)
        
        self.SetAutoLayout(True)
        self.SetSizer(panelSizer)
        self.Layout()
        
        return
    
#################################################################################################################################