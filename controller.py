import logging
from typing import Dict, List, Optional
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QImage
from cameraSelector import CameraInfoFetcher
from emailSubscribersController import EmailSubscribersController, GifCreator
from frame_processors.frameDrawer import FrameDrawer
from frame_processors.frameFetcher import FrameFetcher, FrameFetcherSettings
from frame_processors.frameFetcherFactory import FrameFetcherFactory
from frameToNetworkStreamer import FrameToNetworkStreamer
from frame_processors.frameTransformator import ContoursInfo, FrameTransforamtorFactory, FrameTransformator
from frame_processors.objectDetector import ObjectDetectionSettings, ObjectDetector
from movementLogger import MovementLogger, MovementLoggerFactory
from movementRecorder import MovementRecorder
from frame_processors.movementTracker import MovementTracker, MovementTrackerFactory
from settingsManager import SettingsManager
from soundDetector import SoundDetector, SoundDetectorFactory
from tcpServer import TcpServer
from utils import Frame, PointCoords, PreviewFrames, SourceMediaType, convertCvFrameToQImage, MovementPresentationType
from PyQt5.sip import voidptr
from workerThreadController import WorkerGroupInfo, WorkerThreadController

logger = logging.getLogger(__name__)

FRAME_FETCHING_GROUP = "FRAME_FETCHING_GROUP"
FRAME_RECORDING_GROUP = "FRAME_RECORDING_GROUP"
SOUND_PROCESSING_GROUP = "SOUND_PROCESSING_GROUP"
LOGGER_PROCESSING_GROUP = "LOGGER_PROCESSING_GROUP"
FRAME_STREAMING_GROUP = "FRAME_STREAMING_GROUP"
CAMERA_INFO_FETCHER_GROUP = "CAMERA_INFO_FETCHER_GROUP"
EMAIL_SUBSCRIBERS_PROCESSING_GROUP = "EMAIL_SUBSCRIBERS_PROCESSING_GROUP"

class Controller(QObject):

    imageIsReadyForDisplay = pyqtSignal(QImage)
    previewImagesReadyForDisplay = pyqtSignal(dict)
    contoursReceivedFromTransforamtor = pyqtSignal(PointCoords)
    dataIsReadyForSocket = pyqtSignal()
    toggleShowPreviewFrames = pyqtSignal(bool)
    infoAboutFrameFetcherAcquired = pyqtSignal(list)
    startFetchingCameraInfo= pyqtSignal()
    frameFetcherTerminated = pyqtSignal()
    startFrameFetcher = pyqtSignal()
    changeFrameFetcherSettings = pyqtSignal(FrameFetcherSettings)
    frameSourceNotFound = pyqtSignal()
    soundDetectionErrorAppeared = pyqtSignal(str)
    movementDisplayTypeToggled = pyqtSignal(MovementPresentationType, bool)
    emailNotificationToggled = pyqtSignal(bool)

    def __init__(
        self, 
        threadController: WorkerThreadController,
        settingsManager: SettingsManager 
        ) -> None:
        super().__init__()
        self.threadController = threadController
        self.settingsManager = settingsManager
        self.frameFetcher: FrameFetcher = FrameFetcherFactory.createFrameFetcher(
            SourceMediaType.CAMERA, 
            FrameFetcherSettings(self.settingsManager.getCameraSettings()["cameraIndex"]))
        self.frameTransforamtor: FrameTransformator = FrameTransforamtorFactory.get_frame_transformator(settingsManager.getFrameTransformationSettings())
        self.frameDrawer: FrameDrawer = FrameDrawer()
        self.movementTracker: MovementTracker = MovementTrackerFactory.createMovementTracker(settingsManager.getMovementTrackerSettings())
        self.movementRecorder: MovementRecorder = MovementRecorder()
        self.movementLogger: MovementLogger = MovementLoggerFactory.createMovementLogger(settingsManager.getMovementLoggerSettingss())
        self.soundDetector:SoundDetector = SoundDetectorFactory.createSoundDetector(settingsManager.getSoundDetectionSettings())
        self.tcpServer = TcpServer(9500)
        self.objectDetector = ObjectDetector(
            ObjectDetectionSettings(
                self.settingsManager.getObjectDetectionSettings()["confidenceThreshold"],
                self.settingsManager.getObjectDetectionSettings()["detectionEnabled"],
            )
        )
        self.cameraInfoFetcher = CameraInfoFetcher()
        self.emailSubsribersController = EmailSubscribersController()
        self.emailSubsribersController.loadSubscriberSettings(settingsManager.getEmailSubscriberSettings())
        self.gifCreator = GifCreator() 
        self.subscribers: List[FrameToNetworkStreamer] = []

        self.connectFrameFetcherSignalAndSlots()
        self.connectFrameTransforamtorSignalAndSlots()
        self.connectFrameDrawerSignalAndSlots()
        self.connectMovementTrackerSignalAndSlots()
        self.connectMovementRecorderSignalAndSlots()
        self.connectSoundDetectorSignalAndSlots()
        self.connectMovementLoggerSignalAndSlots()
        self.connectTcpServerSignalAndSlots()
        self.connectSettingsManager()
        self.connectCameraInfoFetcher()
        self.connectObjectDetector()
        self.connectEmailSubscribersController()
        self.createThreadingGroups()
        self.startServer()
        self.startWorkerGroups()
        
    def connectFrameFetcherSignalAndSlots(self) -> None:
        self.frameFetcher.frameFetched.connect(self.objectDetector.onFrameReceived)
        self.frameFetcher.frameFetched.connect(self.frameTransforamtor.onFrameReceived)
        self.frameFetcher.frameResolutionFetched.connect(self.frameTransforamtor.onFrameResolutionReceived)
        self.frameFetcher.noInputFoundError.connect(self.onNoInputFoundFromFrameFetcher)
        self.startFrameFetcher.connect(self.frameFetcher.onStartSignalReceived)
        self.changeFrameFetcherSettings.connect(self.frameFetcher.onFrameFetcherSettingsChanged)
    
    def connectFrameTransforamtorSignalAndSlots(self) -> None:
        self.frameTransforamtor.frameReadyForDrawing.connect(self.frameDrawer.onPrepareFrameForDisplay)
        self.frameTransforamtor.contoursFound.connect(self.frameDrawer.onContourDataReceived)
        self.frameTransforamtor.contoursFound.connect(self.onContoursReceivedFromTransformator)
        self.frameTransforamtor.previewFramesReadyForDrawing.connect(self.frameDrawer.onPreparePreviewFramesForDisplay)
        self.frameTransforamtor.movementInFrameDetected.connect(self.movementTracker.onMovementPresentToggled)
        self.frameTransforamtor.broadcastInitialFrame.connect(self.movementRecorder.onFrameReceived)
        self.frameTransforamtor.resizedFrameDimensionInfoCalculated.connect(self.movementLogger.onOriginalFrameDimensionInfoReceived)
        self.frameTransforamtor.broadcastInitialFrame.connect(self.gifCreator.onFrameReceived)
        self.toggleShowPreviewFrames.connect(self.frameTransforamtor.onShowPreviewFramesToggled)
        
    def connectFrameDrawerSignalAndSlots(self) -> None:
        self.frameDrawer.frameReadyForDisplay.connect(self.onFrameReceivedFromDrawer)
        self.frameDrawer.previewFramesReadyForDisplay.connect(self.onPreviewFramesReceivedFromDrawer)
        self.movementDisplayTypeToggled.connect(self.frameDrawer.onToggleShowMovementType)

    def connectSoundDetectorSignalAndSlots(self) -> None:
        self.soundDetector.soundAbowThresholdDetected.connect(self.frameDrawer.onSetIsSoundDetectedText)
        self.soundDetector.soundAbowThresholdDetected.connect(self.movementLogger.onSoundDetectedReceived)
        self.soundDetector.errorOccured.connect(self.onErrorOccuredInSoundDetector)

    def connectMovementTrackerSignalAndSlots(self) -> None:
        self.movementTracker.movementContinouslyPresent.connect(self.movementRecorder.onRecordingToggled)
        self.movementTracker.movementContinouslyPresent.connect(self.onObjectDetectionToggled)
        self.movementTracker.movementContinouslyPresent.connect(self.emailSubsribersController.onContinuousMovementToggled)
    
    def connectMovementRecorderSignalAndSlots(self) -> None:
        self.movementRecorder.toggleIsRecording.connect(self.frameDrawer.onSetIsRecordingText)
        self.movementRecorder.toggleIsRecording.connect(self.frameTransforamtor.onBroadcastingInitialFrameToggled)
    
    def connectMovementLoggerSignalAndSlots(self) -> None:
        self.contoursReceivedFromTransforamtor.connect(self.movementLogger.onMovementCoordinatesReceived)
    
    def connectTcpServerSignalAndSlots(self) -> None:
        self.tcpServer.connectionToServerMade.connect(self.onSomeoneConnectedToServer)

    def connectSettingsManager(self) -> None:
        self.settingsManager.frameDetectionSettingsSet.connect(self.frameTransforamtor.onFrameTransformatorSettingsChanged)
        self.settingsManager.frameRecordingSettingsSet.connect(self.movementRecorder.onRecorderSettingsChanged)
        self.settingsManager.frameRecordingSettingsSet.connect(self.movementTracker.onSettingsChanged)
        self.settingsManager.soundDetectionSettingsSet.connect(self.onSoundDetectedSettingsChanged)
        self.settingsManager.objectDetectionSettingsSet.connect(self.onObjectDetectionSettingsChanged)
        self.settingsManager.movementLoggerSettingsSet.connect(self.movementLogger.onSettingsChanged)
        self.settingsManager.cameraSettingsSet.connect(self.onCameraSettingsChanged)
        self.settingsManager.emailSubscriberAdded.connect(self.emailSubsribersController.onSubscriberAdded)
        self.settingsManager.emailNotificatioToggle.connect(self.emailSubsribersController.onEnableNotificationsToggled)
    
    def connectObjectDetector(self) -> None:
        self.objectDetector.objectsInFrameDetected.connect(self.frameDrawer.onObjectForDrawingReceived)

    def connectCameraInfoFetcher(self) -> None:
        self.startFetchingCameraInfo.connect(self.cameraInfoFetcher.onStart)
        self.cameraInfoFetcher.sendAllCameraInfo.connect(self.onCameraInfoFetcherFinished)

    def connectEmailSubscribersController(self) -> None:
        self.emailSubsribersController.toggleCreatingMovementGIF.connect(self.gifCreator.onCreateGifToggle)
        self.gifCreator.gifReady.connect(self.emailSubsribersController.onGifCreated)
        self.gifCreator.toggledRunning.connect(self.frameTransforamtor.onBroadcastingInitialFrameToggled)

    def createThreadingGroups(self) -> None:
        self.threadController.addWorkerToGroup(
            WorkerGroupInfo(
                self.frameFetcher,
                FRAME_FETCHING_GROUP,
                self.frameFetcher.startCapturingFrames,
                self.frameFetcher.stopRunning
            )
        )
        self.threadController.addWorkerToGroup(
            WorkerGroupInfo(
                self.objectDetector,
                FRAME_FETCHING_GROUP
            ),
            use_existing_thread=True
        )
        self.threadController.addWorkerToGroup(
            WorkerGroupInfo(
                self.movementRecorder,
                FRAME_RECORDING_GROUP
            )
        )
        if self.isSoundDetectorEnabled():
            self.threadController.addWorkerToGroup(
                WorkerGroupInfo(
                    self.soundDetector,
                    SOUND_PROCESSING_GROUP,
                    self.soundDetector.startCapturingAudioBlocks,
                    self.soundDetector.onClosingSoundDetector
                )
            )
        self.threadController.addWorkerToGroup(
            WorkerGroupInfo(
                self.movementLogger,
                LOGGER_PROCESSING_GROUP,
                self.movementLogger.onStart,
                self.movementLogger.onStop
            )
        )
        self.threadController.addWorkerToGroup(
            WorkerGroupInfo(
                self.cameraInfoFetcher,
                CAMERA_INFO_FETCHER_GROUP
            )
        )
        self.threadController.addWorkerToGroup(
            WorkerGroupInfo(
                self.emailSubsribersController,
                EMAIL_SUBSCRIBERS_PROCESSING_GROUP,
                self.emailSubsribersController.onStart
            )
        )
        self.threadController.addWorkerToGroup(
            WorkerGroupInfo(
                self.gifCreator,
                EMAIL_SUBSCRIBERS_PROCESSING_GROUP
            ),
            True
        )

    def startServer(self) -> None:
        self.tcpServer.startListening()
    
    def startWorkerGroups(self) -> None:
        self.threadController.startWorkerGroup(FRAME_FETCHING_GROUP)
        self.threadController.startWorkerGroup(FRAME_RECORDING_GROUP)
        if self.isSoundDetectorEnabled():
            self.threadController.startWorkerGroup(SOUND_PROCESSING_GROUP)
        self.threadController.startWorkerGroup(LOGGER_PROCESSING_GROUP)
        self.threadController.startWorkerGroup(CAMERA_INFO_FETCHER_GROUP)
        self.threadController.startWorkerGroup(EMAIL_SUBSCRIBERS_PROCESSING_GROUP)

    def isSoundDetectorEnabled(self) -> bool:
        return self.settingsManager.getSoundDetectionSettings()["soundDetectionEnabled"]

    @pyqtSlot(Frame)
    def onFrameReceivedFromDrawer(self, frame: Frame) -> None:
        self.imageIsReadyForDisplay.emit(
            convertCvFrameToQImage(frame)
            )
    
    @pyqtSlot(bool)
    def onPreviewFramesToggled(self, toggled:bool) -> None:
        self.toggleShowPreviewFrames.emit(toggled)

    @pyqtSlot(PreviewFrames)
    def onPreviewFramesReceivedFromDrawer(self, previewFrames: PreviewFrames) -> None:
        previewQImages = {
            "originalFrame":convertCvFrameToQImage(previewFrames.originalFrame),
            "grayAndBluredFrame":convertCvFrameToQImage(previewFrames.grayAndBluredFrame),
            "thresholdedFrame":convertCvFrameToQImage(previewFrames.thresholdedFrame),
            "erodedAndDilatedFrame":convertCvFrameToQImage(previewFrames.erodedAndDilatedFrame),
        }
        self.previewImagesReadyForDisplay.emit(previewQImages)

    @pyqtSlot(ContoursInfo)
    def onContoursReceivedFromTransformator(self, contours_info: ContoursInfo) -> None:
        self.contoursReceivedFromTransforamtor.emit(contours_info.center_of_the_mass)

    @pyqtSlot()
    def onCloseSignalReceived(self):
        self.frameFetcher.stopRunning()
        self.soundDetector.toggleRunning(False)
        self.threadController.stopWorkerGroup(FRAME_FETCHING_GROUP)
        self.threadController.stopWorkerGroup(SOUND_PROCESSING_GROUP)
        self.threadController.stopWorkerGroup(FRAME_RECORDING_GROUP)
        self.threadController.stopWorkerGroup(LOGGER_PROCESSING_GROUP)
        self.threadController.stopWorkerGroup(CAMERA_INFO_FETCHER_GROUP)
        self.threadController.stopWorkerGroup(EMAIL_SUBSCRIBERS_PROCESSING_GROUP)
        self.threadController.stopWorkerGroup(FRAME_STREAMING_GROUP)
        self.settingsManager.saveSettings()

    @pyqtSlot(voidptr)
    def onSomeoneConnectedToServer(self, handle): 
        socketWorker = FrameToNetworkStreamer(handle)
        self.threadController.addWorkerToGroup(
            WorkerGroupInfo(
                socketWorker,
                FRAME_STREAMING_GROUP,
                socketWorker.onStart,
                id = socketWorker.get_id()
            )
        )
        #self.frameFetcher.frameFetched.connect(socketWorker.onFrameReceived)
        self.frameDrawer.frameReadyForDisplay.connect(socketWorker.onFrameReceived)
        socketWorker.connectionTerminated.connect(self.onSocketWorkerConnectionTerminated)
        self.threadController.startWorkerGroup(FRAME_STREAMING_GROUP)
        self.subscribers.append(socketWorker)

    @pyqtSlot(str)
    def onSocketWorkerConnectionTerminated(self, worker_id:str) -> None:
        index = 0
        worker_found = False
        for worker in self.subscribers:
            id_of_worker = worker.get_id()
            if id_of_worker == worker_id:
                logger.info("Found subsriber by id: %s", worker_id)
                self.threadController.deleteObjectByIdFromWorkerGroup(worker_id, FRAME_STREAMING_GROUP)
                worker_found = True   
                break
            index += 1 
        if worker_found:
            del self.subscribers[index] 

    @pyqtSlot(dict)
    def onSoundDetectedSettingsChanged(self, new_settings: Dict) -> None:
        if new_settings["soundDetectionEnabled"] == self.soundDetector.isRunning():
            self.soundDetector.soundThreshold = new_settings["volumeThreshold"]
            return

        if new_settings["soundDetectionEnabled"]:
            self.soundDetector = SoundDetectorFactory.createSoundDetector(new_settings)
            #self.soundDetector.soundThreshold = new_settings["volumeThreshold"]
            self.connectSoundDetectorSignalAndSlots()
            self.threadController.addWorkerToGroup(
                WorkerGroupInfo(
                    self.soundDetector,
                    SOUND_PROCESSING_GROUP,
                    self.soundDetector.startCapturingAudioBlocks,
                    self.soundDetector.onClosingSoundDetector
                )
            )
            self.threadController.startWorkerGroup(SOUND_PROCESSING_GROUP)
        else:
            self.soundDetector.toggleRunning(False)
            self.threadController.stopWorkerGroup(SOUND_PROCESSING_GROUP)

    @pyqtSlot()
    def onCameraInfoFetcherStart(self) -> None:
        self.frameTransforamtor.toggleApplyTransforamtion(False)
        self.frameFetcher.stopRunning()
        self.startFetchingCameraInfo.emit()
        self.frameTransforamtor.toggleApplyTransforamtion(True)
    
    @pyqtSlot(list)
    def onCameraInfoFetcherFinished(self, camera_info_list: List) -> None:
        self.infoAboutFrameFetcherAcquired.emit(camera_info_list)
    
    @pyqtSlot(dict)
    def onCameraSettingsChanged(self, cameraSettings: dict) -> None:
        self.frameTransforamtor.reset()
        self.movementTracker.stopTimers()
        self.changeFrameFetcherSettings.emit(
            FrameFetcherSettings(cameraSettings["cameraIndex"])
            )
        self.startFrameFetcher.emit()
    
    @pyqtSlot(dict)
    def onObjectDetectionSettingsChanged(self, objectDetectionSettings: dict) -> None:
        newObjDetectionSettings = ObjectDetectionSettings(
            objectDetectionSettings["confidenceThreshold"],
            objectDetectionSettings["detectionEnabled"]
        )
        self.objectDetector.setDetectionParams(newObjDetectionSettings)
    
    @pyqtSlot(bool)
    def onObjectDetectionToggled(self, toggled: bool) -> None:
        self.objectDetector.setDetectionTriggered(toggled)

    @pyqtSlot()
    def onNoInputFoundFromFrameFetcher(self) -> None:
        self.frameSourceNotFound.emit()

    @pyqtSlot(str)
    def onErrorOccuredInSoundDetector(self, msg:str) -> None:
        self.soundDetectionErrorAppeared.emit(msg)
    
    @pyqtSlot(MovementPresentationType, bool)
    def onToggledMovementDisplayType(self, movementPresentationType: MovementPresentationType, toggled: bool) -> None:
        self.movementDisplayTypeToggled.emit(movementPresentationType, toggled)
    
    @pyqtSlot(bool)
    def onEmailNotificationEnabledToggled(self, toggle: bool)-> None:
        #self.emailNotificationToggled.emit(toggle)
        self.settingsManager.toggleEmailNotifications(toggle)