"""
Value Object imutável representando um vetor tridimensional no espaço (km ou unidades adimensionais).
"""

from dataclasses import dataclass
import math
import numpy as np

@dataclass(frozen=True)
class Vector3DVO:
    x: float
    y: float
    z: float

    def magnitude(self) -> float:
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalized(self) -> 'Vector3DVO':
        mag = self.magnitude()
        if mag == 0.0:
            return Vector3DVO(0.0, 0.0, 0.0)
        return Vector3DVO(self.x / mag, self.y / mag, self.z / mag)

    def dot(self, other: 'Vector3DVO') -> float:
        return self.x * other.x + self.y * other.y + self.z * other.z

    def cross(self, other: 'Vector3DVO') -> 'Vector3DVO':
        return Vector3DVO(
            self.y * other.z - self.z * other.y,
            self.z * other.x - self.x * other.z,
            self.x * other.y - self.y * other.x
        )

    def to_numpy(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z], dtype=np.float64)

    @classmethod
    def from_numpy(cls, arr: np.ndarray) -> 'Vector3DVO':
        return cls(float(arr[0]), float(arr[1]), float(arr[2]))
