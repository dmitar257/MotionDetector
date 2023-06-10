from typing import Optional, Dict
from PyQt5.QtCore import pyqtSignal,pyqtSlot,QMutexLocker,QMutex, QObject
import pyaudio, math, struct
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

FRAME_CHUNK_SIZE = 1024
NUM_OF_CHANNELS = 2
SAMPLING_RATE = 44100

@dataclass
class SoundDetectorParameters:
    soundThreshold: int
    enabled: bool


class SoundDetector(QObject):
    soundAbowThresholdDetected = pyqtSignal(bool, int)
    errorOccured = pyqtSignal(str)

    def __init__(
            self,
            sound_detector_params: SoundDetectorParameters
            ) -> None:
        super().__init__()
        self.__running = False
        self.chunk = FRAME_CHUNK_SIZE
        self.channels = NUM_OF_CHANNELS
        self.rate = SAMPLING_RATE
        self.shortNormalize = (1.0/32768.0)
        self.silenceThresh = int(self.rate / self.chunk * 0.5)
        self.__pa = pyaudio.PyAudio()
        self.__stream = self.openMicStream()
        self.__runningMutex = QMutex()
        self.__thresholdMutex = QMutex()
        self.enabled = sound_detector_params.enabled
        self.soundThreshold = sound_detector_params.soundThreshold
        self.closeStream = False
    
    def isRunning(self):
        with QMutexLocker(self.__runningMutex):
            return self.__running
    
    def toggleRunning(self, toggle):
        with QMutexLocker(self.__runningMutex):
            self.__running = toggle
    
    @property
    def soundThreshold(self):
        return self.__soundThreshold
    
    @soundThreshold.setter
    def soundThreshold(self, value):
        with QMutexLocker(self.__thresholdMutex):
            self.__soundThreshold = value

    def findInputDevice(self) -> Optional[int]:
        device_index = None             
        for i in range( self.__pa.get_device_count() ):     
            devinfo = self.__pa.get_device_info_by_index(i)   
            for keyword in ["mic","input"]:
                if keyword in devinfo["name"].lower():
                    logger.info( "Found an input: device %d - %s", i, devinfo["name"])
                    device_index = i
                    return device_index

        if device_index == None:
            raise Exception("Could not find any Microphone Device connected")

    def openMicStream(self) -> pyaudio.Stream:
        try:
            device_index = self.findInputDevice()
            stream = self.__pa.open(format = pyaudio.paInt16,
                            channels = self.channels,
                            rate = self.rate,
                            input = True,
                            input_device_index = device_index,
                            frames_per_buffer = self.chunk)
            return stream
        except Exception as e:
            logger.error(str(e))
            return None

    def startCapturingAudioBlocks(self) -> None:
        if not self.__stream:
            logger.warning("No sound streamer for sound detection")
            self.errorOccured.emit("Error appeared when trying to open sound stream with")
            return
        self.__running = True
        loud_sequence_found = False
        num_of_sequential_silent_blocks = 0
        while self.isRunning():
            rmsLog = self.get_rms_log_for_block(self.__stream.read(self.chunk))
            if not rmsLog:
                continue
            if loud_sequence_found:
                if abs(rmsLog) > self.soundThreshold:
                    num_of_sequential_silent_blocks += 1
                    if num_of_sequential_silent_blocks > self.silenceThresh:
                        self.soundAbowThresholdDetected.emit(False, -1)
                        loud_sequence_found = False
                else:
                    num_of_sequential_silent_blocks = 0
            elif not (abs(rmsLog) > self.soundThreshold):
                self.soundAbowThresholdDetected.emit(True, abs(rmsLog))
                loud_sequence_found = True

        self.soundAbowThresholdDetected.emit(False, -1)
    
    def get_rms_log_for_block(self, block: bytes) -> Optional[float]:
        try:
            block = self.__stream.read(self.chunk)
            rms = self.get_rms(block)
            return 20 * math.log10(rms)
        except ValueError as valErr:
            if "math domain error" in str(valErr):
                logger.error("Log error when calculating RMS for sound block")
                return None
            raise valErr
        except Exception as e:
            logger.error("Unexpected error appeared when trying to calculate rms_log for audio block. "
                         f"Error details {e}"
                         )
            return None
    
    def get_rms(self, block: bytes) -> float:
        count = len(block) / 2
        format = "%dh"%(count)
        shorts = struct.unpack( format, block )
        sum_squares = 0.0
        for sample in shorts:
            n = sample * self.shortNormalize
            sum_squares += n*n
        return math.sqrt( sum_squares / count )
    
    @pyqtSlot()
    def onClosingSoundDetector(self) -> None:
        self.terminateStream() 
    
    def terminateStream(self) -> None:
        self.__stream.stop_stream()
        self.__stream.close()
        self.__pa.terminate()
    
class SoundDetectorFactory:
    @classmethod
    def createSoundDetector(cls, settings_dict: Dict) -> SoundDetector:
        return SoundDetector(
            SoundDetectorParameters(
                settings_dict["volumeThreshold"],
                settings_dict["soundDetectionEnabled"]
            )
        )
