from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import time

class AppState(Enum):
    IDLE = "IDLE"
    BUILDING = "BUILDING"
    CONFIRM_PENDING = "CONFIRM_PENDING"
    MENU_OPEN = "MENU_OPEN"
    ORBIT_VIEW = "ORBIT_VIEW"
    SHIFT_STRUCTURE = "SHIFT_STRUCTURE"
    MOVE_MODE = "MOVE_MODE"

class StateMachine:
    def __init__(self, config):
        self.config = config
        self.state = AppState.IDLE
        self._confirm_start: Optional[float] = None
        self._last_left_palm_open_times: List[float] = []
        self._shift_active = False
        self._last_midpoint: Optional[Tuple[float, float]] = None
        self.hovered_voxel: Optional[Tuple[int, int, int]] = None
        self.selected_voxel: Optional[Tuple[int, int, int]] = None
        self.pre_move_pos: Optional[Tuple[int, int, int]] = None

    def reset(self):
        self.state = AppState.IDLE
        self._confirm_start = None
        self._shift_active = False
        self._last_midpoint = None
        self.selected_voxel = None

    def update(self, shared_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []
        self.hovered_voxel = shared_state.get("hovered_voxel")
        
        if self.state == AppState.CONFIRM_PENDING and self._confirm_start is not None and (time.time() - self._confirm_start) >= self.config.CONFIRM_TIMEOUT_SECONDS:
            self.state = AppState.IDLE
            self._confirm_start = None
            actions.append({"type": "discard_build_buffer"})
        return actions

    def process_event(self, event: str, payload: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        actions: List[Dict[str, Any]] = []
        p = payload or {}

        # 1. Building / Move Flow
        if event == "RIGHT_PINCH_START":
            if self.state == AppState.IDLE:
                if self.hovered_voxel:
                    self.state = AppState.MOVE_MODE
                    self.selected_voxel = self.hovered_voxel
                    self.pre_move_pos = self.hovered_voxel
                    actions.append({"type": "move_start", "pos": self.hovered_voxel})
                else:
                    self.state = AppState.BUILDING
                    actions.append({"type": "building_start"})
            elif self.state == AppState.MOVE_MODE:
                self.state = AppState.IDLE
                actions.append({"type": "move_commit", "old_pos": self.pre_move_pos, "new_pos": self.selected_voxel})
                self.selected_voxel = None
                self.pre_move_pos = None

        elif event == "RIGHT_PINCH_HOLD":
            if self.state == AppState.BUILDING:
                actions.append({"type": "building_add_pos"})
            elif self.state == AppState.MOVE_MODE:
                actions.append({"type": "move_update"})

        elif event == "RIGHT_PINCH_RELEASE":
            if self.state == AppState.BUILDING:
                self.state = AppState.CONFIRM_PENDING
                self._confirm_start = time.time()
                actions.append({"type": "confirm_pending_start"})
        
        # Confirmation (Palm Open)
        elif event == "RIGHT_PALM_OPEN" or event == "LEFT_PALM_OPEN":
            if self.state == AppState.CONFIRM_PENDING:
                self.state = AppState.IDLE
                self._confirm_start = None
                actions.append({"type": "commit_build_buffer"})
            
            # Orbit Reset Logic (Double Left Palm Open)
            if event == "LEFT_PALM_OPEN":
                now = time.time()
                self._last_left_palm_open_times.append(now)
                self._last_left_palm_open_times = [t for t in self._last_left_palm_open_times if now - t <= 0.5]
                
                if self.state == AppState.IDLE:
                    self.state = AppState.ORBIT_VIEW
                    actions.append({"type": "orbit_start"})
                
                if (self.state == AppState.ORBIT_VIEW or self.state == AppState.IDLE) and len(self._last_left_palm_open_times) >= 2:
                    actions.append({"type": "orbit_reset_view"})
                    self._last_left_palm_open_times = []

        # 2. Menu Flow
        elif event == "LEFT_WRIST_CIRCLE":
            if self.state == AppState.IDLE:
                self.state = AppState.MENU_OPEN
                actions.append({"type": "menu_open"})

        elif event == "MENU_RELEASE" or event == "LEFT_PALM_CLOSE":
            if self.state == AppState.MENU_OPEN:
                self.state = AppState.IDLE
                actions.append({"type": "menu_close"})

        # 3. Orbit Flow
        elif event == "LEFT_PALM_MOVE":
            if self.state == AppState.ORBIT_VIEW:
                actions.append({"type": "orbit_move", "delta": p.get("delta", (0.0, 0.0))})
        
        elif event == "LEFT_PALM_CLOSE":
            if self.state == AppState.ORBIT_VIEW:
                self.state = AppState.IDLE
                actions.append({"type": "orbit_stop"})

        # 4. Deletion
        elif event == "LEFT_FIST_START":
            actions.append({"type": "delete_voxel_under_cursor"})

        # 5. Shift Flow
        elif event == "BOTH_PINCH_START":
            if self.state == AppState.IDLE:
                self.state = AppState.SHIFT_STRUCTURE
                self._shift_active = True
                self._last_midpoint = p.get("midpoint")
                actions.append({"type": "shift_start"})
        elif event == "BOTH_PINCH_HOLD":
            if self.state == AppState.SHIFT_STRUCTURE and self._shift_active:
                current_midpoint = p.get("midpoint")
                if self._last_midpoint and current_midpoint:
                    delta = (current_midpoint[0] - self._last_midpoint[0], current_midpoint[1] - self._last_midpoint[1])
                    actions.append({"type": "shift_delta", "delta": delta})
                self._last_midpoint = current_midpoint
        elif event == "BOTH_PINCH_RELEASE":
            if self.state == AppState.SHIFT_STRUCTURE:
                self.state = AppState.IDLE
                self._shift_active = False
                self._last_midpoint = None
                actions.append({"type": "shift_stop"})

        # 6. Safety
        elif event == "FRAME_LEAVE":
            if self.state in [AppState.ORBIT_VIEW, AppState.SHIFT_STRUCTURE, AppState.BUILDING, AppState.MOVE_MODE]:
                self.state = AppState.IDLE
                actions.append({"type": "orbit_stop"})
                actions.append({"type": "discard_build_buffer"})
                self._shift_active = False

        return actions

