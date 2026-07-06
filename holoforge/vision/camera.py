import threading
import time
from typing import Dict, Any, Optional

import cv2
import numpy as np

from .hand_tracker import HandTracker
from .gesture_engine import GestureEngine

class CameraCapture:
    def __init__(self, config, shared_state: Dict[str, Any]):
        self.config = config
        self.shared_state = shared_state
        self._cap: Optional[cv2.VideoCapture] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        self._tracker = HandTracker(
            max_num_hands=2,
            min_detection_confidence=self.config.min_detection_confidence if hasattr(self.config, "min_detection_confidence") else 0.7,
            min_tracking_confidence=self.config.min_tracking_confidence if hasattr(self.config, "min_tracking_confidence") else 0.7,
        )
        self._gestures = GestureEngine(self.config)

    def start(self):
        self._cap = cv2.VideoCapture(self.config.CAMERA_INDEX, cv2.CAP_DSHOW)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.CAMERA_HEIGHT)
        self._running = True
        self.shared_state["frame_lock"] = self._lock
        self.shared_state["frame"] = None
        self.shared_state["frame_time"] = 0.0
        self.shared_state["gesture_events"] = []
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        if self._cap:
            self._cap.release()
        if self._tracker:
            self._tracker.close()

    def _run(self):
        target_interval = 1.0 / 30.0
        while self._running:
            ret, frame_bgr = self._cap.read() if self._cap else (False, None)
            if ret and frame_bgr is not None:
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                hands = self._tracker.process(frame_rgb)
                events = self._gestures.update(hands or {"hands": []})
                
                if hands and hands.get("hands"):
                    num_hands = len(hands["hands"])
                    # Briefly log detection status every ~2 seconds
                    if time.time() % 2 < 0.05:
                        print(f"[Vision] Detected {num_hands} hand(s)")
                
                if events:
                    for e in events:
                        print(f"[Gesture] Event: {e['name']}")

                with self._lock:
                    self.shared_state["frame"] = frame_rgb
                    self.shared_state["frame_time"] = time.time()
                    self.shared_state["hands"] = hands
                    self.shared_state["gesture_events"] = events
            time.sleep(target_interval)
