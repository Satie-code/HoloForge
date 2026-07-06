from typing import Dict, Tuple, List, Optional

from .voxel_object import VoxelObject


class VoxelGrid:
    def __init__(self, default_color=(0.0, 1.0, 1.0), default_emissive: bool = True, default_metallic: float = 0.0, default_roughness: float = 0.5):
        self.voxels: Dict[Tuple[int, int, int], VoxelObject] = {}
        self.build_buffer: List[Tuple[int, int, int]] = []
        self.default_color = default_color
        self.default_emissive = default_emissive
        self.default_metallic = default_metallic
        self.default_roughness = default_roughness
        self.version = 0
        self.build_version = 0

    def add(self, pos: Tuple[int, int, int], color: Optional[Tuple[float, float, float]] = None, emissive: Optional[bool] = None, metallic: Optional[float] = None, roughness: Optional[float] = None):
        c = color if color is not None else self.default_color
        e = emissive if emissive is not None else self.default_emissive
        m = metallic if metallic is not None else self.default_metallic
        r = roughness if roughness is not None else self.default_roughness
        self.voxels[pos] = VoxelObject(position=pos, color=c, emissive=e, metallic=m, roughness=r)
        self.version += 1

    def delete(self, pos: Tuple[int, int, int]):
        if pos in self.voxels:
            del self.voxels[pos]
            self.version += 1

    def exists(self, pos: Tuple[int, int, int]) -> bool:
        return pos in self.voxels

    def commit_build_buffer(self):
        for pos in self.build_buffer:
            self.add(pos)
        self.build_buffer.clear()
        self.build_version += 1

    def discard_build_buffer(self):
        self.build_buffer.clear()
        self.build_version += 1

    def centroid(self) -> Tuple[float, float, float]:
        if not self.voxels:
            return 0.0, 0.0, 0.0
        xs = [p[0] for p in self.voxels.keys()]
        ys = [p[1] for p in self.voxels.keys()]
        zs = [p[2] for p in self.voxels.keys()]
        return sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)

    def shift(self, delta: Tuple[int, int, int]):
        if delta == (0, 0, 0):
            return
        new_voxels: Dict[Tuple[int, int, int], VoxelObject] = {}
        for pos, vox in self.voxels.items():
            new_pos = (pos[0] + delta[0], pos[1] + delta[1], pos[2] + delta[2])
            new_voxels[new_pos] = VoxelObject(position=new_pos, color=vox.color, emissive=vox.emissive, metallic=vox.metallic, roughness=vox.roughness)
        self.voxels = new_voxels
        if self.build_buffer:
            self.build_buffer = [(p[0] + delta[0], p[1] + delta[1], p[2] + delta[2]) for p in self.build_buffer]
        self.version += 1
        self.build_version += 1
