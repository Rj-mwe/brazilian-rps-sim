"""
Value Object imutável representando uma atitude/rotação espacial 3D via quatérnion normalizado.
"""

from dataclasses import dataclass
import math
import numpy as np

@dataclass(frozen=True)
class QuaternionVO:
    x: float
    y: float
    z: float
    w: float

    @classmethod
    def identity(cls) -> 'QuaternionVO':
        return cls(0.0, 0.0, 0.0, 1.0)

    @classmethod
    def from_euler(cls, roll: float, pitch: float, yaw: float) -> 'QuaternionVO':
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)

        w = cr * cp * cy + sr * sp * sy
        x = sr * cp * cy - cr * sp * sy
        y = cr * sp * cy + sr * cp * sy
        z = cr * cp * sy - sr * sp * cy
        return cls(x, y, z, w)

    @classmethod
    def from_two_vectors(cls, v_from: np.ndarray, v_to: np.ndarray) -> 'QuaternionVO':
        v0 = v_from / np.linalg.norm(v_from)
        v1 = v_to / np.linalg.norm(v_to)
        dot = float(np.dot(v0, v1))

        if dot >= 0.999999:
            return cls.identity()
        if dot <= -0.999999:
            ortho = np.array([1.0, 0.0, 0.0]) if abs(v0[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
            axis = np.cross(v0, ortho)
            axis = axis / np.linalg.norm(axis)
            return cls(float(axis[0]), float(axis[1]), float(axis[2]), 0.0)

        cross = np.cross(v0, v1)
        w = math.sqrt((1.0 + dot) * 2.0)
        inv_w = 1.0 / w
        return cls(float(cross[0] * inv_w), float(cross[1] * inv_w), float(cross[2] * inv_w), float(w * 0.5))
