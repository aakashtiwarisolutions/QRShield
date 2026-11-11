import time

import cv2
import numpy as np

from qrshield.qr import decode_frame, looks_like_url
from qrshield.service import QRShield
from qrshield import storage

GREEN = (60, 180, 75)
RED = (40, 40, 220)
ORANGE = (0, 140, 255)
GREY = (120, 120, 120)


def draw_banner(frame, result):
    color = {'PHISHING': RED, 'CAUTION': ORANGE}.get(result['verdict'], GREEN)
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, h - 110), (w, h), color, -1)
    title = result['verdict'] if result['risk'] is None else f"{result['verdict']}  |  risk {result['risk'] * 100:.0f}%"
    cv2.putText(frame, title, (15, h - 75), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    cv2.putText(frame, result['host'][:60], (15, h - 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    if result['reasons']:
        cv2.putText(frame, 'Why: ' + result['reasons'][0][:70], (15, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)


def draw_message(frame, text):
    h, w = frame.shape[:2]
    cv2.rectangle(frame, (0, h - 50), (w, h), GREY, -1)
    cv2.putText(frame, text, (15, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)


def main():
    shield = QRShield()
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print('Could not open the webcam.')
        return
    print('QRShield scanner running. Q = quit, W = mark last result as wrong, H = show recent scans')
    last_text, last_result, last_seen = None, None, 0.0

    while True:
        ok, frame = camera.read()
        if not ok:
            break
        text, points = decode_frame(frame)
        if text:
            last_seen = time.time()
            if text != last_text:
                last_text = text
                last_result = shield.check(text, source='webcam') if looks_like_url(text) else {'not_url': text}
            if points is not None:
                color = GREY if 'not_url' in last_result else {'PHISHING': RED, 'CAUTION': ORANGE}.get(last_result['verdict'], GREEN)
                cv2.polylines(frame, [np.int32(points).reshape(-1, 1, 2)], True, color, 3)

        if last_result and time.time() - last_seen < 3:
            if 'not_url' in last_result:
                draw_message(frame, 'QR code does not contain a web link')
            else:
                draw_banner(frame, last_result)
        else:
            draw_message(frame, 'Show a QR code to the camera')

        cv2.imshow('QRShield', frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('w') and last_result and 'not_url' not in last_result:
            corrected = shield.mark_wrong(last_result)
            last_result['verdict'] = corrected
            last_result['reasons'] = ['corrected by you']
            print(f"Saved feedback: {last_result['host']} is {corrected}")
        if key == ord('h'):
            for row in storage.recent_scans(shield.db, 10):
                print(row)

    camera.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
