'''
Created on Sep 12, 2014

@author: roehrig
'''
from pylab import *
from matplotlib.widgets import RectangleSelector
from matplotlib.patches import Rectangle

class ROI(object):
    '''
    This class is used to create a region of interest on a plot.
    '''

    def __init__(self, ax, fig, canvas):

        self.ax = ax
        self.fig = fig
        self.canvas = canvas
        self.grab_line = None

        self.SetEventHandlers()

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

    def motion_notify_callback(self, event):
        return

    def button_press_callback(self, event):
        return

    def button_release_callback(self, event):
        return

    def object_picked_callback(self, event):
        return

    def RemoveLines(self):
        return

    def AddLines(self):
        return

    def SetNewAxes(self, ax):
        self.ax = ax
        return

class RectROI(ROI):

    def __init__(self, ax, fig, canvas, red=0.5, green=0.5, blue=0.5):

        ROI.__init__(self, ax, fig, canvas)

        self.x0 = 0
        self.y0 = 0
        self.x1 = 0
        self.y1 = 0
        self.line_color = (red, green, blue)
        self.rect = None
        return

    def button_press_callback(self, event):

        if event.inaxes:
            if event.button == 1:  # If you press the left mouse button
                if self.rect is None:
                    self.x0 = event.xdata
                    self.y0 = event.ydata
        return

    def button_release_callback(self, event):
        # When the user releases the mouse button, make sure the ROI line
        # no longer moves with the mouse.
        if event.button == 1:

            if self.rect is None:
                self.x1 = event.xdata
                self.y1 = event.ydata
                width = self.x1 - self.x0
                height = self.y1 - self.y0
                self.rect = Rectangle((self.x0, self.y0), width, height, color=self.line_color, fill=False, picker=True,
                                      visible=True, figure=self.fig)

                ax = event.inaxes
                ax.add_patch(self.rect)
                self.fig.canvas.draw()

        self.grab_line = None

        return

    def motion_notify_callback(self, event):
        '''
        This is called when the user moves the mouse over the plot.
        It will change the size or position of the ROI.
        '''

        if event.inaxes:
            if (event.button == 1) and (not (self.grab_line is None)):
                # Change the position of the bottom right corner of the ROI
                # as the mouse is dragged across the image.
                self.x1 = event.xdata
                self.y1 = event.ydata
                width = self.x1 - self.x0
                height = self.y1 - self.y0

                self.rect.set_width(width)
                self.rect.set_height(height)

                self.fig.canvas.draw()

            if (event.button == 3) and (not (self.grab_line is None)):
                # Change the position of the top left corner of the ROI
                # as the mouse is dragged across the image.
                self.x0 = event.xdata
                self.y0 = event.ydata

                self.rect.set_xy((self.x0, self.y0))

                self.fig.canvas.draw()

        return

    def object_picked_callback(self, event):
        # Set the line grabbed to the object that is clicked on.
        contains, attrd = self.rect.contains(event.mouseevent)
        if contains:
            self.grab_line = event.artist
        return

    def AddLines(self):
        if self.rect is not None:
            self.ax.add_patch(self.rect)
            self.ax.figure.canvas.draw()

        return

    def RemoveLines(self):
        try:
            self.rect.remove()
            self.fig.canvas.draw()
        except AttributeError:
            return
        return

    def GetDimensions(self):
        dim_list = []
        dim_list.append(self.x0)
        dim_list.append(self.y0)
        dim_list.append(self.x1)
        dim_list.append(self.y1)

        return dim_list

    def EditROI(self):

        if self.x0 == 0 or self.y0 == 0 or self.x1 == 0 or self.y1 == 0:
            return

        width = self.x0 - self.x1
        height = self.y0 - self.y1

        if self.rect is None:
            self.rect = Rectangle((self.x1, self.y1), width, height, color=self.line_color, fill=False, picker=True,
                                      visible=True, figure=self.fig, axes=self.fig.gca())
            ax = self.fig.gca()
            ax.add_patch(self.rect)
        else:
            self.rect.set_height(height)
            self.rect.set_width(width)
            self.rect.set_xy((self.x1, self.y1))

        self.fig.canvas.draw()

        return

    def SetXY(self, x, y, corner=1):

        if corner == 1:
            self.x0 = x
            self.y0 = y

        else:
            self.x1 = x
            self.y1 = y

        return
########################################################################
class LineROI(ROI):
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

        ROI.__init__(self, ax, fig, canvas)

        self.line = None
        self.line2 = None
        self.line_position = 0.0
        self.line2_position = 0.0
        self.line_xdata = None
        self.line2_xdata = None
        self.line_color = (red, green, blue)
        
        self.grab_line = None

        self.fig.canvas.draw()

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
        self.line_xdata = None
        self.line2_xdata = None

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
            if (event.button == 1) and (not (self.grab_line is None)):
                self.grab_line.set_xdata([x, x])
                self.fig.canvas.draw()
                xdata = self.line.get_xdata(False)
                xdata2 = self.line2.get_xdata(False)
                self.line_position = xdata[0]
                self.line2_position = xdata2[0]
                self.line_xdata = xdata
                self.line2_xdata = xdata2

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

                if self.line is None:  # if there is no line, create a line
                    self.line = Line2D([x,  x], ax.get_ybound())
                    self.line.set_picker(True)
                    self.line.set_color(self.line_color)
                    ax.add_line(self.line)
                    xdata = self.line.get_xdata(False)
                    self.line_position = xdata[0]
                    self.line_xdata = xdata
                    self.fig.canvas.draw()
                    
                elif self.line2 is None:  # if there is one line, create a second to define the ROI
                    self.line2 = Line2D([x,  x], ax.get_ybound())
                    self.line2.set_picker(True)
                    self.line2.set_color(self.line_color)
                    ax.add_line(self.line2)
                    xdata2 = self.line2.get_xdata(False)
                    self.line2_position = xdata2[0]
                    self.line2_xdata = xdata2
                    self.fig.canvas.draw()

                print (self.line_position, self.line2_position)
                    
                        
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
        try:
            self.line.remove()
            self.line2.remove()
            self.fig.canvas.draw()
        except AttributeError:
            return
        return

    def AddLines(self):
        '''
        Adds the ROI lines to the plots axes object
        '''

        if (not(self.line == None)):
            self.line.set_xdata(self.line_xdata)
            self.ax.add_line(self.line)
        if (not(self.line2 == None)):
            self.line2.set_xdata(self.line2_xdata)
            self.ax.add_line(self.line2)
        self.fig.canvas.draw()

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

    def SetNewLineData(self):
        if not (self.line == None):
            self.line_xdata = self.line.get_xdata(False)
        if not (self.line2 == None):
            self.line2_xdata = self.line2.get_xdata(False)

        return