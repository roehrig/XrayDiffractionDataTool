'''
Created on Nov 13, 2012

@author: roehrig
'''

import wx
from random import *
from wx.lib.scrolledpanel import ScrolledPanel
from Classes.graphingtools import ROI

########################################################################
class TextControlPanel (wx.Panel):
    '''
    This is a panel that can be used for a dynamically changing number of entries.
    '''

    def __init__(self, parent, plot, roiList=[], sectionNumber=1, *args, **kwargs):
        '''
        Constructor
        
        Create a label, a text control, and a remove button.
        
        textLabel - An ascii string that will be used as a label for the text control
        width - The width in pixels of the text control, it defaults to 200
        height - The height in pixels of the text control, it defaults to 20
        sectionNumber - The number of the text control, which is added to the label
        sectionList - A list of text controls that the new text control is appended to
        '''
        wx.Panel.__init__(self, parent=parent, style=wx.BORDER_RAISED, id=wx.ID_ANY ,*args, **kwargs)
        
        self._parentPanel = parent
        self._sectionNumber = sectionNumber
        self.plot = plot
        self.red = random()
        self.blue = random()
        self.green = random()
        self.color = wx.Colour((self.red * 255), (self.green * 255), (self.blue * 255))
        self.labelColor = wx.Colour(255,255,255)
        self.roi = ROI(self.plot[0], self.plot[1], self.plot[2], self.red, self.green, self.blue)
        roiList.append(self.roi)
        
        return
        
    def OnRemoveButtonClick(self, event):
        self._parentPanel.OnRemoveSection(self, self.sectionTxtCtrl, self._sectionNumber)
        return
        
    def GetSectionNumber(self):
        return self._sectionNumber
    
    def SetSectionNumber(self, number):
        self._sectionNumber = number
        return
    
    def SetSectionNumberText(self, text, number):
        newLabel = "%s %s" % (text, number)
        self.sectionNumberLabel.SetLabel(newLabel)
        self.SetSectionNumber(number)
        self.Layout()
        return

########################################################################
class SingleTextControlPanel (TextControlPanel):
    '''
    This is a panel that can be used for a dynamically changing number of entries.
    '''
    
    def __init__(self, parent, textLabel, plot, textCtrlList=[], roiList=[], width=200, height=20, sectionNumber=1, *args, **kwargs):
        '''
        Constructor
        
        Create a label, a text control, and a remove button.
        
        textLabel - An ascii string that will be used as a label for the text control
        width - The width in pixels of the text control, it defaults to 200
        height - The height in pixels of the text control, it defaults to 20
        sectionNumber - The number of the text control, which is added to the label
        secionList - A list of text controls that the new text control is appended to
        '''
        
        TextControlPanel.__init__(self, parent, plot, roiList, sectionNumber)
        
        panelSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.sectionNumberLabel = wx.StaticText(self, -1, textLabel + " %s" % self._sectionNumber, style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER)
        
        self.sectionTxtCtrl = wx.TextCtrl(self, -1, "", size=wx.Size(width,height), style=wx.SIMPLE_BORDER)
        
        textCtrlList.append(self.sectionTxtCtrl)
        
        self.removeButton = wx.Button(self, -1, "Remove")
        self.removeButton.SetToolTipString("Remove %s" % textLabel)
        self.Bind(wx.EVT_BUTTON, self.OnRemoveButtonClick, self.removeButton)
        
        panelSizer.Add(self.removeButton, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 2)
        panelSizer.Add(self.sectionNumberLabel, 0, wx.EXPAND| wx.LEFT | wx.RIGHT, 2)
        panelSizer.Add(self.sectionTxtCtrl, 1, wx.EXPAND| wx.LEFT | wx.RIGHT, 2)
        
        self.SetAutoLayout(True)
        self.SetSizer(panelSizer)
        self.Fit()
        self.Layout()
        
        return
    
########################################################################
class DualTextControlPanel (TextControlPanel):
    '''
    This is a panel that can be used for a dynamically changing number of entries.
    '''
    
    def __init__(self, parent, textLabel, plot, textCtrlList=[], roiList=[], width=200, height=20, sectionNumber=1, *args, **kwargs):
        '''
        Constructor
        
        Create a label, two text controls, and a remove button.
        
        textLabel - An ascii string that will be used as a label for the text control
        width - The width in pixels of the text control, it defaults to 200
        height - The height in pixels of the text control, it defaults to 20
        sectionNumber - The number of the text control, which is added to the label
        secionList - A list of tuples of text controls to which the new text controls are appended as a tuple.
        '''

        TextControlPanel.__init__(self, parent, plot, roiList, sectionNumber)
        
        self._parentPanel = parent
        self._sectionNumber = sectionNumber
        
        panelSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.sectionNumberLabel = wx.StaticText(self, -1, textLabel + " %s" % self._sectionNumber,
                                                style=wx.ALIGN_CENTER_VERTICAL | wx.SIMPLE_BORDER | wx.ALIGN_CENTER_HORIZONTAL)
        
        self.firstSectionTxtCtrl = wx.TextCtrl(self, -1, "", size=wx.Size(width,height), style=wx.SIMPLE_BORDER)
        self.secondSectionTxtCtrl = wx.TextCtrl(self, -1, "", size=wx.Size(width,height), style=wx.SIMPLE_BORDER)
        self.SetBackgroundColour(self.color)
        self.sectionTxtCtrl = (self.firstSectionTxtCtrl, self.secondSectionTxtCtrl)
        
        textCtrlList.append(self.sectionTxtCtrl)
        
        self.removeButton = wx.Button(self, -1, "Remove")
        self.removeButton.SetToolTipString("Remove %s" % textLabel)
        self.Bind(wx.EVT_BUTTON, self.OnRemoveButtonClick, self.removeButton)
        
        panelSizer.Add(self.removeButton, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 2)
        panelSizer.Add(self.sectionNumberLabel, 0, wx.EXPAND| wx.LEFT | wx.RIGHT, 2)
        panelSizer.Add(self.firstSectionTxtCtrl, 1, wx.EXPAND| wx.LEFT | wx.RIGHT, 2)
        panelSizer.Add(self.secondSectionTxtCtrl, 1, wx.EXPAND| wx.LEFT | wx.RIGHT, 2)
        
        self.SetAutoLayout(True)
        self.SetSizer(panelSizer)
        self.Fit()
        self.Layout()
        
        return
        
########################################################################
class CommonButtonPanel (wx.Panel):
    '''
    This class just creates a panel with an add and a close button.
    '''
    
    def __init__(self, parent, toolTipText="text box", *args, **kwargs):
        '''
        Constructor
        '''
        wx.Panel.__init__(self, parent=parent, style=wx.DEFAULT, id=wx.ID_ANY ,*args, **kwargs)

        panelSizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.addSectionButton = wx.Button(self, -1, "Add")
        
        self.addSectionButton.SetToolTipString("Add new %s" % toolTipText)
        
        panelSizer.Add(self.addSectionButton, 0, wx.ALL |  wx.ALIGN_CENTER)
        
        self.SetAutoLayout(True)
        self.SetSizer(panelSizer)
        self.Layout()
        
        return

########################################################################
class TextControlPanelChooser():
    '''
    This class creates an object that inherits from TextPanelControl and returns it.
    '''
    def __init__(self, numTextCtrls=1):
        
        self.numTextCtrls = numTextCtrls
        
        return
    
    def CreateTextControlPanel(self, parentObject, label, controlList, roiList, plot, controlWidth, controlHeight, sectionNum):
        
        if self.numTextCtrls == 1:
            panel = SingleTextControlPanel(parentObject, label, plot, controlList, roiList, controlWidth, controlHeight, sectionNum)
        elif self.numTextCtrls == 2:
            panel = DualTextControlPanel(parentObject, label, plot, controlList, roiList, controlWidth, controlHeight, sectionNum)
            
        return panel
    
########################################################################
class DynamicTextControlPanel(ScrolledPanel):
    '''
    This is a panel that can have text controls added to or removed from it
    to accommodate needs.  Each text control, label, and remove button is wrapped
    in its own sub-panel and added to this panel.
    '''
    #----------------------------------------------------------------------
    def __init__(self, parent, textLabel, plot, width=200, height=20, sectionNumber=1, panelType=1, userFunction=None, *args, **kwargs):
        '''
        Constructor
        
        textLabel - A label for each text control
        textCtrlList - A list containing each text control
        width - The width, in pixels, of the text control.  The default is 200.
        height - The height, in pixels, of the text control.  The default is 20.
        sectionNumber - A number asscoiated with the text control sub-panel. The default is 1.
        '''
 
        ScrolledPanel.__init__(self, parent=parent, id=wx.ID_ANY, size=(150,200), style=wx.SUNKEN_BORDER)

        self._parent = parent
        self._textLabel = textLabel
        self._textWidth = width
        self._textHeight = height
        self._panelType = panelType
        self._plot = plot
        
        self._roiList = []
        self._textCtrlList = []
        
        self.chooser = TextControlPanelChooser(self._panelType)
 
        txtCtrlPanel = self.chooser.CreateTextControlPanel(self, self._textLabel, self._textCtrlList, self._roiList,
                                                           self._plot, self._textWidth, self._textHeight, sectionNumber)
        buttonPanel = CommonButtonPanel(self, self._textLabel)
        
        self._dynPanelList = [txtCtrlPanel]    # This is a list of panels that each contain a wx.TxtCtrl.
        
        # Bind the initial section buttons to functions
        self.Bind(wx.EVT_BUTTON, self.OnAddSection, buttonPanel.addSectionButton)
                
        self.sectionSizer = wx.BoxSizer(wx.VERTICAL)
        self.sectionSizer.Add(txtCtrlPanel, 0, wx.EXPAND)
        
        self.panelSizer = wx.BoxSizer(wx.VERTICAL)
        self.panelSizer.Add(self.sectionSizer, 0, wx.EXPAND)
        self.panelSizer.Add(buttonPanel, 0, wx.EXPAND)
 
        self.SetSizer(self.panelSizer)
        self.Layout()
        self.Fit()
        
        return
        
    def OnAddSection(self, event):
        '''
        This function adds a text control panel to the user display.
        '''
        # Create a new panel and add that panel to the list of panels.
        sectionNum = (len(self._dynPanelList) + 1)
        panel = self.chooser.CreateTextControlPanel(self, self._textLabel, self._textCtrlList, self._roiList,
                                                    self._plot, self._textWidth, self._textHeight, sectionNum)
        self._dynPanelList.append(panel)
        
        # Add the new panel to the the sizer
        # that contains all of the section panels.
        self.sectionSizer.Add(panel, 0, wx.EXPAND)

        # Have the panel sizer and the panel's parent redraw its self.
        self.panelSizer.Layout()
        self.Fit()
        self._parent.Redraw()
        return
        
    def OnRemoveSection(self, panel, sectionTextCtrl, sectionNumber):
        '''
        This function removes a section panel from the dynamic list and
        causes the panel to redraw itself with the new list.
        
        panel - The panel that should be removed from the list and the user display
        sectionTextCtrl - The text control object that should be removed.
        sectionNumber - The number of the section panel that should be removed.
        '''
        if (self.sectionSizer.GetChildren()):
            panel.roi.RemoveLines()
            self._roiList.remove(panel.roi)
            # Remove the panel from the list of panels
            self._dynPanelList.remove(panel)
            # Remove the section text control object
            self._textCtrlList.remove(sectionTextCtrl)
            
            # Destroy the panel and remove its sizer from the sectionSizer.
            panel.Destroy()
            
            # Renumber the sections so that they are continuous.
            newSectionNumber = 1
            for element in self._dynPanelList:
                element.SetSectionNumberText(self._textLabel, newSectionNumber)
                newSectionNumber = newSectionNumber + 1
            
            # Redraw the screen.
            self.Fit()
            self._parent.Redraw()
            return
        
    def GetRoiList(self):
        return self._roiList
    
    def GetTextControlList(self):
        return self._textCtrlList
        
########################################################################