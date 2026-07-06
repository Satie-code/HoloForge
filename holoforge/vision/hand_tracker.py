from typing import Optional, Dict, Any

import cv2
import numpy as np
HandsClass = None
try:
    import mediapipe as mp
    HandsClass = getattr(getattr(mp, "solutions", object()), "hands", None)
    if HandsClass is not None:
        HandsClass = HandsClass.Hands  # type: ignore
except Exception:
    try:
        from mediapipe.python.solutions.hands import Hands as HandsClass  # type: ignore
    except Exception:
        HandsClass = None


class HandTracker:
    def __init__(self, max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.7):
        if HandsClass is not None:
            print("[Vision] MediaPipe Hands loaded successfully.")
            self.hands = HandsClass(
                static_image_mode=False,
                max_num_hands=max_num_hands,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence,
                model_complexity=1,
            )
        else:
            print("[Vision] ERROR: MediaPipe Hands failed to load. Check installations.")
            self.hands = None

    def process(self, frame_rgb: np.ndarray) -> Optional[Dict[str, Any]]:
        if self.hands is None:
            return None
        result = self.hands.process(frame_rgb)
        if not result or not result.multi_hand_landmarks or not result.multi_handedness:
            return None
        hands_data = []
        for landmarks, handedness in zip(result.multi_hand_landmarks, result.multi_handedness):
            label = handedness.classification[0].label
            # The horizontal flip causes my real Right hand to look like a Left hand to MediaPipe.
            label = "Right" if label == "Left" else "Left"
            coords = [(lm.x, lm.y, lm.z) for lm in landmarks.landmark]
            hands_data.append({"label": label, "landmarks": coords})
        return {"hands": hands_data}

    def close(self):
        if self.hands:
            self.hands.close()
