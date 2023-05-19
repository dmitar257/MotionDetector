from typing import Dict, Optional
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget

class MotionLoggingSettingsDialog(QtWidgets.QDialog):
    def __init__(
        self, 
        currentConfig: Dict,
        defaultConfig: Dict, 
        parent: Optional[QWidget] = None):
        super().__init__(parent)
        uic.loadUi('ui/motionLoggerSettingsDialog.ui',self)
        self.setWindowTitle("Configure Motion Logging Parameters")
        self.loggingIntervalSpinBox = self.findChild(QtWidgets.QSpinBox, 'loggingIntervalSpinBox')
        self.scalingWidthComboBox = self.findChild(QtWidgets.QComboBox,'scalingWidthComboBox')
        self.invertedAxisCheckBox = self.findChild(QtWidgets.QCheckBox,'invertedXaxisCheckBox')
        self.logFilePathLineEdit = self.findChild(QtWidgets.QLineEdit,'logFilePathLineEdit')
        self.browseFilesBtn = self.findChild(QtWidgets.QPushButton,'browseFilesPushButton')
        self.oneLineCheckBox = self.findChild(QtWidgets.QCheckBox,'oneLineCheckBox')
        self.acceptBtn = self.findChild(QtWidgets.QPushButton,'acceptButton')
        self.cancelButton = self.findChild(QtWidgets.QPushButton,'cancelButton')
        self.loadDefaultBtn = self.findChild(QtWidgets.QPushButton, 'loadDefaultBtn')
        self.acceptBtn.clicked.connect(self.onApplyBtnClicked)
        self.cancelButton.clicked.connect(self.onCancelBtnClicked)
        self.browseFilesBtn.clicked.connect(self.onBrowseFoldersBtnClicked)
        self.loadDefaultBtn.clicked.connect(self.onLoadDefaultBtnClicked)
        self.defaultConfig = defaultConfig
        self.updateWidgetValues(currentConfig)
        self.setWhatsThisTips()
    
    def updateWidgetValues(self, current_config: Dict) -> None:
        self.loggingIntervalSpinBox.setValue(current_config['loggingInterval'])
        self.scalingWidthComboBox.setCurrentIndex(self.scalingWidthComboBox.findText(str(current_config['scalingWidth'])))
        self.invertedAxisCheckBox.setChecked(current_config['invertedXaxis'])
        self.logFilePathLineEdit.setText(current_config['loggingPath'])
        self.oneLineCheckBox.setChecked(current_config['oneLineLog'])

    
    def getData(self) -> Dict:
        return{
            'loggingInterval': self.loggingIntervalSpinBox.value(),
            'scalingWidth': int(self.scalingWidthComboBox.currentText()),
            'invertedXaxis': self.invertedAxisCheckBox.isChecked(),
            'loggingPath': self.logFilePathLineEdit.text(),
            'oneLineLog': self.oneLineCheckBox.isChecked()
        }

    def onBrowseFoldersBtnClicked(self):
        file = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        if file:
            self.logFilePathLineEdit.setText(file)

    def onApplyBtnClicked(self):
        self.accept()

    def onCancelBtnClicked(self):
        self.reject()
    
    def onLoadDefaultBtnClicked(self) -> None:
        self.updateWidgetValues(self.defaultConfig)
    
    def setWhatsThisTips(self) -> None:
        loggingIntervalInfo = "The app will periodically check for movement after this interval expires, and if it is present the movement center of the mass coordinates would be logged in log file."
        scalingWidthInfo = 'The logging width of screen.'
        invertedXaxisInfo = 'Wheather or not the 0 x value begins on left, or on right.'
        logFilePathInfo = 'Location on disc where logging file would be stored'
        oneLineLogInfo = 'If checked, log file will contain only last movement, othervise it would contain previous movement info'
        self.findChild(QtWidgets.QLabel, 'loggingIntervalLabel').setWhatsThis(loggingIntervalInfo)
        self.findChild(QtWidgets.QSpinBox, 'loggingIntervalSpinBox').setWhatsThis(loggingIntervalInfo)
        self.findChild(QtWidgets.QLabel, 'scalingWidthLabel').setWhatsThis(scalingWidthInfo)
        self.findChild(QtWidgets.QComboBox,'scalingWidthComboBox').setWhatsThis(scalingWidthInfo)
        self.findChild(QtWidgets.QLabel, 'invertedXaxisLabel').setWhatsThis(invertedXaxisInfo)
        self.findChild(QtWidgets.QCheckBox,'invertedXaxisCheckBox').setWhatsThis(invertedXaxisInfo)
        self.findChild(QtWidgets.QLabel, 'logFilePathLabel').setWhatsThis(logFilePathInfo)
        self.findChild(QtWidgets.QLineEdit,'logFilePathLineEdit').setWhatsThis(logFilePathInfo)
        self.findChild(QtWidgets.QLabel, 'oneLineLabel').setWhatsThis(oneLineLogInfo)
        self.findChild(QtWidgets.QCheckBox,'oneLineCheckBox').setWhatsThis(oneLineLogInfo)


