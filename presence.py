import cv2
import time

_detector = cv2.FaceDetectorYN.create(
    "face_detection_yunet_2023mar.onnx", "", (320, 320), score_threshold=0.7
)


def is_face_present(camera_index: int = 0) -> bool:
    """Quickly checks the webcam for one frame to see if a face is visible."""
    try:
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return False
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return False

        height, width = frame.shape[:2]
        _detector.setInputSize((width, height))
        _, faces = _detector.detect(frame)
        return faces is not None and len(faces) > 0
    except Exception as e:
        print(f"⚠️ Camera check failed: {e}")
        return False


def watch_for_presence(on_detected, check_interval=5, away_threshold=60):
    """
    Continuously watches the camera. Calls on_detected() the moment a face appears
    after being away for at least `away_threshold` seconds.
    """
    last_seen_absent_at = time.time()
    was_present = False

    while True:
        present = is_face_present()

        if present and not was_present:
            time_away = time.time() - last_seen_absent_at
            if time_away >= away_threshold:
                on_detected()
            was_present = True
        elif not present:
            if was_present:
                last_seen_absent_at = time.time()
            was_present = False

        time.sleep(check_interval)