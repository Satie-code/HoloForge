from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class VoxelObject:
    position: Tuple[int, int, int]
    color: Tuple[float, float, float]
    emissive: bool = True
    metallic: float = 0.0
    roughness: float = 0.5
