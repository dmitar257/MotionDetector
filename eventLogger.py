from dataclasses import dataclass
from datetime import datetime
import logging
import os
from queue import Queue
from typing import Dict, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSlot, QTimer

from utils import PointCoords

logger = logging.getLogger(__name__)
LOG_FILE_NAME = "log.txt"
PENDING_QUEUE_SIZE = 1000

@dataclass
class EventLoggerParameters:
    loggingInterval: int
    loggingFile: str
    scalingWidth: int = 800
    calculateInverse: bool = False
    useOneLineLogs: bool = False
    
class EventLogger(QObject):
    def __init__(self, eventLoggerParams: EventLoggerParameters) -> None:
        super().__init__()
        self.loggerParams = eventLoggerParams
        self.originalFrameResolution: Optional[Tuple[int, int]] = None
        self.aspectRatio: Optional[Tuple[int, int]] = None
        self.scaledFrameResolution: Optional[Tuple[int, int]] = None
        self.currentMovementPos: Optional[PointCoords] = None
        self.currentSoundIntensity: int = -1
        self.pendingWriteQueue = Queue(PENDING_QUEUE_SIZE)
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
    
    @pyqtSlot(bool, int)
    def onSoundDetectedReceived(self, isSoundDetected:bool, soundIntesinty: int) -> None:
        if isSoundDetected:
            self.currentSoundIntensity = soundIntesinty
    
    @pyqtSlot()
    def processMovementIfPresent(self) -> None:
        self.flushPendingQueue()
        self.writeToLog()
            
    def writeToLog(self):
        if not self.currentMovementPos and self.currentSoundIntensity == -1:
            return
        log_entry = ""
        try:
            writing_mode = "w" if self.loggerParams.useOneLineLogs else "a"
            with open(os.path.join(self.loggerParams.loggingFile, LOG_FILE_NAME), writing_mode, encoding = "ascii") as f:
                timestamp = datetime.now().strftime("%b_%d_%Y_%H_%M_%S")
                log_entry = self.__create_log_entry(timestamp)
                f.write(log_entry)
        except OSError as err:
            logger.warning("Error when trying to write entry to log file, err details: %s", err)
            if log_entry:
                self.pendingWriteQueue.put(log_entry)
        finally:
            self.currentMovementPos = None
            self.currentSoundIntensity = -1
    
    def flushPendingQueue(self) -> None:
        try:
            if not self.pendingWriteQueue.empty():
                writing_mode = "w" if self.loggerParams.useOneLineLogs else "a"
                with open(os.path.join(self.loggerParams.loggingFile, LOG_FILE_NAME), writing_mode, encoding = "ascii") as f:
                    if self.loggerParams.useOneLineLogs:
                        log_entry = self.pendingWriteQueue.get()
                        f.write(log_entry)
                    else:                        
                        while not self.pendingWriteQueue.empty():
                            log_entry = self.pendingWriteQueue.get()
                            f.write(log_entry)
        except OSError as err:
            logger.error("Error appeared when trying to flush logging pending queue. Error details: %s",  str(err))
        finally:
            while not self.pendingWriteQueue.empty():
                self.pendingWriteQueue.get()

    def __create_log_entry(self, timestamp: str) -> str:
        res_str = ""
        if self.currentSoundIntensity != -1:
            res_str += f"sound -{self.currentSoundIntensity}dB {timestamp} \n"
        if self.currentMovementPos:
            scaledX,scaledY = self.processCoordinates(self.currentMovementPos)
            res_str += f"video {scaledX} {scaledY} {timestamp} \n"
        return res_str
    
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
        self.loggerParams = EventLoggerParameters(
            settings["loggingInterval"],
            settings["loggingPath"],
            settings["scalingWidth"],
            settings["invertedXaxis"],
            settings["oneLineLog"]
            
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
    def createMovementLogger(cls, settings_dict: Dict) -> EventLogger:
        return EventLogger(
            EventLoggerParameters(
                settings_dict["loggingInterval"],
                settings_dict["loggingPath"],
                settings_dict["scalingWidth"],
                settings_dict["invertedXaxis"],
                settings_dict["oneLineLog"]
            )
        )
