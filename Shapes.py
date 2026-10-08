"""
Implements four geometric primitives (Sphere, Cube, Cone, Cylinder) using the DisplayableMesh class

Modified by Daniel Scrivener 09/2023
"""
from __future__ import annotations

from collada import *
from DisplayableMesh import DisplayableMesh
from Component import Component
import GLUtility
import ColorType
import numpy as np


def getVertexData(filename: str) -> tuple[np.ndarray, np.ndarray]:

    colladaData = Collada(filename)

    # generate vertices from model data
    # also generate indices

    geo = colladaData.geometries[0]
    tridata = geo.primitives[0]
    trilist = list(tridata)

    # construct vertex list
    vertices = np.array([])

    for vert in tridata.vertex:
        vert = np.concatenate((vert, [0.,0.,0.]), axis=0) # empty normals
        vert = np.concatenate((vert, [0.,0.,0.]), axis=0) # color
        vert = np.concatenate((vert, [0.,0.]), axis=0) # empty UV
        vertices = np.append(vertices, vert)

    # construct indices
    indices = np.array([])

    for tri in trilist:
        indices = np.append(indices, tri.indices)

    return (vertices, indices)

class Shape(Component):
    vertexData: np.ndarray | None = None
    indexData: np.ndarray | None = None
    mesh: DisplayableMesh | None = None

    def __init__(self, position: object, shaderProg: object,
                 size: list[float] | tuple[float, ...],
                 vertexData: np.ndarray, indexData: np.ndarray,
                 color: ColorType.ColorType = ColorType.YELLOW) -> None:
        self.mesh = DisplayableMesh(shaderProg, size, vertexData, indexData, color)
        super(Shape, self).__init__(position, self.mesh)

class Cone(Shape):

    pathname = "assets/cone0.dae"
    pathnameLP = "assets/coneLP.dae"
    data = getVertexData(pathname)
    dataLP = getVertexData(pathnameLP)
    vertices = data[0]
    verticesLP = dataLP[0]
    indices = data[1]
    indicesLP = dataLP[1]

    def __init__(self, position: object, shaderProg: object,
                 size: list[float] | tuple[float, ...],
                 color: ColorType.ColorType = ColorType.YELLOW,
                 limb: bool = True, lowPoly: bool = False) -> None:
        if lowPoly:
            super(Cone, self).__init__(position, shaderProg, size, self.verticesLP.copy(), self.indicesLP.copy(), color)
        else:
            super(Cone, self).__init__(position, shaderProg, size, self.vertices.copy(), self.indices.copy(), color)

        # translate object by -z extent of the new component so that rotations occur @ the joint
        # rather than around the object's true center
        glutility = GLUtility.GLUtility()
        if limb:
            tIn = glutility.translate(0, 0, size[2], False)
            tOut = glutility.translate(0, 0, -size[2], False)
        else:
            tIn = np.identity(4)
            tOut = np.identity(4)
        self.setPreRotation(tIn)
        self.setPostRotation(tOut)

class Cube(Shape):

    pathname = "assets/cube0.dae"
    data = getVertexData(pathname)
    vertices = data[0]
    indices = data[1]

    def __init__(self, position: object, shaderProg: object,
                 size: list[float] | tuple[float, ...],
                 color: ColorType.ColorType = ColorType.RED,
                 limb: bool = True) -> None:
        super(Cube, self).__init__(position, shaderProg, size, self.vertices.copy(), self.indices.copy(), color)
        # translate object by -z extent of the new component so that rotations occur @ the joint
        # rather than around the object's true center
        glutility = GLUtility.GLUtility()
        if limb:
            tIn = glutility.translate(0, 0, size[2] / 2, False)
            tOut = glutility.translate(0, 0, -size[2] / 2, False)
        else:
            tIn = np.identity(4)
            tOut = np.identity(4)
        self.setPreRotation(tIn)
        self.setPostRotation(tOut)

class Cylinder(Shape):

    pathname = "assets/cylinder0.dae"
    pathnameLP = "assets/cylinderLP.dae"
    data = getVertexData(pathname)
    dataLP = getVertexData(pathnameLP)
    vertices = data[0]
    verticesLP = dataLP[0]
    indices = data[1]
    indicesLP = dataLP[1]

    def __init__(self, position: object, shaderProg: object,
                 size: list[float] | tuple[float, ...],
                 color: ColorType.ColorType = ColorType.GREEN,
                 limb: bool = True, lowPoly: bool = False) -> None:
        if lowPoly:
            super(Cylinder, self).__init__(position, shaderProg, size, self.verticesLP.copy(), self.indicesLP.copy(), color)
        else:
            super(Cylinder, self).__init__(position, shaderProg, size, self.vertices.copy(), self.indices.copy(), color)
        # translate object by -z extent of the new component so that rotations occur @ the joint
        # rather than around the object's true center
        glutility = GLUtility.GLUtility()
        if limb:
            tIn = glutility.translate(0, 0, size[2], False)
            tOut = glutility.translate(0, 0, -size[2], False)
        else:
            tIn = np.identity(4)
            tOut = np.identity(4)
        self.setPreRotation(tIn)
        self.setPostRotation(tOut)

class Sphere(Shape):

    pathname = "assets/sphere0.dae"
    pathnameLP = "assets/sphereLP.dae"
    data = getVertexData(pathname)
    dataLP = getVertexData(pathnameLP)
    vertices = data[0]
    verticesLP = dataLP[0]
    indices = data[1]
    indicesLP = dataLP[1]

    def __init__(self, position: object, shaderProg: object,
                 size: list[float] | tuple[float, ...],
                 color: ColorType.ColorType = ColorType.BLUE,
                 limb: bool = True, lowPoly: bool = False) -> None:
        if lowPoly:
            super(Sphere, self).__init__(position, shaderProg, size, self.verticesLP.copy(), self.indicesLP.copy(), color)
        else:
            super(Sphere, self).__init__(position, shaderProg, size, self.vertices.copy(), self.indices.copy(), color)
        # translate object by -z extent of the new component so that rotations occur @ the joint
        # rather than around the object's true center
        glutility = GLUtility.GLUtility()
        if limb:
            tIn = glutility.translate(0, 0, size[2], False)
            tOut = glutility.translate(0, 0, -size[2], False)
        else:
            tIn = np.identity(4)
            tOut = np.identity(4)
        self.setPreRotation(tIn)
        self.setPostRotation(tOut)
