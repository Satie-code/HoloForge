import math
from collections import deque
from typing import Dict, Any, List, Tuple, Optional


class GestureEngine:
    def __init__(self, config):
        self.config = config
        self.left_wrist_path = deque(maxlen=30)
        self.right_wrist_path = deque(maxlen=30)
        self._right_pinch_active = False
        self._left_pinch_active = False
        self._both_pinch_active = False
        self._last_midpoint: Optional[Tuple[float, float]] = None
        self._left_palm_active = False
        self._last_left_wrist: Optional[Tuple[float, float]] = None

    def _distance2d(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        return math.hypot(dx, dy)

    def _pinch(self, landmarks: List[Tuple[float, float, float]]) -> bool:
        thumb = landmarks[4]
        idx = landmarks[8]
        return self._distance2d((thumb[0], thumb[1]), (idx[0], idx[1])) < self.config.PINCH_THRESHOLD

    def _fingers_extended(self, landmarks: List[Tuple[float, float, float]]) -> List[bool]:
        ids = [(4, 8), (8, 12), (12, 16), (16, 20)]
        extended = []
        for a, b in ids:
            d = self._distance2d((landmarks[a][0], landmarks[a][1]), (landmarks[b][0], landmarks[b][1]))
            extended.append(d > self.config.FINGER_EXTEND_THRESHOLD)
        palm_open = all(extended)
        index_only = extended[0] and not any(extended[1:])
        fist = not any(extended)
        return [palm_open, index_only, fist]

    def _wrist_circle(self, path: deque) -> bool:
        if len(path) < 20:
            return False
        xs = [p[0] for p in path]
        ys = [p[1] for p in path]
        x0 = sum(xs) / len(xs)
        y0 = sum(ys) / len(ys)
        rs = [math.hypot(x - x0, y - y0) for x, y in path]
        radius = sum(rs) / len(rs)
        if radius <= 0.1:
            return False
        angles = [math.atan2(y - y0, x - x0) for x, y in path]
        total = 0.0
        for i in range(1, len(angles)):
            d = angles[i] - angles[i - 1]
            while d > math.pi:
                d -= 2 * math.pi
            while d < -math.pi:
                d += 2 * math.pi
            total += d
        return abs(total) >= 2 * math.pi

    def update(self, hands_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        left = None
        right = None
        for h in hands_result.get("hands", []):
            if h["label"] == "Left":
                left = h
            elif h["label"] == "Right":
                right = h

        if left:
            wrist = left["landmarks"][0]
            self.left_wrist_path.append((wrist[0], wrist[1]))
        if right:
            wrist = right["landmarks"][0]
            self.right_wrist_path.append((wrist[0], wrist[1]))

        l_palm_open, l_point, l_fist = False, False, False
        r_palm_open, r_point, r_fist = False, False, False

        if left:
            l_palm_open, l_point, l_fist = self._fingers_extended(left["landmarks"])
        if right:
            r_palm_open, r_point, r_fist = self._fingers_extended(right["landmarks"])

        # 1. Pinch Detection (High Priority)
        r_pinched = right and self._pinch(right["landmarks"])
        l_pinched = left and self._pinch(left["landmarks"])

        if r_pinched:
            if not self._right_pinch_active:
                events.append({"name": "RIGHT_PINCH_START"})
            self._right_pinch_active = True
            events.append({"name": "RIGHT_PINCH_HOLD"})
        elif self._right_pinch_active:
            self._right_pinch_active = False
            events.append({"name": "RIGHT_PINCH_RELEASE"})

        if l_pinched:
            if not self._left_pinch_active:
                events.append({"name": "LEFT_PINCH_START"})
            self._left_pinch_active = True
        else:
            self._left_pinch_active = False

        # 2. Both Pinch (Shift)
        if self._right_pinch_active and self._left_pinch_active:
            midpoint = None
            if left and right:
                lw, rw = left["landmarks"][0], right["landmarks"][0]
                midpoint = ((lw[0] + rw[0]) * 0.5, (lw[1] + rw[1]) * 0.5)
            if not self._both_pinch_active:
                self._both_pinch_active = True
                events.append({"name": "BOTH_PINCH_START", "midpoint": midpoint})
            else:
                events.append({"name": "BOTH_PINCH_HOLD", "midpoint": midpoint})
        elif self._both_pinch_active:
            self._both_pinch_active = False
            events.append({"name": "BOTH_PINCH_RELEASE"})

        # 3. Palm/Fist (Lower Priority - suppressed if pinched)
        if l_palm_open and not l_pinched:
            if not self._left_palm_active:
                self._left_palm_active = True
                events.append({"name": "LEFT_PALM_OPEN"})
                self._last_left_wrist = self.left_wrist_path[-1] if self.left_wrist_path else None
            
            if self.left_wrist_path:
                curr = self.left_wrist_path[-1]
                if self._last_left_wrist:
                    dx = curr[0] - self._last_left_wrist[0]
                    dy = curr[1] - self._last_left_wrist[1]
                    events.append({"name": "LEFT_PALM_MOVE", "delta": (dx, dy)})
                self._last_left_wrist = curr
        elif self._left_palm_active:
            self._left_palm_active = False
            self._last_left_wrist = None
            events.append({"name": "LEFT_PALM_CLOSE"})

        if r_palm_open and not r_pinched:
            events.append({"name": "RIGHT_PALM_OPEN"})

        if l_fist and not l_pinched:
            events.append({"name": "LEFT_FIST_START"})

        # 4. Wrist Circle (Menu Trigger)
        if self._wrist_circle(self.left_wrist_path) and l_pinched:
            events.append({"name": "LEFT_WRIST_CIRCLE"})
            self.left_wrist_path.clear() 

        return events

