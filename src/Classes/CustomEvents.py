'''
Created on Nov 7, 2014

@author: roehrig
'''

import wx

myEVT_SUM_DATA = wx.NewEventType()
EVT_SUM_DATA = wx.PyEventBinder(myEVT_SUM_DATA, 1)

myEVT_UPDATE_PROGRESS = wx.NewEventType()
EVT_UPDATE_PROGRESS = wx.PyEventBinder(myEVT_UPDATE_PROGRESS, 1)

myEVT_PLOT_IMAGE_SUM = wx.NewEventType()
EVT_PLOT_IMAGE_SUM = wx.PyEventBinder(myEVT_PLOT_IMAGE_SUM, 1)

class DataSummationEvent(wx.PyCommandEvent):
    '''
    This event object is used to signal that the ROI data
    has been summed and is ready for plotting.
    '''
    
    def __init__(self, etype, eid, value=None):
        
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value
        
        return
    
    def GetValue(self):
        return self._value
    
class UpdateProgressEvent(wx.PyCommandEvent):
    '''
    This event object is used to update the value of 
    a wx.Gauge widget.
    '''
    
    def __init__(self, etype, eid, value=None):
        
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value
        
        return
    
    def GetValue(self):
        return self._value

class ImageSummationEvent(wx.PyCommandEvent):
    '''
    This event object is used to signal that the ROI data
    has been summed and is ready for plotting.
    '''

    def __init__(self, etype, eid, value=None):

        wx.PyCommandEvent.__init__(self, etype, eid)
        self._value = value

        return

    def GetValue(self):
        return self._value
