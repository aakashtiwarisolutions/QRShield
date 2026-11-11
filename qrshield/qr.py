import cv2
import numpy as np

_detectors = [cv2.QRCodeDetector(), cv2.QRCodeDetectorAruco()]


def looks_like_url(text):
    text = text.strip()
    return text.lower().startswith(('http://', 'https://')) or ('.' in text and ' ' not in text and len(text) < 2048)


def _try(image):
    for detector in _detectors:
        text, points, _ = detector.detectAndDecode(image)
        if text:
            return text, points
    return None, None


def decode_frame(frame):
    text, points = _try(frame)
    if text:
        return text, points
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
    for image in (gray, cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)):
        text, _ = _try(image)
        if text:
            return text, None
    return None, None


def decode_image_bytes(data):
    frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return None
    return decode_frame(frame)[0]
