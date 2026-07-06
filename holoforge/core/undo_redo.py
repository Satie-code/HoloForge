from typing import List, Optional, Tuple, Any

class Action:
    def execute(self, voxel_grid):
        raise NotImplementedError

    def undo(self, voxel_grid):
        raise NotImplementedError


class AddVoxelAction(Action):
    def __init__(self, pos: Tuple[int, int, int], color: Tuple[float, float, float], emissive: bool, metallic: float, roughness: float):
        self.pos = pos
        self.color = color
        self.emissive = emissive
        self.metallic = metallic
        self.roughness = roughness

    def execute(self, voxel_grid):
        voxel_grid.add(self.pos, self.color, self.emissive, self.metallic, self.roughness)

    def undo(self, voxel_grid):
        voxel_grid.delete(self.pos)


class DeleteVoxelAction(Action):
    def __init__(self, pos: Tuple[int, int, int], color: Tuple[float, float, float], emissive: bool, metallic: float, roughness: float):
        self.pos = pos
        self.color = color
        self.emissive = emissive
        self.metallic = metallic
        self.roughness = roughness

    def execute(self, voxel_grid):
        voxel_grid.delete(self.pos)

    def undo(self, voxel_grid):
        voxel_grid.add(self.pos, self.color, self.emissive, self.metallic, self.roughness)


class MoveVoxelAction(Action):
    def __init__(self, old_pos: Tuple[int, int, int], new_pos: Tuple[int, int, int]):
        self.old_pos = old_pos
        self.new_pos = new_pos
        self._voxel_data = None

    def execute(self, voxel_grid):
        if self.old_pos in voxel_grid.voxels:
            self._voxel_data = voxel_grid.voxels[self.old_pos]
            voxel_grid.delete(self.old_pos)
            voxel_grid.add(
                self.new_pos,
                self._voxel_data.color,
                self._voxel_data.emissive,
                self._voxel_data.metallic,
                self._voxel_data.roughness
            )

    def undo(self, voxel_grid):
        if self.new_pos in voxel_grid.voxels and self._voxel_data:
            voxel_grid.delete(self.new_pos)
            voxel_grid.add(
                self.old_pos,
                self._voxel_data.color,
                self._voxel_data.emissive,
                self._voxel_data.metallic,
                self._voxel_data.roughness
            )


class UndoRedoManager:
    def __init__(self, voxel_grid, max_history: int = 50):
        self.voxel_grid = voxel_grid
        self.undo_stack: List[Action] = []
        self.redo_stack: List[Action] = []
        self.max_history = max_history

    def perform_action(self, action: Action):
        action.execute(self.voxel_grid)
        self.undo_stack.append(action)
        self.redo_stack.clear()
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

    def undo(self):
        if self.undo_stack:
            action = self.undo_stack.pop()
            action.undo(self.voxel_grid)
            self.redo_stack.append(action)

    def redo(self):
        if self.redo_stack:
            action = self.redo_stack.pop()
            action.execute(self.voxel_grid)
            self.undo_stack.append(action)
