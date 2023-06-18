from dataclasses import dataclass
import enum
from functools import lru_cache
from typing import NewType, Tuple,List, TypeVar
import cv2
import math
import numpy as np
from PyQt5.QtGui import QImage
import os
import logging

logger = logging.getLogger(__name__)

Frame = np.ndarray
Contour = np.ndarray
PointCoords  = tuple

@dataclass
class PreviewFrames:
    originalFrame: Frame
    grayAndBluredFrame: Frame
    thresholdedFrame: Frame
    erodedAndDilatedFrame: Frame

class AlgorithmType(enum.Enum):
    RUNNING_AVG = 0
    MIXTURE_OF_GAUSSIANS = 1
    KNN = 2

class SourceMediaType(enum.Enum):
    CAMERA = 0
    VIDEO = 1

class WorkerTypes(enum.Enum):
    FRAME_FETCHER = 0
    SOUND_FETCHER = 1
    FRAME_TRANSFORMATOR = 2
    FRAME_RECORDER = 3
    LOG_WRITER = 4

class TextToPutOnFrameType(enum.Enum):
    CENTER_OF_THE_MASS_MSG = 0
    RECORDING_MOVEMENT_MSG = 1
    SOUND_PRESENT_MSG = 2

class MovementPresentationType(enum.Enum):
    CROSSHAIR = 0
    RECTANGLE = 1
    CONTOUR = 2

def meanByColumn(mat: List[PointCoords]):
    meanMat = [ sum(x)//len(mat) for x in zip(*mat) ]
    return tuple(meanMat)

def convertCvFrameToQImage(frame: Frame) -> QImage:
    rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)              
    h, w, ch = rgbImage.shape
    bytesPerLine = ch * w	
    return QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)

@lru_cache(maxsize=1)
def get_aspect_ratio_from_resolution(width: int, height: int) -> Tuple[int, int]:
    gcd_value = math.gcd(width, height)
    return (width // gcd_value, height // gcd_value)

def createFolderIfNoExisting(folderPath):
    if not os.path.exists(folderPath):
        logger.info("Creating folder: %s", folderPath)
        os.makedirs(folderPath)
        logger.info("Created folder: %s", folderPath)
        

