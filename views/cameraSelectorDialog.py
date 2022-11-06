from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, pyqtSlot
from PyQt5.QtGui import QMovie

class SelectCameraDialog(QtWidgets.QDialog):
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        uic.loadUi('ui/selectCameraDialog.ui',self)
        self.setWindowTitle("Choose camera input")
        self.stackWidget = self.findChild(QtWidgets.QStackedWidget, 'stackedWidget')
        self.applyChangesBtn = self.findChild(QtWidgets.QPushButton, 'selectCameraButton')
        self.cancelBtn = self.findChild(QtWidgets.QPushButton, 'cancelButton')
        self.selectCameraComboBox = self.findChild(QtWidgets.QComboBox,'cameraDevicesComboBox')
        self.loadingLabel = self.findChild(QtWidgets.QLabel, 'loadingLabel')
        self.stackWidget.setCurrentIndex(0)
        self.applyChangesBtn.clicked.connect(self.onApplyBtnClicked)
        self.cancelBtn.clicked.connect(self.onCancelBtnClicked)
        movie = QMovie("resources/loading.gif")
        self.loadingLabel.setMovie(movie)
        movie.start()
    
    @pyqtSlot(list)
    def onCameraInfoAcquired(self, cameraInfo):
        self.stackWidget.setCurrentIndex(1)
        for cam in cameraInfo:
            self.selectCameraComboBox.addItem("Camera input {} ({} x {})".format(cam["index"],cam["frameWidth"],cam["frameHeight"]))
        self.selectCameraComboBox.setCurrentIndex(0)
    
    def getData(self):
        return {
            "cameraIndex":self.selectCameraComboBox.currentIndex()
        }

    def onApplyBtnClicked(self):
        self.accept()

    def onCancelBtnClicked(self):
        self.reject()