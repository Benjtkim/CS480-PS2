"""
This is the main entry of your program. Almost all things you need to implement are in this file.
The main class Sketch inherits from CanvasBase. For the parts you need to implement, they are all marked with TODO.
First version Created on 09/28/2018

:author: micou(Zezhou Sun)
:version: 2021.1.1

Modified by Daniel Scrivener 07/2022
"""
from __future__ import annotations

import math

import numpy as np
from ModelAxes import ModelAxes
from ModelLinkage import ModelLinkage

import ColorType
from Point import Point
from Component import Component
from CanvasBase import CanvasBase
from GLProgram import GLProgram
from Quaternion import Quaternion
import GLUtility

try:
    import wx
    from wx import glcanvas
except ImportError:
    raise ImportError("Required dependency wxPython not present")
try:
    # From pip package "Pillow"
    from PIL import Image
except:
    print("Need to install PIL package. Pip package name is Pillow")
    raise ImportError
try:
    import OpenGL

    try:
        import OpenGL.GL as gl
        import OpenGL.GLU as glu
    except ImportError:
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


class Sketch(CanvasBase):
    """
    Drawing methods and interrupt methods will be implemented in this class.

    Variable Instruction:
        * debug(int): Define debug level for log printing

        * 0 for stable version, minimum log is printed
        * 1 will print general logs for lines and triangles
        * 2 will print more details and do some type checking, which might be helpful in debugging


    Method Instruction:


    Here are the list of functions you need to override:
        * Interrupt_MouseL: Used to deal with mouse click interruption. Canvas will be refreshed with updated buff
        * Interrupt_MouseLeftDragging: Used to deal with mouse dragging interruption.
        * Interrupt_Keyboard: Used to deal with keyboard press interruption. Use this to add new keys or new methods

    Here are some public variables in parent class you might need:


    """
    context: glcanvas.GLContext | None = None

    debug: int = 1

    last_mouse_leftPosition: list[int] | None = None
    last_mouse_middlePosition: list[int] | None = None
    components: dict[str, Component] | None = None

    texture: object | None = None
    shaderProg: GLProgram | None = None
    glutility: GLUtility.GLUtility | None = None

    lookAtPt: list[float] | None = None
    upVector: list[float] | None = None
    backgroundColor: ColorType.ColorType | None = None
    # use these three to control camera position, mainly used in mouse dragging
    cameraDis: float | None = None
    cameraTheta: float | None = None  # theta on horizontal sphere cut, in range [0, 2pi]
    cameraPhi: float | None = None  # in range [-pi, pi], for smooth purpose

    viewMat: np.ndarray | None = None
    perspMat: np.ndarray | None = None

    # Depth precision falls off with the znear/zfar ratio, so znear is kept as
    # large as the scene allows: too small a value causes z-fighting far away.
    Z_NEAR: float = 0.1
    Z_FAR: float = 100

    select_obj_index: int = -1  # index of selected component in self.components
    select_axis_index: int = -1  # index of selected axis
    select_color: list[ColorType.ColorType] = [ColorType.ColorType(1, 0, 0), ColorType.ColorType(0, 1, 0), ColorType.ColorType(0, 0, 1)]

    # If you are having trouble rotating the camera, try increasing this parameter
    # (Windows users with trackpads may need this)
    MOUSE_ROTATE_SPEED: float = 1
    MOUSE_SCROLL_SPEED: float = 2.5

    def __init__(self, parent: wx.Frame) -> None:
        super(Sketch, self).__init__(parent)
        # prepare OpenGL context
        contextAttrib = glcanvas.GLContextAttrs()
        contextAttrib.PlatformDefaults().CoreProfile().MajorVersion(3).MinorVersion(3).EndList()
        self.context = glcanvas.GLContext(self, ctxAttrs=contextAttrib)
        # Initialize Parameters
        self.last_mouse_leftPosition = [0, 0]
        self.last_mouse_middlePosition = [0, 0]
        self.backgroundColor = ColorType.BLUEGREEN

        # add components to top level
        self.resetView()

        self.glutility = GLUtility.GLUtility()

    def resetView(self) -> None:
        self.lookAtPt = [0, 0, 0]
        self.upVector = [0, 1, 0]
        self.cameraDis = 6
        self.cameraPhi = math.pi / 6
        self.cameraTheta = math.pi / 2


    def InitGL(self) -> None:
        """
        Called once in order to initialize the OpenGL environemnt.
        You must set your model here (and not in __init__)
        due to the fact that the shader is only compiled once we reach this function.
        """
        self.shaderProg = GLProgram()
        self.shaderProg.compile()

        ##### TODO 3: Initialize your model
        # You should initialize your model here.
        # self.topLevelComponent should refer to your model, and self.components
        # should refer to your model's components: a dictionary that maps a name
        # to each component, e.g. {"link1": link1, "link2": link2}.
        # Index it by name to reach a specific component (self.components["link1"]),
        # or iterate over self.components.values() to reach every one of them.

        model = ModelLinkage(self, Point((0, 0, 0)), self.shaderProg)
        axes = ModelAxes(self, Point((-1, -1, -1)), self.shaderProg)

        self.topLevelComponent.clear()
        self.topLevelComponent.addChild(model)
        self.topLevelComponent.addChild(axes)
        self.topLevelComponent.initialize()

        self.components = model.components

        gl.glClearColor(*self.backgroundColor, 1.0)
        gl.glClearDepth(1.0)
        gl.glViewport(0, 0, self.width, self.height)

        # enable depth checking
        gl.glEnable(gl.GL_DEPTH_TEST)

        # set basic viewing matrix
        self.perspMat = self.glutility.perspective(45, self.width, self.height,
                                                   self.Z_NEAR, self.Z_FAR)
        self.shaderProg.setMat4("projection", self.perspMat)
        self.shaderProg.setMat4("view", self.glutility.view(self.getCameraPos(), self.lookAtPt, self.upVector))
        self.shaderProg.setMat4("model", np.identity(4))

    def getCameraPos(self) -> list[float]:
        ct = math.cos(self.cameraTheta)
        st = math.sin(self.cameraTheta)
        cp = math.cos(self.cameraPhi)
        sp = math.sin(self.cameraPhi)
        result = [self.lookAtPt[0] + self.cameraDis * ct * cp,
                  self.lookAtPt[1] + self.cameraDis * sp,
                  self.lookAtPt[2] + self.cameraDis * st * cp]
        return result

    def OnResize(self, event: wx.SizeEvent) -> None:
        contextAttrib = glcanvas.GLContextAttrs()
        contextAttrib.PlatformDefaults().CoreProfile().MajorVersion(3).MinorVersion(3).EndList()
        self.context = glcanvas.GLContext(self, ctxAttrs=contextAttrib)
        self.size = self.GetClientSize()
        self.size[1] = max(1, self.size[1])  # avoid divided by 0
        self.SetCurrent(self.context)

        self.init = False
        self.Refresh(eraseBackground=True)
        self.Update()

    def OnPaint(self, event: wx.Event | None = None) -> None:
        """
        This will be called at every frame
        """
        self.SetCurrent(self.context)
        if not self.init:
            # Init the OpenGL environment if not initialized
            self.InitGL()
            self.init = True
        # the draw method
        self.OnDraw()

    def OnDraw(self) -> None:
        gl.glClearColor(*self.backgroundColor, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        # These are per-frame updates to the shader. Update the viewing matrix
        self.viewMat = self.glutility.view(self.getCameraPos(), self.lookAtPt, self.upVector)
        self.shaderProg.setMat4("view", self.viewMat)

        self.topLevelComponent.update(np.identity(4))
        self.topLevelComponent.draw(self.shaderProg)

        self.SwapBuffers()

    def OnDestroy(self, event: wx.WindowDestroyEvent) -> None:
        """
        Window destroy event binding

        :param event: Window destroy event
        :return: None
        """
        # Super stops the refresh timer, so it runs before GL resources go away.
        super(Sketch, self).OnDestroy(event)
        if self.shaderProg is not None:
            del self.shaderProg

    def Interrupt_MouseMoving(self, x: int, y: int) -> None:
        ##### TODO 6 (CS680 Required, CS480 Extra Credit): Eye movement
        # Make your creature's eyes follow the cursor.
        # The eye rotation only needs to work correctly when the creature is looking toward the viewer.
        # You do NOT need to account for other camera orientations.
        # Once you've completed the task using Euler rotations,
        # add a second implementation using quaternions for additional credit! (TODO 7)

        return

    def Interrupt_Scroll(self, wheelRotation: int) -> None:
        """
        When mouse wheel rotating detected, do following things

        :param wheelRotation: mouse wheel changes, normally +120 or -120
        :return: None
        """
        if wheelRotation == 0:
            return
        wheelChange = wheelRotation / abs(wheelRotation)  # normalize wheel change
        if self.select_obj_index != -1:
            components_list = list(self.components.values())
            selected = components_list[self.select_obj_index]
            selected.rotate(wheelChange * self.MOUSE_SCROLL_SPEED,
                                selected.axisBucket[self.select_axis_index])
        self.update()

    def unprojectCanvas(self, x: int, y: int, u: float = 0.5) -> Point:
        """
        unproject a canvas point to world coordiantes. 2D -> 3D
        you need give an extra parameter u, to tell the method how far are you from znear
        u is the proportion of distance to znear / zfar-znear
        in the gluUnProject, the distribution of z is not linear when using perspective projection,
        so z=0.5 is not in the middle,
        that's why we compute out the ray and use linear interpolation and u to get the point

        :param u: u is the proportion to the znear/, in range [0, 1]
        :type u: float
        """
        result1 = self._unproject(x, y, 0.0)
        result2 = self._unproject(x, y, 1.0)
        result = Point([(1 - u) * r1 + u * r2 for r1, r2 in zip(result1, result2)])
        return result

    def _unproject(self, x: int, y: int, z: float) -> np.ndarray:
        model_matrix = np.identity(4)
        proj_matrix = self.viewMat @ self.perspMat
        viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        model_view_proj_matrix = proj_matrix @ model_matrix
        inv_model_view_proj_matrix = np.linalg.inv(model_view_proj_matrix)

        x_ndc = (x - viewport[0]) / viewport[2] * 2.0 - 1.0
        y_ndc = (y - viewport[1]) / viewport[3] * 2.0 - 1.0
        z_ndc = 2.0 * z - 1.0

        ndc_coords = np.array([x_ndc, y_ndc, z_ndc, 1.0])
        world_coords = inv_model_view_proj_matrix.T @ ndc_coords # transpose because they are row-major
        if world_coords[3] != 0:
            world_coords /= world_coords[3]
        return world_coords[:3]

    def Interrupt_MouseL(self, x: int, y: int) -> None:
        """
        When mouse click detected, store current position in last_mouse_leftPosition

        :param x: Mouse click's x coordinate
        :type x: int
        :param y: Mouse click's y coordinate
        :type y: int
        :return: None
        """
        self.last_mouse_leftPosition[0] = x
        self.last_mouse_leftPosition[1] = y

    def Interrupt_MouseMiddleDragging(self, x: int, y: int) -> None:
        """
        When mouse drag motion with middle key detected, interrupt with new mouse position

        :param x: Mouse drag new position's x coordinate
        :type x: int
        :param y: Mouse drag new position's x coordinate
        :type y: int
        :return: None
        """

        if self.new_dragging_event:
            self.last_mouse_middlePosition[0] = x
            self.last_mouse_middlePosition[1] = y
            return

        dx = x - self.last_mouse_middlePosition[0]
        dy = y - self.last_mouse_middlePosition[1]

        originalMidPt = self.unprojectCanvas(*self.last_mouse_middlePosition, 0.5)

        self.last_mouse_middlePosition[0] = x
        self.last_mouse_middlePosition[1] = y

        currentMidPt = self.unprojectCanvas(x, y, 0.5)
        changes = currentMidPt - originalMidPt
        moveSpeed = 0.185 * self.cameraDis / 6
        self.lookAtPt = [self.lookAtPt[0] - changes[0] * moveSpeed,
                         self.lookAtPt[1] - changes[1] * moveSpeed,
                         self.lookAtPt[2] - changes[2] * moveSpeed]

    def Interrupt_MouseLeftDragging(self, x: int, y: int) -> None:
        """
        When mouse drag motion detected, interrupt with new mouse position

        :param x: Mouse drag new position's x coordinate
        :type x: int
        :param y: Mouse drag new position's x coordinate
        :type y: int
        :return: None
        """

        if self.new_dragging_event:
            self.last_mouse_leftPosition[0] = x
            self.last_mouse_leftPosition[1] = y
            return

        # Change viewing angle when dragging happened
        dx = x - self.last_mouse_leftPosition[0]
        dy = y - self.last_mouse_leftPosition[1]

        # restrict phi movement range, stop cameraphi changes at pole points
        self.cameraPhi = min(math.pi / 2, max(-math.pi / 2, self.cameraPhi - dy / 50))
        self.cameraTheta += dx / 100 * (self.MOUSE_ROTATE_SPEED)

        self.cameraTheta = self.cameraTheta % (2 * math.pi)

        self.last_mouse_leftPosition[0] = x
        self.last_mouse_leftPosition[1] = y

    def update(self) -> None:
        """
        Update current canvas
        :return: None
        """
        self.topLevelComponent.update(np.identity(4))

    def Interrupt_Keyboard(self, keycode: int) -> None:
        """
        Keyboard interrupt bindings

        :param keycode: wxpython keyboard event's keycode
        :return: None
        """

        ##### TODO 5: Set up your poses and finish the user interface
        # Define keyboard events to make your creature act in different ways when keys are pressed.
        # Create five unique poses to demonstrate your creature's joint rotations.
        # HINT: self.components is indexed by name, so binding a key to a specific
        # part of your creature is just self.components["leg1"].

        components_list = list(self.components.values())
        selected = None if self.select_obj_index == -1 else components_list[self.select_obj_index]

        if keycode in [wx.WXK_RETURN]:
            # enter component editing mode
            self.select_axis_index = 0
            if len(self.components) > 0:
                # reset color of last selected component
                if selected:
                    selected.reset("color")
                # set new selected component & its color
                self.select_obj_index = (self.select_obj_index + 1) % len(components_list)
                selected = components_list[self.select_obj_index]
                selected.setCurrentColor(self.select_color[self.select_axis_index])
            self.update()
        if keycode in [wx.WXK_LEFT]:
            # Last rotation axis of this component
            if selected:
                self.select_axis_index = (self.select_axis_index - 1) % 3
                selected.setCurrentColor(self.select_color[self.select_axis_index])
                self.update()
        if keycode in [wx.WXK_RIGHT]:
            # Next rotation axis of this component
            if selected:
                self.select_axis_index = (self.select_axis_index + 1) % 3
                selected.setCurrentColor(self.select_color[self.select_axis_index])
                self.update()
        if keycode in [wx.WXK_UP]:
            # Increase rotation angle
            self.Interrupt_Scroll(1)
            self.update()
        if keycode in [wx.WXK_DOWN]:
            # Decrease rotation angle
            self.Interrupt_Scroll(-1)
            self.update()
        if keycode in [wx.WXK_ESCAPE]:
            # exit component editing mode
            if selected:
                selected.reset("color")
            self.select_obj_index = -1
            self.select_axis_index = -1
            self.update()
        if chr(keycode) in "r":
            # reset viewing angle only
            self.resetView()
        if chr(keycode) in "R":
            # reset everything
            for c in self.components.values():
                c.reset()
            self.resetView()
            self.select_obj_index = -1
            self.select_axis_index = -1
            self.update()


if __name__ == "__main__":
    print("This is the main entry! ")
    app = wx.App(False)
    # Set FULL_REPAINT_ON_RESIZE will repaint everything when scaling the frame, here is the style setting for it: wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE
    # Resize disabled in this one
    frame = wx.Frame(None, size=(500, 500), title="Test",
                     style=wx.DEFAULT_FRAME_STYLE | wx.FULL_REPAINT_ON_RESIZE)  # Disable Resize: ^ wx.RESIZE_BORDER
    canvas = Sketch(frame)

    frame.Show()
    app.MainLoop()
