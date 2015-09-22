'''
Created on Sep 12, 2014

@author: roehrig
'''
from pylab import *

class ROI:
    '''
    This class is used to create a region of interest on a 2D plot.
    '''
    
    def __init__(self, ax, fig, canvas, red=0.5, green=0.5, blue=0.5):
        '''
        Create the ROI object
        
        ax - The matplotlib 2D axes object which is plotted
        fig - The matplotlib figure object that holds the canvas.
        canvas - The matplotlib canvas object used to draw the plot
        red - The value of the red component of the color, between 0 and 1
        green - The value of the green component of the color, between 0 and 1
        blue - The value of the blue component of the color, between 0 and 1
        
        '''

        self.line = None
        self.line2 = None
        self.line_position = 0.0
        self.line2_position = 0.0
        self.line_color = (red, green, blue)
        
        self.canvas = canvas
        
        self.grab_line = None
        
        self.fig =  fig
        self.fig.canvas.draw()
        
        self.SetEventHandlers()
        
        self.ax = ax
        
        return
    
    def SetEventHandlers(self):
        '''
        Set up the event handlers for the matplotlib canvas
        '''
        
        self.canvas.mpl_connect('motion_notify_event', self.motion_notify_callback)
        self.canvas.mpl_connect('button_press_event', self.button_press_callback)
        self.canvas.mpl_connect('button_release_event', self.button_release_callback)
        self.canvas.mpl_connect('pick_event', self.object_picked_callback)
        
        return
    
    def ClearLines(self):
        '''
        Clear the lines on the plot and reset the ROI values to zero.
        '''
        
        self.line = None
        self.line2 = None
        self.grab_line = None
        self.line_position = 0.0
        self.line2_position = 0.0
        return
    
    def GetLinePositions(self):
        '''
        Return the position of the start and end of the ROI
        '''
        
        return self.line_position, self.line2_position
    
    def motion_notify_callback(self, event):
        '''
        This is called when the user moves the mouse over the plot.
        It will move the position of one of the ROI lines.
        '''
        
        if event.inaxes: 
            x = event.xdata
            # Change the position of the line that the user has clicked on.
            # Update the x position values for each line.
            if (event.button == 1) and (not (self.grab_line == None)):
                self.grab_line.set_xdata([x,x])
                self.fig.canvas.draw()
                self.line_position = self.line.get_xdata(False)[0]
                self.line2_position = self.line2.get_xdata(False)[0]

        return
    
    def button_press_callback(self, event):
        '''
        This is called when the user clicks a mouse button over the canvas.
        If necessary, it will create a new line on the canvas to represent one edge
        of the ROI.
        '''

        if event.inaxes:
            x= event.xdata
            ax = event.inaxes
            if event.button == 1:  # If you press the left mouse button

                if self.line == None: # if there is no line, create a line
                    self.line = Line2D([x,  x], ax.get_ybound())
                    self.line.set_picker(True)
                    self.line.set_color(self.line_color)
                    ax.add_line(self.line)
                    self.line_position = self.line.get_xdata(False)[0]
                    self.fig.canvas.draw()
                    
                elif self.line2 == None: # if there is one line, create a second to define the ROI
                    self.line2 = Line2D([x,  x], ax.get_ybound())
                    self.line2.set_picker(True)
                    self.line2.set_color(self.line_color)
                    ax.add_line(self.line2)
                    self.line2_position = self.line2.get_xdata(False)[0]
                    self.fig.canvas.draw()
                    
                        
        return
    
    def button_release_callback(self, event):
        # When the user releases the mouse button, make sure the ROI line
        # no longer moves with the mouse.
        if event.button == 1:
            self.grab_line = None
            
        return
    
    def object_picked_callback(self, event):
        # Set the line grabbed to the object that is clicked on.
        self.grab_line = event.artist
        return
        
    def RemoveLines(self):
        self.line.remove()
        self.line2.remove()
        self.fig.canvas.draw()
        return

    def AddLines(self):
        '''
        Adds the ROI lines to the plots axes object
        '''
        
        if (not(self.line == None)):
            self.ax.add_line(self.line)
        if (not(self.line2 == None)):
            self.ax.add_line(self.line2)
        
        return
    
    def SetNewAxes(self, ax):
        self.ax = ax
        return
    
    def GetStart(self):
        if (self.line_position <= self.line2_position):
            return self.line_position
        else:
            return self.line2_position
        
    def GetEnd(self):
        if (self.line_position > self.line2_position):
            return self.line_position
        else:
            return self.line2_position
