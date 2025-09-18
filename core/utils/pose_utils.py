import cv2
import numpy as np
from typing import Any, Dict, Optional, Tuple, Union


def _load_image(path: str):
    image = cv2.imread(path)
    if image is None:
        raise FileNotFoundError(f"Image not found or unreadable: {path}")
    return image


def _process_image(image: np.ndarray) -> Dict[str, Any]:
    """Core processing: receive BGR image, return landmark dict structure."""
    try:
        try:
            import mediapipe as mp  # type: ignore
        except ImportError:
            return {
                "success": False,
                "landmarks": None,
                "width": None,
                "height": None,
                "backend": "unavailable",
                "error": "mediapipe not installed"
            }

        h, w = image.shape[:2]
        pose = mp.solutions.pose.Pose(
            static_image_mode=True,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
        )
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)
        pose.close()

        if not results.pose_landmarks:
            return {
                "success": True,
                "landmarks": None,
                "width": w,
                "height": h,
                "backend": "mediapipe"
            }

        raw_list = [
            {
                "x": lm.x,
                "y": lm.y,
                "z": lm.z,
                "visibility": lm.visibility,
            }
            for lm in results.pose_landmarks.landmark  # type: ignore
        ]

        return {
            "success": True,
            "landmarks": raw_list,
            "width": w,
            "height": h,
            "backend": "mediapipe"
        }
    except Exception as e:  # pragma: no cover - defensive
        return {
            "success": False,
            "landmarks": None,
            "width": None,
            "height": None,
            "backend": "mediapipe",
            "error": str(e)
        }


def extract_pose(source: Union[str, np.ndarray]) -> Optional[Dict[str, Any]]:
    """Extract raw pose landmarks from either an image path or a BGR numpy array.

    Args:
        source: file path (str) or already-loaded BGR image (np.ndarray)
    """
    if isinstance(source, str):
        image = _load_image(source)
    else:
        image = source
    return _process_image(image)


def extract_pose_from_array(image: np.ndarray) -> Optional[Dict[str, Any]]:
    """Explicit helper when caller already has a BGR frame."""
    return _process_image(image)


def extract_pose_pair(img1: Union[str, np.ndarray], img2: Union[str, np.ndarray]) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Extract raw pose landmarks for two inputs (paths or arrays)."""
    return extract_pose(img1), extract_pose(img2)
