import enum
import logging
from typing_extensions import Protocol
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from utils import AlgorithmType, Frame, Contour, PointCoords, PreviewFrames, get_aspect_ratio_from_resolution, meanByColumn
import cv2
import imutils

logger = logging.getLogger(__name__)

@dataclass
class GausianBlurParameters:
    kernel_size: int

@dataclass
class ErosionParameters:
    kernel_size: int
    iterations: int

@dataclass
class DilationParameters:
    kernel_size: int
    iterations: int

@dataclass
class BackgroundSubstractingParams:
    algorithmType: AlgorithmType
    thresholdValue: int
    runningAvgAlpha: float
    gaussianMixtureHistory: int
    knnHistory:int

@dataclass
class ContourCalculationParams:
    min_area: int

@dataclass
class FrameTransforamtorSettings:
    gausianBlurParams: GausianBlurParameters
    erosionParams: ErosionParameters
    dilationParams: DilationParameters
    backgroundSubstractorParams: BackgroundSubstractingParams
    min_contour_area: int

class FrameTransformatorType(enum.Enum):
    OPEN_CV = 0
    
class FrameSimpleTransformationApplyer(Protocol):
    def resizeImage(self, frame:Frame, new_width: int) -> Frame:
        ...
    
    def transformImageToGrayscale(self, frame: Frame) -> Frame:
        ...
    
    def applyGaussianBlurToImage(self, frame: Frame, gausian_blur_params: GausianBlurParameters) -> Frame:
        ...

    def applyErrosionToImage(self, frame: Frame, erosion_params: ErosionParameters) -> Frame:
        ...

    def applyDilationToImage(self, frame: Frame, dilation_params: DilationParameters) -> Frame:
        ...

class BackgroundSubstractor(Protocol):
    threshold_bin_val:int
    def applyBackgroundSubstraction(self, blured_bw_frame: Frame) -> Frame:
        ...
    
    def reset(self) -> None:
        ...

class ContoursInfo:
    def __init__(self, contour_list:List[Contour], center_of_the_mass: PointCoords) -> None:
        self.contour_list = contour_list
        self.center_of_the_mass = center_of_the_mass

class ContourCalculator(Protocol):
    def extractContours(self, binarized_frame: Frame, min_area: int) -> Optional[ContoursInfo]:
        ...
    
    def calculateCenterOfTheMass(self, countour_list: List[Contour]) -> Tuple[int, int]:
        ...

    def reset(self) -> None:
        ...

class OpenCVSimpleTransformationApplyer:
    def resizeImage(self, frame:Frame, new_width: int) -> Frame:
        return imutils.resize(frame, width = new_width)
    
    def transformImageToGrayscale(self, frame: Frame) -> Frame:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    def applyGaussianBlurToImage(self, frame: Frame, gausian_blur_params: GausianBlurParameters) -> Frame:
        return cv2.GaussianBlur(frame, (gausian_blur_params.kernel_size, gausian_blur_params.kernel_size), 0)
    
    def applyErrosionToImage(self, frame: Frame, erosion_params: ErosionParameters) -> Frame:
        erode_kernel = np.ones((erosion_params.kernel_size, erosion_params.kernel_size), np.uint8) 
        return cv2.erode(frame, kernel = erode_kernel, iterations= erosion_params.iterations)
    
    def applyDilationToImage(self, frame: Frame, dilation_params: DilationParameters) -> Frame:
        dilated_kernel = np.ones((dilation_params.kernel_size, dilation_params.kernel_size), np.uint8) 
        return cv2.dilate(frame ,kernel = dilated_kernel, iterations=dilation_params.iterations)

class RunninAverageBackgroundSubstractor:
    def __init__(self, alpha: float, threshold_bin_val: int) -> None:
        self.backgroundFrame: Optional[np.floating] = None
        self.runningAvgAlpha: float = alpha
        self.threshold_bin_val = threshold_bin_val

    def applyBackgroundSubstraction(self, blured_bw_frame: Frame) -> Frame:
        if self.backgroundFrame is None:
            self.backgroundFrame = np.float32(blured_bw_frame)
        cv2.accumulateWeighted(blured_bw_frame, self.backgroundFrame, self.runningAvgAlpha)
        convertedBackground = cv2.convertScaleAbs(self.backgroundFrame)
        diff = cv2.absdiff(blured_bw_frame, convertedBackground)
        _,thresh_img = cv2.threshold(diff, self.threshold_bin_val, 255, cv2.THRESH_BINARY) 
        return thresh_img

    def reset(self) -> None:
        self.backgroundFrame = None

class MixtureOfGaussiansBackgroundSubstractor:
    def __init__(self, gaussian_mixture_history: int, threshold_val: int) -> None:
        self.gaussian_mixture_history = gaussian_mixture_history
        self.threshold_val = threshold_val
        self.background_substraction_model = cv2.createBackgroundSubtractorMOG2(
            history = self.gaussian_mixture_history,
            varThreshold = self.threshold_val, 
            detectShadows = False)
        
    def applyBackgroundSubstraction(self, blured_bw_frame: Frame) -> Frame:
        return self.background_substraction_model.apply(blured_bw_frame)
    
    def reset(self) -> None:
        self.background_substraction_model = cv2.createBackgroundSubtractorMOG2(
            history = self.gaussian_mixture_history,
            varThreshold = self.threshold_val, 
            detectShadows = False)

class KNNBackgroundSubstractor:
    def __init__(self, knn_history: int, dist_threshold: int) -> None:
        self.knn_history = knn_history
        self.dist_threshold = dist_threshold
        self.background_substraction_model = cv2.createBackgroundSubtractorKNN(
            history = self.knn_history,
            dist2Threshold = self.dist_threshold, 
            detectShadows = False)
        
    def applyBackgroundSubstraction(self, blured_bw_frame: Frame) -> Frame:
        return self.background_substraction_model.apply(blured_bw_frame)
    
    def reset(self) -> None:
        self.background_substraction_model = cv2.createBackgroundSubtractorKNN(
            history = self.knn_history,
            dist2Threshold = self.dist_threshold, 
            detectShadows = False) 


class OpenCVContourCalculator:
    def __init__(self) -> None:
        self.center_of_the_mass_queue: List[PointCoords] = []
        self.center_of_the_mass_queue_size = 50
        self.inertion_tolerance_counter = 0
        self.intertion_tolerance_limit = 18

    def extractContours(self, binarized_frame: Frame, min_area: int) -> Optional[ContoursInfo]:
        contours,_ = cv2.findContours(binarized_frame,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
        contours = [c for c in contours if cv2.contourArea(c) > min_area]
        contours_found = False if len(contours) == 0 else True
        if not contours_found:
            self.increaseToleranceCounter()
            return None
        return self.extractDetectedContoursInfo(contours)

    def increaseToleranceCounter(self):
        self.inertion_tolerance_counter += 1
        if self.inertion_tolerance_counter == self.intertion_tolerance_limit:
            self.intertion_tolerance_counter = 0
            self.center_of_the_mass_queue.clear()
        
    def extractDetectedContoursInfo(self, contours:List[Contour]) -> ContoursInfo:
        self.inertion_tolerance_counter = 0
        center_of_the_mass = self.calculateCenterOfTheMass(contours)
        center_of_the_mass_with_inertion = self.applyInertion(center_of_the_mass)
        return ContoursInfo(contours, center_of_the_mass_with_inertion)

    def calculateCenterOfTheMass(self, contours: List[Contour]) -> PointCoords:
        mx = my = area = 0
        for c in contours:
            M = cv2.moments(c)
            counturArea = cv2.contourArea(c)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            mx += cx*counturArea
            my += cy*counturArea
            area += counturArea 

        mx = int(round(mx/area,0))
        my = int(round(my/area,0))
        return (mx,my)
    
    def applyInertion(self, center_of_the_mass: PointCoords) -> PointCoords:
        if len(self.center_of_the_mass_queue) == self.center_of_the_mass_queue_size:
            del self.center_of_the_mass_queue[0]
        self.center_of_the_mass_queue.append(center_of_the_mass)
        return meanByColumn(self.center_of_the_mass_queue)
    
    def reset(self) -> None:
        self.center_of_the_mass_queue.clear()
        self.inertion_tolerance_counter = 0

class FrameTransformator(QObject):
    contoursFound = pyqtSignal(ContoursInfo)
    previewFramesReadyForDrawing = pyqtSignal(PreviewFrames)
    movementInFrameDetected = pyqtSignal(bool)
    resizedFrameDimensionInfoCalculated = pyqtSignal(dict)

    def __init__(self, 
        frameProcessor: FrameSimpleTransformationApplyer,
        backgroundSubstractor: BackgroundSubstractor,
        contourCalculator: ContourCalculator,
        transformatorSettings: FrameTransforamtorSettings
        ) -> None:
        super().__init__()
        self.frameProcessor = frameProcessor
        self.backgroundSubstractor = backgroundSubstractor
        self.contourCalculator = contourCalculator
        self.sendPreviewFrames = False
        self.numOfSubscribersForInitialFrame = 0
        self.settings = transformatorSettings
        self.transforamtorEnabled = True
    
    def toggleApplyTransforamtion(self, toggle: bool) -> None:
        self.transforamtorEnabled  = toggle

    @pyqtSlot(Frame)
    def onFrameReceived(self, frame: Frame) -> None:
        self.processReceivedFrame(frame)
    
    @pyqtSlot(bool)
    def onToggleShowPreviewFrames(self, toggled: bool) -> None:
        self.sendPreviewFrames = toggled

    def reset(self) -> None:
        self.backgroundSubstractor.reset()
        self.contourCalculator.reset()
        self.numOfSubscribersForInitialFrame = 0
    
    @classmethod
    def getTransfornmatorSettingsFromDict(cls, transformatorSettings: Dict) -> FrameTransforamtorSettings:
        gausianBlurParams = GausianBlurParameters(transformatorSettings["gaussianBlurKernelSize"])
        erosionParams = ErosionParameters(transformatorSettings["erosionKernelSize"], transformatorSettings["erosionIterations"])
        dilationParams = DilationParameters(transformatorSettings["dilationKernelSize"], transformatorSettings["dilationIterations"])
        backgroundSubstractorParams = BackgroundSubstractingParams(
            transformatorSettings["backgroundSubstractionSettings"]["algorithmType"],
            transformatorSettings["backgroundSubstractionSettings"]["runningAvgThresholdBinValue"],
            transformatorSettings["backgroundSubstractionSettings"]["runningAvgAlpha"],
            transformatorSettings["backgroundSubstractionSettings"]["gaussianMixtureHistory"],
            transformatorSettings["backgroundSubstractionSettings"]["knnHistory"]
        )
        min_area = transformatorSettings["backgroundSubstractionSettings"]["runningAvgMinArea"]
        if backgroundSubstractorParams.algorithmType == AlgorithmType.MIXTURE_OF_GAUSSIANS:
            min_area = transformatorSettings["backgroundSubstractionSettings"]["gaussianMixtureMinArea"]
            backgroundSubstractorParams.thresholdValue = transformatorSettings["backgroundSubstractionSettings"]["gaussianMixtureThresholdValue"]
        if backgroundSubstractorParams.algorithmType == AlgorithmType.KNN:
            min_area = transformatorSettings["backgroundSubstractionSettings"]["knnMinArea"]
            backgroundSubstractorParams.thresholdValue = transformatorSettings["backgroundSubstractionSettings"]["knnThresholdValue"]
        return FrameTransforamtorSettings(
            gausianBlurParams,
            erosionParams,
            dilationParams,
            backgroundSubstractorParams,
            min_area
            )
    
    def processReceivedFrame(self, frame: Frame) -> None:
        if not self.transforamtorEnabled:
            logger.info("Droping received frame !")
            return
        grayed_frame = self.frameProcessor.transformImageToGrayscale(frame)
        blured_frame = self.frameProcessor.applyGaussianBlurToImage(grayed_frame, self.settings.gausianBlurParams)
        binarized_frame = self.backgroundSubstractor.applyBackgroundSubstraction(blured_frame)
        eroded_frame = self.frameProcessor.applyErrosionToImage(binarized_frame, self.settings.erosionParams)
        dilated_frame = self.frameProcessor.applyDilationToImage(eroded_frame, self.settings.dilationParams)
        contour_info = self.contourCalculator.extractContours(dilated_frame, self.settings.min_contour_area)
        movement_detected = False
        if contour_info:
            self.contoursFound.emit(contour_info)
            movement_detected = True
        self.movementInFrameDetected.emit(movement_detected)
        if self.sendPreviewFrames:
            self.previewFramesReadyForDrawing.emit(
                PreviewFrames(
                    frame,
                    blured_frame,
                    binarized_frame,
                    dilated_frame
                ))

    # @pyqtSlot(bool)
    # def onBroadcastingInitialFrameToggled(self, broadcast_init_frame: bool) -> None:
    #     if broadcast_init_frame:
    #         self.numOfSubscribersForInitialFrame += 1
    #     else:
    #         if self.numOfSubscribersForInitialFrame > 0:
    #             self.numOfSubscribersForInitialFrame -= 1
            

    @pyqtSlot(bool)
    def onShowPreviewFramesToggled(self, show_preview_frames: bool) -> None:
        self.sendPreviewFrames = show_preview_frames  

    @pyqtSlot(tuple)
    def onFrameResolutionReceived(self, frame_res_info: Tuple[int, int, int]) -> None:
        logger.info("Original frame resolution: %s x %s", frame_res_info[0], frame_res_info[1])
        aspectRatio = get_aspect_ratio_from_resolution(frame_res_info[0], frame_res_info[1])
        resizedFrameResolution = (frame_res_info[2], int(frame_res_info[2] * aspectRatio[1]/aspectRatio[0]))
        logger.info("Resized frame resolution: %s x %s", resizedFrameResolution[0], resizedFrameResolution[1])
        self.resizedFrameDimensionInfoCalculated.emit(
            {
                "aspectRatio": aspectRatio,
                "resizedFrameResolution": resizedFrameResolution
            }
        )

    @pyqtSlot(dict)
    def onFrameTransformatorSettingsChanged(self, newSettings: Dict) -> None:
        logger.info("New frame transforamtor params: %s", newSettings)
        newFrameTransformParams = FrameTransformator.getTransfornmatorSettingsFromDict(newSettings)
        self.settings = newFrameTransformParams
        self.backgroundSubstractor = FrameTransforamtorFactory.get_background_substractor(
            self.settings.backgroundSubstractorParams
        )
        self.contourCalculator.reset()
        logger.info("Frame transforamtor params changed")
          
class FrameTransforamtorFactory:
    @classmethod
    def get_frame_transformator(cls, settings: Dict) -> FrameTransformator:
        transformator_settings: FrameTransforamtorSettings = FrameTransformator.getTransfornmatorSettingsFromDict(settings)
        frame_simple_transofrmation_appyer = cls.get_simple_transforamtion_applyer(FrameTransformatorType.OPEN_CV)
        background_substractor = cls.get_background_substractor(transformator_settings.backgroundSubstractorParams)
        contour_calculator = OpenCVContourCalculator()
        return FrameTransformator(
            frame_simple_transofrmation_appyer,
            background_substractor,
            contour_calculator,
            transformator_settings
        )
    
    @classmethod
    def get_simple_transforamtion_applyer(cls, frame_transformator_type: FrameTransformatorType) -> FrameSimpleTransformationApplyer:
        if frame_transformator_type.OPEN_CV:
            return OpenCVSimpleTransformationApplyer()
        raise BaseException("Unknown frame transforamtor type provided to simple transformation applyer factory object")

    @classmethod
    def get_background_substractor(cls, bckg_substractor_settings: BackgroundSubstractingParams) -> BackgroundSubstractor:
        if bckg_substractor_settings.algorithmType == AlgorithmType.RUNNING_AVG:
            return RunninAverageBackgroundSubstractor(
                bckg_substractor_settings.runningAvgAlpha,
                bckg_substractor_settings.thresholdValue
            )
        elif bckg_substractor_settings.algorithmType == AlgorithmType.MIXTURE_OF_GAUSSIANS:
            return MixtureOfGaussiansBackgroundSubstractor(
                bckg_substractor_settings.gaussianMixtureHistory,
                bckg_substractor_settings.thresholdValue
            )
        elif bckg_substractor_settings.algorithmType == AlgorithmType.KNN:
            return KNNBackgroundSubstractor(
                bckg_substractor_settings.knnHistory,
                bckg_substractor_settings.thresholdValue
            )
        else:
            raise BaseException("Unknown algorithm type provided for background substraction creation")