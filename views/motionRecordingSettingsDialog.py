from typing import Any, Dict, Optional
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget

class MotionRecordingSettingsDialog(QtWidgets.QDialog):
    def __init__(
        self, 
        currentConfig: Dict, 
        defaultConfig: Dict,
        parent: Optional[QWidget] = None):
        super().__init__(parent)
        uic.loadUi('ui/motionRecordingSettingsDialog.ui',self)
        self.setWindowTitle("Configure Motion Recording Parameters")
        self.movementPresentThresholdSpinBox = self.findChild(QtWidgets.QSpinBox, 'MovementPresentThresholdSpinBox')
        self.movementAbsenceThresholdSpinBox = self.findChild(QtWidgets.QSpinBox, 'MovementAbsenceThresholdSpinBox')
        self.recordingLocationLineEdit = self.findChild(QtWidgets.QLineEdit, 'RecordingLocationLineEdit')
        self.applyChangesBtn = self.findChild(QtWidgets.QPushButton, 'applyChangesBtn')
        self.cancelBtn = self.findChild(QtWidgets.QPushButton, 'cancelBtn')
        self.browseRecordingFileBtn = self.findChild(QtWidgets.QPushButton, 'BrowseFoldersBtn')
        self.loadDefaultBtn = self.findChild(QtWidgets.QPushButton, 'loadDefaultBtn')

        self.applyChangesBtn.clicked.connect(self.onApplyChanges)
        self.cancelBtn.clicked.connect(self.onCancelBtnClicked)
        self.browseRecordingFileBtn.clicked.connect(self.onBrowseFoldersBtnClicked)
        self.loadDefaultBtn.clicked.connect(self.onLoadDefaultBtnClicked)
        self.defaultConfig = defaultConfig
        self.setWhatsThisTips()
        self.updateWidgetValues(currentConfig)

    def updateWidgetValues(self, config: Dict) -> None:
        self.movementPresentThresholdSpinBox.setValue(int(config['movementPresentThreshold'] / 1000))
        self.movementAbsenceThresholdSpinBox.setValue(int(config['movementAbsenceThreshold'] / 1000))
        self.recordingLocationLineEdit.setText(config['recordingsDir'])
    
    def getData(self) -> Dict:
        return {
            "movementPresentThreshold": self.movementPresentThresholdSpinBox.value() * 1000,
            "movementAbsenceThreshold": self.movementAbsenceThresholdSpinBox.value() * 1000,
            "recordingsDir": self.recordingLocationLineEdit.text()
        }
    
    def onApplyChanges(self) -> None:
        self.accept()

    def onCancelBtnClicked(self) -> None:
        self.reject()

    def onBrowseFoldersBtnClicked(self) -> None:
        file = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        if file:
            self.recordingLocationLineEdit.setText(file)
    
    def onLoadDefaultBtnClicked(self) -> None:
        self.updateWidgetValues(self.defaultConfig)
    
    def setWhatsThisTips(self) -> None:
        movementDetectionIntervalInfo = "If the movement is contuously present during this time interval (in seconds), even with short breaks, the application will start recording stream from camera on disc."
        recordingTimerInfo = 'After the recording has started, if the movement is not present during this time interval, the app would stop recording.'
        recordingLocationINfo = 'The location on disc on which the app will use for storing the recordings.'
        self.findChild(QtWidgets.QLabel, 'MovementPresentLabel').setWhatsThis(movementDetectionIntervalInfo)
        self.findChild(QtWidgets.QSpinBox, 'MovementPresentThresholdSpinBox').setWhatsThis(movementDetectionIntervalInfo)
        self.findChild(QtWidgets.QLabel, 'MovementAbsentThresholdLabel').setWhatsThis(recordingTimerInfo)
        self.findChild(QtWidgets.QSpinBox, 'MovementAbsenceThresholdSpinBox').setWhatsThis(recordingTimerInfo)
        self.findChild(QtWidgets.QLabel, 'RecordingLocationLabel').setWhatsThis(recordingLocationINfo)
        self.findChild(QtWidgets.QLineEdit, 'RecordingLocationLineEdit').setWhatsThis(recordingLocationINfo)
            
