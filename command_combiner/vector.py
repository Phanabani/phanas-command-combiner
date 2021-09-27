from __future__ import annotations

import math
from numbers import Real
from typing import Union

__all__ = ['Vector3']


class Vector3:
    def __init__(self, x: Real = 0, y: Real = 0, z: Real = 0):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"

    def __eq__(self, other: Vector3):
        rel_tol = 1e-9
        abs_tol = 1e-8
        return (
            math.isclose(self.x, other.x, rel_tol=rel_tol, abs_tol=abs_tol)
            and math.isclose(self.y, other.y, rel_tol=rel_tol, abs_tol=abs_tol)
            and math.isclose(self.z, other.z, rel_tol=rel_tol, abs_tol=abs_tol)
        )

    def set(self, x: Real, y: Real, z: Real):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other: Vector3):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __iadd__(self, other: Vector3):
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def __sub__(self, other: Vector3):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __isub__(self, other: Vector3):
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self

    def __mul__(self, other: Union[Real, Vector3]):
        try:
            return Vector3(self.x * other.x, self.y * other.y, self.z * other.z)
        except AttributeError:
            return Vector3(self.x * other, self.y * other, self.z * other)

    def __imul__(self, other: Union[Real, Vector3]):
        try:
            x = other.x
            y = other.y
            z = other.z
        except AttributeError:
            x = y = z = other
        self.x *= x
        self.y *= y
        self.z *= z
        return self

    def __div__(self, other: Union[Real, Vector3]):
        try:
            return Vector3(self.x / other.x, self.y / other.y, self.z / other.z)
        except AttributeError:
            return Vector3(self.x / other, self.y / other, self.z / other)

    def __idiv__(self, other: Union[Real, Vector3]):
        try:
            x = other.x
            y = other.y
            z = other.z
        except AttributeError:
            x = y = z = other
        self.x /= x
        self.y /= y
        self.z /= z
        return self
