import unittest
from holoforge.voxel.voxel_grid import VoxelGrid
from holoforge.core.undo_redo import UndoRedoManager, AddVoxelAction, DeleteVoxelAction, MoveVoxelAction
from holoforge.core.state_machine import StateMachine, AppState

class TestHoloForgeLogic(unittest.TestCase):
    def setUp(self):
        self.grid = VoxelGrid()
        self.undo_redo = UndoRedoManager(self.grid)
        self.fsm = StateMachine(None) # Config not strictly needed for basic state tests

    def test_add_voxel_action(self):
        pos = (1, 2, 3)
        action = AddVoxelAction(pos, (1,1,1), True, 0.0, 0.5)
        self.undo_redo.perform_action(action)
        self.assertTrue(self.grid.exists(pos))
        
        self.undo_redo.undo()
        self.assertFalse(self.grid.exists(pos))
        
        self.undo_redo.redo()
        self.assertTrue(self.grid.exists(pos))

    def test_delete_voxel_action(self):
        pos = (5, 5, 5)
        self.grid.add(pos, (1,0,0), False, 0.5, 0.2)
        action = DeleteVoxelAction(pos, (1,0,0), False, 0.5, 0.2)
        self.undo_redo.perform_action(action)
        self.assertFalse(self.grid.exists(pos))
        
        self.undo_redo.undo()
        self.assertTrue(self.grid.exists(pos))
        self.assertEqual(self.grid.voxels[pos].color, (1,0,0))
        
        self.undo_redo.redo()
        self.assertFalse(self.grid.exists(pos))

    def test_move_voxel_action(self):
        p1 = (1, 1, 1)
        p2 = (2, 2, 2)
        self.grid.add(p1, (0,1,0), True, 1.0, 0.0)
        action = MoveVoxelAction(p1, p2)
        self.undo_redo.perform_action(action)
        
        self.assertFalse(self.grid.exists(p1))
        self.assertTrue(self.grid.exists(p2))
        
        self.undo_redo.undo()
        self.assertTrue(self.grid.exists(p1))
        self.assertFalse(self.grid.exists(p2))
        
        self.undo_redo.redo()
        self.assertFalse(self.grid.exists(p1))
        self.assertTrue(self.grid.exists(p2))

    def test_state_machine_transitions(self):
        self.assertEqual(self.fsm.state, AppState.IDLE)
        
        # Idle -> Building
        self.fsm.process_event("RIGHT_PINCH_START")
        self.assertEqual(self.fsm.state, AppState.BUILDING)
        
        # Building -> ConfirmPending
        self.fsm.process_event("RIGHT_PINCH_RELEASE")
        self.assertEqual(self.fsm.state, AppState.CONFIRM_PENDING)
        
        # ConfirmPending -> Idle
        self.fsm.process_event("RIGHT_PALM_OPEN")
        self.assertEqual(self.fsm.state, AppState.IDLE)
        
        # Idle -> MoveMode
        self.fsm.hovered_voxel = (0,0,0)
        self.grid.add((0,0,0), (1,1,1), False, 0, 0.5)
        self.fsm.process_event("RIGHT_PINCH_START")
        self.assertEqual(self.fsm.state, AppState.MOVE_MODE)
        self.assertEqual(self.fsm.selected_voxel, (0,0,0))
        
        # MoveMode -> MoveUpdate (Hold)
        self.fsm.process_event("RIGHT_PINCH_HOLD")
        # No state change, but actions would be emitted
        
        # MoveMode commit second pinch start
        self.fsm.process_event("RIGHT_PINCH_START")
        self.assertEqual(self.fsm.state, AppState.IDLE)

if __name__ == "__main__":
    unittest.main()
