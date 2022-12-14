from typing import Any, Dict, Optional
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QWidget
from utils import AlgorithmType

class MotionDetectionSettingsDialog(QtWidgets.QDialog):
    def __init__(
        self, 
        currentConfig: Dict, 
        defaultConfig: Dict,
        hardDetectionConfig: Dict, 
        parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        uic.loadUi('ui/motionDetectionSettingsDialog.ui',self)
        self.setWindowTitle("Configure Motion Detection Parameters")
        self.algorithmParamsStackWidget = self.findChild(QtWidgets.QStackedWidget, 'stackedWidget')
        self.algorithmTypeComboBox = self.findChild(QtWidgets.QComboBox, 'AlgorithmTypeComboBox')
        self.gaussianBlurKernelSizeSpinBox = self.findChild(QtWidgets.QSpinBox, 'GaussianBlurKernleSizeSpinBox')
        self.thresholdBinarizationSpinBox = self.findChild(QtWidgets.QSpinBox, 'ThresholdBinarizationSpinBox')
        self.erosionKernelSizeComboBox = self.findChild(QtWidgets.QComboBox, 'ErosionKernelSizeComboBox')
        self.erosionNumOfItersSpinBox = self.findChild(QtWidgets.QSpinBox, 'ErosionNumOfItersSpinBox')
        self.dilationKernelSizeComboBox  = self.findChild(QtWidgets.QComboBox, 'DilationKernelSizeComboBox')
        self.dilationNumOfItersSpinBox = self.findChild(QtWidgets.QSpinBox, 'DilationNumOfItersSpinBox')
        self.runninAvgMinAreaSpinBox = self.findChild(QtWidgets.QSpinBox, 'RAminAreaSpinBox')
        self.runningAvgAlphaSpinBox = self.findChild(QtWidgets.QDoubleSpinBox, 'RunningAvgAlphaSpinBox')
        self.gaussianMixtureMinAreaSpinBox = self.findChild(QtWidgets.QSpinBox, 'GMMinAreaSpinBox')
        self.gaussianMixtureHistorySpinBox = self.findChild(QtWidgets.QSpinBox, 'GaussianMixtureHistorySpinBox')

        self.applyChangesBtn = self.findChild(QtWidgets.QPushButton, 'applyChangesBtn')
        self.cancelBtn = self.findChild(QtWidgets.QPushButton, 'cancelBtn')
        self.loadDefaultBtn = self.findChild(QtWidgets.QPushButton, 'loadDefaultBtn')
        self.hardDetetctionValuesBtn = self.findChild(QtWidgets.QPushButton, 'hardDetetctionValuesBtn')

        self.loadDefaultBtn.clicked.connect(self.onLoadDefaultValuesClicked)
        self.hardDetetctionValuesBtn.clicked.connect(self.onLoadHardDetetctionClicked)
        self.gaussianBlurKernelSizeSpinBox.valueChanged.connect(self.onGBlurvalueChanged)

        self.applyChangesBtn.clicked.connect(self.onApplyChanges)
        self.cancelBtn.clicked.connect(self.onCancelBtnClicked)
        self.algorithmTypeComboBox.currentIndexChanged.connect(self.onAlgorithmTypeChanged)
        self.defaultConfig = defaultConfig
        self.hardDetectionConfig = hardDetectionConfig
        self.updateWidgetValues(currentConfig)
        self.setWhatsThisTips()
    
    def updateWidgetValues(self, config: Dict) -> None:
        self.algorithmTypeComboBox.setCurrentIndex(config["backgroundSubstractionSettings"]['algorithmType'].value)
        self.gaussianBlurKernelSizeSpinBox.setValue(config['gaussianBlurKernelSize'])
        self.thresholdBinarizationSpinBox.setValue(config['backgroundSubstractionSettings']['thresholdBinValue'])
        self.erosionKernelSizeComboBox.setCurrentIndex(self.erosionKernelSizeComboBox.findText(str(config['erosionKernelSize'])))
        self.erosionNumOfItersSpinBox.setValue(config['erosionIterations'])
        self.dilationKernelSizeComboBox.setCurrentIndex(self.dilationKernelSizeComboBox.findText(str(config['dilationKernelSize'])))
        self.dilationNumOfItersSpinBox.setValue(config['dilationIterations'])
        self.runninAvgMinAreaSpinBox.setValue(config['backgroundSubstractionSettings']['runningAvgMinArea'])
        self.runningAvgAlphaSpinBox.setValue(config['backgroundSubstractionSettings']['runningAvgAlpha'])
        self.gaussianMixtureMinAreaSpinBox.setValue(config['backgroundSubstractionSettings']['gaussianMixtureMinArea'])
        self.gaussianMixtureHistorySpinBox.setValue(config['backgroundSubstractionSettings']['gaussianMixtureHistory'])
    
    def onAlgorithmTypeChanged(self, index: int) -> None:
        if index == AlgorithmType.RUNNING_AVG.value:
            self.algorithmParamsStackWidget.setCurrentIndex(AlgorithmType.RUNNING_AVG.value)
        if index == AlgorithmType.MIXTURE_OF_GAUSSIANS.value:
            self.algorithmParamsStackWidget.setCurrentIndex(AlgorithmType.MIXTURE_OF_GAUSSIANS.value)

    def getData(self) -> Dict:
        return {
            "backgroundSubstractionSettings":{
                "algorithmType": AlgorithmType(self.algorithmTypeComboBox.currentIndex()),
                "thresholdBinValue": self.thresholdBinarizationSpinBox.value(),
                "runningAvgMinArea": self.runninAvgMinAreaSpinBox.value(),
                "runningAvgAlpha": self.runningAvgAlphaSpinBox.value(),
                "gaussianMixtureMinArea": self.gaussianMixtureMinAreaSpinBox.value(),
                "gaussianMixtureHistory": self.gaussianMixtureHistorySpinBox.value()
            },
            "resizeDimension":500,
            "gaussianBlurKernelSize": self.gaussianBlurKernelSizeSpinBox.value(),
            "erosionKernelSize": int(self.erosionKernelSizeComboBox.currentText()),
            "erosionIterations": self.erosionNumOfItersSpinBox.value(),
            "dilationKernelSize": int(self.dilationKernelSizeComboBox.currentText()),
            "dilationIterations": self.dilationNumOfItersSpinBox.value()
        }
    
    def onLoadDefaultValuesClicked(self) -> None:
        self.updateWidgetValues(self.defaultConfig)
    
    def onLoadHardDetetctionClicked(self) -> None:
        self.updateWidgetValues(self.hardDetectionConfig)

    def onApplyChanges(self) -> None:
        self.accept()

    def onCancelBtnClicked(self):
        self.reject()
    
    def onGBlurvalueChanged(self, val:int) -> None:
        if val %  2 == 0:
            self.gaussianBlurKernelSizeSpinBox.setValue(val-1)
    
    def setWhatsThisTips(self) -> None:
        gaussianBlurInfo = 'Kernel dimensions (n x n) used for bluring the frame in the preprocessing.'
        thresholdBinarizationInfo = 'Threshold used after background subtraction for determining if a pixel should be considered white (movement) or black (background).'
        erosionKernelSizeInfo = 'Kernel dimensions (n x n) used for applying the erosion operation on the frame. Erosion is used for eliminating sparkles on image.'
        erosionNumOfItersInfo = 'Number of subseqvent applyment of erosion operation on the frame.'
        dilationKernelSizeInfo = 'Kernel dimensions (n x n) used for dilation operation on the frame. Dilation is used for improved connecting of the neigboring contours.'
        dilationNumOfItersInfo = 'Number of subseqvent applyment of dilation operation on the frame.'
        algorithmTypeInfo = 'Type of algorithm used for background subtraction.'
        rAminAreaInfo = 'Minimum area used by Running Average algorithm for determination if some change on frame is considered to be a movement.'
        runningAvgAlphaInfo = 'Floating value between 0 and 1 for setting the adaptation factor of Runnin Average algorithm. The lower the value, the backround is updated more slowly.'
        gMMinAreaInfo = 'Minimum area used by Gaussian Mixture Model algorithm for determination if some change on frame is considered to be a movement.'
        gaussianMixtureHistoryInfo = "N last frames used by Gaussian mixture algorithm for modeling the background."
        self.findChild(QtWidgets.QLabel, 'GaussianBlurKernleSizeLabel').setWhatsThis(gaussianBlurInfo)
        self.findChild(QtWidgets.QSpinBox, 'GaussianBlurKernleSizeSpinBox').setWhatsThis(gaussianBlurInfo)
        self.findChild(QtWidgets.QLabel, 'ThresholdBinarizationLabel').setWhatsThis(thresholdBinarizationInfo)
        self.findChild(QtWidgets.QSpinBox, 'ThresholdBinarizationSpinBox').setWhatsThis(thresholdBinarizationInfo)
        self.findChild(QtWidgets.QLabel, 'ErosionKernelSizeLabel').setWhatsThis(erosionKernelSizeInfo)
        self.findChild(QtWidgets.QComboBox, 'ErosionKernelSizeComboBox').setWhatsThis(erosionKernelSizeInfo)
        self.findChild(QtWidgets.QLabel, 'ErosionNumOfItersLabel').setWhatsThis(erosionNumOfItersInfo)
        self.findChild(QtWidgets.QSpinBox, 'ErosionNumOfItersSpinBox').setWhatsThis(erosionNumOfItersInfo)
        self.findChild(QtWidgets.QLabel, 'DilationKernelSizeLabel').setWhatsThis(dilationKernelSizeInfo)
        self.findChild(QtWidgets.QComboBox, 'DilationKernelSizeComboBox').setWhatsThis(dilationKernelSizeInfo)
        self.findChild(QtWidgets.QLabel, 'DilationNumOfItersLabel').setWhatsThis(dilationNumOfItersInfo)
        self.findChild(QtWidgets.QSpinBox, 'DilationNumOfItersSpinBox').setWhatsThis(dilationNumOfItersInfo)
        self.findChild(QtWidgets.QLabel, 'AlgorithTypeLabel').setWhatsThis(algorithmTypeInfo)
        self.findChild(QtWidgets.QComboBox, 'AlgorithmTypeComboBox').setWhatsThis(algorithmTypeInfo)
        self.findChild(QtWidgets.QLabel, 'RAminAreaLabel').setWhatsThis(rAminAreaInfo)
        self.findChild(QtWidgets.QSpinBox, 'RAminAreaSpinBox').setWhatsThis(rAminAreaInfo)
        self.findChild(QtWidgets.QLabel, 'RunningAvgAlphaLabel').setWhatsThis(runningAvgAlphaInfo)
        self.findChild(QtWidgets.QDoubleSpinBox, 'RunningAvgAlphaSpinBox').setWhatsThis(runningAvgAlphaInfo)
        self.findChild(QtWidgets.QLabel, 'GMMinAreaLabel').setWhatsThis(gMMinAreaInfo)
        self.findChild(QtWidgets.QSpinBox, 'GMMinAreaSpinBox').setWhatsThis(gMMinAreaInfo)
        self.findChild(QtWidgets.QLabel, 'GaussianMixtureHistoryLabel').setWhatsThis(gaussianMixtureHistoryInfo)
        self.findChild(QtWidgets.QSpinBox, 'GaussianMixtureHistorySpinBox').setWhatsThis(gaussianMixtureHistoryInfo)