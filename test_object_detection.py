from datetime import datetime, timedelta
import cv2

source  = 5
cameraController = cv2.VideoCapture(source, cv2.CAP_DSHOW)
if cameraController is None or not cameraController.isOpened():
    print('Warning: unable to open video source: ', source)
