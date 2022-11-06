from typing import Any, Dict, Optional
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget

class ObjectDetectionSettingsDialog(QtWidgets.QDialog):
    def __init__(
        self, 
        currentConfig: Dict, 
        defaultConfig: Dict,
        parent: Optional[QWidget] = None):
        super().__init__(parent)
        uic.loadUi('ui/objectDetectionSettingsDialog.ui',self)
        self.setWindowTitle("Configure Object Detection Parameters")
        self.confidenceThresholdSpinBox = self.findChild(QtWidgets.QDoubleSpinBox, 'ConfidenceThresholdSpinBox')
        self.enableObjectDetectionCheckBox = self.findChild(QtWidgets.QCheckBox, 'EnableObjectDetectionCheckBox')
        self.applyChangesBtn = self.findChild(QtWidgets.QPushButton, 'applyChangesBtn')
        self.cancelBtn = self.findChild(QtWidgets.QPushButton, 'cancelBtn')
        self.loadDefaultBtn = self.findChild(QtWidgets.QPushButton, 'loadDefaultBtn')
        self.defaultConfig = defaultConfig
        self.updateWidgetValues(currentConfig)
        self.setWhatsThisTips()

        self.applyChangesBtn.clicked.connect(self.onApplyChanges)
        self.cancelBtn.clicked.connect(self.onCancelBtnClicked)
        self.loadDefaultBtn.clicked.connect(self.onLoadDefaultBtnClicked)
    
    def updateWidgetValues(self, config: Dict) -> None:
        self.confidenceThresholdSpinBox.setValue(config['confidenceThreshold'])
        self.enableObjectDetectionCheckBox.setChecked(config['detectionEnabled'])

    def getData(self) -> Dict:
        return {
            "confidenceThreshold": self.confidenceThresholdSpinBox.value(),
            "detectionEnabled": self.enableObjectDetectionCheckBox.isChecked()
        }

    def onApplyChanges(self) -> None:
        self.accept()

    def onCancelBtnClicked(self) -> None:
        self.reject()
    
    def onLoadDefaultBtnClicked(self) -> None:
        self.updaconfidenceThresholdteWidgetValues(self.defaultConfig)
    
    def setWhatsThisTips(self) -> None:
        enableObjectDetectionInfo = 'Turning on or off the object detection. If turned on, object detection would be activated when continuous motion is detected'
        confidenceThresholdInfo = 'Only objects for which the algorithm calculated confidence higher or equal to this probability value would be displayed'
        self.findChild(QtWidgets.QLabel, 'EnableObjectDetectionLabel').setWhatsThis(enableObjectDetectionInfo)
        self.findChild(QtWidgets.QCheckBox, 'EnableObjectDetectionCheckBox').setWhatsThis(enableObjectDetectionInfo)
        self.findChild(QtWidgets.QLabel, 'ConfidenceThresholdLabel').setWhatsThis(confidenceThresholdInfo)
        self.findChild(QtWidgets.QDoubleSpinBox, 'ConfidenceThresholdSpinBox').setWhatsThis(confidenceThresholdInfo)