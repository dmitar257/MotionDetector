from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import cv2
from typing import Any, Dict, List, Optional, Tuple
from frame_processors.frameTransformator import ContoursInfo
from utils import Contour, Frame, PointCoords, PreviewFrames, TextToPutOnFrameType, MovementPresentationType
from dataclasses import dataclass


@dataclass
class TextImageParameters:
    text: str
    position:PointCoords
    fontScale: float
    thickness: float
    color: Tuple[int, int, int]

class FrameDrawer(QObject):
    frameReadyForDisplay = pyqtSignal(Frame)
    previewFramesReadyForDisplay = pyqtSignal(PreviewFrames)

    def __init__(self) -> None:
        super().__init__()
        self.initializeFields()

    
    def initializeFields(self) -> None:
        self.showSoundDetected = False
        self.showIsRecording = False
        self.showCrosshair = True
        self.showConturShapes = False
        self.showRectangles = False
        self.objectsForDrawing: Optional[List[Dict]] = None
        self.contoursForDrawing: Optional[List[Contour]] = None
        self.centerOfTheMass: Optional[PointCoords] = None
        self.msgTypesForDrawing: List[TextToPutOnFrameType] = []
    

    @pyqtSlot(list)
    def onObjectForDrawingReceived(self, list_of_obj: List[Dict]) -> None:
        self.objectsForDrawing = list_of_obj

    @pyqtSlot(ContoursInfo)
    def onContourDataReceived(self, contours_info: ContoursInfo) -> None:
        self.contoursForDrawing = contours_info.contour_list
        self.centerOfTheMass = contours_info.center_of_the_mass

    @pyqtSlot(TextToPutOnFrameType)
    def onTextTypeReceived(self, msg_type: TextToPutOnFrameType) -> None:
        self.msgTypesForDrawing.append(msg_type)

    @pyqtSlot(Frame)
    def onPrepareFrameForDisplay(self, frame: Frame) -> None:
        self.drawElementsOnFrame(frame)
        self.frameReadyForDisplay.emit(frame)
    
    @pyqtSlot(bool)
    def onSetIsRecordingText(self, isRecording:bool) -> None:
        self.showIsRecording = isRecording
    
    @pyqtSlot(bool)
    def onSetIsSoundDetectedText(self, isSoundDetected:bool) -> None:
        self.showSoundDetected = isSoundDetected

    @pyqtSlot(PreviewFrames)
    def onPreparePreviewFramesForDisplay(self, previewFrames: PreviewFrames) -> None:
        previewFrames.originalFrame = self.drawTextOnPreviewFrame(
            previewFrames.originalFrame,
            "Original Frame"
            )
        previewFrames.grayAndBluredFrame = self.drawTextOnPreviewFrame(
            previewFrames.grayAndBluredFrame,
            "Gray&Blured Frame"
            )
        previewFrames.thresholdedFrame = self.drawTextOnPreviewFrame(
            previewFrames.thresholdedFrame,
            "Binary thresholded Frame"
            )
        previewFrames.erodedAndDilatedFrame = self.drawTextOnPreviewFrame(
            previewFrames.erodedAndDilatedFrame,
            "Eroded&Dilated Frame"
            )
        self.previewFramesReadyForDisplay.emit(previewFrames)

    def onToggleShowMovementType(self, shapeType: MovementPresentationType, toggle: bool) -> None:
        if shapeType == MovementPresentationType.CROSSHAIR:
            self.showCrosshair = toggle
        elif shapeType == MovementPresentationType.CONTOUR:
            self.showConturShapes = toggle
        elif shapeType == MovementPresentationType.RECTANGLE:
            self.showRectangles = toggle
    
    def drawElementsOnFrame(self, frame:Frame) -> None:
        self.drawObjects(frame)
        self.drawContours(frame)
        self.drawTextMessages(frame)
        self.clear_qeues()
    
    def drawObjects(self, frame: Frame) -> None:
        if not self.objectsForDrawing:
            return
        for info in self.objectsForDrawing:
            cv2.rectangle(frame, (info["x"], info["y"]), (info["x"] + info["w"], info["y"] + info["h"]), info["color"], 2)
            text = "{}: {:.4f}".format(info["label"], info["confidence"])
            cv2.putText(frame, text, (info["x"], info["y"] - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, info["color"], 1,cv2.LINE_AA)       
        self.objectsForDrawing = None

    def drawContours(self, frame:Frame) -> None:
        if self.showRectangles:
            self.drawRectanglesAroundContours(frame)
        if self.showConturShapes:
            self.drawContourShape(frame)
        if self.drawContourCrosshair and self.centerOfTheMass:
            self.drawContourCrosshair(frame)

    def drawRectanglesAroundContours(self, frame: Frame) ->  None:
        if self.contoursForDrawing:
            for contour in self.contoursForDrawing:
                x,y,w,h = cv2.boundingRect(contour)
                rx = x+int(w/2)
                ry = y+int(h/2)
                cv2.circle(frame,(rx,ry),2,(0,255,0),2)
                cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)

    def drawContourShape(self, frame: Frame) -> None:
        if self.contoursForDrawing:
            for contour in self.contoursForDrawing:
                M = cv2.moments(contour)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])   
                cv2.circle(frame,(cx,cy),2,(0,0,255),2)
                cv2.drawContours(frame,[contour], 0, (0,0,255), 2)
    
    def drawContourCrosshair(self, frame: Frame) -> None:
        if not self.centerOfTheMass:
            raise BaseException("No Ceneter of the mass received for drawing Crossahir")
        tr  = 30
        cv2.circle(frame,self.centerOfTheMass,tr,(0,0,255,0),2)
        cv2.line(frame,(self.centerOfTheMass[0]-tr,self.centerOfTheMass[1]),(self.centerOfTheMass[0]+tr,self.centerOfTheMass[1]),(0,0,255,0),2)
        cv2.line(frame,(self.centerOfTheMass[0],self.centerOfTheMass[1]-tr),(self.centerOfTheMass[0],self.centerOfTheMass[1]+tr),(0,0,255,0),2)
    
    def drawTextMessages(self, frame: Frame) -> None:
        if self.centerOfTheMass:
            text_msg_params = TextImageParameters(
                f"Center of the mass: {self.centerOfTheMass[0]} x {self.centerOfTheMass[1]}",
                (10,25),
                0.5,
                1,
                (255,0,0)
                )
            self.drawText(frame, text_msg_params)
        if self.showIsRecording:
            text_msg_params = TextImageParameters(
                f"Recording Frames",
                (10,40),
                0.5,
                1,
                (255,0,0)
                )
            self.drawText(frame, text_msg_params)
        if self.showSoundDetected:
            text_msg_params = TextImageParameters(
                f"Sound Detected...",
                (10,55),
                0.5,
                1,
                (0,255,0)
                )
            self.drawText(frame, text_msg_params)


    def drawText(self, frame: Frame, text_params: TextImageParameters) -> None:
        cv2.putText(frame, text_params.text, text_params.position,  cv2.FONT_HERSHEY_SIMPLEX, text_params.fontScale, text_params.color, text_params.thickness, cv2.LINE_AA)

    def clear_qeues(self) -> None:
        self.contoursForDrawing = None
        self.centerOfTheMass = None
        self.msgTypesForDrawing.clear()
    
    def drawTextOnPreviewFrame(self, preview_frame: Frame, text_to_write: str) -> Frame:
        cv2.putText(preview_frame, text_to_write, (10,30),  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1, cv2.LINE_AA) 
        return preview_frame