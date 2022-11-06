from dataclasses import dataclass
from typing import Dict
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer

@dataclass
class MovementTrackerParameters:
    movementPresentThreshold: int
    movementAbsenceThreshold:int
    inactivityToleranceThreshold: int = 1000


class MovementTracker(QObject):
    movementContinouslyPresent = pyqtSignal(bool)

    def __init__(self, movementTrackerParams: MovementTrackerParameters) -> None:
        super().__init__()
        self.isMovementContinouslyPresent = False
        self.params = movementTrackerParams
        self.movementContinuouslyPresentTimer = QTimer()
        self.movementAbsentTimer = QTimer()
        self.inactivityToleranceTimer = QTimer()
        self.initializeTimers()

    def initializeTimers(self) -> None: 
        self.movementContinuouslyPresentTimer.setInterval(self.params.movementPresentThreshold)
        self.inactivityToleranceTimer.setInterval(self.params.inactivityToleranceThreshold)
        self.movementAbsentTimer.setInterval(self.params.movementAbsenceThreshold)
        self.movementContinuouslyPresentTimer.timeout.connect(self.onContinousMovementDetected)
        self.inactivityToleranceTimer.timeout.connect(self.onInactivityToleranceBreached)
        self.movementAbsentTimer.timeout.connect(self.onContinuosMovementStoped)
        self.movementContinuouslyPresentTimer.setSingleShot(True)
        self.movementAbsentTimer.setSingleShot(True)
        self.inactivityToleranceTimer.setSingleShot(True)    

    def stopTimers(self) -> None:
        self.movementContinuouslyPresentTimer.stop()
        self.movementAbsentTimer.stop()
        self.inactivityToleranceTimer.stop()
        self.isMovementContinouslyPresent = False
        self.movementContinouslyPresent.emit(False)

    @pyqtSlot()
    def onContinousMovementDetected(self) -> None:
        self.isMovementContinouslyPresent = True
        self.movementContinouslyPresent.emit(True)
    
    @pyqtSlot()
    def onInactivityToleranceBreached(self) -> None:
        self.movementContinuouslyPresentTimer.stop()

    @pyqtSlot()
    def onContinuosMovementStoped(self) -> None:
        self.isMovementContinouslyPresent = False
        self.movementContinouslyPresent.emit(False)

    @pyqtSlot(bool)
    def onMovementPresentToggled(self, movementPresent:bool) -> None:
        if movementPresent:
            if self.movementAbsentTimer.isActive():
                self.movementAbsentTimer.stop()
            if self.isMovementContinouslyPresent:
                return
            if not self.movementContinuouslyPresentTimer.isActive():
                self.movementContinuouslyPresentTimer.start()
            if self.inactivityToleranceTimer.isActive():
                self.inactivityToleranceTimer.stop()
        else:
            if not self.isMovementContinouslyPresent and not self.inactivityToleranceTimer.isActive():
                self.inactivityToleranceTimer.start()
            if self.isMovementContinouslyPresent and not self.movementAbsentTimer.isActive():
                self.movementAbsentTimer.start()
    
    @pyqtSlot(dict)
    def onSettingsChanged(self, new_settings: Dict) -> None:
        self.stopTimers()
        new_params = MovementTrackerParameters(
            new_settings["movementPresentThreshold"],
            new_settings["movementAbsenceThreshold"]
        )
        self.params = new_params
        self.initializeTimers()

class MovementTrackerFactory:
    @classmethod
    def createMovementTracker(cls, settings_dict: Dict) -> MovementTracker:
        return MovementTracker(
            MovementTrackerParameters(
                settings_dict["movementPresentThreshold"],
                settings_dict["movementAbsenceThreshold"]
            )
        )



            
            



