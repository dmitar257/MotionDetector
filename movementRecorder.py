from datetime import datetime
from typing import Dict, Optional
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import os
import cv2
from utils import Frame
import logging

RECORDING_FPS = 20
RECORDING_RESOLUTION = (1080, 720) 

logger = logging.getLogger(__name__)

class MovementRecorder(QObject):
    toggleIsRecording = pyqtSignal(bool)
    def __init__(self):
        super().__init__()
        self.recording = False
        self.frame_writer: Optional[cv2.VideoWriter] = None
        self.recordingFolder = os.path.join(os.getcwd(),'recordings')

    def prepareWriter(self) -> None:
        recName = datetime.now().strftime("%b_%d_%Y_%H_%M_%S")+".avi"
        fullPath = os.path.join(self.recordingFolder, recName)
        self.frame_writer = cv2.VideoWriter(fullPath, cv2.VideoWriter_fourcc('I','4','2','0'), RECORDING_FPS, RECORDING_RESOLUTION)

    @pyqtSlot(bool)
    def onRecordingToggled(self, isRecording:bool) -> None:
        if isRecording:
            self.recording = True
            self.prepareWriter()
            self.toggleIsRecording.emit(True)
        else:
            self.recording = False
            if self.frame_writer:
                self.frame_writer.release()
            self.frame_writer = None
            self.toggleIsRecording.emit(False)
    
    @pyqtSlot(Frame)
    def onFrameReceived(self, frame: Frame) -> None:
        if not self.recording:
            return
        if not self.frame_writer:
            raise Exception("No frame writter provided")
        resized_frame = cv2.resize(frame, RECORDING_RESOLUTION, cv2.INTER_AREA)
        self.frame_writer.write(resized_frame)
    
    @pyqtSlot(dict)
    def onRecorderSettingsChanged(self, settings: Dict) -> None:
        self.recordingFolder = settings["recordingsDir"]
        