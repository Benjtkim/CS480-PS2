"""
Model our creature and wrap it in one class.
First version on 09/28/2021

:author: micou(Zezhou Sun)
:version: 2021.2.1

----------------------------------

Modified by Daniel Scrivener 09/2023
"""
from __future__ import annotations

from Component import Component
from Displayable import Displayable
from Point import Point
import ColorType as Ct
from Shapes import Cube, Cylinder, Sphere, Cone
import numpy as np


class ModelLinkage(Component):
    """
    Define our linkage model
    """

    ##### TODO 2: Model the Creature
    # Build the class(es) of objects that could utilize your built geometric object/combination classes. E.g., you could define
    # three instances of the cyclinder trunk class and link them together to be the "limb" class of your creature.
    #
    # In order to simplify the process of constructing your model, the rotational origin of each Shape has been offset by -1/2 * dz,
    # where dz is the total length of the shape along its z-axis. In other words, the rotational origin lies along the smallest
    # local z-value rather than being at the translational origin, or the object's true center.
    #
    # This allows Shapes to rotate "at the joint" when chained together, much like segments of a limb.
    #
    # In general, you should construct each component such that it is longest in its local z-direction:
    # otherwise, rotations may not behave as expected.
    #
    # Please see the assignment handout for an illustration of how this behavior works.

    # Maps a name to each component of the creature, e.g. {"link1": link1}.
    # Sketch indexes this by name to select components; iterate over
    # .values() when you need every component in order.
    components: dict[str, Component]
    contextParent: object | None = None

    def __init__(self, parent: object, position: Point, shaderProg: object,
                 display_obj: Displayable | None = None) -> None:
        super().__init__(position, display_obj)
        self.contextParent = parent

        linkageLength = 0.5
        link1 = Cube(Point(0, 0, 0), shaderProg, [0.2, 0.2, linkageLength], Ct.DARKORANGE1)
        # putting link2 exactly at (0, 0, 0.95 * linkageLength) would cause z-fighting
        # across parallel top faces, so we nudge it up by a small (imperceptible) amount
        link2 = Cube(Point(0, +1e-4, 0.95 * linkageLength), shaderProg, [0.2, 0.2, linkageLength], Ct.DARKORANGE2)
        link3 = Cube(Point(0, -1e-4, 0.95 * linkageLength), shaderProg, [0.2, 0.2, linkageLength], Ct.DARKORANGE3)
        link4 = Cube(Point(0, +1e-4, 0.95 * linkageLength), shaderProg, [0.2, 0.2, linkageLength], Ct.DARKORANGE4)

        link2.setRotateExtent(link2.uAxis, -40, 40)
        link2.setRotateExtent(link2.vAxis, -40, 40)
        link3.setRotateExtent(link3.uAxis, -40, 40)
        link3.setRotateExtent(link3.vAxis, -40, 40)
        link4.setDefaultAngle(90, link4.vAxis)
        link4.setRotateExtent(link4.vAxis, -20, 60)
        # the preferred way to scale objects is actually with the "size" parameter at creation.
        # the following is just a way to ensure one canonical ordering for TODO 1
        link4.setDefaultScale((1,1,1.5)) 

        self.addChild(link1)
        link1.addChild(link2)
        link2.addChild(link3)
        link3.addChild(link4)

        self.components = {
            "link1": link1,
            "link2": link2,
            "link3": link3,
            "link4": link4
        }

        ##### TODO 4: Define creature's joint behavior
        # Requirements:
        #   1. Set a reasonable rotation range for each joint,
        #      so that creature won't intersect itself or bend in unnatural ways
        #   2. Orientation of joint rotations for the left and right parts should mirror each other.
