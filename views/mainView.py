from enum import Enum
from typing import Any, Dict, List
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import  pyqtSlot, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QImage, QPixmap
from views.addEmailSubscriberDialog import AddEmailSubscriberDialog
from views.cameraSelectorDialog import SelectCameraDialog
from views.motionDetectionSettingsDialog import MotionDetectionSettingsDialog
import logging
from views.motionRecordingSettingsDialog import MotionRecordingSettingsDialog
from views.movementLoggerSettingsDialog import MotionLoggingSettingsDialog
from settingsManager import SettingsManager
from views.objectionDetectionSettingsDialog import ObjectDetectionSettingsDialog
from views.soundDetectionSettingsDialog import SoundDetectionSettingsDialog
from utils import MovementPresentationType

logger = logging.getLogger(__name__)

class StackWidgetPage(Enum):
  CAMERA = 0
  PREVIEW_FRAMES = 2

class MainView(QtWidgets.QMainWindow):

    closingWindow = pyqtSignal()
    toogleShowPreviewFrames = pyqtSignal(bool)
    cameraInfoListReceived = pyqtSignal(list)
    startFetchingCameraInfo = pyqtSignal()
    toggleMovementDisplayType = pyqtSignal(MovementPresentationType, bool)

    def __init__(self, settingsManger: SettingsManager):
        super(MainView, self).__init__()
        self.settingsManger = settingsManger
        self.setupUI()

    def setupUI(self) -> None:
        self.setWindowIcon(QIcon('resources/icon.png')) 
        uic.loadUi('ui/mainwindow.ui', self)
        self.cameraCanvasLabel = self.getUiElement(QtWidgets.QLabel, 'cameraCanvas')
        self.viewFramesAction = self.getUiElement(QtWidgets.QAction, 'actionFrameChangeProcess')
        self.stackWidget = self.getUiElement(QtWidgets.QStackedWidget, 'stackedWidget')
        self.cameraAction = self.getUiElement(QtWidgets.QAction, 'actionCamera')
        self.originalFrameLabel  = self.getUiElement(QtWidgets.QLabel, 'previewFrameLabel1')
        self.grayBluredFrameLabel  = self.getUiElement(QtWidgets.QLabel, 'previewFrameLabel2')
        self.subAndThresholdFrameLabel  = self.getUiElement(QtWidgets.QLabel, 'previewFrameLabel3')
        self.erodeAndDilatedFrameLabel  = self.getUiElement(QtWidgets.QLabel, 'previewFrameLabel4')
        self.actionMotionDetectionParams = self.findChild(QtWidgets.QAction, 'actionMotionDetectionParams')
        self.actionMotionRecordingParams = self.findChild(QtWidgets.QAction, 'actionMotionRecordingParameters')
        self.actionSoundDetectionParams = self.findChild(QtWidgets.QAction, 'actionSoundDetectionParameters')
        self.actionObjectDetectionParameters = self.findChild(QtWidgets.QAction, 'actionObjectDetectionParameters')
        self.actionMotionLoggingParams = self.findChild(QtWidgets.QAction, 'actionMotionLoggingParameters')
        self.actionSelectCamera = self.findChild(QtWidgets.QAction, 'actionSelectCamera')
        self.actionAddEmailSubscription = self.findChild(QtWidgets.QAction, 'actionAddEmailSubscriber')
        self.rectangleAction = self.findChild(QtWidgets.QAction, 'actionRectangles')
        self.contourAction = self.findChild(QtWidgets.QAction, 'actionContours')
        self.crosshairAction = self.findChild(QtWidgets.QAction, 'actionCrosshair')

        self.cameraCanvasLabel.setScaledContents(True)
        self.originalFrameLabel.setScaledContents(True)
        self.grayBluredFrameLabel.setScaledContents(True)
        self.subAndThresholdFrameLabel.setScaledContents(True)
        self.erodeAndDilatedFrameLabel.setScaledContents(True)
        self.viewFramesAction.triggered.connect(self.onShowPreviewFramesToggled)
        self.actionMotionDetectionParams.triggered.connect(self.onDetectionParamsActionClicked)
        self.actionMotionRecordingParams.triggered.connect(self.onDetectionRecordingsParamsActionClicked)
        self.actionSoundDetectionParams.triggered.connect(self.onSoundDetectionParamsActionClicked)
        self.actionObjectDetectionParameters.triggered.connect(self.onObjectDetectionParamsActionClicked)
        self.actionMotionLoggingParams.triggered.connect(self.onMotionLoggingParamsActionClicked)
        self.actionSelectCamera.triggered.connect(self.onSelectCameraActionClicked)
        self.actionAddEmailSubscription.triggered.connect(self.onActionAddEmailSubscriptionClicked)
        self.rectangleAction.triggered.connect(self.onRectanglesActionToggled)
        self.contourAction.triggered.connect(self.onContourActionToggled)
        self.crosshairAction.triggered.connect(self.onCrosshairActionToggled)

    @pyqtSlot(QImage)
    def onImageReceived(self, frame: QImage) -> None:
        if self.stackWidget.currentIndex() == StackWidgetPage.CAMERA.value:
            self.cameraCanvasLabel.setPixmap(QPixmap.fromImage(frame))
    
    @pyqtSlot(dict)
    def onPreviewImagesReceived(self, preview_imgs_dict: Dict[str, QImage] ) -> None:
        if self.stackWidget.currentIndex()  == StackWidgetPage.PREVIEW_FRAMES.value:
            self.originalFrameLabel.setPixmap(QPixmap.fromImage(preview_imgs_dict["originalFrame"]))
            self.grayBluredFrameLabel.setPixmap(QPixmap.fromImage(preview_imgs_dict["grayAndBluredFrame"]))
            self.subAndThresholdFrameLabel.setPixmap(QPixmap.fromImage(preview_imgs_dict["thresholdedFrame"]))
            self.erodeAndDilatedFrameLabel.setPixmap(QPixmap.fromImage(preview_imgs_dict["erodedAndDilatedFrame"]))
        
    @pyqtSlot(bool)
    def onShowPreviewFramesToggled(self, checked: bool) -> None:
        self.toogleShowPreviewFrames.emit(checked)
        if checked:
            self.stackWidget.setCurrentIndex(StackWidgetPage.PREVIEW_FRAMES.value)
        else:
            self.stackWidget.setCurrentIndex(StackWidgetPage.CAMERA.value)

    def closeEvent(self, event):
        self.closingWindow.emit()
        event.accept()
    
    def getUiElement(self, element_type: Any, element_name: str) -> QObject:
        gui_element = self.findChild(element_type, element_name)
        if gui_element:
            return gui_element
        raise BaseException(f"Can not find {element_name} ui element !")
    
    def onDetectionParamsActionClicked(self) -> None:
        motionDetectionSettingsDialog = MotionDetectionSettingsDialog(
            self.settingsManger.getFrameTransformationSettings(),
            self.settingsManger.getFrameTransformationSettings(True),
            self.settingsManger.getHardDetectionFrameTransformationSettings()
            )
        if motionDetectionSettingsDialog.exec_():
            response = motionDetectionSettingsDialog.getData()
            self.settingsManger.setFrameTransformationSettings(response)
    
    def onDetectionRecordingsParamsActionClicked(self) -> None:
        motionRecordingSettingsDialog = MotionRecordingSettingsDialog(
            self.settingsManger.getMovementTrackerSettings(),
            self.settingsManger.getMovementTrackerSettings(True)
            )
        if motionRecordingSettingsDialog.exec_():
            response = motionRecordingSettingsDialog.getData()
            self.settingsManger.setFrameRecordingSettings(response)

    def onSoundDetectionParamsActionClicked(self) -> None:
        soundDetectionSettingsDialog = SoundDetectionSettingsDialog(
            self.settingsManger.getSoundDetectionSettings(),
            self.settingsManger.getSoundDetectionSettings(True)
            )
        if soundDetectionSettingsDialog.exec_():
            response = soundDetectionSettingsDialog.getData()
            self.settingsManger.setSoundDetectionSettings(response)
    
    def onObjectDetectionParamsActionClicked(self) -> None:
        objectDetectionSettingsDialog = ObjectDetectionSettingsDialog(
            self.settingsManger.getObjectDetectionSettings(),
            self.settingsManger.getObjectDetectionSettings(True))
        if objectDetectionSettingsDialog.exec_():
            response = objectDetectionSettingsDialog.getData()
            self.settingsManger.setObjectDetectionSettings(response)

    def onMotionLoggingParamsActionClicked(self) -> None:
        motionLoggingSettingsDialog = MotionLoggingSettingsDialog(
            self.settingsManger.getMovementLoggerSettingss(),
            self.settingsManger.getMovementLoggerSettingss(True))
        if motionLoggingSettingsDialog.exec_():
            response = motionLoggingSettingsDialog.getData()
            self.settingsManger.setMovementLoggerSettings(response)
    
    def onSelectCameraActionClicked(self) -> None:
        selectCameraDialog = SelectCameraDialog()
        selectCameraDialog.setModal(True)
        self.cameraInfoListReceived.connect(selectCameraDialog.onCameraInfoAcquired)
        self.startFetchingCameraInfo.emit()
        settings = self.settingsManger.getCameraSettings()
        self.clearImages()
        if selectCameraDialog.exec_():
            settings = selectCameraDialog.getData()
        self.settingsManger.setCameraSettings(settings)

    def clearImages(self) -> None:
        self.cameraCanvasLabel.clear()
        self.originalFrameLabel.clear() 
        self.grayBluredFrameLabel.clear() 
        self.subAndThresholdFrameLabel.clear() 
        self.erodeAndDilatedFrameLabel.clear()         

    @pyqtSlot(list)   
    def onListOfCamerasReceived(self, listOfCameraDevices: List)-> None:
        self.cameraInfoListReceived.emit(listOfCameraDevices)
    
    @pyqtSlot()
    def onActionAddEmailSubscriptionClicked(self) -> None:
        addEmailSubscriptionDialog = AddEmailSubscriberDialog()
        if addEmailSubscriptionDialog.exec_():
            subscriberData = addEmailSubscriptionDialog.getData()
            self.settingsManger.addEmailSubscription(subscriberData)
    
    @pyqtSlot()
    def onNoFrameInputFound(self) -> None:
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("No camera input detected")
        msg.setInformativeText("Could not find input device to take frames from. Please select working camera.")
        msg.setWindowTitle("Input error")
        msg.exec_()

    @pyqtSlot(str)
    def onSoundDetectionError(self, msgStr: str) -> None:
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("Sound detection error")
        msg.setInformativeText(msgStr)
        msg.setWindowTitle("Input error")
        msg.exec_()

    @pyqtSlot(bool)
    def onContourActionToggled(self, toggled: bool) -> None:
        self.toggleMovementDisplayType.emit(MovementPresentationType.CONTOUR, toggled)           

    @pyqtSlot(bool)
    def onRectanglesActionToggled(self, toggled: bool) -> None:
        self.toggleMovementDisplayType.emit(MovementPresentationType.RECTANGLE, toggled)             
    
    @pyqtSlot(bool)
    def onCrosshairActionToggled(self, toggled: bool) -> None:
        self.toggleMovementDisplayType.emit(MovementPresentationType.CROSSHAIR, toggled)       