'''
Created on Aug 19, 2014

@author: roehrig
'''

import wx
from wx.lib.mixins.listctrl import CheckListCtrlMixin

class CheckListControl(wx.ListCtrl, CheckListCtrlMixin):
    '''
    classdocs
    '''

    def __init__(self, parent, size):
        '''
        Constructor
        '''
        
        wx.ListCtrl.__init__(self, parent, -1, size=size, style=wx.LC_REPORT)
        CheckListCtrlMixin.__init__(self)
        
        self._numItemsChecked = 0

        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)

        return

    def OnItemActivated(self, evt):
        self.ToggleItem(evt.m_itemIndex)
        
        return


    # This is called by the base class when an item is checked/unchecked
    def OnCheckItem(self, index, flag):
        
        data = self.GetItemText(index)
        if flag:
            self._numItemsChecked = self._numItemsChecked + 1
        else:
            self._numItemsChecked = self._numItemsChecked - 1
        #print 'item "%s", at index %d was %s\n' % (data, index, what)
        
        return
    
    def GetItemsCheckedCount(self):
        return self._numItemsChecked