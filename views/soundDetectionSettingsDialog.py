from typing import Any, Dict, Optional
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget

class SoundDetectionSettingsDialog(QtWidgets.QDialog):
    def __init__(
        self, 
        currentConfig: Dict, 
        defaultConfig: Dict,
        parent: Optional[QWidget] = None):
        super().__init__(parent)
        uic.loadUi('ui/soundDetectionSettingsDialog.ui',self)
        self.setWindowTitle("Configure Sound Detection Parameters")
        self.volumeThresholdSpinBox = self.findChild(QtWidgets.QSpinBox, 'VolumeThresholdSpinBox')
        self.enableSoundCheckBox = self.findChild(QtWidgets.QCheckBox, 'EnableSoundCheckBox')
        self.applyChangesBtn = self.findChild(QtWidgets.QPushButton, 'applyChangesBtn')
        self.cancelBtn = self.findChild(QtWidgets.QPushButton, 'cancelBtn')
        self.loadDefaultBtn = self.findChild(QtWidgets.QPushButton, 'loadDefaultBtn')
        self.defaultConfig = defaultConfig
        self.updateWidgetValues(currentConfig)
        self.setWhatsThisTips()

        self.applyChangesBtn.clicked.connect(self.onApplyChanges)
        self.cancelBtn.clicked.connect(self.onCancelBtnClicked)
        self.loadDefaultBtn.clicked.connect(self.onLoadDefaultBtnClicked)
    
    def updateWidgetValues(self, currentConfig: Dict) -> None:
        self.volumeThresholdSpinBox.setValue(-currentConfig['volumeThreshold'])
        self.enableSoundCheckBox.setChecked(currentConfig['soundDetectionEnabled'])

    def getData(self) -> Dict:
        return {
            "volumeThreshold": -self.volumeThresholdSpinBox.value(),
            "soundDetectionEnabled": self.enableSoundCheckBox.isChecked()
        }

    def onApplyChanges(self) -> None:
        self.accept()

    def onCancelBtnClicked(self) -> None:
        self.reject()
    
    def onLoadDefaultBtnClicked(self) -> None:
        self.updateWidgetValues(self.defaultConfig)
    
    def setWhatsThisTips(self) -> None:
        enableSoundInfo = 'Turning on or off the microphone sound detector.'
        volumeThresholdInfo = 'If the detected sound is above this threshold (in dB), the user would be notified.'
        self.findChild(QtWidgets.QLabel, 'EnableSoundLabel').setWhatsThis(enableSoundInfo)
        self.findChild(QtWidgets.QCheckBox, 'EnableSoundCheckBox').setWhatsThis(enableSoundInfo)
        self.findChild(QtWidgets.QLabel, 'VolumeThresholdLabel').setWhatsThis(volumeThresholdInfo)
        self.findChild(QtWidgets.QSpinBox, 'VolumeThresholdSpinBox').setWhatsThis(volumeThresholdInfo)