from __future__ import annotations
from math import ceil, floor

from typing import Optional

from vector import Vector3

__all__ = [
    'Snakey'
]


def triangle_wave(t, period):
    return 1 - abs(1 - t/period + 2*floor(0.5 * t / period))


def back_and_forth(t: int, offset: int):
    # Get a triangle wave with a period one greater than the max offset
    # We phase shift left so that we can remain on the edge when incrementing
    # one dimension
    triangle = triangle_wave(t + 0.5, offset + 1)
    # Amplify the wave and clip so that we stay on the edge
    triangle_amp = (offset + 1) * triangle - 0.5
    triangle_clip = max(0, min(offset, triangle_amp))
    return round(triangle_clip)


def space_filling_curve(t: int, dimensions: Vector3):
    return Vector3(
        back_and_forth(t, dimensions.x-1),
        back_and_forth(
            floor(t / (dimensions.x-1 + 1)), dimensions.z-1
        ),
        back_and_forth(
            floor(t / ((dimensions.x-1 + 1) * (dimensions.z-1 + 1))), dimensions.y-1
        )
    )


class Snakey:

    def __init__(self, dimensions: Vector3, volume_target: Optional[int] = None):
        if dimensions.y == -1 and volume_target is not None:
            dimensions.y = (
                ceil(volume_target / ((dimensions.x + 1) * (dimensions.z + 1)))
            )
        self._dimensions = dimensions
        self._pos = Vector3()
        self._direction = Vector3(1, 0, 0)
        self._index = 0
        self._volume = (dimensions.x + 1) * (dimensions.y + 1) * (dimensions.z + 1)

    @property
    def dimensions(self) -> Vector3:
        return self._dimensions

    @property
    def pos(self) -> Vector3:
        return self._pos

    @property
    def direction(self) -> Vector3:
        return self._direction

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, new_value: int):
        self._index = new_value

    @property
    def volume(self) -> int:
        return self._volume

    def __len__(self):
        return self.volume

    def __next__(self) -> Vector3:
        if self._index >= len(self):
            raise StopIteration

        pos = self[self._index]
        self._index += 1
        return pos

    def __getitem__(self, index: int) -> Vector3:
        if index >= len(self):
            raise IndexError(f"index out of range")
        return space_filling_curve(index, self._dimensions)

    def reset(self):
        self.index = 0
