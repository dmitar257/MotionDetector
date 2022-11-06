from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import cv2
import time 

class CameraInfoFetcher(QObject):
    sendAllCameraInfo = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()

    @pyqtSlot()    
    def onStart(self):
        count = 0
        cameraList = []
        time.sleep(2.0)
        while True:
            cameraDict = {}
            cap = cv2.VideoCapture(count,cv2.CAP_DSHOW)
            if cap.isOpened():
                cameraDict["index"] = count
                cameraDict["frameWidth"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                cameraDict["frameHeight"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cameraList.append(cameraDict)
                cap.release()
            else:
                break
            count += 1
        self.sendAllCameraInfo.emit(cameraList)