from __future__ import annotations
from typing import Optional

try:  # pragma: no cover
    import mediapipe as mp  # type: ignore
    _MP_AVAILABLE = True
except Exception:  # pragma: no cover
    mp = None
    _MP_AVAILABLE = False

try:  # pragma: no cover
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None

from core.experimental.models.pose_data import BodyPose, PoseKeypoint


class PoseProvider:
    """Light wrapper to extract a single-frame BodyPose using MediaPipe.

    Degrades gracefully if mediapipe or cv2 unavailable (returns empty BodyPose)."""
    def __init__(self):
        self._pose_solution = None
        if _MP_AVAILABLE:
            try:
                self._pose_solution = mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1)
            except Exception:
                self._pose_solution = None

    def extract(self, video_path: str, frame_index: int) -> BodyPose:
        if not (self._pose_solution and cv2):
            return BodyPose(frame_index=frame_index)
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return BodyPose(frame_index=frame_index)
        try:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, frame = cap.read()
            if not ok or frame is None:
                return BodyPose(frame_index=frame_index)
            # BGR to RGB
            rgb = frame[:, :, ::-1]
            result = self._pose_solution.process(rgb)
            if not result or not result.pose_landmarks:
                return BodyPose(frame_index=frame_index)
            lm = result.pose_landmarks.landmark
            # Map subset relevant for engines (naming aligns with engine StageConfig expectations)
            def kp(id_):
                return PoseKeypoint(x=lm[id_].x, y=lm[id_].y, z=lm[id_].z, confidence=lm[id_].visibility)
            # Using mediapipe indices per spec
            pose = BodyPose(
                nose=kp(0),
                left_shoulder=kp(11), right_shoulder=kp(12),
                left_elbow=kp(13), right_elbow=kp(14),
                left_wrist=kp(15), right_wrist=kp(16),
                left_hip=kp(23), right_hip=kp(24),
                left_knee=kp(25), right_knee=kp(26),
                left_ankle=kp(27), right_ankle=kp(28),
                frame_index=frame_index
            )
            return pose
        except Exception:
            return BodyPose(frame_index=frame_index)
        finally:
            cap.release()

__all__ = ['PoseProvider']
