from dataclasses import dataclass
from datetime import datetime
import logging
import os
from queue import Queue
from typing import Dict, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSlot, QTimer

from utils import PointCoords

logger = logging.getLogger(__name__)

@dataclass
class MovementLoggerParameters:
    loggingInterval: int
    loggingFile: str
    scalingWidth: 800
    calculateInverse: bool = False
    
class MovementLogger(QObject):
    def __init__(self, movementLoggerParams: MovementLoggerParameters) -> None:
        super().__init__()
        self.loggerParams = movementLoggerParams
        self.originalFrameResolution: Optional[Tuple[int, int]] = None
        self.aspectRatio: Optional[Tuple[int, int]] = None
        self.scaledFrameResolution: Optional[Tuple[int, int]] = None
        self.currentMovementPos: Optional[PointCoords] = None
        self.pendingWriteQueue = Queue(1000)
        self.initializeLoggerDir()
        self.loggingTimer:Optional[QTimer] = None

    def initializeLoggerDir(self) -> None:
        if not os.path.exists(os.path.dirname(self.loggerParams.loggingFile)):
            os.mkdir(os.path.dirname(self.loggerParams.loggingFile))
    
    @pyqtSlot()
    def onStart(self) -> None:
        self.loggingTimer = QTimer()
        self.loggingTimer.setInterval(self.loggerParams.loggingInterval)
        self.loggingTimer.timeout.connect(self.processMovementIfPresent)
        self.loggingTimer.start()
    
    @pyqtSlot()
    def onStop(self) -> None:
        if self.loggingTimer:
            self.loggingTimer.stop()

    @pyqtSlot(dict)
    def onOriginalFrameDimensionInfoReceived(self, frameDimensionInfo: Dict) -> None:
        self.originalFrameResolution = frameDimensionInfo["resizedFrameResolution"]
        self.aspectRatio = frameDimensionInfo["aspectRatio"]
        self.scaledFrameResolution = (self.loggerParams.scalingWidth, int(self.loggerParams.scalingWidth * self.aspectRatio[1] / self.aspectRatio[0])) 
        logger.info("Scalled resolution used for logging: %s x %s", self.scaledFrameResolution[0], self.scaledFrameResolution[1])
    
    @pyqtSlot(PointCoords)
    def onMovementCoordinatesReceived(self, movement_coords: PointCoords) -> None:
        self.currentMovementPos = movement_coords
    
    @pyqtSlot()
    def processMovementIfPresent(self) -> None:
        self.flushPendingQueue()
        self.writeToLog()
            
    def writeToLog(self):
        if not self.currentMovementPos:
            return
        try:
            with open(self.loggerParams.loggingFile, "a", encoding = "ascii") as f:
                scaledCoordinates = self.processCoordinates(self.currentMovementPos)
                timestamp = datetime.now().strftime("%b_%d_%Y_%H_%M_%S")
                f.write(str(scaledCoordinates[0]) + " " + str(scaledCoordinates[1]) + " " + timestamp + "\n")
        except OSError as err:
            self.pendingWriteQueue.put(self.currentMovementPos)
        finally:
            self.currentMovementPos = None
        
    def flushPendingQueue(self):
        try:
            if not self.pendingWriteQueue.empty():
                with open(self.loggerParams.loggingFile,'a',encoding = "ascii") as f:
                    while not self.pendingWriteQueue.empty():
                        coordinates = self.pendingWriteQueue.get()
                        scaledX,scaledY = self.processCoordinates(coordinates)
                        timestamp = datetime.now().strftime("%b_%d_%Y_%H_%M_%S")
                        f.write(str(scaledX) + " " + str(scaledY) + " " + timestamp + "\n")
        except OSError as err:
            logger.error("Error appeared when trying to flush logging pending queue: %s",  str(err))
    
    def processCoordinates(self, point_coords: PointCoords):
        if not self.scaledFrameResolution or not self.originalFrameResolution:
            raise BaseException("Scaled Frame resolution or Original resolution not calculated !")
        x = point_coords[0]
        y = point_coords[1]
        newX = int(self.scaledFrameResolution[0] * x /self.originalFrameResolution[0])
        newY = int(self.scaledFrameResolution[1] * y /self.originalFrameResolution[1])
        if self.loggerParams.calculateInverse:
            newX = self.scaledFrameResolution[0] - newX
        return (newX,newY)
    
    @pyqtSlot(dict)
    def onSettingsChanged(self, settings: Dict) -> None:
        self.loggerParams = MovementLoggerParameters(
            settings["loggingInterval"],
            settings["loggingPath"],
            settings["scalingWidth"],
            settings["invertedXaxis"],
            
        )
        if self.aspectRatio:
            self.scaledFrameResolution = (self.loggerParams.scalingWidth, int(self.loggerParams.scalingWidth * self.aspectRatio[1] / self.aspectRatio[0])) 
            logger.info("New scalled resolution used for logging: %s x %s", self.scaledFrameResolution[0], self.scaledFrameResolution[1])
        if self.loggingTimer and self.loggingTimer.interval() != self.loggerParams.loggingInterval:
            self.loggingTimer.stop()
            self.loggingTimer.setInterval(self.loggerParams.loggingInterval)
            self.loggingTimer.start()

class MovementLoggerFactory:
    @classmethod
    def createMovementLogger(cls, settings_dict: Dict) -> MovementLogger:
        return MovementLogger(
            MovementLoggerParameters(
                settings_dict["loggingInterval"],
                settings_dict["loggingPath"],
                settings_dict["scalingWidth"],
                settings_dict["invertedXaxis"]
            )
        )
