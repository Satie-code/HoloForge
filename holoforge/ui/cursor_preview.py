from typing import Tuple


class CursorPreview:
    def __init__(self, voxel_size: float = 0.1):
        self.voxel_size = voxel_size
        self.grid_pos = (0, 0, 0)

    def update_from_normalized(self, rx: float, ry: float, rz: float):
        gx = int(round((rx - 0.5) / self.voxel_size))
        gy = int(round((ry - 0.5) / self.voxel_size))
        gz = int(round((rz - 0.5) / self.voxel_size))
        self.grid_pos = (gx, gy, gz)

    def get_position(self) -> Tuple[int, int, int]:
        return self.grid_pos
