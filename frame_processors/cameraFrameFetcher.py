import time
from typing import Optional, Tuple, Any
from frame_processors.frameFetcher import FrameFetcher, FrameFetcherSettings, NoVideoInputError,FrameFetchingRuntimeError
import imutils
from PyQt5.QtCore import pyqtSlot
import cv2
import numpy as np
import logging

RESIZE_WIDTH = 500
logger = logging.getLogger(__name__)

class CameraFrameFetcher(FrameFetcher):

    def __init__(self, fetcherSettings: FrameFetcherSettings):
        super().__init__(fetcherSettings)

    def startCapturingFrames(self) -> None:
        try:
            self.cameraController = self.getCameraContoller(self.settings.cameraIndex)
            self.cameraController.set(cv2.CAP_PROP_FRAME_WIDTH,640)
            self.cameraController.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
            time.sleep(2.0)
            self.frameResolutionFetched.emit(self.getFramesResolution())
            self.running = True
            while self.isRunning():
                frame = self.captureSingleFrame()
                if not frame is None:
                    frame = imutils.resize(frame, RESIZE_WIDTH)
                    self.frameFetched.emit(frame)
                    continue
                break
            self.closeCamera()
        except NoVideoInputError as noInputErr:
            logger.error(noInputErr)
            self.stopRunning()
            self.noInputFoundError.emit()
        except Exception as e:
            logger.error(e)
            self.stopRunning()
            self.frameFetchingRunntimeError.emit(str(e))
        
    def getFramesResolution(self) -> Tuple[int, int]:
        frameWidth = int(self.cameraController.get(cv2.CAP_PROP_FRAME_WIDTH))
        frameHeight = int(self.cameraController.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return frameWidth, frameHeight, RESIZE_WIDTH
            
    def closeCamera(self) -> None:
        self.cameraController.release()
    
    def captureSingleFrame(self) -> Optional[np.ndarray]:
        isFrameCaptured, frame = self.cameraController.read()
        if isFrameCaptured:
            return frame
        return None

    def getCameraContoller(self, cameraIndex: int) -> Any:
        cameraController = cv2.VideoCapture(self.settings.cameraIndex, cv2.CAP_DSHOW)
        if cameraController is None or not cameraController.isOpened():
            raise NoVideoInputError(f"No camera input found, with camera index: {cameraIndex}")
        return cameraController

    @pyqtSlot(FrameFetcherSettings)
    def onFrameFetcherSettingsChanged(self, new_settings: FrameFetcherSettings) -> None:
        self.settings = new_settings
