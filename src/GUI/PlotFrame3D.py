'''
Created on Oct 22, 2014

@author: roehrig
'''
import wx
import matplotlib
import numpy as np
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx as Toolbar
from matplotlib.figure import Figure
from matplotlib import cm
from matplotlib.widgets import RadioButtons

class PlotFrame3D(wx.Frame):
    '''
    classdocs
    '''

    def __init__(self, parent, title, numRows, numColumns, z_values, maxValue, minValue):
        '''
        Constructor
        '''
        
        wx.Frame.__init__(self, parent, title=title, pos=(200,200), size=(200,200))
        
        self.x_values = np.empty([numRows,numColumns])
        self.y_values = np.zeros([numRows,numColumns])
        self.z_values = z_values
        self.minValue = minValue
        self.maxValue = maxValue
        
        for i in range(numRows):
            self.x_values[i] = np.arange(1,numColumns + 1)        

        for i in range(numRows):
            self.y_values[i] = self.y_values[i] + (i + 1)

        self.figure = Figure((5,5), 150)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.subplot = self.figure.add_subplot(111)
        
        self.canvas.mpl_connect('motion_notify_event', self.UpdateStatusBar)

        self.toolbar = Toolbar(self.canvas)
        self.toolbar.Realize()
        
        self.imageButton = wx.RadioButton(self, 100, label='Image', size=wx.Size(100,20), style=wx.RB_GROUP)
        self.wireButton = wx.RadioButton(self, 101, label='3D Wire', size=wx.Size(100,20))
        self.surfaceButton = wx.RadioButton(self, 102, label='3D Surface', size=wx.Size(100,20))
        self.twoDButton = wx.RadioButton(self, 103, label='2D Plot', size=wx.Size(100,20))
        
        self.Bind(wx.EVT_RADIOBUTTON, self.ChangePlotType, id=self.imageButton.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.ChangePlotType, id=self.wireButton.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.ChangePlotType, id=self.surfaceButton.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.ChangePlotType, id=self.twoDButton.GetId())
        
        self.statusBar = wx.StatusBar(self, -1)
        self.statusBar.SetFieldsCount(1)
        self.SetStatusBar(self.statusBar)
        
        self.subplot.imshow(z_values, cmap=cm.get_cmap('gnuplot2'), norm=None, aspect='equal', interpolation=None,
                            alpha=None, vmin=minValue, vmax=maxValue, origin='lower')
        
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.Add(self.imageButton, 0)
        buttonSizer.Add(self.wireButton, 0)
        buttonSizer.Add(self.surfaceButton, 0)
        buttonSizer.Add(self.twoDButton, 0)

        panelSizer = wx.BoxSizer(wx.VERTICAL)
        panelSizer.Add(self.canvas, 1, wx.EXPAND)
        panelSizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        panelSizer.Add(buttonSizer, 0, flag=wx.ALL | wx.EXPAND, border=5)
        
        self.SetSizer(panelSizer)
        self.Fit()
        
        return
    
    def OnCloseWindow(self, event):
        self.Destroy()
        return
    
    def UpdateStatusBar(self, event):
        if event.inaxes:
            x, y = int(event.xdata), int(event.ydata)
            self.statusBar.SetStatusText(( "x= " + str(x) + "  y=" +str(y) + "  z=" +str(self.z_values[y][x])), 0)
            
    def ChangePlotType(self, event):
        
        self.figure.clear()
        
        # Create an image plot
        if event.GetId() == 100:
            self.subplot = self.figure.add_subplot(111)
            self.subplot.imshow(self.z_values, cmap=cm.get_cmap('gnuplot2'), norm=None, aspect='equal', interpolation=None,
                            alpha=None, vmin=self.minValue, vmax=self.maxValue, origin='lower')

        # Create a 3D wire plot
        if event.GetId() == 101:
            self.subplot = self.figure.add_subplot(111, projection='3d')
            self.subplot.plot_wireframe(self.x_values, self.y_values, self.z_values)
            
        # Create a 3D surface plt    
        if event.GetId() == 102:
            self.subplot = self.figure.add_subplot(111, projection='3d')
            self.subplot.plot_surface(self.x_values, self.y_values, self.z_values, rstride=1, cstride=1, cmap=cm.get_cmap('cool'),
                                      linewidth=0, antialiased=False)

        if event.GetId() == 103:
            self.subplot = self.figure.add_subplot(111)
            dataCopy = self.z_values.copy(order='K')
            x_values = np.arange(0, dataCopy.size)
            self.subplot.plot(x_values, dataCopy.flatten('A'))
            
        self.canvas.draw()
        
        return
