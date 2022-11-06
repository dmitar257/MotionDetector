from dataclasses import dataclass
from typing import Dict, List
import cv2
import numpy as np
from utils import Frame
import logging
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QMutexLocker

logger = logging.getLogger(__name__)

@dataclass
class ObjectDetectionSettings:
    confidenceThreshold:float = 0.5
    detectionEnabled:bool = False

class ObjectDetector(QObject):
    objectsInFrameDetected = pyqtSignal(list)
    def __init__(self, detectionParams: ObjectDetectionSettings):
        super().__init__()
        self.detectionParams = detectionParams
        self.detectionTriggered = False
        self.__nmsThreshold = 0.4
        self.__labels = open("yolo/labels.txt").read().strip().split("\n")
        self.__colors = np.random.uniform(0, 255, size=(len(self.__labels), 3))
        self.net = cv2.dnn.readNet("yolo/yolov4-tiny.weights", "yolo/yolov4-tiny.cfg")
        self.__ln = self.net.getLayerNames()
        self.__ln = [self.__ln[i[0] - 1] for i in self.net.getUnconnectedOutLayers()]
        self.detectionParamsMutex = QMutex()
        self.detectionTriggeredMutex = QMutex()
    
    def get_prediction_for_frame(self, frame: Frame, filter_labels = None) -> List[Dict]:
        height, width, channels = frame.shape
        # Detecting objects
        blob = cv2.dnn.blobFromImage(frame, 0.00392, (320, 320), (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.__ln)
        class_ids = []
        confidences = []
        boxes = []
        confidence_threshold = self.getDetectionParams().confidenceThreshold
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]
                if confidence > confidence_threshold:
                    # Object detected
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)
                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    boxes.append([x, y, w, h])
                    confidences.append(float(confidence))
                    class_ids.append(class_id)
        idxs = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, self.__nmsThreshold)
        detected_objs = []
        for i in range(len(boxes)):
            if i in idxs:
                x, y, w, h = boxes[i]
                label = str(self.__labels[class_ids[i]])
                color = self.__colors[i]
                detected_objs.append({
                    "x":x,
                    "y":y,
                    "w":w,
                    "h":h,
                    "color": color,
                    "label": label,
                    "confidence": confidences[i]
                })
        return detected_objs
    
    @pyqtSlot(Frame)
    def onFrameReceived(self, frame:Frame) -> None:
        if not self.getDetectionParams().detectionEnabled or not self.getDetectionTriggered():
            return
        predictions = self.get_prediction_for_frame(frame)
        self.objectsInFrameDetected.emit(predictions)
    
    def getDetectionParams(self) -> ObjectDetectionSettings:
        with QMutexLocker(self.detectionParamsMutex):
            return self.detectionParams
    
    def setDetectionParams(self, detectionParams: ObjectDetectionSettings) -> None:
        with QMutexLocker(self.detectionParamsMutex):
            self.detectionParams = detectionParams
    
    def getDetectionTriggered(self) -> bool:
        with QMutexLocker(self.detectionTriggeredMutex):
            return self.detectionTriggered
    
    def setDetectionTriggered(self, detectionTriggered: bool) -> None:
        with QMutexLocker(self.detectionTriggeredMutex):
            self.detectionTriggered = detectionTriggered


