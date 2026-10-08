'''
Set up the pyopengl rendering program, including vertex shader and fragment shader.

:author: micou(Zezhou Sun), Daniel Scrivener
:version: 2026.08.31
'''
from __future__ import annotations

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
import numpy as np
import math

def perspectiveMatrix(angleOfView: float, near: float, far: float) -> np.ndarray:
    result = np.identity(4)
    angleOfView = min(179, max(0, angleOfView))
    scale = 1 / math.tan(0.5 * angleOfView * math.pi / 180)
    fsn = far - near
    result[0, 0] = scale
    result[1, 1] = scale
    result[2, 2] = - far / fsn
    result[3, 2] = - far * near / fsn
    result[2, 3] = -1
    result[3, 3] = 0


class GLProgram:
    program: int = None

    vertexShaderSource: str | None = None
    fragmentShaderSource: str | None = None

    vs: int | None = None  # vertex shader
    fs: int | None = None  # Fragment shader

    ready: bool = False  # a control flag which reflects if this GLprogram is ready
    debug: int = 0

    # if you change either of these, make sure that you also update the shader!
    MAX_LIGHT_NUM: int = 20
    MAX_MATERIAL_NUM: int = 20

    def __init__(self) -> None:
        self.program = gl.glCreateProgram()

        self.ready = False

        with open("./VertexShader.glsl", "r") as fv:
            self.vertexShaderSource = fv.read()

        with open("./FragmentShader.glsl", "r") as ff:
            self.fragmentShaderSource = ff.read()

    def __del__(self) -> None:
        try:
            gl.glDeleteProgram(self.program)
        except Exception as e:
            pass

    @staticmethod
    def load_shader(src: str, shader_type: int) -> int:
        shader = gl.glCreateShader(shader_type)
        gl.glShaderSource(shader, src)
        gl.glCompileShader(shader)
        error = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
        if error != gl.GL_TRUE:
            info = gl.glGetShaderInfoLog(shader)
            gl.glDeleteShader(shader)
            raise Exception(info)
        return shader

    def set_vss(self, vss: str) -> None:
        if not isinstance(vss, str):
            raise TypeError("Vertex shader source code must be a string")
        self.vertexShaderSource = vss

    def set_fss(self, fss: str) -> None:
        if not isinstance(fss, str):
            raise TypeError("Fragment shader source code must be a string")
        self.fragmentShaderSource = fss

    def getAttribLocation(self, name: str) -> int:
        attribLoc = gl.glGetAttribLocation(self.program, name)
        if attribLoc == -1 and self.debug > 1:
            print(f"Warning: Attrib {name} not found. Might have been optimized off")
        return attribLoc

    def getUniformLocation(self, name: str) -> int:
        uniformLoc = gl.glGetUniformLocation(self.program, name)
        if uniformLoc == -1 and self.debug > 1:
            print(f"Warning: Uniform {name} not found. Might have been optimized off")
        return uniformLoc

    def compile(self, vs_src: str | None = None, fs_src: str | None = None) -> None:
        if vs_src:
            self.set_vss(vs_src)
        else:
            vs_src = self.vertexShaderSource

        if fs_src:
            self.set_fss(fs_src)
        else:
            fs_src = self.fragmentShaderSource

        if not (vs_src and fs_src):
            raise Exception("shader source code missing")

        vs = self.load_shader(vs_src, gl.GL_VERTEX_SHADER)
        if not vs:
            return
        fs = self.load_shader(fs_src, gl.GL_FRAGMENT_SHADER)
        if not fs:
            return
        gl.glAttachShader(self.program, vs)
        gl.glAttachShader(self.program, fs)
        gl.glLinkProgram(self.program)
        error = gl.glGetProgramiv(self.program, gl.GL_LINK_STATUS)
        if error != gl.GL_TRUE:
            info = gl.glGetShaderInfoLog(self.program)
            raise Exception(info)

        self.ready = True

    def setFragmentShaderRouting(self, routing: str = "lighting") -> None:
        """
        There will be different rendering routing,
        "lighting"/"illumination": DEFAULT routing. Rendering the scene with lights
        "vertex": use VBO stored vertex color to render object
        "pure": render object with pre-defined color
        "normal": render with vertex's normal
        "bump": normal mapping
        "artist": artist rendering
        "custom": some customized rendering
        "texture": this must use previous routing, if set to true, then mix color with texture
        """
        renderingFlag = 0
        if isinstance(routing, str):
            routing = routing.lower()
            if ("lighting" in routing) or ("illumination" in routing):
                renderingFlag = renderingFlag | 0x1
            if "vertex" in routing:
                renderingFlag = renderingFlag | (0x1 << 1)
            if "pure" in routing:
                renderingFlag = renderingFlag | (0x1 << 2)
            if "normal" in routing:
                renderingFlag = renderingFlag | (0x1 << 3)
            if "bump" in routing:
                renderingFlag = renderingFlag | (0x1 << 4)
            if "artist" in routing:
                renderingFlag = renderingFlag | (0x1 << 5)
            if "custom" in routing:
                renderingFlag = renderingFlag | (0x1 << 6)
            if "texture" in routing:
                renderingFlag = renderingFlag | (0x1 << 8)

        self.use()
        self.setInt("renderingFlag", renderingFlag)

    def use(self) -> None:
        """
        This is required before the uniforms set up.
        """
        if not self.ready:
            raise Exception("GLProgram must compile before use it")
        gl.glUseProgram(self.program)

    def setLight(self, lightIndex: int, light: object) -> None:
        from Light import Light as LightClass
        if not isinstance(light, LightClass):
            raise TypeError("light type must be Light")

        self.setVec3(f"""light[{lightIndex}].position""", light.position)
        self.setVec4(f"""light[{lightIndex}].color""", light.color)

        self.setBool(f"""light[{lightIndex}].infiniteOn""", light.infiniteOn)
        self.setVec3(f"""light[{lightIndex}].infiniteDirection""", light.infiniteDirection)

        self.setBool(f"""light[{lightIndex}].spotOn""", light.spotOn)
        self.setVec3(f"""light[{lightIndex}].spotDirection""", light.spotDirection)
        self.setVec3(f"""light[{lightIndex}].spotRadialFactor""", light.spotRadialFactor)
        self.setFloat(f"""light[{lightIndex}].spotAngleLimit""", light.spotAngleLimit)

    def clearAllLights(self) -> None:
        from Light import Light as LightClass
        light = LightClass()
        for i in range(self.MAX_LIGHT_NUM):
            self.setLight(i, light)

    # some help methods to set uniform in program
    def setMat4(self, name: str, mat: np.ndarray) -> None:
        self.use()
        if mat.shape != (4, 4):
            raise Exception("Matrix must have 4x4 shape")
        gl.glUniformMatrix4fv(self.getUniformLocation(name), 1, gl.GL_FALSE, mat.flatten("C"))

    def setMat3(self, name: str, mat: np.ndarray) -> None:
        self.use()
        if mat.shape != (3, 3):
            raise Exception("Matrix must have 3x3 shape")
        gl.glUniformMatrix3fv(self.getUniformLocation(name), 1, gl.GL_FALSE, mat.flatten("C"))

    def setMat2(self, name: str, mat: np.ndarray) -> None:
        self.use()
        if mat.shape != (2, 2):
            raise Exception("Matrix must have 2x2 shape")
        gl.glUniformMatrix2fv(self.getUniformLocation(name), 1, gl.GL_FALSE, mat.flatten("C"))

    def setVec4(self, name: str, vec: np.ndarray) -> None:
        self.use()
        if vec.size != 4:
            raise Exception("Vector must have size 4")
        gl.glUniform4fv(self.getUniformLocation(name), 1, vec)

    def setVec3(self, name: str, vec: np.ndarray) -> None:
        self.use()
        if vec.size != 3:
            raise Exception("Vector must have size 3")
        gl.glUniform3fv(self.getUniformLocation(name), 1, vec)

    def setVec2(self, name: str, vec: np.ndarray) -> None:
        self.use()
        if vec.size != 2:
            raise Exception("Vector must have size 2")
        gl.glUniform2fv(self.getUniformLocation(name), 1, vec)

    def setBool(self, name: str, value: bool | int) -> None:
        self.use()
        if value not in (0, 1):
            raise Exception("bool only accept True/False/0/1")
        gl.glUniform1i(self.getUniformLocation(name), int(value))

    def setInt(self, name: str, value: int) -> None:
        self.use()
        if value != int(value):
            raise Exception("set int only accept integer")
        gl.glUniform1i(self.getUniformLocation(name), int(value))

    def setFloat(self, name: str, value: float) -> None:
        self.use()
        gl.glUniform1f(self.getUniformLocation(name), float(value))
