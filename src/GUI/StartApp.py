'''
Created on Aug 18, 2014

@author: roehrig
'''

import sys
import os

filePath = os.path.split(__file__)
sys.path.append(filePath[0] + '/..')
sys.path.append(filePath[0] + '/../../../GenericClasses/src')

import wx
import MainFrame
import MDAexplorer

class MyApp(wx.App):
    def __init__(self, redirect=False, filename=None, useBestVisual=False, clearSigInt=False):
        wx.App.__init__(self, redirect, filename, useBestVisual, clearSigInt)
        
    def OnInit(self):
        
        # Create the window for looking at the integrated diffraction data.
        startWindow = MainFrame.MainFrame(None, "X-Ray Diffraction Data Tool")
        startWindow.Show(True)
        
        # Create the window for displaying the mda files
#        mdaWindow = MDAexplorer.TopFrame(None, -1, 'MDA Explorer', size=(800,500))
#        mdaWindow.Center()
#        (hS, vS) = mdaWindow.GetSize()
#        (hP, vP) = mdaWindow.GetPosition()
#        mdaWindow.width = (hP + hS/2)*2
#        mdaWindow.height = (vP + vS/2)*2
#        mdaWindow.SetMaxSize((mdaWindow.width, mdaWindow.height))
#        mdaWindow.Show(True)
        
        return True

if __name__ == '__main__':

    app = MyApp(False)
    app.MainLoop()