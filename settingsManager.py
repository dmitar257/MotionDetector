from typing import Dict, List
from PyQt5.QtCore import QObject, pyqtSignal, QSettings, QVariant
from utils import AlgorithmType, createFolderIfNoExisting
import os
import logging

logger = logging.getLogger(__name__)

class ValueNotDefinedInINIError(Exception):
    pass

defaultSettings = {
    "frameTransformatorSettings":{
        "backgroundSubstractionSettings":{
            "algorithmType":AlgorithmType.RUNNING_AVG,
            "runningAvgThresholdBinValue" : 25,
            "gaussianMixtureThresholdValue": 16,
            "knnThresholdValue": 300,
            "runningAvgAlpha": 0.05,
            "gaussianMixtureHistory": 250,
            "runningAvgMinArea": 2000,
            "gaussianMixtureMinArea": 1000,
            "knnHistory": 500,
            "knnMinArea": 1000,
        },
        "resizeDimension": 500,
        "gaussianBlurKernelSize" : 15,
        "erosionKernelSize": 3,
        "erosionIterations": 4,
        "dilationKernelSize": 3,
        "dilationIterations": 8,  
    },
    "movementRecorderSettings":{
        "movementPresentThreshold": 10000,
        "movementAbsenceThreshold": 3000,
        "recordingsDir": os.path.join(os.getcwd(),'recordings')
    },
    "soundDetectorSettings":{
        "soundDetectionEnabled":True,
        "volumeThreshold":25
    },
    "movementLoggerSettings":{
        "loggingInterval":500,
        "scalingWidth": 800,
        "invertedXaxis":False,
        "loggingPath":"C:\\test",
        "oneLineLog": True
    },
    "cameraSettings":{
        "cameraIndex":0
    },
    "objectDetectionSettings":{
        "detectionEnabled": False,
        "confidenceThreshold": 0.5
    },
    "subscriberSettings":{
        "emailSubscribers": {
        },
        "broadcastToSubscribers": False
    }

}

class MotionDetectorSettings(QSettings):
    def value(self, key, raise_error = True):
        value = super().value(key)
        if value is None and raise_error:
            raise ValueNotDefinedInINIError(f"Value {key} is not defined in INI file")
        return value  

class SettingsManager(QObject):
    frameDetectionSettingsSet = pyqtSignal(dict)
    frameRecordingSettingsSet = pyqtSignal(dict)
    soundDetectionSettingsSet = pyqtSignal(dict)
    movementLoggerSettingsSet = pyqtSignal(dict)
    cameraSettingsSet = pyqtSignal(dict)
    objectDetectionSettingsSet = pyqtSignal(dict)
    emailSubscriberAdded = pyqtSignal(dict)
    emailNotificatioToggle = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.settings = MotionDetectorSettings("MasterWork","MotionDetector")
        self.currentSettings = self.loadSettings()
        self.initializeDirs()
        self.reloadRecordingPathIfNeeded()
        
    def initializeDirs(self) -> None:
        createFolderIfNoExisting(self.currentSettings["movementRecorderSettings"]["recordingsDir"])
        createFolderIfNoExisting(os.path.dirname(self.currentSettings["movementLoggerSettings"]["loggingPath"]))

    def getAllSettings(self, default: bool = False) -> Dict:
        if default:
            return defaultSettings
        return self.currentSettings
    
    def getFrameTransformationSettings(self, default: bool = False) -> Dict:
        if default:
            return defaultSettings["frameTransformatorSettings"]
        return self.currentSettings["frameTransformatorSettings"]
    
    def getHardDetectionFrameTransformationSettings(self) -> Dict:
        return {
            "backgroundSubstractionSettings":{
                "algorithmType":AlgorithmType.RUNNING_AVG,
                "runningAvgThresholdBinValue" : 20,
                "gaussianMixtureThresholdValue": 25,
                "knnThresholdValue": 500,
                "runningAvgAlpha": 0.03,
                "gaussianMixtureHistory": 250,
                "runningAvgMinArea": 10000,
                "gaussianMixtureMinArea": 2000,
                "knnHistory": 500,
                "knnMinArea": 2000,      
            },
            "resizeDimension": 500,
            "gaussianBlurKernelSize" : 15,
            "erosionKernelSize": 7,
            "erosionIterations": 5,
            "dilationKernelSize": 3,
            "dilationIterations": 8,  
        }
    
    def getMovementTrackerSettings(self, default: bool = False) -> Dict:
        if default:
            return defaultSettings["movementRecorderSettings"]
        return self.currentSettings["movementRecorderSettings"]
    
    def getSoundDetectionSettings(self, default: bool = False) -> Dict:
        if default:
            return defaultSettings["soundDetectorSettings"]
        return self.currentSettings["soundDetectorSettings"]

    def getMovementLoggerSettingss(self, default: bool = False) -> Dict:
        if default:
            return defaultSettings["movementLoggerSettings"]        
        return self.currentSettings["movementLoggerSettings"]
    
    def getCameraSettings(self) -> Dict:
        return self.currentSettings["cameraSettings"]
    
    def getObjectDetectionSettings(self, default: bool = False) -> Dict:
        if default:
            return defaultSettings["objectDetectionSettings"]  
        return self.currentSettings["objectDetectionSettings"]
    
    def getEmailSubscriberSettings(self) -> List:
        return self.currentSettings["subscriberSettings"]
    
    def setSoundDetectionSettings(self, soundDetectionSettings: Dict) -> Dict:
        self.currentSettings["soundDetectorSettings"] = soundDetectionSettings
        self.soundDetectionSettingsSet.emit(soundDetectionSettings)

    def setFrameTransformationSettings(self, motionDetectionSettings: Dict) -> None:
        self.currentSettings["frameTransformatorSettings"] = motionDetectionSettings
        self.frameDetectionSettingsSet.emit(motionDetectionSettings)
    
    def setFrameRecordingSettings(self, motionRecordingSettings: Dict) -> None:
        self.currentSettings["movementRecorderSettings"] = motionRecordingSettings
        self.frameRecordingSettingsSet.emit(motionRecordingSettings)
    
    def setMovementLoggerSettings(self, motionRecordingSettings: Dict) -> None:
        self.currentSettings["movementLoggerSettings"] = motionRecordingSettings
        self.movementLoggerSettingsSet.emit(motionRecordingSettings)
    
    def setCameraSettings(self, cameraSettings: Dict) -> None:
        self.currentSettings["cameraSettings"] = cameraSettings
        self.cameraSettingsSet.emit(cameraSettings)
    
    def setObjectDetectionSettings(self, objectDetectionSettings: Dict) -> None:
        self.currentSettings["objectDetectionSettings"] = objectDetectionSettings
        self.objectDetectionSettingsSet.emit(objectDetectionSettings)
    
    def addEmailSubscription(self, emailSubDict: Dict) -> None:
        self.currentSettings["subscriberSettings"]["emailSubscribers"][emailSubDict["email"]] = emailSubDict
        self.emailSubscriberAdded.emit(emailSubDict)

    def toggleEmailNotifications(self, toggle:bool) -> None:
        self.currentSettings["subscriberSettings"]["broadcastToSubscribers"] = toggle
        self.emailNotificatioToggle.emit(toggle)
    
    def saveSettings(self) -> None:
        self.saveSettingsToIniFile()
    
    def loadSettings(self) -> Dict:
        if self.valuesInIniExists():
            logger.info("Found settings .INI file")
            try:
                ini_settings = self.loadSettingsFromIniFile()
                logger.info("INI settings successfully loaded")
                return ini_settings
            except ValueNotDefinedInINIError as e:
                logger.warning(f"Ini file structure corrupted. Using default settings. Error details: {e}")
        return defaultSettings.copy()
    
    def valuesInIniExists(self) -> bool:
        return self.settings.value("configExists", raise_error = False)

    def saveSettingsToIniFile(self) -> None:
        self.settings.setValue("algorithmType", self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['algorithmType'])
        self.settings.setValue("gaussianBlurKernelSize",self.currentSettings['frameTransformatorSettings']['gaussianBlurKernelSize'])
        self.settings.setValue("resizeDimension",self.currentSettings['frameTransformatorSettings']['resizeDimension'])
        self.settings.setValue("runningAvgThresholdBinValue",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['runningAvgThresholdBinValue'])
        self.settings.setValue("gaussianMixtureThresholdValue",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['gaussianMixtureThresholdValue'])
        self.settings.setValue("knnThresholdValue",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['knnThresholdValue'])
        self.settings.setValue("erosionKernelSize",self.currentSettings['frameTransformatorSettings']['erosionKernelSize'])
        self.settings.setValue("erosionIterations",self.currentSettings['frameTransformatorSettings']['erosionIterations'])
        self.settings.setValue("dilationKernelSize",self.currentSettings['frameTransformatorSettings']['dilationKernelSize'])
        self.settings.setValue("dilationIterations",self.currentSettings['frameTransformatorSettings']['dilationIterations'])
        self.settings.setValue("runningAvgMinArea",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['runningAvgMinArea'])
        self.settings.setValue("runningAvgAlpha",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['runningAvgAlpha'])
        self.settings.setValue("gaussianMixtureMinArea",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['gaussianMixtureMinArea'])
        self.settings.setValue("gaussianMixtureHistory",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['gaussianMixtureHistory'])
        self.settings.setValue("knnHistory",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['knnHistory'])
        self.settings.setValue("knnMinArea",self.currentSettings['frameTransformatorSettings']['backgroundSubstractionSettings']['knnMinArea'])  
        self.settings.setValue("movementPresentThreshold", self.currentSettings['movementRecorderSettings']['movementPresentThreshold'])
        self.settings.setValue("movementAbsenceThreshold", self.currentSettings['movementRecorderSettings']['movementAbsenceThreshold'])
        self.settings.setValue("recordingsDir",self.currentSettings['movementRecorderSettings']['recordingsDir'])
        self.settings.setValue("volumeThreshold",self.currentSettings['soundDetectorSettings']['volumeThreshold'])
        self.settings.setValue("soundDetectionEnabled",self.currentSettings['soundDetectorSettings']['soundDetectionEnabled'])
        self.settings.setValue("loggingInterval",self.currentSettings["movementLoggerSettings"]['loggingInterval'])
        self.settings.setValue("scalingWidth",self.currentSettings["movementLoggerSettings"]['scalingWidth'])
        self.settings.setValue("invertedXaxis",self.currentSettings["movementLoggerSettings"]['invertedXaxis'])
        self.settings.setValue("loggingPath",self.currentSettings["movementLoggerSettings"]['loggingPath'])
        self.settings.setValue("oneLineLog",self.currentSettings["movementLoggerSettings"]['oneLineLog'])
        self.settings.setValue("cameraIndex",self.currentSettings["cameraSettings"]['cameraIndex'])
        self.settings.setValue("detectionEnabled",self.currentSettings["objectDetectionSettings"]['detectionEnabled'])
        self.settings.setValue("confidenceThreshold",self.currentSettings["objectDetectionSettings"]['confidenceThreshold'])
        self.settings.setValue("emailSubscribers", self.currentSettings["subscriberSettings"]["emailSubscribers"])
        self.settings.setValue("broadcastToSubscribers", self.currentSettings["subscriberSettings"]["broadcastToSubscribers"])
        self.settings.setValue("configExists", True)

    def loadSettingsFromIniFile(self) -> Dict:
        return {
            "frameTransformatorSettings":{
                "backgroundSubstractionSettings":{
                    "algorithmType": AlgorithmType(self.settings.value("algorithmType")),
                    "runningAvgThresholdBinValue" : self.settings.value("runningAvgThresholdBinValue"),
                    "gaussianMixtureThresholdValue" : self.settings.value("gaussianMixtureThresholdValue"),                   
                    "knnThresholdValue":self.settings.value("knnThresholdValue"),
                    "runningAvgAlpha": float(self.settings.value("runningAvgAlpha")),
                    "gaussianMixtureHistory": self.settings.value("gaussianMixtureHistory"),
                    "runningAvgMinArea": self.settings.value("runningAvgMinArea"),
                    "gaussianMixtureMinArea": self.settings.value("gaussianMixtureMinArea"),
                    "knnHistory":self.settings.value("knnHistory"),
                    "knnMinArea":self.settings.value("knnMinArea")       
                },
                "resizeDimension": self.settings.value("resizeDimension"),
                "gaussianBlurKernelSize" : self.settings.value("gaussianBlurKernelSize"),
                "erosionKernelSize": self.settings.value("erosionKernelSize"),
                "erosionIterations": self.settings.value("erosionIterations"),
                "dilationKernelSize": self.settings.value("dilationKernelSize"),
                "dilationIterations": self.settings.value("dilationIterations"),  
            },
            "movementRecorderSettings":{
                "movementPresentThreshold": self.settings.value("movementPresentThreshold"),
                "movementAbsenceThreshold": self.settings.value("movementAbsenceThreshold"),
                "recordingsDir": self.settings.value("recordingsDir")
            },
            "soundDetectorSettings":{
                "soundDetectionEnabled": True if self.settings.value('soundDetectionEnabled') in ['true','True'] else False,
                "volumeThreshold":self.settings.value("volumeThreshold")
            },
            "movementLoggerSettings":{
                "loggingInterval":self.settings.value("loggingInterval"),
                "scalingWidth": self.settings.value("scalingWidth"),
                "invertedXaxis": True if self.settings.value('invertedXaxis') in ['true','True'] else False,
                "loggingPath":self.settings.value("loggingPath"),
                "oneLineLog": True if self.settings.value("oneLineLog") in ['true','True'] else False
            },
            "cameraSettings":{
                "cameraIndex": self.settings.value("cameraIndex")
            },
            "objectDetectionSettings":{
                "detectionEnabled": True if self.settings.value('detectionEnabled') in ['true','True'] else False,
                "confidenceThreshold": float(self.settings.value("confidenceThreshold"))
            },
            "subscriberSettings": {
                "emailSubscribers": self.settings.value("emailSubscribers"),
                "broadcastToSubscribers": True if self.settings.value('broadcastToSubscribers') in ['true','True'] else False,
            }      
        }
    
    def reloadRecordingPathIfNeeded(self) -> None:
        if not os.path.exists(self.currentSettings["movementRecorderSettings"]["recordingsDir"]):
            self.currentSettings["movementRecorderSettings"]["recordingsDir"] = defaultSettings["movementRecorderSettings"]["recordingsDir"]

