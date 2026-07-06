from typing import List, Tuple, Optional, Dict, Any
import math


class RadialMenu:
    MAIN = "MAIN"
    COLOR = "COLOR"

    def __init__(self):
        self.mode = self.MAIN
        # Positions: TOP (0,1), RIGHT (1,0), BOTTOM (0,-1), LEFT (-1,0)
        self.main_options = [
            ("Toggle Continuous Build", (0.0, 1.0)),
            ("Change Voxel Colour", (1.0, 0.0)),
            ("Clear Scene", (0.0, -1.0)),
            ("Toggle Grid Visibility", (-1.0, 0.0)),
        ]
        self.color_options = [
            ("Cyan", (0.0, 1.0), (0.0, 1.0, 1.0)),
            ("Magenta", (0.866, 0.5), (1.0, 0.0, 1.0)),
            ("Yellow", (0.866, -0.5), (1.0, 1.0, 0.0)),
            ("Green", (0.0, -1.0), (0.0, 1.0, 0.0)),
            ("Orange", (-0.866, -0.5), (1.0, 0.53, 0.0)),
            ("White", (-0.866, 0.5), (1.0, 1.0, 1.0)),
        ]
        self.active_index: Optional[int] = None
        self.open = False
        self.hold_start_time: Optional[float] = None
        self.hold_duration = 2.0

    def open_menu(self):
        self.open = True
        self.mode = self.MAIN
        self.active_index = None
        self.hold_start_time = None

    def close_menu(self):
        self.open = False
        self.mode = self.MAIN
        self.active_index = None
        self.hold_start_time = None

    def update_selection(self, cursor_xy: Tuple[float, float]):
        if not self.open:
            return
        
        options = self.main_options if self.mode == self.MAIN else self.color_options
        best_i = None
        best_d = 0.5 # Selection threshold
        
        for i, opt in enumerate(options):
            pos = opt[1]
            d = math.hypot(cursor_xy[0] - pos[0], cursor_xy[1] - pos[1])
            if d < best_d:
                best_d = d
                best_i = i
        
        if self.active_index != best_i:
            self.active_index = best_i
            self.hold_start_time = None # Reset hold if selection changes

    def confirm(self) -> Optional[Dict[str, Any]]:
        if not self.open or self.active_index is None:
            return None
        
        if self.mode == self.MAIN:
            opt = self.main_options[self.active_index][0]
            if opt == "Change Voxel Colour":
                self.mode = self.COLOR
                self.active_index = None
                return {"type": "ui_nav", "target": "color_menu"}
            elif opt == "Clear Scene":
                # Handled by hold logic elsewhere or returns a special action
                return {"type": "action", "option": opt}
            return {"type": "action", "option": opt}
        else:
            opt_name, _, color = self.color_options[self.active_index]
            self.mode = self.MAIN
            self.active_index = None
            return {"type": "set_color", "color": color, "name": opt_name}

