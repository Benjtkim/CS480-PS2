"""
Implements the Displayable class by providing import functions for .dae meshes

:author: micou(Zezhou Sun)
:version: 2021.1.1

Modified by Daniel Scrivener 07/22
"""
from __future__ import annotations

from Displayable import Displayable
from GLBuffer import VAO, VBO, EBO
import numpy as np
import ColorType
from collada import *

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


class DisplayableMesh(Displayable):
    vao: VAO | None = None
    vbo: VBO | None = None
    ebo: EBO | None = None
    shaderProg: object | None = None

    vertices: np.ndarray | None = None  # array to store vertex information
    indices: np.ndarray | None = None  # stores triangle indices to vertices

    defaultColor: np.ndarray | None = None

    def __init__(self, shaderProg: object, scale: list[float] | tuple[float, ...],
                 vertexData: np.ndarray, indexData: np.ndarray,
                 color: ColorType.ColorType = ColorType.BLUE) -> None:
        super(DisplayableMesh, self).__init__()
        assert(len(scale) == 3)

        self.defaultColor = np.array(color.getRGB())

        self.shaderProg = shaderProg
        self.shaderProg.use()

        self.vao = VAO()
        self.vbo = VBO()  # vbo can only be initiate with glProgram activated
        self.ebo = EBO()

        self.indices = indexData
        self.vertices = vertexData

        for i in range(len(self.vertices) // 11):
            i = i * 11
            self.vertices[i] = self.vertices[i] * scale[0]
            self.vertices[i + 1] = self.vertices[i + 1] * scale[1]
            self.vertices[i + 2] = self.vertices[i + 2] * scale[2]
            self.vertices[i + 5] = self.defaultColor[0]
            self.vertices[i + 6] = self.defaultColor[1]
            self.vertices[i + 7] = self.defaultColor[2]

    def draw(self) -> None:
        self.vao.bind()
        self.ebo.draw()
        self.vao.unbind()

    def initialize(self) -> None:
        """
        Remember to bind VAO before this initialization. If VAO is not bind, program might throw an error
        in systems that don't enable a default VAO after GLProgram compilation
        """
        self.vao.bind()
        self.vbo.setBuffer(self.vertices, 11)
        self.ebo.setBuffer(self.indices)

        self.vbo.setAttribPointer(self.shaderProg.getAttribLocation("aPos"),
                                  stride=11, offset=0, attribSize=3)
        self.vbo.setAttribPointer(self.shaderProg.getAttribLocation("aNormal"),
                                  stride=11, offset=3, attribSize=3) # unused
        self.vbo.setAttribPointer(self.shaderProg.getAttribLocation("aColor"),
                                  stride=11, offset=6, attribSize=3)
        self.vbo.setAttribPointer(self.shaderProg.getAttribLocation("aTexture"),
                                  stride=11, offset=9, attribSize=2) # unused


        self.vao.unbind()
