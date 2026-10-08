'''
Set up our display pipeline. WxPython is used to solve system compatibility problems. It is mainly focusing on
creating a display window with a canvas. We will let OpenGL draw on it. All these things have been wrapped up,
and the main class should inherit this class. First version Created on 09/27/2018

:author: micou(Zezhou Sun)
:version: 2024.11.11
'''
from __future__ import annotations

from Component import Component

try:
    import wx
    from wx import glcanvas
except ImportError:
    raise ImportError("Required dependency wxPython not present")

try:
    import OpenGL

    try:
        import OpenGL.GL as gl
        import OpenGL.GLU as glu
    except ImportError:
        print('Patching for Big Sur')
        from ctypes import util

        orig_util_find_library = util.find_library


        def new_util_find_library(name):
            res = orig_util_find_library(name)
            if res:
                return res
            return '/System/Library/Frameworks/' + name + '.framework/' + name


        util.find_library = new_util_find_library
        import OpenGL.GL as gl
        import OpenGL.GLU as glu
except ImportError:
    raise ImportError("Required dependency PyOpenGL not present")

import math
import random
import numpy as np

from Point import Point
from ColorType import ColorType
from Quaternion import Quaternion

############################### System Checking ################################

WX_MINIMUM_REQUIRED = "3.0.0"
OPENGL_MINIMUM_REQUIRED = "3.1.0"

# Package version checking
if wx.__version__ < WX_MINIMUM_REQUIRED:
    # Not fully tested yet. But version 3.0.0+ should work based on changelog
    raise ImportError("wxPython minimum required " + WX_MINIMUM_REQUIRED)
if OpenGL.__version__ < OPENGL_MINIMUM_REQUIRED:
    # Not fully tested yet.
    raise ImportError("PyOpenGL minimum required " + OPENGL_MINIMUM_REQUIRED)


############################ End of System Checking #############################


class CanvasBase(glcanvas.GLCanvas):
    """
    All functions work on interruptions and events start with capital letter
    functions for public use start with lower case letter
    functions for local use (accessible from outside) start with _(single underscore)
    functions for private use (not accessible outside) start with __ (double underscore)
    """
    size: tuple[int, int] | None = None
    context: glcanvas.GLContext | None = None
    stateChanged: bool = False
    topLevelComponent: Component | None = None
    init: bool = False
    viewing_quaternion: Quaternion | None = None
    dragging_event: bool = False
    new_dragging_event: bool = False

    fps: int = 120  # frame per second, -1 to disable auto refresh

    def __init__(self, parent: wx.Frame) -> None:
        """
        Inherit from WxPython GLCanvas class. Bind implemented methods to window events.

        :param parent: The WxPython frame you want to inherit from
        :type parent: wx.Frame
        """
        # Initialize parent class
        attrib = glcanvas.GLAttributes()
        # Defaults() is required. Otherwise MacOS will get blank screen,
        # For the depth size, macOS support <= 24, Windows support 16-32, Linux requires >= 24
        attrib.Defaults().Depth(24).EndList()
        super(CanvasBase, self).__init__(parent, attrib)
        # Initialize public variables
        self.stateChanged = False
        self.init = False
        self.size = (0, 0)
        self.topLevelComponent = Component(Point((0, 0, 0)))
        self.viewing_quaternion = Quaternion()
        self.timer = wx.Timer(self, 1)  # TIMER_ID set to 1
        # Bind event to functions
        # self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseLeft)
        self.Bind(wx.EVT_RIGHT_UP, self.OnMouseRight)
        self.Bind(wx.EVT_CHAR, self.OnKeyDown)
        self.Bind(wx.EVT_SIZE, self.OnResize)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnScroll)
        # refresh canvas with constant frame rate
        self.Bind(wx.EVT_TIMER, self.OnPaint)

        if self.fps > 0:
            self.timer.Start(int(1000 / self.fps), oneShot=wx.TIMER_CONTINUOUS)

    # Indexed rather than self.size.width/.height: size starts out as a plain
    # tuple and only becomes a wx.Size once the canvas has been laid out.
    @property
    def width(self) -> int:
        return self.size[0]

    @property
    def height(self) -> int:
        return self.size[1]

    def OnScroll(self, event: wx.MouseEvent) -> None:
        """
        Bind method to mouse wheel rotation

        :param event: mouse event
        :return: None
        """
        self.Interrupt_Scroll(event.GetWheelRotation())
        self.Refresh(True)

    def OnTimer(self, event: wx.TimerEvent) -> None:
        self.OnPaint(event)

    def OnResize(self, event: wx.SizeEvent) -> None:
        """
        Called when resize of window happen, this will run before OnPaint in first running

        :param event: Canvas resize event
        :return: None
        """
        self.context = glcanvas.GLContext(self)
        self.size = self.GetClientSize()
        self.size[1] = max(1, self.size[1])  # avoid divided by 0
        self.SetCurrent(self.context)

        # Update screen and display
        self.init = False
        self.Refresh(eraseBackground=True)
        self.Update()

    def OnIdle(self, event: wx.IdleEvent) -> None:
        pass

    def OnPaint(self, event: wx.Event | None = None) -> None:
        """
        Bind to wxPython paint event, this will be called in every frame drawing.
        This method will also control the environment initialization and model update
        with control flag self.init and self.stateChanged

        :param event: wxpython paint event
        :return: None
        """
        self.SetCurrent(self.context)
        if not self.init:
            # Init the OpenGL environment if not initialized
            self.InitGL()
            self.init = True
        if self.stateChanged:
            # If there is any changes in model, we need to update the model from the very beginning
            self.ModelChanged()
            self.stateChanged = False
        # the draw method
        self.OnDraw()

    def OnDraw(self) -> None:
        """
        Wrap OpenGL commands, to draw on canvas
        :return: None
        """
        self.SetCurrent(self.context)
        # clear color buffer and depth buffer
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # Swap Buffer to display canvas
        self.SwapBuffers()

    def ModelChanged(self) -> None:
        """
        Reinitialize model start from the top level if model value changed
        """
        self.topLevelComponent.initialize()
        self.topLevelComponent.update()

    def InitGL(self) -> None:
        """
        Initialize the OpenGL environment. Called once from OnPaint before the
        first frame is drawn: compile shaders, build the model, and set up any
        GL state the scene needs.

        :return: None
        """
        pass  # Fully Override please

    def OnDestroy(self, event: wx.WindowDestroyEvent) -> None:
        """
        Window destroy event binding

        :param event: Window destroy event
        :return: None
        """
        # Stop first: a tick landing mid-teardown would draw to a dead canvas.
        self.timer.Stop()
        print("Destroy Window")

    def OnMouseMotion(self, event: wx.MouseEvent) -> None:
        """
        Mouse motion interrupt bindings

        :param event: mouse motion event
        :return: None
        """
        if event.LeftIsDown():
            # If this is a dragging event with left button down
            self.new_dragging_event = not self.dragging_event
            self.dragging_event = True
            self.Interrupt_MouseLeftDragging(event.GetX(), self.height - event.GetY())
            self.Refresh(True)
        elif event.RightIsDown():
            # If this is a dragging event with right button down
            self.new_dragging_event = not self.dragging_event
            self.dragging_event = True
            self.Interrupt_MouseMiddleDragging(event.GetX(), self.height - event.GetY()) # use middle method
            self.Refresh(True)
        elif event.MiddleIsDown():
            self.new_dragging_event = not self.dragging_event
            self.dragging_event = True
            self.Interrupt_MouseMiddleDragging(event.GetX(), self.height - event.GetY())
            self.Refresh(True)
        else:
            # Normal Mouse Moving
            self.dragging_event = False
            self.Interrupt_MouseMoving(event.GetX(), self.height - event.GetY())
            self.Refresh(True)

    # Definition for interface
    def OnMouseLeft(self, event: wx.MouseEvent) -> None:
        """
        Mouse left click event binding

        :param event: left mouse click event
        :return: None
        """
        x = event.GetX()
        y = event.GetY()
        self.Interrupt_MouseL(x, self.height - y)
        self.Refresh(True)

    def OnMouseRight(self, event: wx.MouseEvent) -> None:
        """
        Mouse right click event binding

        :param event: right mouse click event
        :return: None
        """
        x = event.GetX()
        y = event.GetY()
        self.Interrupt_MouseR(x, self.height - y)
        self.Refresh(True)

    def OnKeyDown(self, event: wx.KeyEvent) -> None:
        """
        keyboard press event binding

        :param event: keyboard press event
        :return: None
        """
        keycode = event.GetKeyCode()
        self.Interrupt_Keyboard(keycode)
        self.Refresh(True)

    def modelUpdate(self) -> None:
        """
        Call this method once model changed, update model on canvas

        :return: None
        """
        self.stateChanged = True
        self.Refresh(True)

    def Interrupt_Scroll(self, wheelRotation: int) -> None:
        pass

    def Interrupt_MouseL(self, x: int, y: int) -> None:
        pass  # Fully Override please

    def Interrupt_MouseR(self, x: int, y: int) -> None:
        pass  # Fully Override please

    def Interrupt_Keyboard(self, keycode: int) -> None:
        pass  # Fully Override please

    def Interrupt_MouseLeftDragging(self, x: int, y: int) -> None:
        pass  # Fully Override please

    def Interrupt_MouseRightDragging(self, x: int, y: int) -> None:
        pass  # Fully Override please

    def Interrupt_MouseMiddleDragging(self, x: int, y: int) -> None:
        pass  # Fully Override please

    def Interrupt_MouseMoving(self, x: int, y: int) -> None:
        pass  # Fully Override please


if __name__ == "__main__":
    app = wx.App(False)
    # Set FULL_REPAINT_ON_RESIZE will repaint everything when scaling the frame, here is the style setting for it: wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE
    # Resize disabled in this one
    frame = wx.Frame(None, size=(500, 500), title="Test", style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE)
    canvas = CanvasBase(frame)

    frame.Show()
    app.MainLoop()
