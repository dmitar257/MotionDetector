from dataclasses import dataclass
from typing import Tuple
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QMutexLocker
import numpy as np


class NoVideoInputError(Exception):
    pass

class FrameFetchingRuntimeError(Exception):
    pass

@dataclass
class FrameFetcherSettings:
    cameraIndex:int

class FrameFetcher(QObject):
    frameFetched = pyqtSignal(np.ndarray)
    frameResolutionFetched = pyqtSignal(tuple)
    noInputFoundError = pyqtSignal()
    frameFetchingRunntimeError = pyqtSignal(str)

    def __init__(self, fetcherSettings: FrameFetcherSettings):
        super().__init__()
        self.running = False
        self.runningMutex = QMutex()
        self.settings = fetcherSettings 
    
    def startCapturingFrames(self) -> None:
        pass
    
    def stopRunning(self) -> None:
        with QMutexLocker(self.runningMutex):
            self.running = False
    
    def isRunning(self) -> bool:
        with QMutexLocker(self.runningMutex):
            return self.running

    @pyqtSlot()
    def onStartSignalReceived(self) -> None:
        self.startCapturingFrames()
    
    @pyqtSlot(FrameFetcherSettings)
    def onFrameFetcherSettingsChanged(self, new_settings: FrameFetcherSettings) -> None:
        pass
